#!/usr/bin/env python3
"""Pin the minimal API surface and lifecycle symbols of the handset probe."""

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def symbols(nm: str, *arguments: str) -> set[str]:
    result = subprocess.run(
        [nm, *arguments],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        fields[-1]
        for line in result.stdout.splitlines()
        if len(fields := line.split()) >= 2
    }


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: check_handset_probe.py OBJECT ELF NM")
    object_path = Path(sys.argv[1])
    elf_path = Path(sys.argv[2])
    nm = sys.argv[3]
    profile = json.loads(
        (ROOT / "spec/install/sch-w8300-qpst-probe.json").read_text(
            encoding="utf-8"
        )
    )
    expected = set(profile["imports"]["required_public_apis"])
    undefined = symbols(nm, "--undefined-only", str(object_path))
    used_public = {name for name in undefined if name.startswith("MC_")}
    if used_public != expected:
        raise AssertionError(
            f"probe API surface differs: missing={sorted(expected - used_public)}, "
            f"extra={sorted(used_public - expected)}"
        )

    object_defined = symbols(nm, "--defined-only", str(object_path))
    lifecycle = {
        "startClet",
        "destroyClet",
        "pauseClet",
        "resumeClet",
        "paintClet",
        "handleCletEvent",
    }
    missing = lifecycle - object_defined
    if missing:
        raise AssertionError(f"probe object lacks lifecycle callbacks: {sorted(missing)}")
    elf_defined = symbols(nm, "--defined-only", str(elf_path))
    if "startClet" not in elf_defined:
        raise AssertionError("probe ELF does not keep its start callback")
    print(
        f"verified SCH-W8300 probe: {len(expected)} public APIs and "
        f"{len(lifecycle)} source lifecycle callbacks; start is linked"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
