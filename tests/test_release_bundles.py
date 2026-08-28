import json
from pathlib import Path, PurePosixPath
import tempfile
import unittest
import zipfile

from tools import build_release_bundles


ROOT = Path(__file__).resolve().parents[1]


class ReleaseBundleTests(unittest.TestCase):
    def test_checked_in_bundles_have_explicit_compatibility_axes(self):
        manifest = json.loads(
            (ROOT / "spec/releases/bundles.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema"], 1)
        self.assertTrue(manifest["bundles"])
        for bundle in manifest["bundles"]:
            self.assertTrue(bundle["api_level"])
            self.assertTrue(bundle["abi_profile"])
            self.assertTrue(bundle["install_profile"])
            self.assertFalse(bundle["real_device"])

    def test_archive_is_safe_and_reproducible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repository"
            for relative, content in {
                "LICENSE": "license\n",
                "docs/testing.md": "# Testing\n",
                "fixture/package.zip": "package bytes\n",
                "fixture/main.c": "void fixture(void) {}\n",
                "fixture/suite.json": "{}\n",
                "spec/evidence.json": "{}\n",
                "spec/releases/bundles.json": "{}\n",
                "spec/versions.json": "{}\n",
                "spec/profiles/test.json": "{}\n",
                "spec/install/test.json": "{}\n",
            }.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            specification = {
                "schema": 1,
                "repository": "example/libwipi",
                "bundles": [
                    {
                        "id": "fixture",
                        "title": "Fixture",
                        "description": "A deterministic fixture.",
                        "api_level": "1.2.1",
                        "abi_profile": "test",
                        "install_profile": "test",
                        "build_target": "fixture",
                        "suite_manifest": "fixture/suite.json",
                        "evidence": "spec/evidence.json",
                        "packages": ["fixture/package.zip"],
                        "source_paths": ["fixture/main.c"],
                        "runner_owner": "test runner",
                        "real_device": False,
                    }
                ],
            }
            first = root / "out-a"
            second = root / "out-b"
            first_assets = build_release_bundles.build_bundles(
                root, specification, first, "v1.0.0", 315532800
            )
            second_assets = build_release_bundles.build_bundles(
                root, specification, second, "v1.0.0", 315532800
            )
            self.assertEqual(first_assets[0].read_bytes(), second_assets[0].read_bytes())

            with zipfile.ZipFile(first_assets[0]) as archive:
                names = archive.namelist()
                self.assertEqual(names, sorted(names))
                self.assertIn("bundle-manifest.json", names)
                self.assertIn("SHA256SUMS", names)
                self.assertIn("packages/package.zip", names)
                for name in names:
                    path = PurePosixPath(name)
                    self.assertFalse(path.is_absolute())
                    self.assertNotIn("..", path.parts)
                    self.assertNotIn("\\", name)


if __name__ == "__main__":
    unittest.main()
