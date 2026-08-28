"""Sphinx configuration for the versioned libwipi documentation portal."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_VERSION = os.environ.get("LIBWIPI_DOCS_VERSION", "latest")
SITE_ROOT = os.environ.get(
    "LIBWIPI_DOCS_SITE_URL", "https://mirusu400.github.io/libwipi"
).rstrip("/")
VERSION_URL = f"{SITE_ROOT}/{DOCS_VERSION}"

project = "libwipi"
author = "libwipi contributors"
copyright = "libwipi contributors"
version = DOCS_VERSION
release = DOCS_VERSION

extensions = [
    "myst_parser",
    "breathe",
    "sphinx_design",
    "sphinx_llm.txt",
]

source_suffix = {".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
templates_path = ["_templates"]
primary_domain = "c"
highlight_language = "c"

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 4

doxygen_xml = os.environ.get(
    "LIBWIPI_DOXYGEN_XML", str(ROOT / "build" / "docs" / "doxygen" / "xml")
)
breathe_projects = {"libwipi": doxygen_xml}
breathe_default_project = "libwipi"
breathe_domain_by_extension = {"h": "c"}

html_theme = "pydata_sphinx_theme"
html_title = f"libwipi {DOCS_VERSION}"
html_baseurl = VERSION_URL + "/"
html_static_path = ["_static"]
html_extra_path = ["versions.json"]
html_css_files = ["custom.css"]
html_favicon = "_static/favicon.svg"
html_last_updated_fmt = None
html_show_sourcelink = True
html_theme_options = {
    "navbar_align": "left",
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["version-switcher", "theme-switcher", "navbar-icon-links"],
    "header_links_before_dropdown": 5,
    "header_dropdown_text": "Resources",
    "show_version_warning_banner": False,
    "switcher": {
        "json_url": "versions.json",
        "version_match": DOCS_VERSION,
    },
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/mirusu400/libwipi",
            "icon": "fa-brands fa-github",
            "type": "fontawesome",
        }
    ],
    "footer_start": ["copyright"],
    "footer_end": ["sphinx-version"],
}
html_context = {
    "default_mode": "auto",
    "github_user": "mirusu400",
    "github_repo": "libwipi",
    "github_version": "main" if DOCS_VERSION == "latest" else DOCS_VERSION,
    "doc_path": "docs",
}
myst_html_meta = {
    "description": (
        "Freestanding WIPI-C SDK API, ABI profile, packaging, and emulator "
        "conformance documentation."
    ),
    "og:type": "website",
    "og:site_name": "libwipi documentation",
}

# The llms.txt source is curated and reviewable. Builds never call an LLM.
llms_txt_summary_enabled = False
llms_txt_override_source = "llms-source"
llms_txt_suffix_mode = "url-suffix"
llms_txt_full_build = True
llms_txt_build_parallel = False
markdown_http_base = VERSION_URL

# Same-repository links are generated from checked-in paths and would otherwise
# trigger GitHub's anonymous link-check rate limiter hundreds of times.
linkcheck_ignore = [r"https://github\.com/mirusu400/libwipi(?:/.*)?$"]
linkcheck_retries = 3
linkcheck_timeout = 20
linkcheck_workers = 1
