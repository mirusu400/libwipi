#!/usr/bin/env python3
import csv
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ID = "skt-samsung-sch-w830-dl21"


def function_block(disassembly: str, name: str) -> str:
    match = re.search(rf"^[0-9a-f]+ <{re.escape(name)}>:\s*$", disassembly, re.M)
    if match is None:
        raise AssertionError(f"missing disassembly for {name}")
    next_section = disassembly.find("\nDisassembly of section ", match.end())
    return disassembly[match.end() : None if next_section < 0 else next_section]


def immediate_pattern(value: int) -> str:
    return rf"(?:{value}|0x{value:x})\b"


def require_field(block: str, value: int, name: str) -> None:
    if value == 0:
        plain_loads = re.findall(r"ldr\s+r0,\s*\[r0(?:,\s*#0)?\]", block)
        if len(plain_loads) < 3:
            raise AssertionError(f"{name}: missing root field +0x00 load")
        return
    if re.search(
        rf"ldr\s+r0,\s*\[r0,\s*#{immediate_pattern(value)}\]", block
    ) is None:
        raise AssertionError(f"{name}: missing root field {value:#x}")


def require_slot(block: str, value: int, name: str) -> None:
    if value == 0:
        return
    if re.search(
        rf"adds?\s+r0,\s*#{immediate_pattern(value)}", block
    ) is None:
        raise AssertionError(f"{name}: missing method slot {value:#x}")


path = Path(sys.argv[1])
text = path.read_text()
symbols = set(re.findall(r"^[0-9a-f]+ <(MC_[A-Za-z0-9_]+)>:\s*$", text, re.M))

with (ROOT / "spec/wipi-1.2.1/api.csv").open(
    encoding="utf-8", newline=""
) as stream:
    catalog = {row["name"]: row for row in csv.DictReader(stream)}
with (ROOT / "spec/profiles" / f"{PROFILE_ID}-bindings.csv").open(
    encoding="utf-8", newline=""
) as stream:
    bindings = list(csv.DictReader(stream))

eligible = {
    binding["name"]: binding
    for binding in bindings
    if catalog[binding["name"]]["abi_class"] != "variadic-unverified"
}
if symbols != set(eligible):
    raise AssertionError(
        f"SKT veneer symbols differ: missing={sorted(set(eligible) - symbols)}, "
        f"extra={sorted(symbols - set(eligible))}"
    )
if len(symbols) != 69:
    raise AssertionError(f"expected 69 exact-profile veneers, found {len(symbols)}")

for name, binding in eligible.items():
    block = function_block(text, name)
    if "01001000" not in block.lower():
        raise AssertionError(f"{name}: missing fixed import pointer 0x01001000")
    require_field(block, int(binding["root_field"], 16), name)
    require_slot(block, int(binding["slot"][1:], 16), name)
    if "__wipi_missing_import" not in block:
        raise AssertionError(f"{name}: missing explicit absent-import path")

timer = function_block(text, "MC_knlSetTimer")
for pattern, description in (
    (r"movs?\s+r1,\s*r2", "timeout low word r2 -> r1"),
    (r"movs?\s+r2,\s*r3", "timeout high word r3 -> r2"),
    (r"ldr\s+r3,\s*\[sp(?:,\s*#0)?\]", "stack parm -> r3"),
):
    if re.search(pattern, timer) is None:
        raise AssertionError(f"MC_knlSetTimer: missing {description}")

for unavailable in (
    "MC_grpPutPixel",
    "MC_fsSetMode",
    "MC_netSocketAccept",
    "MC_knlExecute",
    "MC_uicCreateApplicationContext",
    "MC_mdaClipCreate",
):
    if unavailable in symbols:
        raise AssertionError(f"unverified SKT method was generated: {unavailable}")

print("verified 69 SCH-W830 fixed-root veneers, every field/slot, and timer ABI")
