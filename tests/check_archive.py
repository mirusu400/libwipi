#!/usr/bin/env python3
import csv
import json
from pathlib import Path
import subprocess
import sys


archive = Path(sys.argv[1])
nm = sys.argv[2]
profile = sys.argv[3] if len(sys.argv) > 3 else "ktf-samsung"
install_profile = sys.argv[4] if len(sys.argv) > 4 else "aram-wie-raptor"
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
    if install_profile not in {"aram-raptor", "aram-wie-raptor"}:
        raise AssertionError(f"unknown LGT install profile: {install_profile}")
    install = json.loads(
        (root / "spec" / "install" / f"{install_profile}.json").read_text(
            encoding="utf-8"
        )
    )
    if install.get("id") != install_profile:
        raise AssertionError("install profile identity does not match its filename")
    required.update(install["imports"]["confirmed_public_methods"])
    required.update(
        {
            "_start",
            "__wipi_lgt_clet",
            "__wipi_lgt_environment",
            "__wipi_lgt_resolver",
        }
    )
elif profile == "skt-samsung-sch-w830-dl21":
    skt_profile = json.loads(
        (root / "spec/profiles/skt-samsung-sch-w830-dl21.json").read_text(
            encoding="utf-8"
        )
    )
    with (root / skt_profile["bindings"]).open(
        encoding="utf-8", newline=""
    ) as stream:
        bindings = list(csv.DictReader(stream))
    catalog = {row["name"]: row for row in rows}
    eligible = {
        binding["name"]
        for binding in bindings
        if catalog[binding["name"]]["abi_class"] != "variadic-unverified"
    }
    required.update(eligible)
    table_symbols = {
        row["name"] for row in rows if row["implementation"] == "table"
    }
    unexpected = sorted((table_symbols - eligible) & defined)
    if unexpected:
        raise AssertionError(f"unverified SKT table symbols were defined: {unexpected}")
    if len(eligible) != skt_profile["coverage"]["generated_table_veneers"]:
        raise AssertionError("SKT archive coverage metadata is stale")
else:
    raise AssertionError(f"unknown archive profile: {profile}")

for name in required:
    if name not in defined:
        raise AssertionError(f"archive does not define {name}")
for name in ("MC_knlPrintk", "MC_knlSprintk", "MC_knlExecute"):
    if name in defined:
        raise AssertionError(f"unverified variadic symbol was defined: {name}")

print(
    f"verified deterministic {profile}/{install_profile} archive ({member_count} members, "
    f"{len(defined)} definitions)"
)
