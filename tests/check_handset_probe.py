#!/usr/bin/env python3
"""Pin the minimal API surface and lifecycle symbols of the handset probe."""

import json
from pathlib import Path
import subprocess
import sys
import zipfile

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
    if len(sys.argv) != 5:
        raise SystemExit("usage: check_handset_probe.py OBJECT ELF PACKAGE NM")
    object_path = Path(sys.argv[1])
    elf_path = Path(sys.argv[2])
    package_path = Path(sys.argv[3])
    nm = sys.argv[4]
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
    dynamic_binding = {
        "wipi_ktf_bind_kernel_interface",
        "__wipi_ktf_table_mc_knl",
        "__wipi_ktf_table_mc_grp",
    }
    missing_binding = dynamic_binding - elf_defined
    if missing_binding:
        raise AssertionError(
            "probe ELF lacks KTF dynamic-provider binding: "
            f"{sorted(missing_binding)}"
        )
    if b"WIPIC_knlInterface\0" not in elf_path.read_bytes():
        raise AssertionError("probe ELF lacks the KTF kernel provider lookup name")

    slot = profile["qpst_slot"]
    slot_aid = slot["aid"]
    if package_path.name != slot["payload_archive"]:
        raise AssertionError(
            f"QPST payload archive is {package_path.name!r}, "
            f"expected {slot['payload_archive']!r}"
        )
    with zipfile.ZipFile(package_path) as archive:
        if archive.namelist() != slot["payload_files"]:
            raise AssertionError(
                f"QPST payload files differ: {archive.namelist()!r}"
            )
        descriptor = archive.read("__adf__").decode("ascii")
    descriptor_fields = dict(
        line.partition(":")[::2]
        for line in descriptor.splitlines()
        if ":" in line
    )
    if descriptor_fields.get("AID") != slot_aid:
        raise AssertionError(f"QPST payload is not bound to slot {slot_aid}")
    print(
        f"verified SCH-W8300 probe: {len(expected)} public APIs and "
        f"{len(lifecycle)} source lifecycle callbacks; KTF binding is linked; "
        f"QPST slot is {slot_aid}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
