#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
OBJDUMP = sys.argv[1]
EXAMPLES = (
    "graphics-gallery",
    "memory-resource",
    "audio-player",
    "vibrate",
    "system-services",
    "image-pipeline",
    "network-lifecycle",
    "database-crud",
    "filesystem",
    "media-suite",
)

for example in EXAMPLES:
    binary = (
        ROOT
        / "examples"
        / example
        / "build/wipi-1.2.1/lgt-raptor/aram-raptor/binary.mod"
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tests/check_raptor_elf.py"),
            str(binary),
            OBJDUMP,
        ],
        cwd=ROOT,
        check=True,
    )

print(f"verified {len(EXAMPLES)} ARAM SDK example ELF files")
