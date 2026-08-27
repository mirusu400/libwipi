from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_IDS = ("graphics-gallery", "memory-resource", "audio-player")


class SDKExampleTests(unittest.TestCase):
    def test_manifest_keeps_build_and_runtime_axes_explicit(self):
        manifest = json.loads(
            (ROOT / "examples/sdk-lab.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema"], 1)
        self.assertEqual(manifest["api_level"], "1.2.1")
        self.assertEqual(manifest["abi_profile"], "lgt-raptor")
        self.assertEqual(manifest["install_profile"], "aram-wie-raptor")
        self.assertEqual(manifest["runtime_profile"], "wipi-1.2.1/lgt/raptor")
        self.assertRegex(manifest["aram"]["core_revision"], r"^[0-9a-f]{40}$")
        self.assertRegex(manifest["aram"]["runner_revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(
            tuple(example["id"] for example in manifest["examples"]),
            EXAMPLE_IDS,
        )
        for example in manifest["examples"]:
            package = Path(example["package"])
            self.assertFalse(package.is_absolute())
            self.assertNotIn("..", package.parts)
            self.assertEqual(example["probe"]["controls"].count(",") + 1,
                             len(example["probe"]["controls"].split(",")))
            self.assertGreater(example["expect"]["min_observed_apis"], 0)
            self.assertGreaterEqual(example["expect"]["min_frame_changes"], 1)

    def test_examples_use_the_shared_application_build(self):
        for example_id in EXAMPLE_IDS:
            with self.subTest(example=example_id):
                makefile = (ROOT / "examples" / example_id / "Makefile").read_text(
                    encoding="utf-8"
                )
                self.assertIn("mk/application.mk", makefile)
                for forbidden in ("-mcpu", "-mthumb", "-mfloat-abi", "-nostdlib"):
                    self.assertNotIn(forbidden, makefile)

    def test_examples_are_profile_independent_and_cover_their_families(self):
        required = {
            "graphics-gallery": (
                "MC_grpPutPixel",
                "MC_grpDrawLine",
                "MC_grpDrawRect",
                "MC_grpFillRect",
                "MC_grpDrawArc",
                "MC_grpFillArc",
                "MC_grpGetStringWidth",
            ),
            "memory-resource": (
                "MC_knlAlloc",
                "MC_knlCalloc",
                "MC_GETDPTR",
                "MC_knlFree",
                "MC_knlGetResourceID",
                "MC_knlGetResource",
            ),
            "audio-player": (
                "MC_mdaClipCreate",
                "MC_mdaClipPutData",
                "MC_mdaClipGetVolume",
                "MC_mdaClipSetVolume",
                "MC_mdaPlay",
                "MC_mdaStop",
                "MC_mdaClipFree",
            ),
        }
        for example_id, APIs in required.items():
            with self.subTest(example=example_id):
                source = (ROOT / "examples" / example_id / "main.c").read_text(
                    encoding="utf-8"
                )
                for API in APIs:
                    self.assertIn(API, source)
                for forbidden in (
                    "LIBWIPI_INSTALL_ARAM",
                    "LIBWIPI_LGT_ENVIRONMENT",
                    "aram-emu",
                    "ARAM",
                    "Wie",
                ):
                    self.assertNotIn(forbidden, source)

    def test_memory_example_packages_an_original_text_resource(self):
        resource = ROOT / "examples/memory-resource/assets/sdk-message.txt"
        self.assertEqual(resource.read_bytes(), b"LIBWIPI RESOURCE OK\n")
        makefile = (ROOT / "examples/memory-resource/Makefile").read_text(
            encoding="utf-8"
        )
        self.assertIn("assets/sdk-message.txt=res/sdk-message.txt", makefile)

    def test_root_makefile_exposes_one_sdk_example_gate(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("sdk-examples:", makefile)
        self.assertIn("test-sdk-examples:", makefile)
        for example_id in EXAMPLE_IDS:
            self.assertIn(f"examples/{example_id}", makefile)

    def test_example_documentation_avoids_em_dash(self):
        paths = [ROOT / "examples/README.md"]
        paths.extend(ROOT / "examples" / name / "README.md" for name in EXAMPLE_IDS)
        for path in paths:
            with self.subTest(path=path):
                self.assertNotIn("\u2014", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
