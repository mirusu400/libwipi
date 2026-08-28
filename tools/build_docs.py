#!/usr/bin/env python3
"""Build strict, versioned Sphinx documentation and machine-readable outputs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def checked_output(root: Path, output: Path) -> Path:
    root = root.resolve()
    output = output.resolve()
    if output == root or root not in output.parents:
        raise ValueError(f"output must be below {root}: {output}")
    return output


def doxygen_api_define() -> str:
    manifest = json.loads((ROOT / "spec" / "versions.json").read_text(encoding="utf-8"))
    api_level = manifest.get("bootstrap_api_level")
    implemented = {
        entry.get("api_level")
        for entry in manifest.get("levels", [])
        if entry.get("catalog_status") == "implemented"
    }
    if not isinstance(api_level, str) or api_level not in implemented:
        raise ValueError("bootstrap API level is not an implemented documentation level")
    token = re.sub(r"[^0-9A-Za-z]+", "_", api_level).strip("_")
    return f"LIBWIPI_API_LEVEL_{token}=1"


def build(
    site_root: Path,
    version: str,
    base_url: str,
    builder: str,
    jobs: str,
    publish_packages: bool = False,
    source_revision: str | None = None,
) -> None:
    run([sys.executable, "tools/generate.py", "--check"])
    run([sys.executable, "tools/generate_docs.py", "--check"])

    build_root = (ROOT / "build" / "docs").resolve()
    doxygen_output = checked_output(build_root, build_root / "doxygen")
    if doxygen_output.exists():
        shutil.rmtree(doxygen_output)
    doxygen_output.mkdir(parents=True)

    env = os.environ.copy()
    env["LIBWIPI_DOXYGEN_OUTPUT"] = doxygen_output.as_posix()
    env["LIBWIPI_DOXYGEN_XML"] = (doxygen_output / "xml").as_posix()
    env["LIBWIPI_DOXYGEN_API_DEFINE"] = doxygen_api_define()
    env["LIBWIPI_DOCS_VERSION"] = version
    env["LIBWIPI_DOCS_SITE_URL"] = base_url.rstrip("/")
    run(["doxygen", "docs/Doxyfile"], env=env)

    doctrees = checked_output(build_root, build_root / f"doctrees-{builder}")
    if doctrees.exists():
        shutil.rmtree(doctrees)
    if builder == "dirhtml":
        site_root = site_root.resolve()
        site_root.mkdir(parents=True, exist_ok=True)
        output = checked_output(site_root, site_root / version)
    else:
        output = checked_output(build_root, build_root / builder)
    if output.exists():
        shutil.rmtree(output)

    command = [
        sys.executable,
        "-m",
        "sphinx",
        "-b",
        builder,
        "-W",
        "--keep-going",
        "-j",
        jobs,
        "-d",
        str(doctrees),
        "docs",
        str(output),
    ]
    run(command, env=env)
    if builder == "dirhtml":
        run(
            [
                sys.executable,
                "tools/finalize_docs_site.py",
                "--site-root",
                str(site_root),
                "--version",
                version,
                "--base-url",
                base_url,
            ]
        )
        if publish_packages:
            package_command = [
                sys.executable,
                "tools/docs_package_assets.py",
                "--site-root",
                str(site_root),
                "--version",
                version,
                "--base-url",
                base_url,
            ]
            if source_revision:
                package_command.extend(["--source-revision", source_revision])
            run(package_command)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, default=ROOT / "build/docs/site")
    parser.add_argument("--version", default=os.environ.get("LIBWIPI_DOCS_VERSION", "latest"))
    parser.add_argument(
        "--base-url", default="https://mirusu400.github.io/libwipi"
    )
    parser.add_argument("--builder", choices=("dirhtml", "linkcheck"), default="dirhtml")
    parser.add_argument("--jobs", default="auto")
    parser.add_argument("--publish-packages", action="store_true")
    parser.add_argument("--source-revision")
    args = parser.parse_args()
    if not args.version or "/" in args.version or "\\" in args.version:
        parser.error("version must be one path component")
    try:
        build(
            args.site_root,
            args.version,
            args.base_url,
            args.builder,
            args.jobs,
            args.publish_packages,
            args.source_revision,
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
