#!/usr/bin/env python3
"""Verify and publish checked-in example packages into a documentation site."""

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
from urllib.parse import urlencode
import zipfile

if __package__:
    from . import package_raptor
else:
    import package_raptor


ROOT = Path(__file__).resolve().parents[1]
STATIC_PACKAGE_ROOT = Path("docs/packages")
ARAM_PLAYER_URL = "https://aram.mir.sh/player/"
COMPONENT_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z._-]*\Z")
PACKAGE_MARKER_RE = re.compile(
    r"<span\b"
    r"(?=[^>]*\bclass=[\"'][^\"']*\blibwipi-package-download\b[^\"']*[\"'])"
    r"(?=[^>]*\bdata-package-key=[\"'](?P<key>[^\"']+)[\"'])"
    r"[^>]*>.*?</span>",
    re.IGNORECASE | re.DOTALL,
)


def component(record: dict[str, object], field: str) -> str:
    value = str(record.get(field, ""))
    if not COMPONENT_RE.fullmatch(value):
        raise ValueError(f"unsafe package {field}: {value!r}")
    return value


def revision(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
        raise ValueError(f"{label} must be one non-empty line")
    return value


def package_source_path(record: dict[str, object]) -> PurePosixPath:
    value = str(record.get("package", ""))
    if not value or "\\" in value:
        raise ValueError(f"unsafe package source path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"package source must be below repository: {value!r}")
    if path.as_posix() != value:
        raise ValueError(f"unsafe package source path: {value!r}")
    return path


def package_key(record: dict[str, object]) -> str:
    return "::".join(
        component(record, field)
        for field in ("api_level", "abi_profile", "install_profile", "example_id")
    )


def package_site_path(record: dict[str, object]) -> Path:
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


def package_marker(record: dict[str, object]) -> str:
    key = escape(package_key(record), quote=True)
    return (
        '<span class="libwipi-package-download" '
        f'data-package-key="{key}">'
        "Checked-in ZIP is added by the versioned documentation build."
        "</span>"
    )


def checked_child(parent: Path, child: Path, label: str) -> Path:
    parent = parent.resolve()
    child = child.resolve()
    if child == parent or parent not in child.parents:
        raise ValueError(f"{label} must be below {parent}: {child}")
    return child


def write_text_lf(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as destination:
        destination.write(content)


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


def package_entry(
    record: dict[str, object],
    site_relative: Path,
    data: bytes,
    inspection: dict[str, object],
) -> dict[str, object]:
    return {
        "key": package_key(record),
        "example_id": component(record, "example_id"),
        "api_level": component(record, "api_level"),
        "abi_profile": component(record, "abi_profile"),
        "install_profile": component(record, "install_profile"),
        "path": site_relative.as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "aid": inspection["aid"],
        "module": inspection["module"],
        "resources": inspection["resources"],
        "real_device": False,
    }


def checksum_text(entries: list[dict[str, object]]) -> str:
    lines = [
        f"{entry['sha256']}  "
        f"{Path(str(entry['path'])).relative_to('packages').as_posix()}"
        for entry in entries
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def update_static_package_set(
    repository_root: Path,
    built_from: str,
    records: list[dict[str, str]],
) -> list[dict[str, object]]:
    """Copy already-built packages into the checked-in documentation tree."""
    repository_root = repository_root.resolve()
    built_from = revision(built_from, "package build revision")
    prepared: list[tuple[dict[str, str], Path, bytes, dict[str, object]]] = []
    keys: set[str] = set()
    destinations: set[Path] = set()
    for record in sorted(records, key=package_key):
        key = package_key(record)
        if key in keys:
            raise ValueError(f"duplicate package key: {key}")
        keys.add(key)
        source_relative = package_source_path(record)
        source = checked_child(
            repository_root,
            repository_root / Path(*source_relative.parts),
            "package source",
        )
        if not source.is_file():
            raise ValueError(f"compiled package does not exist: {source}")
        site_relative = package_site_path(record)
        if site_relative in destinations:
            raise ValueError(f"duplicate static package path: {site_relative}")
        destinations.add(site_relative)
        inspection = package_raptor.inspect_package(source)
        prepared.append((record, site_relative, source.read_bytes(), inspection))

    static_root = checked_child(
        repository_root,
        repository_root / STATIC_PACKAGE_ROOT,
        "static package root",
    )
    if static_root.exists():
        shutil.rmtree(static_root)
    static_root.mkdir(parents=True)

    entries: list[dict[str, object]] = []
    for record, site_relative, data, inspection in prepared:
        destination = checked_child(
            repository_root,
            repository_root / "docs" / site_relative,
            "static package",
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        entries.append(package_entry(record, site_relative, data, inspection))

    manifest = {
        "schema": 1,
        "built_from": built_from,
        "real_device": False,
        "packages": entries,
    }
    write_text_lf(
        static_root / "manifest.json",
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
    )
    write_text_lf(static_root / "SHA256SUMS", checksum_text(entries))
    return entries


def verify_static_package_set(
    repository_root: Path, records: list[dict[str, str]]
) -> tuple[dict[str, object], list[dict[str, object]]]:
    repository_root = repository_root.resolve()
    static_root = checked_child(
        repository_root,
        repository_root / STATIC_PACKAGE_ROOT,
        "static package root",
    )
    manifest_path = static_root / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"missing checked-in package manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        raise ValueError("unsupported checked-in package manifest schema")
    built_from = revision(manifest.get("built_from", ""), "package build revision")
    if manifest.get("real_device") is not False:
        raise ValueError("checked-in packages must not claim real-device verification")
    raw_entries = manifest.get("packages")
    if not isinstance(raw_entries, list):
        raise ValueError("checked-in package manifest packages must be a list")

    actual_by_key: dict[str, dict[str, object]] = {}
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            raise ValueError("checked-in package entry must be an object")
        key = str(raw_entry.get("key", ""))
        if key in actual_by_key:
            raise ValueError(f"duplicate checked-in package key: {key}")
        actual_by_key[key] = raw_entry

    expected_by_key: dict[str, dict[str, str]] = {}
    for record in records:
        key = package_key(record)
        if key in expected_by_key:
            raise ValueError(f"duplicate package key: {key}")
        expected_by_key[key] = record
    missing = sorted(set(expected_by_key) - set(actual_by_key))
    extra = sorted(set(actual_by_key) - set(expected_by_key))
    if missing or extra:
        raise ValueError(
            f"checked-in package inventory mismatch; missing={missing}, extra={extra}"
        )

    entries: list[dict[str, object]] = []
    for key in sorted(expected_by_key):
        record = expected_by_key[key]
        entry = actual_by_key[key]
        site_relative = package_site_path(record)
        expected_fields: dict[str, object] = {
            "key": key,
            "example_id": component(record, "example_id"),
            "api_level": component(record, "api_level"),
            "abi_profile": component(record, "abi_profile"),
            "install_profile": component(record, "install_profile"),
            "path": site_relative.as_posix(),
            "real_device": False,
        }
        for field, expected in expected_fields.items():
            if entry.get(field) != expected:
                raise ValueError(
                    f"checked-in package {key} has invalid {field}: "
                    f"{entry.get(field)!r} != {expected!r}"
                )
        source = checked_child(
            repository_root,
            repository_root / "docs" / site_relative,
            "checked-in package",
        )
        if not source.is_file():
            raise ValueError(f"missing checked-in package: {source}")
        data = source.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if entry.get("sha256") != digest:
            raise ValueError(f"SHA-256 mismatch for checked-in package: {source}")
        if entry.get("size") != len(data):
            raise ValueError(f"size mismatch for checked-in package: {source}")
        inspection = package_raptor.inspect_package(source)
        for field in ("aid", "module", "resources"):
            if entry.get(field) != inspection[field]:
                raise ValueError(
                    f"inspection mismatch for checked-in package {key}: {field}"
                )
        entries.append(dict(entry))

    expected_checksums = checksum_text(entries)
    checksums_path = static_root / "SHA256SUMS"
    if not checksums_path.is_file():
        raise ValueError(f"missing checked-in package checksums: {checksums_path}")
    if checksums_path.read_text(encoding="utf-8") != expected_checksums:
        raise ValueError("checked-in package SHA256SUMS is not current")
    manifest["built_from"] = built_from
    return manifest, entries


def aram_permalink(url: str, digest: str) -> str:
    return ARAM_PLAYER_URL + "?" + urlencode(
        {
            "ch": "nightly",
            "app": url,
            "sha256": digest,
        }
    )


def package_link(url: str, digest: str, size: int, built_from: str) -> str:
    build_url = f"https://github.com/mirusu400/libwipi/commit/{built_from}"
    build_label = escape(built_from[:12])
    run_url = aram_permalink(url, digest)
    return (
        f'<a class="reference external libwipi-run-aram" '
        f'href="{escape(run_url, quote=True)}" target="_blank" rel="noopener">'
        "Run in ARAM</a> &middot; "
        f'<a class="reference download internal" download href="{escape(url, quote=True)}">'
        "Download compiled ZIP</a><br>"
        f"<small>SHA-256: <code>{digest}</code> · {size} bytes<br>"
        f'Built from: <a href="{escape(build_url, quote=True)}"><code>{build_label}</code></a>'
        "</small>"
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
            write_text_lf(path, rendered)
    missing = sorted(key for key, count in counts.items() if count == 0)
    if missing:
        raise ValueError(f"documentation has no marker for packages: {missing}")
    return counts


def stage_package_assets(
    repository_root: Path,
    site_root: Path,
    version: str,
    base_url: str,
    documentation_revision: str,
    records: list[dict[str, str]],
) -> list[dict[str, object]]:
    if not COMPONENT_RE.fullmatch(version):
        raise ValueError(f"unsafe documentation version: {version!r}")
    documentation_revision = revision(
        documentation_revision, "documentation revision"
    )
    repository_root = repository_root.resolve()
    site_root = site_root.resolve()
    version_dir = checked_child(site_root, site_root / version, "version directory")
    if not (version_dir / "index.html").is_file():
        raise ValueError(f"missing rendered version index: {version_dir / 'index.html'}")

    static_manifest, static_entries = verify_static_package_set(
        repository_root, records
    )
    built_from = str(static_manifest["built_from"])
    packages_dir = checked_child(version_dir, version_dir / "packages", "package output")
    if packages_dir.exists():
        shutil.rmtree(packages_dir)
    packages_dir.mkdir(parents=True)

    entries: list[dict[str, object]] = []
    replacements: dict[str, str] = {}
    destinations: set[Path] = set()
    for static_entry in static_entries:
        key = str(static_entry["key"])
        site_relative = Path(str(static_entry["path"]))
        source = checked_child(
            repository_root,
            repository_root / "docs" / site_relative,
            "checked-in package",
        )
        destination = checked_child(
            version_dir, version_dir / site_relative, "published package"
        )
        if destination in destinations:
            raise ValueError(f"duplicate published package path: {site_relative}")
        destinations.add(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        url = f"{base_url.rstrip('/')}/{version}/{site_relative.as_posix()}"
        replacements[key] = package_link(
            url,
            str(static_entry["sha256"]),
            int(static_entry["size"]),
            built_from,
        )
        entry = dict(static_entry)
        entry["url"] = url
        entries.append(entry)

    replace_package_markers(version_dir, replacements)
    manifest = {
        "schema": 2,
        "version": version,
        "documentation_revision": documentation_revision,
        "built_from": built_from,
        "real_device": False,
        "packages": entries,
    }
    write_text_lf(
        packages_dir / "manifest.json",
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
    )
    write_text_lf(packages_dir / "SHA256SUMS", checksum_text(entries))
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
    parser.add_argument(
        "--documentation-revision",
        "--source-revision",
        dest="documentation_revision",
    )
    args = parser.parse_args()
    try:
        records = repository_package_records()
        entries = stage_package_assets(
            repository_root=ROOT,
            site_root=args.site_root,
            version=args.version,
            base_url=args.base_url,
            documentation_revision=(
                args.documentation_revision or git_revision(ROOT)
            ),
            records=records,
        )
        print(
            f"published {len(entries)} checked-in example packages for {args.version}"
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
