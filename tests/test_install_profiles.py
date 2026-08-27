import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "spec/install/aram-wie-raptor.json"
        cls.profile = json.loads(path.read_text(encoding="utf-8"))

    def test_profile_axes_and_claim_boundary(self):
        profile = self.profile
        self.assertEqual(profile["id"], "aram-wie-raptor")
        self.assertEqual(profile["api_level"], "1.2.1")
        self.assertEqual(profile["abi_profile"], "lgt-raptor")
        self.assertTrue(profile["target_build"])
        self.assertEqual(set(profile["emulators"]), {"aram", "wie"})
        self.assertTrue(profile["claims"]["emulator_package"])
        self.assertTrue(profile["claims"]["aram_runtime_verified"])
        self.assertTrue(profile["claims"]["wie_runtime_verified"])
        self.assertFalse(profile["claims"]["real_device"])

    def test_runtime_claims_point_to_scoped_evidence(self):
        evidence_path = ROOT / self.profile["claims"]["conformance_evidence"]
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertEqual(evidence["install_profile"], self.profile["id"])
        self.assertEqual(evidence["coverage"]["observed_public_apis"], 24)
        self.assertEqual(evidence["aram"]["unimplemented_calls"], 0)
        self.assertGreaterEqual(evidence["wie"]["unique_frames"], 2)
        self.assertRegex(evidence["artifact"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse(evidence["claims"]["real_device_verified"])

    def test_loader_contract_is_explicit(self):
        container = self.profile["container"]
        self.assertEqual(container["outer_archive"], "zip")
        self.assertEqual(container["inner_archive"], "{aid}.jar")
        self.assertEqual(container["executable"], "binary.mod")
        self.assertEqual(container["executable_format"], "ELF32-ARM-ET_EXEC")
        self.assertEqual(container["elf_entry"], "aligned-thumb-code-address")
        self.assertEqual(container["aram_entry_rule"], "entry | 1")
        self.assertEqual(container["wie_entry_rule"], "entry + 1")
        self.assertEqual(container["aram_metadata_section"], ".raptor")
        self.assertEqual(container["dependency_output_offset"], "0x214")
        self.assertEqual(container["clet_descriptor_words"], 12)

    def test_wie_imports_and_aram_deltas_are_revision_pinned(self):
        imports = self.profile["imports"]
        self.assertEqual(imports["module"], "0x1fb")
        self.assertEqual(imports["clet_register_method"], "0x3")
        self.assertEqual(imports["default_environment"], "wie")
        self.assertEqual(len(imports["confirmed_public_methods"]), 59)
        self.assertEqual(
            imports["confirmed_public_methods"]["MC_knlSetTimer"], "0x7b"
        )
        self.assertEqual(
            imports["confirmed_public_methods"]["MC_grpDrawString"], "0xda"
        )
        self.assertEqual(
            imports["aram_method_overrides"],
            {
                "MC_grpCopyArea": "0xd6",
                "MC_grpDrawArc": "0xd7",
                "MC_grpFillArc": "0xd8",
                "MC_grpDrawString": "0xd9",
                "MC_grpGetRGBPixels": "0xdb",
                "MC_grpSetRGBPixels": "0xdc",
            },
        )
        self.assertEqual(
            imports["confirmed_public_methods"]["MC_mdaPlay"], "0x4ba"
        )
        self.assertEqual(
            imports["return_overrides"],
            {
                "MC_grpGetDisplayInfo": {
                    "environment": "wie",
                    "provider_success": 1,
                    "public_success": 0,
                }
            },
        )
        sources = self.profile["evidence"]
        self.assertEqual(
            sources["aram_revision"],
            "d62ce143f0c325a8aff53de005a767c26116fff5",
        )
        self.assertEqual(
            sources["aram_runner_revision"],
            "e8fd74d51a76cbb4ddc11218a9c5eac46ac4ba91",
        )
        self.assertEqual(
            sources["wie_revision"],
            "739389449482cebfba6333f3015466bb76070c21",
        )

    def test_entry_contract_discriminates_adapter_maps_outside_app_code(self):
        entry = self.profile["entry_environment"]
        self.assertEqual(entry["aram_third_argument"], "nonzero-wipic-base")
        self.assertEqual(entry["wie_third_argument"], "zero")
        self.assertEqual(entry["scope"], "abi-adapter-only")

    def test_wie_key_codes_are_normalized_in_the_adapter(self):
        lifecycle = self.profile["lifecycle"]
        self.assertEqual(
            lifecycle["public_key_values"],
            {"up": -1, "down": -2, "left": -3, "right": -4, "select": -5},
        )
        self.assertEqual(
            lifecycle["wie_provider_key_overrides"],
            {"141": -1, "146": -2, "142": -3, "145": -4, "148": -5},
        )
        self.assertEqual(lifecycle["key_normalization_scope"], "abi-adapter-only")

    def test_emulator_memory_rule_is_not_a_device_default(self):
        memory = self.profile["memory_resolution"]
        self.assertEqual(memory["representation"], "direct-guest-address")
        self.assertEqual(memory["scope"], "aram-and-wie-emulator-install-only")
        self.assertFalse(memory["device_abi_claim"])


if __name__ == "__main__":
    unittest.main()
