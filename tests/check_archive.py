#!/usr/bin/env python3
import csv
import json
from pathlib import Path
import subprocess
import sys


archive = Path(sys.argv[1])
nm = sys.argv[2]
profile = sys.argv[3] if len(sys.argv) > 3 else "ktf-samsung"
raw_archive = archive.read_bytes()
if not raw_archive.startswith(b"!<arch>\n"):
    raise AssertionError("library is not a System V archive")
offset = 8
member_count = 0
while offset < len(raw_archive):
    header = raw_archive[offset : offset + 60]
    if len(header) != 60 or header[58:60] != b"`\n":
        raise AssertionError(f"invalid archive member header at {offset:#x}")
    for field, label in ((header[16:28], "timestamp"), (header[28:34], "uid"),
                         (header[34:40], "gid")):
        if field.strip() not in (b"", b"0"):
            raise AssertionError(
                f"non-deterministic archive {label}: {field!r}"
            )
    try:
        size = int(header[48:58].strip() or b"0")
    except ValueError as error:
        raise AssertionError(f"invalid archive member size at {offset:#x}") from error
    offset += 60 + size + (size & 1)
    member_count += 1
if offset != len(raw_archive) or member_count == 0:
    raise AssertionError("invalid or empty archive")

result = subprocess.run(
    [nm, "--defined-only", str(archive)],
    check=True,
    text=True,
    stdout=subprocess.PIPE,
)
defined = {
    fields[-1]
    for line in result.stdout.splitlines()
    if len(fields := line.split()) >= 2
}

root = Path(__file__).resolve().parents[1]
with (root / "spec/wipi-1.2.1/api.csv").open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream))

local = {row["name"] for row in rows if row["implementation"] == "local"}
missing_local = sorted(local - defined)
if missing_local:
    raise AssertionError(f"missing local CSTDLIB symbols: {missing_local}")

required = {"MC_knlSetTimer", "MC_grpFillRect"}
if profile == "ktf-samsung":
    required.add("MC_fsOpen")
elif profile == "lgt-raptor":
    install = json.loads(
        (root / "spec/install/aram-wie-raptor.json").read_text(encoding="utf-8")
    )
    required.update(install["imports"]["confirmed_public_methods"])
    required.update(
        {
            "_start",
            "__wipi_lgt_clet",
            "__wipi_lgt_environment",
            "__wipi_lgt_resolver",
        }
    )
else:
    raise AssertionError(f"unknown archive profile: {profile}")

for name in required:
    if name not in defined:
        raise AssertionError(f"archive does not define {name}")
for name in ("MC_knlPrintk", "MC_knlSprintk", "MC_knlExecute"):
    if name in defined:
        raise AssertionError(f"unverified variadic symbol was defined: {name}")

print(
    f"verified deterministic {profile} archive ({member_count} members, "
    f"{len(defined)} definitions)"
)
