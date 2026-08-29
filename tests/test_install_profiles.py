import json
import csv
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
            "257f10f3d34433ecfc4c72fabbfeb3e50af87723",
        )
        self.assertEqual(
            sources["aram_runner_revision"],
            "7bc29d5c7d55c5c9a93948883769fb2493c69669",
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


class ARAMInstallProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads(
            (ROOT / "spec/install/aram-raptor.json").read_text(encoding="utf-8")
        )
        cls.common = json.loads(
            (ROOT / "spec/install/aram-wie-raptor.json").read_text(
                encoding="utf-8"
            )
        )
        with (ROOT / "spec/wipi-1.2.1/api.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            cls.catalog = list(csv.DictReader(stream))

    def test_profile_is_aram_only_and_not_a_device_claim(self):
        profile = self.profile
        self.assertEqual(profile["id"], "aram-raptor")
        self.assertEqual(profile["api_level"], "1.2.1")
        self.assertEqual(profile["abi_profile"], "lgt-raptor")
        self.assertTrue(profile["target_build"])
        self.assertEqual(set(profile["emulators"]), {"aram"})
        self.assertTrue(profile["claims"]["emulator_package"])
        self.assertTrue(profile["claims"]["aram_runtime_verified"])
        self.assertFalse(profile["claims"]["wie_runtime_verified"])
        self.assertFalse(profile["claims"]["real_device"])
        self.assertFalse(profile["imports"]["synthetic_extension"]["device_abi_claim"])

    def test_synthetic_family_methods_follow_the_pinned_catalog_rule(self):
        methods = self.profile["imports"]["confirmed_public_methods"]
        self.assertEqual(len(methods), 100)
        synthetic_families = {"MC_FS", "MC_DB", "MC_MDA"}
        synthetic = {
            row["name"]: hex(0x7000 + int(row["ordinal"]))
            for row in self.catalog
            if row["family"] in synthetic_families
        }
        self.assertEqual(len(synthetic), 51)
        self.assertEqual(
            {name: methods[name] for name in synthetic},
            synthetic,
        )
        common = self.common["imports"]["confirmed_public_methods"]
        for name, method in common.items():
            family = next(row["family"] for row in self.catalog if row["name"] == name)
            if family not in synthetic_families:
                self.assertEqual(methods[name], method)

    def test_synthetic_contract_is_revision_and_scope_pinned(self):
        extension = self.profile["imports"]["synthetic_extension"]
        self.assertEqual(extension["base"], "0x7000")
        self.assertEqual(extension["rule"], "base-plus-wipi-1.2.1-catalog-ordinal")
        self.assertEqual(extension["families"], ["MC_FS", "MC_DB", "MC_MDA"])
        self.assertEqual(extension["provider_abi"], "aapcs-word-tail")
        self.assertEqual(extension["scope"], "aram-emulator-only")
        self.assertRegex(
            self.profile["emulators"]["aram"]["revision"], r"^[0-9a-f]{40}$"
        )

    def test_sdk_lab_evidence_records_exact_coverage_and_restart_checks(self):
        evidence = json.loads(
            (ROOT / self.profile["claims"]["sdk_lab_evidence"]).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(evidence["install_profile"], "aram-raptor")
        self.assertEqual(evidence["coverage"]["confirmed_imports"], 100)
        self.assertEqual(evidence["coverage"]["declared_required"], 100)
        self.assertEqual(evidence["coverage"]["observed_confirmed"], 100)
        self.assertEqual(evidence["coverage"]["unimplemented_calls"], 0)
        self.assertEqual(len(evidence["examples"]), 10)
        self.assertTrue(evidence["persistence"]["database"]["passed"])
        self.assertTrue(evidence["persistence"]["filesystem"]["passed"])
        self.assertFalse(evidence["claims"]["wie_verified"])
        self.assertFalse(evidence["claims"]["real_device_verified"])


class ARAMKTFInstallProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads(
            (ROOT / "spec/install/aram-ktf.json").read_text(encoding="utf-8")
        )

    def test_profile_keeps_carrier_archive_and_emulator_claims_separate(self):
        profile = self.profile
        self.assertEqual(profile["id"], "aram-ktf")
        self.assertEqual(profile["api_level"], "1.2.1")
        self.assertEqual(profile["abi_profile"], "ktf-samsung")
        self.assertEqual(set(profile["emulators"]), {"aram"})
        self.assertTrue(profile["claims"]["emulator_package"])
        self.assertTrue(profile["claims"]["aram_runtime_verified"])
        self.assertTrue(profile["claims"]["packages"])
        self.assertTrue(profile["claims"]["loads"])
        self.assertTrue(profile["claims"]["entry"])
        self.assertTrue(profile["claims"]["first_frame"])
        self.assertFalse(profile["claims"]["real_device"])

    def test_loader_and_bootstrap_contract_are_explicit(self):
        container = self.profile["container"]
        self.assertEqual(container["outer_archive"], "zip")
        self.assertEqual(container["metadata"], "__adf__")
        self.assertEqual(container["inner_archive"], "{aid}.jar")
        self.assertEqual(container["executable"], "client.bin{decimal_bss_size}")
        self.assertEqual(container["executable_format"], "raw-ARM-image")
        self.assertEqual(container["image_base"], "0x00100000")
        self.assertEqual(container["entry_rule"], "image_base | 1")
        self.assertEqual(container["bootstrap_result"], "WipiExe pointer")

        imports = self.profile["imports"]
        self.assertEqual(imports["lookup_name"], "WIPIC_knlInterface")
        self.assertEqual(imports["master_vector_getter_offset"], "0x84")
        self.assertEqual(imports["provider_abi"], "samsung-packed-words")

    def test_native_wrapper_scope_is_not_a_handset_verification_claim(self):
        lifecycle = self.profile["lifecycle"]
        self.assertEqual(lifecycle["main_class"], "LibwipiClet")
        self.assertEqual(lifecycle["start_bridge"], "startApp -> startClet")
        self.assertEqual(lifecycle["scope"], "libwipi ARAM wrapper")
        self.assertFalse(lifecycle["device_abi_claim"])

        evidence = json.loads(
            (ROOT / self.profile["claims"]["first_frame_evidence"]).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(evidence["install_profile"], "aram-ktf")
        self.assertEqual(evidence["coverage"]["packages"], 14)
        self.assertEqual(evidence["coverage"]["ok_frame"], 14)
        self.assertEqual(evidence["coverage"]["unimplemented_calls"], 0)
        self.assertFalse(evidence["claims"]["interactive_verified"])
        self.assertFalse(evidence["claims"]["real_device_verified"])

if __name__ == "__main__":
    unittest.main()
