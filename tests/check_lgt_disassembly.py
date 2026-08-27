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


def require_number(block: str, instruction: str, register: str, value: int) -> None:
    repeated = rf"(?:{register},\s*)?" if instruction == "lsls" else ""
    pattern = (
        rf"{instruction}\s+{register},\s*{repeated}"
        rf"#(?:{value}|0x{value:x})\b"
    )
    if re.search(pattern, block) is None:
        raise AssertionError(
            f"missing {instruction} {register} immediate {value:#x}"
        )


text = Path(sys.argv[1]).read_text(encoding="utf-8")
symbols = re.findall(r"^[0-9a-f]+ <(MC_[A-Za-z0-9_]+)>:\s*$", text, re.M)
if len(symbols) != 59 or len(set(symbols)) != 59:
    raise AssertionError(f"expected 59 unique LGT veneers, found {len(set(symbols))}")
if re.search(r"\bblx\b", text):
    raise AssertionError("ARMv4T veneer contains an unsupported BLX instruction")

for name in symbols:
    block = function_block(text, name)
    require_number(block, "movs", "r0", 1)
    require_number(block, "lsls", "r0", 8)
    require_number(block, "adds", "r0", 0xFB)
    common_patterns = (
        (r"push\s+\{r0,\s*r1,\s*r2,\s*r3,\s*r4,\s*lr\}", "argument save"),
        (r"ldr\s+r3,\s*\[r3,\s*#4\]", "resolver +4 load"),
        (r"\bbl(?:\.n)?\b", "ARMv4T indirect-call thunk branch"),
        (r"bx\s+r3", "ARMv4T indirect-call thunk"),
    )
    for pattern, description in common_patterns:
        if re.search(pattern, block) is None:
            raise AssertionError(f"{name}: missing {description}")
    if name != "MC_grpGetDisplayInfo":
        for pattern, description in (
            (r"ldr\s+r4,\s*\[sp,\s*#20\]", "saved LR load"),
            (r"pop\s+\{r0,\s*r1,\s*r2,\s*r3,\s*r4\}", "argument restore"),
            (r"add\s+sp,\s*#4", "saved LR discard"),
            (r"bx\s+ip", "provider tail call"),
        ):
            if re.search(pattern, block) is None:
                raise AssertionError(f"{name}: missing {description}")

timer = function_block(text, "MC_knlSetTimer")
require_number(timer, "movs", "r1", 0x7B)
for pattern, description in (
    (r"movs?\s+r1,\s*r2", "timeout low word r2 -> r1"),
    (r"movs?\s+r2,\s*r3", "timeout high word r3 -> r2"),
    (r"ldr\s+r3,\s*\[sp(?:,\s*#0)?\]", "stack parm -> r3"),
):
    if re.search(pattern, timer) is None:
        raise AssertionError(f"MC_knlSetTimer: missing {description}")

media = function_block(text, "MC_mdaPlay")
require_number(media, "movs", "r1", 4)
require_number(media, "lsls", "r1", 8)
require_number(media, "adds", "r1", 0xBA)

backlight = function_block(text, "MC_miscBackLight")
require_number(backlight, "movs", "r1", 5)
require_number(backlight, "lsls", "r1", 8)
require_number(backlight, "adds", "r1", 0x78)

for name, aram_method, wie_method in (
    ("MC_grpCopyArea", 0xD6, 0xD7),
    ("MC_grpDrawArc", 0xD7, 0xD8),
    ("MC_grpFillArc", 0xD8, 0xD9),
    ("MC_grpDrawString", 0xD9, 0xDA),
    ("MC_grpGetRGBPixels", 0xDB, 0xDC),
    ("MC_grpSetRGBPixels", 0xDC, 0xDD),
):
    block = function_block(text, name)
    if "__wipi_lgt_environment" not in block:
        raise AssertionError(f"{name} does not select an environment ABI map")
    require_number(block, "movs", "r1", aram_method)
    require_number(block, "movs", "r1", wie_method)

display_info = function_block(text, "MC_grpGetDisplayInfo")
for pattern, description in (
    (r"pop\s+\{r0,\s*r1,\s*r2,\s*r3\}", "argument restore"),
    (r"cmp\s+r0,\s*#1", "WIE success comparison"),
    (r"movs\s+r0,\s*#0", "public success normalization"),
    (r"pop\s+\{r4\}", "callee register restore"),
    (r"pop\s+\{r1\}", "caller return restore"),
    (r"bx\s+r1", "caller return"),
):
    if re.search(pattern, display_info) is None:
        raise AssertionError(f"MC_grpGetDisplayInfo: missing {description}")

print("verified 59 ARMv4T LGT veneers, environment import IDs, and timer shuffle")
