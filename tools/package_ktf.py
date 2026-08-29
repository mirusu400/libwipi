#!/usr/bin/env python3
"""Create and inspect deterministic KTF WIPI distribution ZIPs."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile


FIXED_TIME = (1980, 1, 1, 0, 0, 0)
MANIFEST = b"Manifest-Version: 1.0\r\nCreated-By: libwipi\r\n\r\n"
MAX_BSS_SIZE = 256 << 20
NM_SYMBOL = "__wipi_bss_size"


def safe_identifier(value: str, field: str) -> str:
    encoded = value.encode("ascii", errors="strict")
    if (
        not encoded
        or len(encoded) > 255
        or any(character < 0x20 or character > 0x7E for character in encoded)
        or any(character in value for character in "/\\:")
        or value in {".", ".."}
    ):
        raise ValueError(f"unsafe {field}: {value!r}")
    return value


def safe_archive_name(value: str) -> str:
    if not value or "\\" in value or ":" in value or value.startswith("/"):
        raise ValueError(f"unsafe archive path: {value!r}")
    parsed = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in parsed.parts):
        raise ValueError(f"unsafe archive path: {value!r}")
    normalized = parsed.as_posix()
    if normalized != value or normalized.endswith("/"):
        raise ValueError(f"unsafe archive path: {value!r}")
    return normalized


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(safe_archive_name(name), FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def make_zip(entries: list[tuple[str, bytes]]) -> bytes:
    names = [safe_archive_name(name) for name, _ in entries]
    folded = [name.casefold() for name in names]
    if len(folded) != len(set(folded)):
        raise ValueError("unsafe duplicate archive path")
    output = io.BytesIO()
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, data in entries:
            archive.writestr(zip_info(name), data, compresslevel=9)
    return output.getvalue()


def parse_resource(value: str) -> tuple[str, bytes]:
    if "=" not in value:
        raise ValueError("resource must use SOURCE=ARCHIVE_PATH")
    source_text, destination = value.rsplit("=", 1)
    destination = safe_archive_name(destination)
    source = Path(source_text)
    if not source.is_file():
        raise ValueError(f"resource source is not a file: {source}")
    return destination, source.read_bytes()


def parse_bss_size(value: str) -> int:
    try:
        size = int(value, 0)
    except ValueError as error:
        raise ValueError(f"invalid BSS size: {value!r}") from error
    if size < 0 or size > MAX_BSS_SIZE:
        raise ValueError(f"BSS size is outside 0..{MAX_BSS_SIZE}: {size}")
    return size


def bss_size_from_elf(elf: Path, nm: str) -> int:
    if not elf.is_file():
        raise ValueError(f"ELF is not a file: {elf}")
    result = subprocess.run(
        [nm, "-P", str(elf)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    matches: list[int] = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[0] == NM_SYMBOL:
            matches.append(parse_bss_size("0x" + fields[2]))
    if len(matches) != 1:
        raise ValueError(
            f"ELF must define exactly one {NM_SYMBOL} symbol; found {len(matches)}"
        )
    return matches[0]


def parse_display_size(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([0-9]+)[x*]([0-9]+)", value)
    if match is None:
        raise ValueError(f"display size must use WIDTHxHEIGHT: {value!r}")
    width, height = (int(part) for part in match.groups())
    if not 1 <= width <= 4096 or not 1 <= height <= 4096:
        raise ValueError(f"display size is outside 1..4096: {value!r}")
    return width, height


def descriptor(
    aid: str,
    pid: str,
    name: str,
    version: str,
    vendor: str,
    main_class: str,
    display_size: tuple[int, int],
) -> bytes:
    safe_identifier(aid, "AID")
    safe_identifier(pid, "PID")
    safe_identifier(main_class, "MClass")
    for field, value in (("Name", name), ("Ver", version), ("Vdr", vendor)):
        safe_identifier(value, field)
    width, height = display_size
    return (
        f"PID:{pid}\r\n"
        f"AID:{aid}\r\n"
        f"Name:{name}\r\n"
        f"Ver:{version}\r\n"
        f"MClass:{main_class}\r\n"
        f"DisplaySize:{width}*{height}\r\n"
        f"Vdr:{vendor}\r\n"
    ).encode("ascii")


def checked_entries(archive: zipfile.ZipFile) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    folded: set[str] = set()
    for info in archive.infolist():
        name = safe_archive_name(info.filename)
        key = name.casefold()
        if info.is_dir() or key in folded:
            raise ValueError(f"unsafe duplicate or directory archive path: {name!r}")
        folded.add(key)
        result[name] = archive.read(info)
    return result


def descriptor_fields(data: bytes) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in data.decode("ascii").splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key] = value
    return fields


def inspect_package(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as outer_archive:
        outer = checked_entries(outer_archive)
    if "__adf__" not in outer:
        raise ValueError("package has no __adf__ descriptor")
    fields = descriptor_fields(outer["__adf__"])
    aid = safe_identifier(fields.get("AID", ""), "AID")
    pid = safe_identifier(fields.get("PID", ""), "PID")
    main_class = safe_identifier(fields.get("MClass", ""), "MClass")
    display_size = parse_display_size(fields.get("DisplaySize", ""))
    jar_name = f"{aid}.jar"
    if jar_name not in outer:
        raise ValueError(f"package has no AID-named JAR: {jar_name}")
    with zipfile.ZipFile(io.BytesIO(outer[jar_name])) as inner_archive:
        inner = checked_entries(inner_archive)
    clients = sorted(name for name in inner if name.startswith("client.bin"))
    if len(clients) != 1:
        raise ValueError(f"application JAR must have one client.bin image; found {len(clients)}")
    client_name = clients[0]
    suffix = client_name.removeprefix("client.bin")
    if not suffix or not suffix.isdecimal():
        raise ValueError(f"client image has invalid BSS suffix: {client_name!r}")
    bss_size = parse_bss_size(suffix)
    if not inner[client_name]:
        raise ValueError("client image is empty")
    resources = sorted(
        name
        for name in inner
        if name not in {client_name, "META-INF/MANIFEST.MF"}
    )
    return {
        "aid": aid,
        "pid": pid,
        "main_class": main_class,
        "display_size": list(display_size),
        "jar": jar_name,
        "client": client_name,
        "module": client_name,
        "bss_size": bss_size,
        "resources": resources,
        "client_size": len(inner[client_name]),
    }


def build_package(args: argparse.Namespace) -> None:
    if args.output is None:
        raise ValueError("--output is required with --client")
    client_path = Path(args.client)
    if not client_path.is_file():
        raise ValueError(f"client is not a file: {client_path}")
    client = client_path.read_bytes()
    if not client:
        raise ValueError("client image is empty")
    if args.bss_size is not None:
        bss_size = parse_bss_size(args.bss_size)
    elif args.elf is not None:
        bss_size = bss_size_from_elf(Path(args.elf), args.nm)
    else:
        raise ValueError("one of --bss-size or --elf is required")

    aid = safe_identifier(args.aid, "AID")
    resources = sorted((parse_resource(item) for item in args.resource), key=lambda item: item[0])
    client_name = f"client.bin{bss_size}"
    reserved = {"META-INF/MANIFEST.MF", client_name}
    if any(name in reserved or name.startswith("client.bin") for name, _ in resources):
        raise ValueError("unsafe resource path collides with package metadata")
    jar = make_zip(
        [("META-INF/MANIFEST.MF", MANIFEST), (client_name, client), *resources]
    )
    outer = make_zip(
        [
            (
                "__adf__",
                descriptor(
                    aid,
                    args.pid,
                    args.name,
                    args.version,
                    args.vendor,
                    args.main_class,
                    parse_display_size(args.display_size),
                ),
            ),
            (f"{aid}.jar", jar),
        ]
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(outer)
    print(f"packaged {output} ({len(outer)} bytes, BSS {bss_size})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--client")
    mode.add_argument("--inspect", type=Path)
    size = parser.add_mutually_exclusive_group()
    size.add_argument("--bss-size")
    size.add_argument("--elf")
    parser.add_argument("--nm", default="arm-none-eabi-nm")
    parser.add_argument("--output")
    parser.add_argument("--aid", default="libwipi-app")
    parser.add_argument("--pid", default="libwipi")
    parser.add_argument("--name", default="libwipi application")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--vendor", default="libwipi")
    parser.add_argument("--main-class", default="LibwipiClet")
    parser.add_argument("--display-size", default="240x320")
    parser.add_argument("--resource", action="append", default=[])
    args = parser.parse_args()
    try:
        if args.inspect is not None:
            print(json.dumps(inspect_package(args.inspect), indent=2, sort_keys=True))
        else:
            build_package(args)
    except (
        OSError,
        UnicodeError,
        ValueError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
