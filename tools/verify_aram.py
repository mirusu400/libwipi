#!/usr/bin/env python3
"""Build and run the libwipi conformance package through pinned ARAM sources."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "spec" / "install" / "aram-wie-raptor.json"
DEFAULT_PACKAGE = (
    ROOT
    / "build"
    / "wipi-1.2.1"
    / "lgt-raptor"
    / "aram-wie-raptor"
    / "examples"
    / "conformance"
    / "libwipi-conformance.zip"
)
PLATFORMER_PACKAGE = (
    ROOT
    / "examples"
    / "platformer"
    / "build"
    / "wipi-1.2.1"
    / "lgt-raptor"
    / "aram-wie-raptor"
    / "libwipi-sky-hopper.zip"
)
DEFAULT_PROBE = ROOT / ".cache" / (
    "aram-probe.exe" if os.name == "nt" else "aram-probe"
)


def suite_package(name: str) -> Path:
    if name == "conformance":
        return DEFAULT_PACKAGE
    if name == "platformer":
        return PLATFORMER_PACKAGE
    raise ValueError(f"unknown ARAM suite: {name}")


def command_output(arguments: list[str], cwd: Path) -> str:
    result = subprocess.run(
        arguments,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def verify_revision(repository: Path, expected: str, label: str) -> None:
    if not (repository / ".git").exists():
        raise ValueError(f"not an {label} git repository: {repository}")
    actual = command_output(["git", "rev-parse", "HEAD"], repository)
    if actual != expected:
        raise ValueError(f"{label} revision is {actual}, expected {expected}")


def build_probe(aram_emu_root: Path, probe: Path) -> None:
    probe.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["go", "build", "-trimpath", "-o", str(probe), "./cmd/aram-probe"],
        cwd=aram_emu_root,
        check=True,
    )


def run_probe(probe: Path, arguments: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        [str(probe), *arguments],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    output = completed.stdout.strip()
    try:
        report = json.loads(output)
    except json.JSONDecodeError as error:
        raise ValueError(f"ARAM probe did not return JSON: {output}") from error
    if completed.returncode != 0:
        raise ValueError(f"ARAM probe failed: {json.dumps(report, ensure_ascii=False)}")
    return report


def validate_interactive(report: dict[str, object]) -> None:
    if report.get("status") != "ok_frame" or report.get("level") != "interactive":
        raise ValueError("ARAM did not reach the interactive frame milestone")
    if report.get("format") != "raptor-wipi-c":
        raise ValueError("ARAM did not identify the Raptor WIPI-C package")
    if report.get("profile_id") != "wipi-1.2.1/lgt/raptor":
        raise ValueError("ARAM selected an unexpected runtime profile")
    image = report.get("image")
    if not isinstance(image, dict) or image.get("mode") != "Thumb":
        raise ValueError("ARAM did not enter the package in Thumb mode")
    wipi = report.get("wipi")
    if not isinstance(wipi, dict):
        raise ValueError("ARAM omitted WIPI diagnostics")
    if wipi.get("unimplemented_calls") != 0:
        raise ValueError("ARAM observed an unimplemented WIPI call")
    if wipi.get("implemented_calls") != wipi.get("api_calls"):
        raise ValueError("ARAM did not implement every observed WIPI call")
    if int(wipi.get("observed_apis", 0)) < 24:
        raise ValueError("ARAM observed fewer conformance APIs than expected")
    if int(report.get("input_events", 0)) < 2:
        raise ValueError("ARAM did not deliver key press and release")
    if int(report.get("frame_changes", 0)) < 2:
        raise ValueError("ARAM did not observe timer/input frame changes")


def validate_platformer(report: dict[str, object]) -> None:
    if report.get("status") != "ok_frame" or report.get("level") != "interactive":
        raise ValueError("ARAM platformer did not reach the interactive milestone")
    if report.get("format") != "raptor-wipi-c":
        raise ValueError("ARAM did not identify the platformer Raptor package")
    if report.get("profile_id") != "wipi-1.2.1/lgt/raptor":
        raise ValueError("ARAM selected an unexpected platformer runtime profile")
    image = report.get("image")
    if not isinstance(image, dict) or image.get("mode") != "Thumb":
        raise ValueError("ARAM did not enter the platformer in Thumb mode")
    wipi = report.get("wipi")
    if not isinstance(wipi, dict):
        raise ValueError("ARAM omitted platformer WIPI diagnostics")
    if wipi.get("unimplemented_calls") != 0:
        raise ValueError("ARAM observed an unimplemented platformer WIPI call")
    if wipi.get("implemented_calls") != wipi.get("api_calls"):
        raise ValueError("ARAM did not implement every platformer WIPI call")
    if int(wipi.get("observed_apis", 0)) < 13:
        raise ValueError("ARAM observed fewer platformer APIs than expected")
    if int(report.get("input_events", 0)) < 4:
        raise ValueError("ARAM did not deliver platformer move/jump input")
    if int(report.get("frame_changes", 0)) < 3:
        raise ValueError("ARAM observed too few platformer frame changes")


def validate_performance(report: dict[str, object]) -> None:
    if report.get("status") != "ok_frame" or report.get("level") != "performance":
        raise ValueError("ARAM did not reach the performance milestone")
    performance = report.get("performance")
    if not isinstance(performance, dict):
        raise ValueError("ARAM omitted performance diagnostics")
    audio = performance.get("audio")
    if not isinstance(audio, dict):
        raise ValueError("ARAM omitted audio diagnostics")
    if int(audio.get("chunks", 0)) <= 0 or int(audio.get("frames", 0)) <= 0:
        raise ValueError("ARAM generated no audio")
    if audio.get("sample_rate") != 44100 or audio.get("channels") != 2:
        raise ValueError("ARAM generated an unexpected audio format")
    for key in (
        "generation_changes",
        "discontinuities",
        "missing_frames",
        "overlapping_frames",
        "format_changes",
        "invalid_chunks",
        "published_dropped_samples",
        "media_dropped_samples",
    ):
        if audio.get(key) != 0:
            raise ValueError(f"ARAM audio diagnostic {key} is not zero")


def run(
    aram_core_root: Path,
    aram_emu_root: Path,
    probe: Path,
    package: Path,
    should_build_probe: bool,
    suite: str = "conformance",
) -> dict[str, object]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    emulator = contract["emulators"]["aram"]
    verify_revision(aram_core_root, emulator["revision"], "aram-core")
    verify_revision(aram_emu_root, emulator["runner_revision"], "aram-emu")
    if not package.is_file():
        raise ValueError(f"conformance package does not exist: {package}")
    if should_build_probe:
        build_probe(aram_emu_root, probe)
    if not probe.is_file():
        raise ValueError(f"ARAM probe does not exist: {probe}; pass --build-probe")

    if suite == "platformer":
        interactive = run_probe(
            probe,
            [
                "-input",
                str(package),
                "-label",
                "libwipi-sky-hopper",
                "-timeout",
                "20s",
                "-slices",
                "768",
                "-post-frame-slices",
                "256",
                "-controls",
                "right,ok",
                "-pre-input-slices",
                "16",
                "-control-hold-slices",
                "40",
                "-control-release-slices",
                "20",
            ],
        )
        validate_platformer(interactive)
        return {
            "schema": 1,
            "suite": suite,
            "aram_core_revision": emulator["revision"],
            "aram_emu_revision": emulator["runner_revision"],
            "package_sha256": interactive["sha256"],
            "interactive": {
                "status": interactive["status"],
                "level": interactive["level"],
                "api_calls": interactive["wipi"]["api_calls"],
                "observed_apis": interactive["wipi"]["observed_apis"],
                "input_events": interactive["input_events"],
                "frame_changes": interactive["frame_changes"],
            },
        }
    if suite != "conformance":
        raise ValueError(f"unknown ARAM suite: {suite}")

    common = ["-input", str(package), "-timeout", "20s"]
    interactive = run_probe(
        probe,
        [
            *common,
            "-label",
            "libwipi-conformance",
            "-slices",
            "512",
            "-post-frame-slices",
            "128",
            "-controls",
            "enter",
            "-pre-input-slices",
            "24",
            "-control-hold-slices",
            "8",
            "-control-release-slices",
            "8",
        ],
    )
    validate_interactive(interactive)
    performance = run_probe(
        probe,
        [
            "-input",
            str(package),
            "-label",
            "libwipi-conformance-audio",
            "-performance-duration",
            "1s",
            "-warmup-frames",
            "1",
        ],
    )
    validate_performance(performance)
    if interactive.get("sha256") != performance.get("sha256"):
        raise ValueError("ARAM runs did not use the same package")
    return {
        "schema": 1,
        "aram_core_revision": emulator["revision"],
        "aram_emu_revision": emulator["runner_revision"],
        "package_sha256": interactive["sha256"],
        "interactive": {
            "status": interactive["status"],
            "level": interactive["level"],
            "api_calls": interactive["wipi"]["api_calls"],
            "observed_apis": interactive["wipi"]["observed_apis"],
            "input_events": interactive["input_events"],
            "frame_changes": interactive["frame_changes"],
        },
        "performance": {
            "status": performance["status"],
            "level": performance["level"],
            "measured_frames": performance["performance"]["measured_frames"],
            "audio": performance["performance"]["audio"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--aram-core-root", type=Path, default=ROOT.parent / "aram-core"
    )
    parser.add_argument(
        "--aram-emu-root", type=Path, default=ROOT.parent / "aram-emu"
    )
    parser.add_argument("--probe", type=Path, default=DEFAULT_PROBE)
    parser.add_argument(
        "--suite",
        choices=("conformance", "platformer"),
        default="conformance",
    )
    parser.add_argument("--package", type=Path)
    parser.add_argument("--build-probe", action="store_true")
    arguments = parser.parse_args()
    try:
        package = (
            arguments.package
            if arguments.package is not None
            else suite_package(arguments.suite)
        )
        report = run(
            arguments.aram_core_root.resolve(),
            arguments.aram_emu_root.resolve(),
            arguments.probe.resolve(),
            package.resolve(),
            arguments.build_probe,
            arguments.suite,
        )
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
