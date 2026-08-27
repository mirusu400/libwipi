#!/usr/bin/env python3
from pathlib import Path
import json
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


def require_u16(block: str, register: str, value: int) -> None:
    if value <= 0xFF:
        require_number(block, "movs", register, value)
        return
    require_number(block, "movs", register, value >> 8)
    require_number(block, "lsls", register, 8)
    if value & 0xFF:
        require_number(block, "adds", register, value & 0xFF)


text = Path(sys.argv[1]).read_text(encoding="utf-8")
install_id = sys.argv[2] if len(sys.argv) > 2 else "aram-wie-raptor"
if install_id not in {"aram-raptor", "aram-wie-raptor"}:
    raise AssertionError(f"unknown LGT install profile: {install_id}")
root = Path(__file__).resolve().parents[1]
contract = json.loads(
    (root / "spec" / "install" / f"{install_id}.json").read_text(
        encoding="utf-8"
    )
)
methods = contract["imports"]["confirmed_public_methods"]
method_overrides = contract["imports"].get("aram_method_overrides", {})
return_overrides = contract["imports"].get("return_overrides", {})
symbols = re.findall(r"^[0-9a-f]+ <(MC_[A-Za-z0-9_]+)>:\s*$", text, re.M)
if set(symbols) != set(methods) or len(symbols) != len(methods):
    raise AssertionError(
        f"expected {len(methods)} exact LGT veneers, found {len(set(symbols))}"
    )
if re.search(r"\bblx\b", text):
    raise AssertionError("ARMv4T veneer contains an unsupported BLX instruction")

for name in symbols:
    block = function_block(text, name)
    require_u16(block, "r0", int(contract["imports"]["module"], 0))
    require_u16(block, "r1", int(methods[name], 0))
    common_patterns = (
        (r"push\s+\{r0,\s*r1,\s*r2,\s*r3,\s*r4,\s*lr\}", "argument save"),
        (r"ldr\s+r3,\s*\[r3,\s*#4\]", "resolver +4 load"),
        (r"\bbl(?:\.n)?\b", "ARMv4T indirect-call thunk branch"),
        (r"bx\s+r3", "ARMv4T indirect-call thunk"),
    )
    for pattern, description in common_patterns:
        if re.search(pattern, block) is None:
            raise AssertionError(f"{name}: missing {description}")
    if name not in return_overrides:
        for pattern, description in (
            (r"ldr\s+r4,\s*\[sp,\s*#20\]", "saved LR load"),
            (r"pop\s+\{r0,\s*r1,\s*r2,\s*r3,\s*r4\}", "argument restore"),
            (r"add\s+sp,\s*#4", "saved LR discard"),
            (r"bx\s+ip", "provider tail call"),
        ):
            if re.search(pattern, block) is None:
                raise AssertionError(f"{name}: missing {description}")

timer = function_block(text, "MC_knlSetTimer")
require_u16(timer, "r1", int(methods["MC_knlSetTimer"], 0))
for pattern, description in (
    (r"movs?\s+r1,\s*r2", "timeout low word r2 -> r1"),
    (r"movs?\s+r2,\s*r3", "timeout high word r3 -> r2"),
    (r"ldr\s+r3,\s*\[sp(?:,\s*#0)?\]", "stack parm -> r3"),
):
    if re.search(pattern, timer) is None:
        raise AssertionError(f"MC_knlSetTimer: missing {description}")

media = function_block(text, "MC_mdaPlay")
require_u16(media, "r1", int(methods["MC_mdaPlay"], 0))

backlight = function_block(text, "MC_miscBackLight")
require_u16(backlight, "r1", int(methods["MC_miscBackLight"], 0))

for name, encoded_aram_method in method_overrides.items():
    block = function_block(text, name)
    if "__wipi_lgt_environment" not in block:
        raise AssertionError(f"{name} does not select an environment ABI map")
    require_u16(block, "r1", int(encoded_aram_method, 0))
    require_u16(block, "r1", int(methods[name], 0))

for name, override in return_overrides.items():
    block = function_block(text, name)
    provider_success = override["provider_success"]
    public_success = override["public_success"]
    for pattern, description in (
        (r"pop\s+\{r0,\s*r1,\s*r2,\s*r3\}", "argument restore"),
        (rf"cmp\s+r0,\s*#{provider_success}", "provider success comparison"),
        (rf"movs\s+r0,\s*#{public_success}", "public success normalization"),
        (r"pop\s+\{r4\}", "callee register restore"),
        (r"pop\s+\{r1\}", "caller return restore"),
        (r"bx\s+r1", "caller return"),
    ):
        if re.search(pattern, block) is None:
            raise AssertionError(f"{name}: missing {description}")

print(
    f"verified {len(methods)} ARMv4T LGT veneers for {install_id}, "
    "environment import IDs, and timer shuffle"
)
