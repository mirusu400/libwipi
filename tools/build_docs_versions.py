#!/usr/bin/env python3
"""Add every documentation-capable SDK release tag to one Pages artifact."""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def git_command(*arguments: str) -> list[str]:
    """Build a Git command that trusts only this mounted repository."""
    return ["git", "-c", f"safe.directory={ROOT}", *arguments]


def release_tags() -> list[str]:
    output = subprocess.run(
        git_command("tag", "--list", "v[0-9]*", "--sort=-version:refname"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line.strip() for line in output.splitlines() if line.strip()]


def tag_revision(tag: str) -> str:
    return subprocess.run(
        git_command("rev-list", "-n", "1", tag),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def export_tag(tag: str, destination: Path) -> None:
    archive = subprocess.run(
        git_command("archive", "--format=zip", tag),
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    with zipfile.ZipFile(BytesIO(archive)) as source:
        for info in source.infolist():
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in info.filename:
                raise ValueError(f"unsafe path in git archive for {tag}: {info.filename}")
            target = (destination / Path(*path.parts)).resolve()
            if destination.resolve() not in target.parents and target != destination.resolve():
                raise ValueError(f"tag archive escapes destination: {info.filename}")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read(info))


def build_tags(site_root: Path, base_url: str, tags: list[str]) -> None:
    temporary_parent = ROOT / "build" / "docs" / "tag-sources"
    temporary_parent.mkdir(parents=True, exist_ok=True)
    for tag in tags:
        with tempfile.TemporaryDirectory(prefix="release-", dir=temporary_parent) as name:
            checkout = Path(name)
            export_tag(tag, checkout)
            builder = checkout / "tools" / "build_docs.py"
            if not builder.is_file():
                print(f"warning: skipping {tag}; it predates the versioned docs builder")
                continue
            command = [
                sys.executable,
                str(builder),
                "--site-root",
                str(site_root.resolve()),
                "--version",
                tag,
                "--base-url",
                base_url,
                "--jobs",
                "auto",
            ]
            if (checkout / "tools" / "docs_package_assets.py").is_file():
                command.extend(
                    [
                        "--publish-packages",
                        "--source-revision",
                        tag_revision(tag),
                    ]
                )
            subprocess.run(
                command,
                cwd=checkout,
                check=True,
            )
    if temporary_parent.exists() and not any(temporary_parent.iterdir()):
        shutil.rmtree(temporary_parent)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, default=ROOT / "build/docs/site")
    parser.add_argument(
        "--base-url", default="https://mirusu400.github.io/libwipi"
    )
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("limit must not be negative")
    try:
        tags = release_tags()
        build_tags(args.site_root, args.base_url, tags[: args.limit or None])
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
