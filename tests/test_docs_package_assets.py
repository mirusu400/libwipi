import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import docs_package_assets
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

    def test_stage_publishes_download_hash_and_manifest(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            repository = root / "repository"
            site = root / "site"
            version = site / "latest"
            package = repository / "out/libwipi-audio-player.zip"
            self.package(package)
            record = self.record()
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

            docs_package_assets.stage_package_assets(
                repository_root=repository,
                site_root=site,
                version="latest",
                base_url="https://example.invalid/libwipi",
                source_revision="abc123",
                records=[record],
            )

            relative = docs_package_assets.package_site_path(record)
            published = version / relative
            self.assertEqual(published.read_bytes(), package.read_bytes())
            digest = hashlib.sha256(package.read_bytes()).hexdigest()
            rendered = (
                version / "generated/examples/audio-player/index.html"
            ).read_text(encoding="utf-8")
            self.assertIn(
                f"https://example.invalid/libwipi/latest/{relative.as_posix()}",
                rendered,
            )
            self.assertIn("download", rendered)
            self.assertIn(digest, rendered)
            self.assertNotIn("data-package-key", rendered)

            manifest = json.loads(
                (version / "packages/manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["source_revision"], "abc123")
            self.assertFalse(manifest["real_device"])
            self.assertEqual(manifest["packages"][0]["sha256"], digest)
            self.assertEqual(
                (version / "packages/SHA256SUMS").read_text(encoding="utf-8"),
                f"{digest}  {relative.relative_to('packages').as_posix()}\n",
            )

    def test_stage_rejects_a_package_path_outside_the_repository(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            repository = root / "repository"
            site = root / "site"
            (site / "latest").mkdir(parents=True)
            (site / "latest/index.html").write_text("home", encoding="utf-8")
            record = self.record()
            record["package"] = "../escape.zip"
            with self.assertRaisesRegex(ValueError, "below repository"):
                docs_package_assets.stage_package_assets(
                    repository_root=repository,
                    site_root=site,
                    version="latest",
                    base_url="https://example.invalid/libwipi",
                    source_revision="abc123",
                    records=[record],
                )

    def test_audio_page_declares_both_profile_package_markers(self):
        page = (ROOT / "docs/generated/examples/audio-player.md").read_text(
            encoding="utf-8"
        )
        for install_profile in ("aram-wie-raptor", "aram-raptor"):
            record = self.record()
            record["install_profile"] = install_profile
            self.assertIn(docs_package_assets.package_key(record), page)

    def test_every_compiled_example_variant_has_a_unique_marker(self):
        records = docs_package_assets.repository_package_records()
        self.assertEqual(len(records), 22)
        keys = {docs_package_assets.package_key(record) for record in records}
        self.assertEqual(len(keys), len(records))
        generated = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "docs/generated/examples").glob("*.md"))
        )
        for key in keys:
            self.assertEqual(generated.count(f'data-package-key="{key}"'), 1)

    def test_download_page_points_to_profile_specific_example_packages(self):
        page = (ROOT / "docs/generated/downloads.md").read_text(encoding="utf-8")
        self.assertIn("[Compiled example gallery](examples/index.md)", page)
        self.assertIn("profile-specific compiled ZIP", page)


if __name__ == "__main__":
    unittest.main()
