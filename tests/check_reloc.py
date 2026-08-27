#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys


image = Path(sys.argv[1])
nm = sys.argv[2]
result = subprocess.run(
    [nm, "--undefined-only", str(image)],
    check=True,
    text=True,
    stdout=subprocess.PIPE,
)
undefined = [line.split()[-1] for line in result.stdout.splitlines() if line.split()]
if undefined:
    raise AssertionError(f"relocatable example has undefined symbols: {undefined}")

print("verified relocatable example has no unresolved symbols")
