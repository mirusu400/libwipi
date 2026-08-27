#!/usr/bin/env python3
from pathlib import Path
import re
import sys


def function_block(disassembly: str, name: str) -> str:
    match = re.search(rf"^[0-9a-f]+ <{re.escape(name)}>:\s*$", disassembly, re.M)
    if match is None:
        raise AssertionError(f"missing disassembly for {name}")
    next_section = disassembly.find("\nDisassembly of section ", match.end())
    return disassembly[match.end() : None if next_section < 0 else next_section]


def require_immediate(block: str, value: int, name: str) -> None:
    if not re.search(rf"adds?\s+r0,\s*#(?:{value}|0x{value:x})\b", block):
        raise AssertionError(f"{name}: missing r0 slot immediate {value:#x}")


path = Path(sys.argv[1])
text = path.read_text()
symbols = re.findall(r"^[0-9a-f]+ <(MC_[A-Za-z0-9_]+)>:\s*$", text, re.M)
if len(symbols) != 205 or len(set(symbols)) != 205:
    raise AssertionError(f"expected 205 unique veneers, found {len(set(symbols))}")

timer = function_block(text, "MC_knlSetTimer")
for pattern, description in (
    (r"movs?\s+r1,\s*r2", "timeout low word r2 -> r1"),
    (r"movs?\s+r2,\s*r3", "timeout high word r3 -> r2"),
    (r"ldr\s+r3,\s*\[sp(?:,\s*#0)?\]", "stack parm -> r3"),
):
    if re.search(pattern, timer) is None:
        raise AssertionError(f"MC_knlSetTimer: missing {description}")
require_immediate(timer, 0x68, "MC_knlSetTimer")
if "__wipi_ktf_table_mc_knl" not in timer:
    raise AssertionError("MC_knlSetTimer: missing MC_KNL table relocation")

for name, slot in (
    ("MC_knlCreateSharedBuf", 0x3C),
    ("MC_knlGetSharedBuf", 0x40),
    ("MC_knlGetSharedBufSize", 0x44),
    ("MC_knlResizeSharedBuf", 0x48),
    ("MC_knlDestroySharedBuf", 0x4C),
):
    require_immediate(function_block(text, name), slot, name)

print(f"verified {len(symbols)} Thumb veneers and pinned special ABI slots")
