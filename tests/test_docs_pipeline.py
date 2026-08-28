import csv
import json
from pathlib import Path
import re
import tempfile
import unittest

from tools.finalize_docs_site import finalize


ROOT = Path(__file__).resolve().parents[1]


class DocumentationPipelineTests(unittest.TestCase):
    def test_catalog_location_is_manifest_driven(self):
        generator = (ROOT / "tools/generate.py").read_text(encoding="utf-8")
        self.assertNotIn(
            'ROOT / "spec" / "wipi-1.2.1" / "api.csv"', generator
        )
        self.assertIn("read_catalogs", generator)

    def test_api_docs_schema_and_inventory_are_versioned(self):
        schema = json.loads(
            (ROOT / "spec/schema/api-docs.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["title"], "libwipi API documentation")

        manifest = json.loads(
            (ROOT / "spec/versions.json").read_text(encoding="utf-8")
        )
        implemented = [
            entry
            for entry in manifest["levels"]
            if entry["catalog_status"] == "implemented"
        ]
        self.assertTrue(implemented)
        for entry in implemented:
            docs = json.loads((ROOT / entry["api_docs"]).read_text(encoding="utf-8"))
            self.assertEqual(docs["schema"], 1)
            self.assertEqual(docs["api_level"], entry["api_level"])
            self.assertEqual(docs["reference_revision"], entry["reference_revision"])
            self.assertTrue(docs["families"])
            self.assertTrue(docs["symbols"])

            with (ROOT / entry["catalog"]).open(encoding="utf-8", newline="") as stream:
                names = {row["name"] for row in csv.DictReader(stream)}
            self.assertLessEqual(set(docs["symbols"]), names)

    def test_generated_site_inventory_is_complete(self):
        manifest = json.loads(
            (ROOT / "spec/versions.json").read_text(encoding="utf-8")
        )
        for entry in manifest["levels"]:
            if entry["catalog_status"] != "implemented":
                continue
            api_root = ROOT / "docs/generated/api" / entry["api_level"]
            self.assertTrue((api_root / "index.md").is_file())
            with (ROOT / entry["catalog"]).open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            for row in rows:
                page = api_root / "symbols" / f"{row['name']}.md"
                self.assertTrue(page.is_file(), row["name"])
                text = page.read_text(encoding="utf-8")
                self.assertIn(row["prototype"], text)
                self.assertIn("API level", text)
                self.assertIn("Profile availability", text)

    def test_site_has_generated_support_examples_and_downloads(self):
        required = (
            "docs/generated/support-matrix.md",
            "docs/generated/examples/index.md",
            "docs/generated/downloads.md",
            "docs/llms-source.md",
            "docs/ko/index.md",
            "docs/ko/architecture.md",
            "docs/ko/testing.md",
            "docs/conf.py",
            "docs/Doxyfile",
            "docs/index.md",
        )
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)
        generated = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "docs/generated").rglob("*.md")
        )
        self.assertNotIn("github.com/mirusu400/libwipi/blob/main", generated)

    def test_support_matrix_counts_only_cataloged_public_apis(self):
        text = (ROOT / "docs/generated/support-matrix.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("| 59 observed APIs |", text)
        self.assertNotIn("| 60 observed APIs |", text)
        self.assertIn(
            "| `1.2.1/lgt-raptor/aram-raptor` | interactive on the named emulator contract",
            text,
        )

    def test_llms_source_is_v2_shaped_and_states_boundaries(self):
        text = (ROOT / "docs/llms-source.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"\A# libwipi\n\n> ")
        for required in (
            "API level, device ABI profile, and install profile are independent",
            "no real-device claim",
            "## Start here",
            "## API reference",
            "## Tests and downloads",
        ):
            self.assertIn(required, text)
        self.assertNotIn("llms-full.txt is the standard", text)

    def test_sphinx_build_is_strict_and_llm_generation_is_deterministic(self):
        conf = (ROOT / "docs/conf.py").read_text(encoding="utf-8")
        for extension in (
            '"myst_parser"',
            '"breathe"',
            '"sphinx_design"',
            '"sphinx_llm.txt"',
        ):
            self.assertIn(extension, conf)
        self.assertIn('html_theme = "pydata_sphinx_theme"', conf)
        self.assertIn("llms_txt_summary_enabled = False", conf)
        self.assertIn('llms_txt_override_source = "llms-source"', conf)
        self.assertIn("myst_html_meta = {", conf)
        self.assertIn('"show_version_warning_banner": False', conf)

        doxyfile = (ROOT / "docs/Doxyfile").read_text(encoding="utf-8")
        self.assertIn("$(LIBWIPI_DOXYGEN_API_DEFINE)", doxyfile)
        self.assertNotIn("LIBWIPI_API_LEVEL_1_2_1", doxyfile)

        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        for target in ("docs:", "docs-check:", "docs-linkcheck:", "release-bundles:"):
            self.assertIn(target, makefile)

    def test_pages_and_release_workflows_are_checked_in(self):
        docs = ROOT / ".github/workflows/docs.yml"
        release = ROOT / ".github/workflows/release.yml"
        self.assertTrue(docs.is_file())
        self.assertTrue(release.is_file())
        docs_text = docs.read_text(encoding="utf-8")
        release_text = release.read_text(encoding="utf-8")
        self.assertIn("actions/deploy-pages", docs_text)
        self.assertIn("python tools/build_docs.py", docs_text)
        self.assertIn("--builder linkcheck", docs_text)
        self.assertIn("tools/build_release_bundles.py", release_text)
        self.assertIn("actions/attest-build-provenance", release_text)
        self.assertIn("REQUESTED_TAG:", release_text)
        self.assertIn('tag="$REQUESTED_TAG"', release_text)

    def test_discovery_link_postprocessor_is_present(self):
        script = (ROOT / "tools/finalize_docs_site.py").read_text(encoding="utf-8")
        self.assertIn('rel="alternate"', script)
        self.assertIn('rel="describedby"', script)
        self.assertIn("versions.json", script)

    def test_discovery_only_targets_pages_with_markdown_alternates(self):
        html = '<html lang="en"><head><title>{}</title></head><body></body></html>'
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary)
            latest = site / "latest"
            for relative, title in (
                ("index.html", "Home"),
                ("ko/index.html", "한국어"),
                ("search/index.html", "Search"),
            ):
                path = latest / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(html.format(title), encoding="utf-8")
            download = latest / "_downloads" / "abc" / "fixture.txt"
            download.parent.mkdir(parents=True)
            download.write_text("fixture\n", encoding="utf-8")
            (latest / "index.md").write_text(
                "# Home\n\n"
                "[fixture](https://example.invalid/libwipi/latest/generated/"
                "_downloads/abc/fixture.txt)\n",
                encoding="utf-8",
            )
            (latest / "ko.md").write_text("# 한국어\n", encoding="utf-8")
            for version in ("v1.2.0", "v1.10.0"):
                path = site / version / "index.html"
                path.parent.mkdir(parents=True)
                path.write_text(html.format(version), encoding="utf-8")

            finalize(site, "latest", "https://example.invalid/libwipi")

            home = (latest / "index.html").read_text(encoding="utf-8")
            korean = (latest / "ko/index.html").read_text(encoding="utf-8")
            search = (latest / "search/index.html").read_text(encoding="utf-8")
            self.assertIn('rel="alternate"', home)
            self.assertIn('rel="describedby"', home)
            markdown = (latest / "index.md").read_text(encoding="utf-8")
            self.assertIn(
                "https://example.invalid/libwipi/latest/_downloads/abc/fixture.txt",
                markdown,
            )
            self.assertNotIn("latest/generated/_downloads", markdown)
            self.assertIn('<html lang="ko"', korean)
            self.assertNotIn('rel="alternate"', search)
            self.assertNotIn('rel="describedby"', search)
            self.assertFalse((latest / "search/llms.txt").exists())
            self.assertTrue((site / "schema/api-docs.schema.json").is_file())
            root_llms = (site / "llms.txt").read_text(encoding="utf-8")
            self.assertIn("schema/api-docs.schema.json", root_llms)
            versions = json.loads((site / "versions.json").read_text(encoding="utf-8"))
            self.assertEqual(
                [entry["version"] for entry in versions],
                ["latest", "v1.10.0", "v1.2.0"],
            )


if __name__ == "__main__":
    unittest.main()
