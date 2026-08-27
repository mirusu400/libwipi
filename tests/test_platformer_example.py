from pathlib import Path
import hashlib
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PlatformerExampleTests(unittest.TestCase):
    def test_example_uses_the_shared_application_build(self):
        makefile = (ROOT / "examples/platformer/Makefile").read_text(
            encoding="utf-8"
        )
        self.assertIn("mk/application.mk", makefile)
        for forbidden in ("-mcpu", "-mthumb", "-mfloat-abi", "-nostdlib"):
            self.assertNotIn(forbidden, makefile)

    def test_game_is_original_and_profile_independent(self):
        source = (ROOT / "examples/platformer/main.c").read_text(
            encoding="utf-8"
        )
        for required in (
            "SKY HOPPER",
            "MC_knlDefTimer",
            "MC_grpFillRect",
            "WIPI_CLET_KEY_LEFT",
            "WIPI_CLET_KEY_SELECT",
            "handleCletEvent",
        ):
            self.assertIn(required, source)
        for forbidden in (
            "Mario",
            "mario",
            "LIBWIPI_INSTALL_ARAM",
            "LIBWIPI_LGT_ENVIRONMENT",
        ):
            self.assertNotIn(forbidden, source)

    def test_readme_documents_gameplay_and_scope(self):
        readme = (ROOT / "examples/platformer/README.md").read_text(
            encoding="utf-8"
        )
        for required in (
            "Left/Right",
            "Up/OK",
            "original",
            "platformer",
            "aram-wie-raptor",
        ):
            self.assertIn(required, readme)

    def test_emulator_evidence_is_artifact_scoped(self):
        evidence = json.loads(
            (ROOT / "spec/evidence/platformer-example.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(evidence["example"], "examples/platformer/main.c")
        self.assertRegex(evidence["artifact"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(evidence["aram"]["unimplemented_calls"], 0)
        self.assertGreaterEqual(evidence["aram"]["frame_changes"], 3)
        self.assertGreaterEqual(evidence["wie"]["unique_frames"], 3)
        self.assertFalse(evidence["claims"]["real_device_verified"])
        package = ROOT / evidence["artifact"]["package"]
        if package.is_file():
            package_bytes = package.read_bytes()
            self.assertEqual(len(package_bytes), evidence["artifact"]["size"])
            self.assertEqual(
                hashlib.sha256(package_bytes).hexdigest(),
                evidence["artifact"]["sha256"],
            )


if __name__ == "__main__":
    unittest.main()
