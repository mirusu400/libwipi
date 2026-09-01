import hashlib
from html import unescape
import json
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import parse_qs, urlparse

from tools import docs_package_assets
from tools import package_ktf
from tools import package_raptor


ROOT = Path(__file__).resolve().parents[1]


class DocumentationPackageAssetTests(unittest.TestCase):
    def package(self, path: Path, aid: str = "libwipi-audio-player") -> None:
        inner = package_raptor.make_zip(
            [
                ("META-INF/MANIFEST.MF", package_raptor.MANIFEST),
                ("binary.mod", b"\x7fELF" + bytes(48)),
            ]
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            package_raptor.make_zip(
                [
                    (
                        "app_info",
                        package_raptor.descriptor(
                            aid, "libwipi", "Audio Player", "01.00.00", "libwipi"
                        ),
                    ),
                    (f"{aid}.jar", inner),
                ]
            )
        )

    def record(self) -> dict[str, str]:
        return {
            "example_id": "audio-player",
            "api_level": "1.2.1",
            "abi_profile": "lgt-raptor",
            "install_profile": "aram-wie-raptor",
            "package": "out/libwipi-audio-player.zip",
        }

    def ktf_package(self, path: Path, aid: str = "libwipi-audio-player") -> None:
        inner = package_ktf.make_zip(
            [
                ("META-INF/MANIFEST.MF", package_ktf.MANIFEST),
                ("client.bin64", b"\x00\xb5\x00\xbd"),
            ]
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            package_ktf.make_zip(
                [
                    (
                        "__adf__",
                        package_ktf.descriptor(
                            aid,
                            "libwipi",
                            "AudioPlayer",
                            "01.00.00",
                            "libwipi",
                            "LibwipiClet",
                            (240, 320),
                        ),
                    ),
                    (f"{aid}.jar", inner),
                ]
            )
        )

    def rendered_site(self, site: Path, record: dict[str, str]) -> None:
        version = site / "latest"
        marker = docs_package_assets.package_marker(record)
        (version / "generated/examples/audio-player").mkdir(
            parents=True, exist_ok=True
        )
        (version / "index.html").write_text("home", encoding="utf-8")
        (version / "generated/examples/audio-player/index.html").write_text(
            marker, encoding="utf-8"
        )
        (version / "generated/examples/audio-player.md").write_text(
            marker, encoding="utf-8"
        )

    def test_update_then_stage_uses_the_checked_in_package(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            repository = root / "repository"
            site = root / "site"
            package = repository / "out/libwipi-audio-player.zip"
            self.package(package)
            record = self.record()
            docs_package_assets.update_static_package_set(
                repository_root=repository,
                built_from="build123",
                records=[record],
            )
            static_package = repository / "docs" / docs_package_assets.package_site_path(
                record
            )
            self.assertEqual(static_package.read_bytes(), package.read_bytes())

            # Publication must not depend on ignored compiler output still existing.
            package.unlink()
            self.rendered_site(site, record)

            docs_package_assets.stage_package_assets(
                repository_root=repository,
                site_root=site,
                version="latest",
                base_url="https://example.invalid/libwipi",
                documentation_revision="docs456",
                records=[record],
            )

            version = site / "latest"
            relative = docs_package_assets.package_site_path(record)
            published = version / relative
            self.assertEqual(published.read_bytes(), static_package.read_bytes())
            digest = hashlib.sha256(static_package.read_bytes()).hexdigest()
            rendered = (
                version / "generated/examples/audio-player/index.html"
            ).read_text(encoding="utf-8")
            self.assertIn(
                f"https://example.invalid/libwipi/latest/{relative.as_posix()}",
                rendered,
            )
            self.assertIn("download", rendered)
            self.assertIn("Run in ARAM", rendered)
            self.assertIn(digest, rendered)
            self.assertIn("build123", rendered)
            self.assertNotIn("data-package-key", rendered)

            run_link = re.search(
                r'<a class="reference external libwipi-run-aram" href="([^"]+)"'
                r' target="_blank" rel="noopener">',
                rendered,
            )
            self.assertIsNotNone(run_link)
            permalink = urlparse(unescape(run_link.group(1)))
            self.assertEqual(
                f"{permalink.scheme}://{permalink.netloc}{permalink.path}",
                "https://aram.mir.sh/player/",
            )
            query = parse_qs(permalink.query)
            self.assertEqual(query["ch"], ["nightly"])
            self.assertEqual(
                query["app"],
                [f"https://example.invalid/libwipi/latest/{relative.as_posix()}"],
            )
            self.assertEqual(query["sha256"], [digest])

            manifest = json.loads(
                (version / "packages/manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["documentation_revision"], "docs456")
            self.assertEqual(manifest["built_from"], "build123")
            self.assertFalse(manifest["real_device"])
            self.assertEqual(manifest["packages"][0]["sha256"], digest)
            self.assertEqual(
                (version / "packages/SHA256SUMS").read_text(encoding="utf-8"),
                f"{digest}  {relative.relative_to('packages').as_posix()}\n",
            )

    def test_update_rejects_a_package_path_outside_the_repository(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            repository = root / "repository"
            record = self.record()
            record["package"] = "../escape.zip"
            with self.assertRaisesRegex(ValueError, "below repository"):
                docs_package_assets.update_static_package_set(
                    repository_root=repository,
                    built_from="build123",
                    records=[record],
                )

    def test_stage_rejects_a_modified_checked_in_package(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            repository = root / "repository"
            site = root / "site"
            package = repository / "out/libwipi-audio-player.zip"
            self.package(package)
            record = self.record()
            docs_package_assets.update_static_package_set(
                repository_root=repository,
                built_from="build123",
                records=[record],
            )
            static_package = repository / "docs" / docs_package_assets.package_site_path(
                record
            )
            static_package.write_bytes(static_package.read_bytes() + b"tampered")
            self.rendered_site(site, record)

            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                docs_package_assets.stage_package_assets(
                    repository_root=repository,
                    site_root=site,
                    version="latest",
                    base_url="https://example.invalid/libwipi",
                    documentation_revision="docs456",
                    records=[record],
                )

    def test_inspector_dispatches_ktf_packages_by_install_profile(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            package = Path(raw_directory) / "libwipi-audio-player.zip"
            self.ktf_package(package)
            record = self.record()
            record["abi_profile"] = "ktf-samsung"
            record["install_profile"] = "aram-ktf"

            inspection = docs_package_assets.inspect_compiled_package(record, package)

            self.assertEqual(inspection["aid"], "libwipi-audio-player")
            self.assertEqual(inspection["module"], "client.bin64")
            self.assertEqual(inspection["bss_size"], 64)

            record["abi_profile"] = "ktf-samsung"
            record["install_profile"] = "sch-w8300-qpst-probe"
            inspection = docs_package_assets.inspect_compiled_package(
                record, package
            )
            self.assertEqual(inspection["aid"], "libwipi-audio-player")
            self.assertEqual(inspection["module"], "client.bin64")

    def test_audio_page_declares_all_profile_package_markers(self):
        page = (ROOT / "docs/generated/examples/audio-player.md").read_text(
            encoding="utf-8"
        )
        for abi_profile, install_profile in (
            ("lgt-raptor", "aram-wie-raptor"),
            ("lgt-raptor", "aram-raptor"),
            ("ktf-samsung", "aram-ktf"),
        ):
            record = self.record()
            record["abi_profile"] = abi_profile
            record["install_profile"] = install_profile
            self.assertIn(docs_package_assets.package_key(record), page)

    def test_every_compiled_example_variant_has_a_unique_marker(self):
        records = docs_package_assets.repository_package_records()
        self.assertEqual(len(records), 37)
        keys = {docs_package_assets.package_key(record) for record in records}
        self.assertEqual(len(keys), len(records))
        generated = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "docs/generated/examples").glob("*.md"))
        )
        for key in keys:
            self.assertEqual(generated.count(f'data-package-key="{key}"'), 1)

    def test_checked_in_package_set_covers_every_compiled_variant(self):
        records = docs_package_assets.repository_package_records()
        manifest, entries = docs_package_assets.verify_static_package_set(ROOT, records)
        self.assertEqual(len(entries), 37)
        self.assertRegex(manifest["built_from"], r"\A[0-9a-f]{40}\Z")

    def test_download_page_points_to_profile_specific_example_packages(self):
        page = (ROOT / "docs/generated/downloads.md").read_text(encoding="utf-8")
        self.assertIn("[Compiled example gallery](examples/index.md)", page)
        self.assertIn("profile-specific checked-in compiled ZIP", page)
        self.assertIn("checked-in", page)

    def test_example_index_explains_integrity_checked_aram_launches(self):
        page = (ROOT / "docs/generated/examples/index.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Run in ARAM", page)
        self.assertIn("SHA-256", page)
        self.assertIn("not uploaded", page)


if __name__ == "__main__":
    unittest.main()
