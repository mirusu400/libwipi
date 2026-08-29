#!/usr/bin/env python3
"""Import only directly evidenced SCH-W830 DL21 WIPI-C bindings."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    ROOT.parent
    / "anycall_magichole"
    / "docs"
    / "maps"
    / "wipi_public_syscall_resolution_audit.csv"
)
DEFAULT_CATALOG = ROOT / "spec" / "wipi-1.2.1" / "api.csv"
DEFAULT_OUTPUT = (
    ROOT / "spec" / "profiles" / "skt-samsung-sch-w830-dl21-bindings.csv"
)
PINNED_SOURCE_REVISION = "ca5a91ad6392f62dd7428711e7a8dd9f621d3949"

OUTPUT_FIELDS = (
    "ordinal",
    "family",
    "name",
    "root_field",
    "slot",
    "confidence",
    "evidence",
)

# These bases require an SCH DAT import call or an equivalent raw SCH
# instruction proof. Provider-only SPH/KTF promotions are deliberately absent.
DIRECT_SCH_BASES = {
    "DAT/import table evidence and selector-boundary rechecks",
    "direct DAT import callsite and public-API-compatible ABI",
    "confirmed from 14 zero-argument raw calls and current-app-ID consumers",
    (
        "confirmed from exact raw import chain "
        "0x01AA1A7C..0x01AA1A98 and post-call pointer stores; "
        "Java Shared.createBuf byte-array method remains separate"
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def import_bindings(
    source: Path, catalog_path: Path, source_revision: str
) -> list[dict[str, str]]:
    source_rows = read_csv(source)
    catalog_rows = read_csv(catalog_path)
    if not source_rows:
        raise ValueError("SKT resolution source is empty")
    required = {
        "ordinal",
        "family",
        "api",
        "selector_identity",
        "selector_kind",
        "selector_confidence",
        "slot",
        "resolution_basis",
    }
    missing = required.difference(source_rows[0])
    if missing:
        raise ValueError(f"SKT resolution source is missing: {sorted(missing)}")

    catalog = {row["name"]: row for row in catalog_rows}
    bindings: list[dict[str, str]] = []
    for source_row in source_rows:
        if source_row["resolution_basis"] not in DIRECT_SCH_BASES:
            continue
        if source_row["family"] == "CSTDLIB":
            continue
        identity = source_row["selector_identity"]
        match = re.match(
            r"^0x01001000 field \+(0x[0-9a-fA-F]+)(?:\s*/|;)", identity
        )
        if match is None:
            raise ValueError(
                f"direct SCH row has no fixed-root field: {source_row['api']}"
            )
        if source_row["selector_kind"] != "WIPI_SYSCALL_KIND_DAT_IMPORT":
            raise ValueError(f"direct SCH row has wrong kind: {source_row['api']}")
        if source_row["selector_confidence"] != "WIPI_SYSCALL_CONF_CONFIRMED":
            raise ValueError(
                f"direct SCH row is not confirmed: {source_row['api']}"
            )

        name = source_row["api"]
        catalog_row = catalog.get(name)
        if catalog_row is None:
            raise ValueError(f"SKT binding is absent from the catalog: {name}")
        slot = source_row["slot"].lower()
        if catalog_row["implementation"] != "table":
            raise ValueError(f"SKT binding is not a table API: {name}")
        if (
            catalog_row["ordinal"] != source_row["ordinal"]
            or catalog_row["family"] != source_row["family"]
            or catalog_row["ktf_samsung_slot"] != slot
        ):
            raise ValueError(f"SKT/catalog binding mismatch: {name}")
        bindings.append(
            {
                "ordinal": str(int(source_row["ordinal"])),
                "family": source_row["family"],
                "name": name,
                "root_field": match.group(1).lower(),
                "slot": slot,
                "confidence": "confirmed",
                "evidence": (
                    f"anycall_magichole@{source_revision}:"
                    "docs/maps/wipi_public_syscall_resolution_audit.csv"
                    f"#ordinal={int(source_row['ordinal'])}"
                ),
            }
        )

    if len(bindings) != 71:
        raise ValueError(f"expected 71 direct SCH table bindings, got {len(bindings)}")
    if len({row["name"] for row in bindings}) != len(bindings):
        raise ValueError("direct SCH binding names are not unique")
    expected_families = {"MC_GRP": 27, "MC_FS": 16, "MC_NET": 10, "MC_KNL": 18}
    actual_families = {
        family: sum(row["family"] == family for row in bindings)
        for family in expected_families
    }
    if actual_families != expected_families:
        raise ValueError(f"direct SCH family counts changed: {actual_families}")
    return bindings


def write_bindings(output: Path, rows: list[dict[str, str]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-revision", default=PINNED_SOURCE_REVISION)
    args = parser.parse_args()

    rows = import_bindings(
        args.source.resolve(), args.catalog.resolve(), args.source_revision
    )
    write_bindings(args.output.resolve(), rows)
    digest = hashlib.sha256(args.output.resolve().read_bytes()).hexdigest()
    print(f"imported {len(rows)} direct SCH bindings to {args.output.resolve()}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
