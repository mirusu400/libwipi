#!/usr/bin/env python3
"""Run the libwipi conformance package through the pinned WIE LGT runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "spec" / "install" / "aram-wie-raptor.json"
CONFORMANCE_HARNESS = ROOT / "tests" / "wie" / "libwipi_conformance.rs"
CONFORMANCE_PACKAGE = (
    ROOT
    / "build"
    / "wipi-1.2.1"
    / "lgt-raptor"
    / "aram-wie-raptor"
    / "examples"
    / "conformance"
    / "libwipi-conformance.zip"
)
PLATFORMER_HARNESS = ROOT / "tests" / "wie" / "libwipi_platformer.rs"
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


def suite_config(name: str) -> tuple[Path, Path]:
    if name == "conformance":
        return CONFORMANCE_HARNESS, CONFORMANCE_PACKAGE
    if name == "platformer":
        return PLATFORMER_HARNESS, PLATFORMER_PACKAGE
    raise ValueError(f"unknown WIE suite: {name}")


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


def verify_revision(wie_root: Path, expected: str) -> None:
    actual = command_output(["git", "rev-parse", "HEAD"], wie_root)
    if actual != expected:
        raise ValueError(f"WIE revision is {actual}, expected {expected}")


def prepare_workspace(wie_root: Path, repository: str, revision: str) -> None:
    if wie_root.exists():
        return
    wie_root.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--no-checkout", repository, str(wie_root)],
        check=True,
    )
    subprocess.run(
        ["git", "checkout", "--detach", revision],
        cwd=wie_root,
        check=True,
    )


def run(
    wie_root: Path,
    package: Path,
    should_prepare: bool,
    harness: Path = CONFORMANCE_HARNESS,
) -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    emulator = contract["emulators"]["wie"]
    expected = emulator["revision"]
    if should_prepare:
        prepare_workspace(wie_root, emulator["repository"], expected)
    if not (wie_root / "wie_lgt" / "Cargo.toml").is_file():
        raise ValueError(f"not a WIE workspace: {wie_root}")
    if not package.is_file():
        raise ValueError(f"conformance package does not exist: {package}")
    verify_revision(wie_root, expected)
    package_hash = hashlib.sha256(package.read_bytes()).hexdigest()
    suite_name = harness.stem.replace("libwipi_", "", 1)
    print(
        f"libwipi-wie-{suite_name}-package "
        f"sha256={package_hash} revision={expected}"
    )

    destination = wie_root / "wie_lgt" / "tests" / harness.name
    if destination.exists():
        raise ValueError(f"refusing to replace existing WIE test: {destination}")
    shutil.copyfile(harness, destination)
    environment = os.environ.copy()
    environment["LIBWIPI_PACKAGE"] = str(package.resolve())
    try:
        completed = subprocess.run(
            [
                "cargo",
                "test",
                "-p",
                "wie_lgt",
                "--test",
                harness.stem,
                "--",
                "--nocapture",
            ],
            cwd=wie_root,
            env=environment,
            check=False,
        )
        return completed.returncode
    finally:
        destination.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wie-root",
        type=Path,
        default=ROOT / ".cache" / "wie",
    )
    parser.add_argument(
        "--suite",
        choices=("conformance", "platformer"),
        default="conformance",
    )
    parser.add_argument("--package", type=Path)
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="clone the pinned WIE revision when --wie-root is absent",
    )
    arguments = parser.parse_args()
    try:
        harness, default_package = suite_config(arguments.suite)
        package = arguments.package if arguments.package else default_package
        return run(
            arguments.wie_root.resolve(),
            package.resolve(),
            arguments.prepare,
            harness,
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
