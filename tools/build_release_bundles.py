#!/usr/bin/env python3
"""Build deterministic, self-describing libwipi test-suite release archives."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPECIFICATION = ROOT / "spec" / "releases" / "bundles.json"
SKIP_DIRECTORY_NAMES = {".cache", ".git", "__pycache__", "build"}


@dataclass(frozen=True)
class Payload:
    archive_path: str
    data: bytes
    kind: str
    source: str


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_archive_path(value: str) -> str:
    if "\\" in value:
        raise ValueError(f"archive paths must use forward slashes: {value}")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"unsafe archive path: {value}")
    if any(part in {"", "."} for part in path.parts):
        raise ValueError(f"non-canonical archive path: {value}")
    return path.as_posix()


def repository_file(root: Path, relative: str) -> Path:
    root = root.resolve()
    candidate = (root / relative).resolve()
    if candidate == root or root not in candidate.parents:
        raise ValueError(f"repository path escapes root: {relative}")
    if not candidate.is_file():
        raise ValueError(f"required bundle input is missing: {relative}")
    return candidate


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON document must be an object: {path}")
    return value


def add_file(
    payloads: dict[str, Payload],
    root: Path,
    relative: str,
    archive_path: str,
    kind: str,
) -> None:
    source = repository_file(root, relative)
    normalized = safe_archive_path(archive_path)
    payload = Payload(normalized, source.read_bytes(), kind, relative)
    existing = payloads.get(normalized)
    if existing is not None and existing.data != payload.data:
        raise ValueError(f"conflicting archive input: {normalized}")
    payloads[normalized] = payload


def add_source_path(
    payloads: dict[str, Payload], root: Path, relative: str
) -> None:
    source = (root / relative).resolve()
    root_resolved = root.resolve()
    if source == root_resolved or root_resolved not in source.parents:
        raise ValueError(f"source path escapes repository: {relative}")
    if source.is_file():
        add_file(payloads, root, relative, f"source/{Path(relative).as_posix()}", "source")
        return
    if not source.is_dir():
        raise ValueError(f"required source path is missing: {relative}")
    for path in sorted(source.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRECTORY_NAMES for part in path.parts):
            continue
        resolved = path.resolve()
        if root_resolved not in resolved.parents:
            raise ValueError(f"source symlink escapes repository: {path}")
        repository_relative = path.relative_to(root).as_posix()
        add_file(
            payloads,
            root,
            repository_relative,
            f"source/{repository_relative}",
            "source",
        )


def bundle_inputs(
    root: Path, bundle: dict[str, object], specification_path: str
) -> dict[str, Payload]:
    payloads: dict[str, Payload] = {}
    suite_relative = str(bundle["suite_manifest"])
    suite = load_json(repository_file(root, suite_relative))

    packages = list(bundle.get("packages", []))
    if bundle.get("packages_from_manifest"):
        packages.extend(str(item["package"]) for item in suite.get("examples", []))
    if not packages:
        raise ValueError(f"bundle has no packages: {bundle['id']}")
    for relative in sorted(set(str(value) for value in packages)):
        add_file(
            payloads,
            root,
            relative,
            f"packages/{Path(relative).name}",
            "package",
        )

    source_paths = list(str(value) for value in bundle.get("source_paths", []))
    if bundle.get("source_paths_from_manifest"):
        source_paths.extend(
            f"examples/{item['id']}" for item in suite.get("examples", [])
        )
    for relative in sorted(set(source_paths)):
        add_source_path(payloads, root, relative)

    metadata_paths = {
        "LICENSE",
        "docs/testing.md",
        "spec/versions.json",
        specification_path,
        suite_relative,
        str(bundle["evidence"]),
        f"spec/profiles/{bundle['abi_profile']}.json",
        f"spec/install/{bundle['install_profile']}.json",
    }
    for relative in sorted(metadata_paths):
        add_file(
            payloads,
            root,
            relative,
            f"metadata/{Path(relative).as_posix()}",
            "metadata",
        )

    readme = (
        f"{bundle['title']}\n"
        f"{'=' * len(str(bundle['title']))}\n\n"
        f"{bundle['description']}\n\n"
        f"SDK version: {{SDK_VERSION}}\n"
        f"API level: {bundle['api_level']}\n"
        f"ABI profile: {bundle['abi_profile']}\n"
        f"Install profile: {bundle['install_profile']}\n"
        "Real-device claim: false\n\n"
        "Start with metadata/docs/testing.md and the suite manifest. Verify "
        "SHA256SUMS before loading any package. Emulator results remain scoped "
        "to the named install contract.\n"
    )
    payloads["README.txt"] = Payload("README.txt", readme.encode(), "guide", "generated")
    return payloads


def zip_datetime(epoch: int) -> tuple[int, int, int, int, int, int]:
    minimum = datetime(1980, 1, 1, tzinfo=timezone.utc)
    value = datetime.fromtimestamp(max(epoch, int(minimum.timestamp())), timezone.utc)
    # ZIP timestamps have a two-second resolution.
    return (value.year, value.month, value.day, value.hour, value.minute, value.second // 2 * 2)


def write_zip(path: Path, entries: dict[str, bytes], epoch: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        with zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for name in sorted(entries):
                info = zipfile.ZipInfo(safe_archive_path(name), zip_datetime(epoch))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, entries[name])
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def build_one(
    root: Path,
    bundle: dict[str, object],
    output_dir: Path,
    version: str,
    epoch: int,
    specification_path: str,
    source_revision: str,
) -> Path:
    payloads = bundle_inputs(root, bundle, specification_path)
    payloads["README.txt"] = Payload(
        "README.txt",
        payloads["README.txt"].data.replace(b"{SDK_VERSION}", version.encode()),
        "guide",
        "generated",
    )
    inventory = [
        {
            "path": payload.archive_path,
            "kind": payload.kind,
            "source": payload.source,
            "size": len(payload.data),
            "sha256": sha256(payload.data),
        }
        for payload in sorted(payloads.values(), key=lambda item: item.archive_path)
    ]
    manifest = {
        "schema": 1,
        "sdk_version": version,
        "source_revision": source_revision,
        "bundle_id": bundle["id"],
        "title": bundle["title"],
        "api_level": bundle["api_level"],
        "abi_profile": bundle["abi_profile"],
        "install_profile": bundle["install_profile"],
        "runner_owner": bundle["runner_owner"],
        "real_device": bool(bundle["real_device"]),
        "source_date_epoch": epoch,
        "payloads": inventory,
    }
    sums = "".join(f"{item['sha256']}  {item['path']}\n" for item in inventory)
    entries = {item.archive_path: item.data for item in payloads.values()}
    entries["bundle-manifest.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()
    entries["SHA256SUMS"] = sums.encode()
    asset = output_dir / f"libwipi-{bundle['id']}-{version}.zip"
    write_zip(asset, entries, epoch)
    return asset


def build_bundles(
    root: Path,
    specification: dict[str, object],
    output_dir: Path,
    version: str,
    epoch: int,
    source_revision: str = "unknown",
    specification_path: str = "spec/releases/bundles.json",
) -> list[Path]:
    if specification.get("schema") != 1:
        raise ValueError("unsupported release bundle schema")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", version):
        raise ValueError(f"unsafe SDK version for asset name: {version}")
    output_dir.mkdir(parents=True, exist_ok=True)
    assets = [
        build_one(
            root,
            bundle,
            output_dir,
            version,
            epoch,
            specification_path,
            source_revision,
        )
        for bundle in specification["bundles"]
    ]
    release_sums = "".join(
        f"{sha256(path.read_bytes())}  {path.name}\n" for path in sorted(assets)
    )
    (output_dir / "SHA256SUMS").write_text(release_sums, encoding="utf-8")
    return assets


def git_revision() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def default_epoch() -> int:
    configured = os.environ.get("SOURCE_DATE_EPOCH")
    if configured:
        return int(configured)
    try:
        value = subprocess.run(
            ["git", "show", "-s", "--format=%ct", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return int(value)
    except (OSError, ValueError, subprocess.CalledProcessError):
        return 315532800


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--source-date-epoch", type=int, default=None)
    parser.add_argument("--source-revision", default=None)
    args = parser.parse_args()
    try:
        assets = build_bundles(
            ROOT,
            load_json(SPECIFICATION),
            args.output,
            args.version,
            args.source_date_epoch if args.source_date_epoch is not None else default_epoch(),
            args.source_revision or git_revision(),
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for asset in assets:
        print(asset.relative_to(ROOT) if ROOT in asset.resolve().parents else asset)
    return 0


if __name__ == "__main__":
    sys.exit(main())
