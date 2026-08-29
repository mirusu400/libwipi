#!/usr/bin/env python3
"""Run every libwipi KTF package through the ordinary ARAM probe path."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "spec/install/aram-ktf.json"
SUITE = ROOT / "examples/sdk-lab-ktf.json"
DEFAULT_PROBE = ROOT / ".cache" / (
    "aram-probe.exe" if os.name == "nt" else "aram-probe"
)


def command_output(arguments: list[str], cwd: Path) -> str:
    return subprocess.run(
        arguments,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()


def build_probe(aram_emu_root: Path, probe: Path) -> None:
    probe.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["go", "build", "-trimpath", "-o", str(probe), "./cmd/aram-probe"],
        cwd=aram_emu_root,
        check=True,
    )


def package_records() -> list[dict[str, object]]:
    suite = json.loads(SUITE.read_text(encoding="utf-8"))
    records = list(suite["examples"])
    records.extend(
        [
            {
                "id": "hello",
                "package": "build/wipi-1.2.1/ktf-samsung/aram-ktf/examples/hello/libwipi-hello.zip",
                "probe": {"slices": 1024},
            },
            {
                "id": "conformance",
                "package": "build/wipi-1.2.1/ktf-samsung/aram-ktf/examples/conformance/libwipi-conformance.zip",
                "probe": {"slices": 1024},
            },
            {
                "id": "template",
                "package": "examples/template/build/wipi-1.2.1/ktf-samsung/aram-ktf/libwipi-starter.zip",
                "probe": {"slices": 1024},
            },
            {
                "id": "platformer",
                "package": "examples/platformer/build/wipi-1.2.1/ktf-samsung/aram-ktf/libwipi-sky-hopper.zip",
                "probe": {"slices": 1024},
            },
        ]
    )
    return sorted(records, key=lambda record: str(record["id"]))


def run_probe(probe: Path, record: dict[str, object]) -> dict[str, object]:
    package = ROOT / str(record["package"])
    if not package.is_file():
        raise ValueError(f"KTF example package is missing: {package}")
    settings = record.get("probe", {})
    slices = int(settings.get("slices", 1024)) if isinstance(settings, dict) else 1024
    completed = subprocess.run(
        [
            str(probe),
            "-input",
            str(package),
            "-label",
            f"libwipi-ktf-{record['id']}",
            "-slices",
            str(slices),
            "-timeout",
            "20s",
            "-trace-mode",
            "counters",
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    try:
        report = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as error:
        raise ValueError(
            f"ARAM probe did not return JSON for {record['id']}: {completed.stdout}"
        ) from error
    if completed.returncode != 0:
        raise ValueError(
            f"ARAM probe failed for {record['id']}: "
            f"{json.dumps(report, ensure_ascii=False)}"
        )
    return report


def validate_report(report: dict[str, object]) -> None:
    if report.get("status") != "ok_frame":
        raise ValueError("ARAM did not reach the first-frame milestone")
    if report.get("format") != "ktf-wipi":
        raise ValueError("ARAM did not identify the KTF WIPI package")
    if report.get("profile_id") != "wipi-1.2.1/ktf/generic":
        raise ValueError("ARAM selected an unexpected KTF runtime profile")
    image = report.get("image")
    if not isinstance(image, dict) or image.get("mode") != "Thumb":
        raise ValueError("ARAM did not enter the KTF image in Thumb mode")
    wipi = report.get("wipi")
    if not isinstance(wipi, dict):
        raise ValueError("ARAM omitted KTF WIPI diagnostics")
    if int(wipi.get("present_count", 0)) < 1:
        raise ValueError("ARAM observed no KTF framebuffer presentation")
    if wipi.get("unimplemented_calls") != 0:
        raise ValueError("ARAM observed an unimplemented KTF WIPI call")
    if wipi.get("implemented_calls") != wipi.get("api_calls"):
        raise ValueError("ARAM did not implement every observed KTF WIPI call")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aram-core", type=Path, default=ROOT.parent / "aram-core")
    parser.add_argument("--aram-emu", type=Path, default=ROOT.parent / "aram-emu")
    parser.add_argument("--probe", type=Path, default=DEFAULT_PROBE)
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()
    try:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        expected_core = contract["emulators"]["aram"]["revision"]
        actual_core = command_output(["git", "rev-parse", "HEAD"], args.aram_core)
        if actual_core != expected_core:
            raise ValueError(
                f"aram-core revision is {actual_core}, expected {expected_core}"
            )
        if not args.no_build:
            build_probe(args.aram_emu, args.probe)
        if not args.probe.is_file():
            raise ValueError(f"ARAM probe is missing: {args.probe}")

        results: list[dict[str, object]] = []
        for record in package_records():
            report = run_probe(args.probe, record)
            validate_report(report)
            wipi = report["wipi"]
            results.append(
                {
                    "id": record["id"],
                    "package": record["package"],
                    "sha256": report["sha256"],
                    "size": report["size"],
                    "status": report["status"],
                    "level": report["level"],
                    "present_count": wipi["present_count"],
                    "api_calls": wipi["api_calls"],
                    "unimplemented_calls": wipi["unimplemented_calls"],
                    "instructions": report["total_instructions"],
                }
            )
        runner_revision = command_output(
            ["git", "rev-parse", "HEAD"], args.aram_emu
        )
        result = {
            "schema": 1,
            "install_profile": "aram-ktf",
            "runtime_profile": "wipi-1.2.1/ktf/generic",
            "aram": {
                "core_revision": actual_core,
                "runner_revision": runner_revision,
            },
            "coverage": {
                "packages": len(results),
                "ok_frame": sum(item["status"] == "ok_frame" for item in results),
                "unimplemented_calls": sum(
                    int(item["unimplemented_calls"]) for item in results
                ),
            },
            "examples": results,
            "claims": {
                "first_frame_verified": True,
                "interactive_verified": False,
                "real_device_verified": False,
            },
        }
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
