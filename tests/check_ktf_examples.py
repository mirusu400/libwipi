#!/usr/bin/env python3
"""Inspect every checked-in KTF example build and its raw ARM image."""

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CHECK_IMAGE = ROOT / "tests/check_ktf_image.py"
PACKAGER = ROOT / "tools/package_ktf.py"


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_ktf_examples.py OBJDUMP NM")
    objdump, nm = sys.argv[1:]
    manifest = json.loads(
        (ROOT / "examples/sdk-lab-ktf.json").read_text(encoding="utf-8")
    )
    packages = [ROOT / example["package"] for example in manifest["examples"]]
    packages.extend(
        [
            ROOT / "build/wipi-1.2.1/ktf-samsung/aram-ktf/examples/hello/libwipi-hello.zip",
            ROOT / "build/wipi-1.2.1/ktf-samsung/aram-ktf/examples/conformance/libwipi-conformance.zip",
            ROOT / "examples/template/build/wipi-1.2.1/ktf-samsung/aram-ktf/libwipi-starter.zip",
            ROOT / "examples/platformer/build/wipi-1.2.1/ktf-samsung/aram-ktf/libwipi-sky-hopper.zip",
        ]
    )
    for package in packages:
        directory = package.parent
        elf = directory / ("binary.mod" if directory.parts[-2:] in {
            ("examples", "hello"), ("examples", "conformance")
        } else "client.elf")
        client = directory / "client.bin"
        subprocess.run(
            [sys.executable, str(PACKAGER), "--inspect", str(package)],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            [sys.executable, str(CHECK_IMAGE), str(elf), str(client), objdump, nm],
            cwd=ROOT,
            check=True,
        )
    print(f"verified {len(packages)} KTF example packages and raw images")
    return 0


if __name__ == "__main__":
    sys.exit(main())
