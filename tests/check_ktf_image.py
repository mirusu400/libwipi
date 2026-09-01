#!/usr/bin/env python3
"""Pin the KTF raw-image entry, BSS placement, and bootstrap structures."""

from pathlib import Path
import struct
import subprocess
import sys


IMAGE_BASE = 0x00100000


def run(*arguments: str) -> str:
    return subprocess.run(
        list(arguments),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).stdout


def symbols(nm: str, elf: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for line in run(nm, "-a", "-P", str(elf)).splitlines():
        fields = line.split()
        if len(fields) >= 3:
            try:
                result[fields[0]] = int(fields[2], 16)
            except ValueError:
                pass
    return result


def word(image: bytes, address: int) -> int:
    offset = address - IMAGE_BASE
    if offset < 0 or offset + 4 > len(image):
        raise AssertionError(f"word 0x{address:08x} is outside raw image")
    return struct.unpack_from("<I", image, offset)[0]


def main() -> int:
    if len(sys.argv) != 5:
        raise SystemExit("usage: check_ktf_image.py ELF CLIENT OBJDUMP NM")
    elf = Path(sys.argv[1])
    client = Path(sys.argv[2])
    objdump = sys.argv[3]
    nm = sys.argv[4]

    if elf.read_bytes()[:4] != b"\x7fELF":
        raise AssertionError("KTF link output is not ELF")
    image = client.read_bytes()
    if not image:
        raise AssertionError("KTF raw client image is empty")
    names = symbols(nm, elf)
    required = {
        "_start",
        "__image_end",
        "__bss_start",
        "__bss_end",
        "__wipi_bss_size",
        "__wipi_ktf_wipi_exe",
        "__wipi_ktf_exe_interface",
        "__wipi_ktf_exe_functions",
        "__wipi_ktf_main_class",
        "__wipi_ktf_interface_init",
        "__wipi_ktf_executable_init",
        "__wipi_ktf_get_class",
        "__wipi_ktf_java_constructor",
        "__wipi_ktf_java_start_app",
    }
    missing = sorted(required.difference(names))
    if missing:
        raise AssertionError(f"KTF ELF is missing symbols: {missing}")
    if names["_start"] != IMAGE_BASE:
        raise AssertionError(f"KTF entry = 0x{names['_start']:08x}")
    if names["__image_end"] != IMAGE_BASE + len(image):
        raise AssertionError(
            "raw image length does not end at __image_end: "
            f"0x{names['__image_end']:08x} != 0x{IMAGE_BASE + len(image):08x}"
        )
    if names["__bss_start"] != names["__image_end"]:
        raise AssertionError("KTF BSS is not adjacent to the raw image")
    if names["__bss_end"] - names["__bss_start"] != names["__wipi_bss_size"]:
        raise AssertionError("KTF BSS size symbol does not match its bounds")

    executable = names["__wipi_ktf_wipi_exe"]
    interface = names["__wipi_ktf_exe_interface"]
    functions = names["__wipi_ktf_exe_functions"]
    if word(image, executable) != interface:
        raise AssertionError("WipiExe does not point at ExeInterface")
    if word(image, executable + 5 * 4) != names["__wipi_ktf_executable_init"] | 1:
        raise AssertionError("WipiExe init slot is not pinned")
    if word(image, interface) != functions:
        raise AssertionError("ExeInterface does not point at its function table")
    if word(image, functions + 2 * 4) != names["__wipi_ktf_interface_init"] | 1:
        raise AssertionError("ExeInterface init slot is not pinned")
    if word(image, interface + 2 * 4) == 1:
        candidate_required = {
            "__wipi_ktf_executable_fini",
            "__wipi_ktf_get_state",
            "__wipi_ktf_set_state",
            "__wipi_ktf_contains_address",
        }
        candidate_missing = sorted(candidate_required.difference(names))
        if candidate_missing:
            raise AssertionError(
                f"device-candidate ELF is missing symbols: {candidate_missing}"
            )
        if word(image, functions + 5 * 4) != names["__wipi_ktf_get_class"] | 1:
            raise AssertionError("device-candidate class slot is not +0x14")
        if word(image, executable + 4 * 4) != names["__wipi_ktf_executable_init"] | 1:
            raise AssertionError("device-candidate WipiExe +0x10 is not active")
        if word(image, executable + 8 * 4) != names["__wipi_ktf_executable_fini"] | 1:
            raise AssertionError("device-candidate WipiExe +0x20 is not active")
    elif word(image, functions + 4 * 4) != names["__wipi_ktf_get_class"] | 1:
        raise AssertionError("ExeInterface class slot is not pinned")

    disassembly = run(objdump, "-d", str(elf)).lower()
    start_marker = f"<{('_start')}>:"
    if start_marker not in disassembly:
        raise AssertionError("KTF bootstrap is absent from disassembly")
    start_body = disassembly.split(start_marker, 1)[1].split("\n\n", 1)[0]
    for instruction in ("str", "bx"):
        if instruction not in start_body:
            raise AssertionError(f"KTF bootstrap does not contain {instruction}")
    print(
        f"KTF image verified: {len(image)} bytes, "
        f"BSS {names['__wipi_bss_size']} bytes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
