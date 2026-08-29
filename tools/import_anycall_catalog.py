#!/usr/bin/env python3
"""Import reviewed WIPI API facts into libwipi's standalone catalog."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "spec" / "wipi-1.2.1" / "api.csv"

OUTPUT_FIELDS = (
    "ordinal",
    "family",
    "name",
    "prototype",
    "implementation",
    "abi_class",
    "ktf_samsung_confidence",
    "ktf_samsung_selector_kind",
    "ktf_samsung_slot",
    "evidence",
)

SELECTOR_CONFIDENCE = {
    "confirmed_firmware_selector": "confirmed",
    "candidate_selector": "candidate",
}


def selector_confidence(selector_state: str) -> str:
    try:
        return SELECTOR_CONFIDENCE[selector_state]
    except KeyError as error:
        raise ValueError(
            f"unknown selector_state: {selector_state!r}"
        ) from error


def abi_class(name: str, prototype: str, family: str) -> str:
    if family == "CSTDLIB":
        if "..." in prototype:
            raise ValueError(f"unexpected variadic CSTDLIB prototype: {name}")
        if "double" in prototype or "long long" in prototype:
            return "local-scalar64"
        return "local-word"
    if name == "MC_knlSetTimer":
        return "aapcs-to-packed-i64"
    if "..." in prototype:
        return "variadic-unverified"
    if prototype.startswith("M_Int64 "):
        return "return-i64"
    return "word-tail"


def import_rows(source: Path) -> list[dict[str, str]]:
    with source.open("r", encoding="utf-8-sig", newline="") as stream:
        source_rows = list(csv.DictReader(stream))

    required = {
        "ordinal",
        "family",
        "api",
        "c_prototype",
        "selector_state",
        "selector_kind",
        "slot",
        "c_source_file",
        "c_start_line",
    }
    if not source_rows:
        raise ValueError("source catalog is empty")
    missing = required.difference(source_rows[0])
    if missing:
        raise ValueError(f"source catalog is missing columns: {sorted(missing)}")

    rows: list[dict[str, str]] = []
    for source_row in source_rows:
        family = source_row["family"].strip()
        name = source_row["api"].strip()
        prototype = source_row["c_prototype"].strip()
        selector_state = source_row["selector_state"].strip()
        confidence = selector_confidence(selector_state)
        implementation = "local" if family == "CSTDLIB" else "table"
        slot = source_row["slot"].strip()
        if not re.fullmatch(r"\+0x[0-9a-fA-F]+", slot):
            raise ValueError(f"invalid slot for {name}: {slot!r}")
        evidence = (
            f"anycall_magichole:{source_row['c_source_file'].strip()}:"
            f"{source_row['c_start_line'].strip()}"
        )
        rows.append(
            {
                "ordinal": str(int(source_row["ordinal"])),
                "family": family,
                "name": name,
                "prototype": prototype,
                "implementation": implementation,
                "abi_class": abi_class(name, prototype, family),
                "ktf_samsung_confidence": confidence,
                "ktf_samsung_selector_kind": source_row["selector_kind"].strip(),
                "ktf_samsung_slot": slot.lower(),
                "evidence": evidence,
            }
        )

    ordinals = [int(row["ordinal"]) for row in rows]
    if ordinals != list(range(1, 240)):
        raise ValueError("source ordinals must be exactly 1..239 in order")
    if len({row["name"] for row in rows}) != 239:
        raise ValueError("source API names are not unique")
    confirmed = sum(
        row["ktf_samsung_confidence"] == "confirmed" for row in rows
    )
    candidates = [
        row for row in rows if row["ktf_samsung_confidence"] == "candidate"
    ]
    if confirmed != 229 or len(candidates) != 10:
        raise ValueError(
            f"unexpected evidence split: confirmed={confirmed}, "
            f"candidate={len(candidates)}"
        )
    if any(row["family"] != "CSTDLIB" for row in candidates):
        raise ValueError("all current candidate selectors must be CSTDLIB")
    return rows


def write_catalog(output: Path, rows: list[dict[str, str]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=OUTPUT_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    rows = import_rows(source)
    write_catalog(output, rows)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"imported {len(rows)} APIs to {output}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
