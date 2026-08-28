#!/usr/bin/env python3
"""Explicitly rebuild and update the checked-in documentation packages."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import zipfile

if __package__:
    from . import docs_package_assets
else:
    import docs_package_assets


ROOT = Path(__file__).resolve().parents[1]


def git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.resolve()}", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def clean_head_revision() -> str:
    status = git("status", "--porcelain").stdout
    if status:
        raise ValueError(
            "commit source changes before updating static packages, or pass "
            "--built-from with --use-existing-build for an already verified build"
        )
    return git("rev-parse", "HEAD").stdout.strip()


def canonical_revision(value: str) -> str:
    return git("rev-parse", "--verify", f"{value}^{{commit}}").stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--built-from")
    parser.add_argument(
        "--use-existing-build",
        action="store_true",
        help="copy existing verified build outputs instead of invoking the toolchain",
    )
    args = parser.parse_args()
    try:
        built_from = (
            canonical_revision(args.built_from)
            if args.built_from
            else clean_head_revision()
        )
        if not args.use_existing_build:
            subprocess.run(
                ["make", "clean", "all", "test-target"],
                cwd=ROOT,
                check=True,
            )
        entries = docs_package_assets.update_static_package_set(
            repository_root=ROOT,
            built_from=built_from,
            records=docs_package_assets.repository_package_records(),
        )
        print(
            f"updated {len(entries)} checked-in documentation packages "
            f"built from {built_from}"
        )
    except (
        OSError,
        UnicodeError,
        ValueError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
