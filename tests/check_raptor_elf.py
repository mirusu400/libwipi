#!/usr/bin/env python3
from pathlib import Path
import struct
import subprocess
import sys


image_path = Path(sys.argv[1])
objdump = sys.argv[2]
data = image_path.read_bytes()
if len(data) < 52 or data[:7] != b"\x7fELF\x01\x01\x01":
    raise AssertionError("binary.mod is not ELF32 little-endian")

header = struct.unpack_from("<16sHHIIIIIHHHHHH", data, 0)
e_type, e_machine, entry = header[1], header[2], header[4]
section_offset = header[6]
section_size, section_count, names_index = header[11], header[12], header[13]
if e_type != 2 or e_machine != 40:
    raise AssertionError(f"expected ARM ET_EXEC, got type={e_type} machine={e_machine}")
if section_size != 40 or section_count == 0 or names_index >= section_count:
    raise AssertionError("invalid ELF section table")

raw_sections = [
    struct.unpack_from("<IIIIIIIIII", data, section_offset + index * section_size)
    for index in range(section_count)
]
names_header = raw_sections[names_index]
names = data[names_header[4] : names_header[4] + names_header[5]]


def c_string(blob: bytes, offset: int) -> str:
    end = blob.find(b"\0", offset)
    if end < 0:
        raise AssertionError(f"unterminated string at {offset:#x}")
    return blob[offset:end].decode("ascii")


sections = {}
for raw in raw_sections:
    name = c_string(names, raw[0]) if raw[0] else ""
    sections[name] = {
        "type": raw[1],
        "flags": raw[2],
        "address": raw[3],
        "offset": raw[4],
        "size": raw[5],
    }

for name, address, flags in (
    (".rodata", 0x10000, 0x2),
    (".text", 0x20000, 0x6),
    (".data", 0x30000, 0x3),
):
    section = sections.get(name)
    if section is None or section["address"] != address or section["flags"] != flags:
        raise AssertionError(f"unexpected {name} placement or flags: {section}")

text = sections[".text"]
if entry & 1 != 0 or not (
    text["address"] <= entry < text["address"] + text["size"]
):
    raise AssertionError(
        f"shared ARAM/WIE ELF entry {entry:#x} is not aligned inside .text"
    )

metadata_section = sections.get(".raptor")
if metadata_section is None or metadata_section["address"] != 0 or metadata_section["flags"] != 0:
    raise AssertionError(".raptor must be non-allocated at address zero")
metadata = data[
    metadata_section["offset"] : metadata_section["offset"] + metadata_section["size"]
]
if metadata[:4] != b"RAPT" or len(metadata) < 0x30:
    raise AssertionError("invalid .raptor magic or size")
words = struct.unpack_from("<11I", metadata, 4)
version, declared_size, entry_offset = words[0], words[1], words[2]
checksum, abi_version, flags = words[4], words[5], words[6]
identifier_offset, dependencies_offset = words[8], words[10]
if version != 0x20050512 or declared_size != len(metadata):
    raise AssertionError("invalid .raptor version or declared size")
if entry_offset != (entry - text["address"]):
    raise AssertionError(".raptor entry offset disagrees with ELF entry")
if checksum != 0 or abi_version != 0x00010001 or flags != 1:
    raise AssertionError("invalid .raptor checksum, ABI version, or flags")
if c_string(metadata, identifier_offset) != "libwipi":
    raise AssertionError("invalid .raptor identifier")
if c_string(metadata, dependencies_offset) != "kernel dlet wipic":
    raise AssertionError("invalid .raptor dependencies")

data_section = sections[".data"]
clet = data[data_section["offset"] : data_section["offset"] + 0x30]
clet_words = struct.unpack("<12I", clet)
if clet_words[0] != 3 or clet_words[3:6] != (0, 0, 0):
    raise AssertionError("invalid version-3 Clet descriptor header")
rodata = sections[".rodata"]
if not (rodata["address"] <= clet_words[2] < rodata["address"] + rodata["size"]):
    raise AssertionError("Clet name is not in initialized read-only data")
for callback in (clet_words[1], *clet_words[6:12]):
    if callback & 1 == 0 or not (
        text["address"] <= (callback & ~1) < text["address"] + text["size"]
    ):
        raise AssertionError(f"invalid Thumb Clet callback {callback:#x}")

disassembly = subprocess.run(
    [objdump, "-dr", str(image_path)],
    check=True,
    text=True,
    stdout=subprocess.PIPE,
).stdout
start_label = disassembly.find("<_start>:")
next_label = disassembly.find("\n\n", start_label)
start = disassembly[start_label : None if next_label < 0 else next_label]
for fragment in ("#133", "lsls", "str", "[r0, r2]"):
    if fragment not in start:
        raise AssertionError(f"_start does not write dependency slot +0x214: {fragment}")

print(
    f"verified Raptor ELF, metadata, dependency slot, and 12-word Clet descriptor ({len(data)} bytes)"
)
