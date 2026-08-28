#!/usr/bin/env python3
"""Add llms.txt v2 discovery and version metadata to a built docs site."""

from __future__ import annotations

import argparse
from html import escape, unescape
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote, unquote


TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
DISCOVERY_MARKER = "<!-- libwipi-machine-discovery -->"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def checked_child(parent: Path, child: Path) -> Path:
    parent = parent.resolve()
    child = child.resolve()
    if child == parent or parent not in child.parents:
        raise ValueError(f"path must be below {parent}: {child}")
    return child


def url_join(base: str, *parts: str) -> str:
    encoded = [quote(part.strip("/"), safe="/.-_") for part in parts if part]
    suffix = "/".join(part for part in encoded if part)
    return f"{base.rstrip('/')}/{suffix}" if suffix else base.rstrip("/")


def html_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = TITLE_RE.search(text)
    if match:
        return unescape(re.sub(r"\s+", " ", match.group(1)).strip())
    return path.parent.name.replace("-", " ").title() or "libwipi"


def document_markdown_relative(version_dir: Path, html_path: Path) -> str:
    relative = html_path.relative_to(version_dir)
    if relative == Path("index.html"):
        return "index.md"
    parent = relative.parent.as_posix()
    return f"{parent}.md"


def normalize_markdown_download_urls(
    version_dir: Path, version: str, base_url: str
) -> None:
    version_base = url_join(base_url, version)
    download_base = version_base + "/_downloads/"
    misplaced = re.compile(
        re.escape(version_base) + r"/(?:[^/()\s]+/)+_downloads/"
    )
    paths = set(version_dir.rglob("*.md"))
    paths.update(
        path
        for name in ("llms.txt", "llms-full.txt")
        if (path := version_dir / name).is_file()
    )
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8")
        normalized = misplaced.sub(download_base, text)
        for match in re.finditer(r"\]\(([^)\s]+)\)", normalized):
            url = match.group(1)
            if not url.startswith(download_base):
                continue
            relative = unquote(url[len(download_base) :].split("#", 1)[0])
            target = checked_child(version_dir, version_dir / "_downloads" / relative)
            if not target.is_file():
                raise ValueError(f"Markdown download URL has no site asset: {url}")
        if normalized != text:
            path.write_text(normalized, encoding="utf-8")


def page_url(base_url: str, version: str, version_dir: Path, html_path: Path) -> str:
    relative = html_path.relative_to(version_dir)
    if relative == Path("index.html"):
        return url_join(base_url, version) + "/"
    return url_join(base_url, version, relative.parent.as_posix()) + "/"


def write_nested_llms(
    version_dir: Path, version: str, base_url: str, html_paths: list[Path]
) -> None:
    directories = sorted(
        {path.parent for path in html_paths},
        key=lambda path: path.relative_to(version_dir).as_posix(),
    )
    for directory in directories:
        if directory == version_dir:
            continue
        local_pages = [path for path in html_paths if path.parent == directory]
        direct_children = [
            path
            for path in html_paths
            if path.name == "index.html" and path.parent.parent == directory
        ]
        listed = sorted(
            set(local_pages + direct_children),
            key=lambda path: path.relative_to(version_dir).as_posix(),
        )
        relative_dir = directory.relative_to(version_dir).as_posix()
        lines = [
            f"# libwipi {version}: /{relative_dir}",
            "",
            "> Deterministic index of the Markdown alternatives in this documentation subpath.",
            "",
            "API level, device ABI profile, and install profile remain independent.",
            "",
            "## Pages",
            "",
        ]
        for path in listed:
            markdown = document_markdown_relative(version_dir, path)
            lines.append(
                f"- [{html_title(path)}]({url_join(base_url, version, markdown)}): "
                "Markdown alternate for this rendered documentation page."
            )
        lines.extend(
            [
                "",
                f"- [Version documentation index]({url_join(base_url, version, 'llms.txt')}): "
                "Curated top-level libwipi context.",
                "",
            ]
        )
        (directory / "llms.txt").write_text("\n".join(lines), encoding="utf-8")


def inject_discovery(
    version_dir: Path, version: str, base_url: str, html_paths: list[Path]
) -> None:
    for path in html_paths:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(version_dir)
        language_changed = False
        if relative.parts and relative.parts[0] == "ko":
            text, replacements = re.subn(
                r'(<html\b[^>]*\blang=)["\'][^"\']*["\']',
                r'\1"ko"',
                text,
                count=1,
                flags=re.IGNORECASE,
            )
            if replacements != 1:
                raise ValueError(f"Korean HTML output has no language attribute: {path}")
            language_changed = True
        if DISCOVERY_MARKER in text:
            if language_changed:
                path.write_text(text, encoding="utf-8")
            continue
        markdown = document_markdown_relative(version_dir, path)
        relative_parent = path.parent.relative_to(version_dir).as_posix()
        if relative_parent == ".":
            relative_parent = ""
        describedby = url_join(
            base_url,
            version,
            relative_parent,
            "llms.txt",
        )
        tags = (
            f"  {DISCOVERY_MARKER}\n"
            f'  <link rel="alternate" type="text/markdown" '
            f'href="{escape(url_join(base_url, version, markdown), quote=True)}">\n'
            f'  <link rel="describedby" type="text/plain" '
            f'href="{escape(describedby, quote=True)}">\n'
        )
        if "</head>" not in text:
            raise ValueError(f"HTML output has no closing head: {path}")
        path.write_text(text.replace("</head>", tags + "</head>", 1), encoding="utf-8")


def discover_versions(site_root: Path, current: str, base_url: str) -> list[dict[str, object]]:
    versions = {
        child.name
        for child in site_root.iterdir()
        if child.is_dir() and (child / "index.html").is_file()
    }
    versions.add(current)

    def sort_key(value: str) -> tuple[int, tuple[object, ...]]:
        if value == "latest":
            return (0, ())
        pieces: list[object] = []
        for piece in re.split(r"([0-9]+)", value):
            pieces.append(int(piece) if piece.isdigit() else piece)
        return (1, tuple(pieces))

    ordered = sorted(
        versions.difference({"latest"}),
        key=lambda value: sort_key(value)[1],
        reverse=True,
    )
    if "latest" in versions:
        ordered.insert(0, "latest")
    result = []
    for value in ordered:
        result.append(
            {
                "name": "latest (main)" if value == "latest" else value,
                "version": value,
                "url": url_join(base_url, value) + "/",
                "preferred": value == "latest",
            }
        )
    return result


def write_site_root(site_root: Path, versions: list[dict[str, object]], base_url: str) -> None:
    preferred = next(
        (entry for entry in versions if entry["preferred"]), versions[0]
    )
    target = str(preferred["url"])
    root_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url={escape(target, quote=True)}">
  <link rel="canonical" href="{escape(target, quote=True)}">
  <link rel="describedby" type="text/plain" href="{escape(url_join(base_url, 'llms.txt'), quote=True)}">
  <title>libwipi documentation</title>
</head>
<body><p><a href="{escape(target, quote=True)}">Open the latest libwipi documentation</a>.</p></body>
</html>
"""
    (site_root / "index.html").write_text(root_html, encoding="utf-8")
    versions_text = json.dumps(versions, indent=2, ensure_ascii=False) + "\n"
    (site_root / "versions.json").write_text(versions_text, encoding="utf-8")
    for html_path in site_root.glob("*/**/index.html"):
        (html_path.parent / "versions.json").write_text(
            versions_text, encoding="utf-8"
        )
    llms_lines = [
        "# libwipi documentation versions",
        "",
        "> Version selector and machine-readable entry points for libwipi.",
        "",
        "## Available documentation",
        "",
    ]
    for entry in versions:
        llms_lines.append(
            f"- [{entry['name']}]({url_join(str(entry['url']), 'llms.txt')}): "
            "Curated context for this SDK documentation version."
        )
    if (site_root / "schema" / "api-docs.schema.json").is_file():
        llms_lines.extend(
            [
                "",
                "## Machine-readable schemas",
                "",
                f"- [API documentation schema]({url_join(base_url, 'schema/api-docs.schema.json')}): "
                "JSON Schema for version-scoped api-docs.json files.",
            ]
        )
    llms_lines.append("")
    (site_root / "llms.txt").write_text("\n".join(llms_lines), encoding="utf-8")
    (site_root / ".nojekyll").write_text("", encoding="utf-8")


def write_discovery_files(site_root: Path, base_url: str) -> None:
    html_paths = sorted(site_root.glob("*/**/index.html"))
    urls = []
    for path in html_paths:
        version = path.relative_to(site_root).parts[0]
        version_dir = site_root / version
        urls.append(page_url(base_url, version, version_dir, path))
    sitemap = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    sitemap.extend(f"  <url><loc>{escape(url)}</loc></url>" for url in sorted(set(urls)))
    sitemap.extend(["</urlset>", ""])
    (site_root / "sitemap.xml").write_text("\n".join(sitemap), encoding="utf-8")
    (site_root / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {url_join(base_url, 'sitemap.xml')}\n",
        encoding="utf-8",
    )


def finalize(site_root: Path, version: str, base_url: str) -> None:
    site_root = site_root.resolve()
    version_dir = checked_child(site_root, site_root / version)
    if not (version_dir / "index.html").is_file():
        raise ValueError(f"missing rendered version index: {version_dir / 'index.html'}")
    normalize_markdown_download_urls(version_dir, version, base_url)
    html_paths = [
        path
        for path in sorted(version_dir.rglob("index.html"))
        if (version_dir / document_markdown_relative(version_dir, path)).is_file()
    ]
    if not html_paths:
        raise ValueError(f"no rendered pages have Markdown alternatives below: {version_dir}")
    write_nested_llms(version_dir, version, base_url, html_paths)
    inject_discovery(version_dir, version, base_url, html_paths)
    if version == "latest":
        schema_source = REPOSITORY_ROOT / "spec" / "schema" / "api-docs.schema.json"
        if not schema_source.is_file():
            raise ValueError(f"missing API documentation schema: {schema_source}")
        schema_target = site_root / "schema" / schema_source.name
        schema_target.parent.mkdir(parents=True, exist_ok=True)
        schema_target.write_bytes(schema_source.read_bytes())
    versions = discover_versions(site_root, version, base_url)
    write_site_root(site_root, versions, base_url)
    write_discovery_files(site_root, base_url)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--base-url", default="https://mirusu400.github.io/libwipi"
    )
    args = parser.parse_args()
    try:
        finalize(args.site_root, args.version, args.base_url)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
