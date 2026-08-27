#!/usr/bin/env python3
"""Create and inspect deterministic ARAM/WIE Raptor application packages."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile


FIXED_TIME = (1980, 1, 1, 0, 0, 0)
MANIFEST = b"Manifest-Version: 1.0\r\nCreated-By: libwipi\r\n\r\n"


def safe_identifier(value: str, field: str) -> str:
    encoded = value.encode("ascii", errors="strict")
    if (
        not encoded
        or len(encoded) > 255
        or any(character < 0x21 or character > 0x7E for character in encoded)
        or any(character in value for character in "/\\:")
        or value in {".", ".."}
    ):
        raise ValueError(f"unsafe {field}: {value!r}")
    return value


def safe_archive_name(value: str) -> str:
    if not value or "\\" in value or ":" in value or value.startswith("/"):
        raise ValueError(f"unsafe archive path: {value!r}")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe archive path: {value!r}")
    normalized = path.as_posix()
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
    if len(names) != len(set(names)):
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


def descriptor(aid: str, pid: str, name: str, version: str, vendor: str) -> bytes:
    safe_identifier(aid, "AID")
    safe_identifier(pid, "PID")
    if "\r" in name or "\n" in name or not name:
        raise ValueError(f"unsafe Name: {name!r}")
    if "\r" in version or "\n" in version or not version:
        raise ValueError(f"unsafe version: {version!r}")
    if "\r" in vendor or "\n" in vendor or not vendor:
        raise ValueError(f"unsafe vendor: {vendor!r}")
    return (
        f"PID:{pid}\r\n"
        f"AID:{aid}\r\n"
        f"Name:{name}\r\n"
        f"Ver:{version}\r\n"
        "MClass:Clet\r\n"
        f"Vdr:{vendor}\r\n"
    ).encode("ascii", errors="strict")


def require_elf(data: bytes) -> None:
    if len(data) < 4 or data[:4] != b"\x7fELF":
        raise ValueError("binary.mod is not an ELF image")


def build_package(args: argparse.Namespace) -> None:
    if args.output is None:
        raise ValueError("--output is required with --binary")
    binary_path = Path(args.binary)
    if not binary_path.is_file():
        raise ValueError(f"binary is not a file: {binary_path}")
    binary = binary_path.read_bytes()
    require_elf(binary)
    aid = safe_identifier(args.aid, "AID")
    resources = sorted((parse_resource(item) for item in args.resource), key=lambda x: x[0])
    reserved = {"META-INF/MANIFEST.MF", "binary.mod"}
    if any(name in reserved for name, _ in resources):
        raise ValueError("unsafe resource path collides with package metadata")
    jar = make_zip(
        [("META-INF/MANIFEST.MF", MANIFEST), ("binary.mod", binary), *resources]
    )
    outer = make_zip(
        [
            (
                "app_info",
                descriptor(aid, args.pid, args.name, args.version, args.vendor),
            ),
            (f"{aid}.jar", jar),
        ]
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(outer)
    print(f"packaged {output} ({len(outer)} bytes)")


def checked_entries(archive: zipfile.ZipFile) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for info in archive.infolist():
        name = safe_archive_name(info.filename)
        if info.is_dir() or name in result:
            raise ValueError(f"unsafe duplicate or directory archive path: {name!r}")
        result[name] = archive.read(info)
    return result


def inspect_package(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as outer_archive:
        outer = checked_entries(outer_archive)
    if "app_info" not in outer:
        raise ValueError("package has no app_info")
    fields: dict[str, str] = {}
    for line in outer["app_info"].decode("ascii").splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key] = value
    aid = safe_identifier(fields.get("AID", ""), "AID")
    jar_name = f"{aid}.jar"
    if jar_name not in outer:
        raise ValueError(f"package has no AID-named JAR: {jar_name}")
    with zipfile.ZipFile(io.BytesIO(outer[jar_name])) as inner_archive:
        inner = checked_entries(inner_archive)
    module = "binary.mod"
    if module not in inner:
        raise ValueError("application JAR has no binary.mod")
    require_elf(inner[module])
    resources = sorted(
        name
        for name in inner
        if name not in {module, "META-INF/MANIFEST.MF"}
    )
    return {
        "aid": aid,
        "pid": fields.get("PID", ""),
        "main_class": fields.get("MClass", ""),
        "jar": jar_name,
        "module": module,
        "resources": resources,
        "module_size": len(inner[module]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--binary")
    mode.add_argument("--inspect")
    parser.add_argument("--output")
    parser.add_argument("--aid", default="libwipi-demo")
    parser.add_argument("--pid", default="libwipi")
    parser.add_argument("--name", default="libwipi demo")
    parser.add_argument("--version", default="01.00.00")
    parser.add_argument("--vendor", default="libwipi")
    parser.add_argument("--resource", action="append", default=[])
    args = parser.parse_args()
    try:
        if args.inspect:
            print(
                json.dumps(
                    inspect_package(Path(args.inspect)),
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            build_package(args)
        return 0
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
