#!/usr/bin/env python3
"""Publish verified example packages into a versioned documentation site."""

from __future__ import annotations

import argparse
import hashlib
from html import escape
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import zipfile

if __package__:
    from . import package_raptor
else:
    import package_raptor


ROOT = Path(__file__).resolve().parents[1]
COMPONENT_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z._-]*\Z")
PACKAGE_MARKER_RE = re.compile(
    r"<span\b"
    r"(?=[^>]*\bclass=[\"'][^\"']*\blibwipi-package-download\b[^\"']*[\"'])"
    r"(?=[^>]*\bdata-package-key=[\"'](?P<key>[^\"']+)[\"'])"
    r"[^>]*>.*?</span>",
    re.IGNORECASE | re.DOTALL,
)


def component(record: dict[str, str], field: str) -> str:
    value = str(record.get(field, ""))
    if not COMPONENT_RE.fullmatch(value):
        raise ValueError(f"unsafe package {field}: {value!r}")
    return value


def package_source_path(record: dict[str, str]) -> PurePosixPath:
    value = str(record.get("package", ""))
    if not value or "\\" in value:
        raise ValueError(f"unsafe package source path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"package source must be below repository: {value!r}")
    if path.as_posix() != value:
        raise ValueError(f"unsafe package source path: {value!r}")
    return path


def package_key(record: dict[str, str]) -> str:
    return "::".join(
        component(record, field)
        for field in ("api_level", "abi_profile", "install_profile", "example_id")
    )


def package_site_path(record: dict[str, str]) -> Path:
    source = package_source_path(record)
    filename = source.name
    if not COMPONENT_RE.fullmatch(filename):
        raise ValueError(f"unsafe package filename: {filename!r}")
    return Path(
        "packages",
        component(record, "api_level"),
        component(record, "abi_profile"),
        component(record, "install_profile"),
        component(record, "example_id"),
        filename,
    )


def package_marker(record: dict[str, str]) -> str:
    key = escape(package_key(record), quote=True)
    return (
        '<span class="libwipi-package-download" '
        f'data-package-key="{key}">'
        "Compiled ZIP is added by the versioned documentation build."
        "</span>"
    )


def checked_child(parent: Path, child: Path, label: str) -> Path:
    parent = parent.resolve()
    child = child.resolve()
    if child == parent or parent not in child.parents:
        raise ValueError(f"{label} must be below {parent}: {child}")
    return child


def repository_package_records() -> list[dict[str, str]]:
    if __package__:
        from . import generate, generate_docs
    else:
        import generate
        import generate_docs

    manifest, levels = generate.read_version_manifest()
    catalogs = generate.read_catalogs(levels)
    api_level = str(manifest["bootstrap_api_level"])
    examples = generate_docs.read_example_records(catalogs[api_level], api_level)
    result: list[dict[str, str]] = []
    for example_id, example in sorted(examples.items()):
        for variant in example["variants"]:
            package = variant.get("package")
            if not package:
                continue
            result.append(
                {
                    "example_id": str(example_id),
                    "api_level": str(variant["api_level"]),
                    "abi_profile": str(variant["abi_profile"]),
                    "install_profile": str(variant["install_profile"]),
                    "package": str(package),
                }
            )
    return result


def package_link(url: str, digest: str, size: int) -> str:
    return (
        f'<a class="reference download internal" download href="{escape(url, quote=True)}">'
        "Download compiled ZIP</a><br>"
        f"<small>SHA-256: <code>{digest}</code> · {size} bytes</small>"
    )


def replace_package_markers(
    version_dir: Path, replacements: dict[str, str]
) -> dict[str, int]:
    counts = {key: 0 for key in replacements}
    paths = [
        path
        for path in version_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".html", ".md", ".txt"}
    ]
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            key = match.group("key")
            if key not in replacements:
                raise ValueError(f"documentation contains unknown package key: {key}")
            counts[key] += 1
            return replacements[key]

        rendered = PACKAGE_MARKER_RE.sub(replace, text)
        if rendered != text:
            path.write_text(rendered, encoding="utf-8")
    missing = sorted(key for key, count in counts.items() if count == 0)
    if missing:
        raise ValueError(f"documentation has no marker for packages: {missing}")
    return counts


def stage_package_assets(
    repository_root: Path,
    site_root: Path,
    version: str,
    base_url: str,
    source_revision: str,
    records: list[dict[str, str]],
) -> list[dict[str, object]]:
    if not COMPONENT_RE.fullmatch(version):
        raise ValueError(f"unsafe documentation version: {version!r}")
    if not source_revision or "\n" in source_revision or "\r" in source_revision:
        raise ValueError("source revision must be one non-empty line")
    repository_root = repository_root.resolve()
    site_root = site_root.resolve()
    version_dir = checked_child(site_root, site_root / version, "version directory")
    if not (version_dir / "index.html").is_file():
        raise ValueError(f"missing rendered version index: {version_dir / 'index.html'}")
    packages_dir = checked_child(version_dir, version_dir / "packages", "package output")
    if packages_dir.exists():
        shutil.rmtree(packages_dir)
    packages_dir.mkdir(parents=True)

    entries: list[dict[str, object]] = []
    replacements: dict[str, str] = {}
    destinations: set[Path] = set()
    for record in sorted(records, key=package_key):
        key = package_key(record)
        if key in replacements:
            raise ValueError(f"duplicate package key: {key}")
        source_relative = package_source_path(record)
        source = checked_child(
            repository_root,
            repository_root / Path(*source_relative.parts),
            "package source",
        )
        if not source.is_file():
            raise ValueError(f"compiled package does not exist: {source}")
        inspection = package_raptor.inspect_package(source)
        site_relative = package_site_path(record)
        destination = checked_child(
            version_dir, version_dir / site_relative, "published package"
        )
        if destination in destinations:
            raise ValueError(f"duplicate published package path: {site_relative}")
        destinations.add(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        data = destination.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        url = (
            f"{base_url.rstrip('/')}/{version}/{site_relative.as_posix()}"
        )
        replacements[key] = package_link(url, digest, len(data))
        entries.append(
            {
                "key": key,
                "example_id": component(record, "example_id"),
                "api_level": component(record, "api_level"),
                "abi_profile": component(record, "abi_profile"),
                "install_profile": component(record, "install_profile"),
                "path": site_relative.as_posix(),
                "url": url,
                "sha256": digest,
                "size": len(data),
                "aid": inspection["aid"],
                "module": inspection["module"],
                "resources": inspection["resources"],
                "real_device": False,
            }
        )

    replace_package_markers(version_dir, replacements)
    manifest = {
        "schema": 1,
        "version": version,
        "source_revision": source_revision,
        "real_device": False,
        "packages": entries,
    }
    (packages_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    checksum_lines = [
        f"{entry['sha256']}  {Path(str(entry['path'])).relative_to('packages').as_posix()}"
        for entry in entries
    ]
    (packages_dir / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + ("\n" if checksum_lines else ""),
        encoding="utf-8",
    )
    return entries


def git_revision(repository_root: Path) -> str:
    return subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={repository_root.resolve()}",
            "rev-parse",
            "HEAD",
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-root", type=Path, default=ROOT / "build/docs/site")
    parser.add_argument("--version", default="latest")
    parser.add_argument(
        "--base-url", default="https://mirusu400.github.io/libwipi"
    )
    parser.add_argument("--source-revision")
    args = parser.parse_args()
    try:
        records = repository_package_records()
        entries = stage_package_assets(
            repository_root=ROOT,
            site_root=args.site_root,
            version=args.version,
            base_url=args.base_url,
            source_revision=args.source_revision or git_revision(ROOT),
            records=records,
        )
        print(f"published {len(entries)} compiled example packages for {args.version}")
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
