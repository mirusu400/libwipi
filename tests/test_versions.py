import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ApiVersionManifestTests(unittest.TestCase):
    def setUp(self):
        with (ROOT / "spec/versions.json").open(encoding="utf-8") as stream:
            self.manifest = json.load(stream)
        self.profiles = {
            path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in (ROOT / "spec/profiles").glob("*.json")
        }

    def test_supported_version_line_is_explicit(self):
        levels = [entry["api_level"] for entry in self.manifest["levels"]]
        self.assertEqual(
            levels,
            ["1.2.1", "2.0", "2.0.1", "2.1.0", "2.2.0"],
        )
        self.assertEqual(self.manifest["bootstrap_api_level"], "1.2.1")

    def test_catalog_claims_have_checked_in_sources(self):
        for entry in self.manifest["levels"]:
            catalog = entry.get("catalog")
            if entry["catalog_status"] == "implemented":
                self.assertIsNotNone(catalog)
                self.assertTrue((ROOT / catalog).is_file())
                self.assertTrue((ROOT / entry["api_docs"]).is_file())
                invariants = entry["catalog_invariants"]
                self.assertGreater(invariants["public_rows"], 0)
                self.assertGreater(invariants["family_count"], 0)
            else:
                self.assertIsNone(catalog)
                self.assertIsNone(entry.get("api_docs"))

    def test_version_is_not_conflated_with_device_profile(self):
        for entry in self.manifest["levels"]:
            self.assertNotIn("profile", entry)
            self.assertNotIn("carrier", entry)

        known_levels = {entry["api_level"] for entry in self.manifest["levels"]}
        for name, profile in self.profiles.items():
            self.assertEqual(profile["id"], name)
            self.assertNotIn("wipi", profile)
            mappings = profile["api_level_mappings"]
            self.assertTrue(mappings)
            self.assertLessEqual(set(mappings), known_levels)
            for mapping in mappings.values():
                self.assertIsInstance(mapping["headers"], bool)
                self.assertIsInstance(mapping["target_build"], bool)

        available = {
            f"{level}/{profile['id']}"
            for profile in self.profiles.values()
            for level, mapping in profile["api_level_mappings"].items()
            if mapping["target_build"]
        }
        self.assertEqual(
            available,
            {
                "1.2.1/ktf-samsung",
                "1.2.1/lgt-raptor",
                "1.2.1/skt-samsung-sch-w830-dl21",
            },
        )

    def test_profile_abi_fact_groups_have_evidence(self):
        fact_groups = {
            "host-sim": {"host_layouts_are_device_evidence"},
            "ktf-samsung": {
                "architecture",
                "process_import_root",
                "direct_root_fields",
                "master_vector",
                "master_vector_getter",
                "layouts",
                "shared_buffer_slots",
                "memory_resolution",
            },
            "lgt-raptor": {
                "architecture",
                "container",
                "import_module",
                "known_public_methods",
                "layouts",
                "memory_resolution",
            },
            "skt-samsung-sch-w830-dl21": {
                "architecture",
                "process_import_pointer",
                "direct_root_fields",
                "bindings",
                "coverage",
                "layouts",
                "memory_resolution",
            },
        }
        for name, expected in fact_groups.items():
            profile = self.profiles[name]
            evidence = profile["fact_evidence"]
            self.assertEqual(set(evidence), expected)
            for fact in expected:
                self.assertIn(fact, profile)
                metadata = evidence[fact]
                self.assertEqual(metadata["profile"], name)
                self.assertIn(
                    metadata["confidence"], {"confirmed", "candidate", "unknown"}
                )
                self.assertTrue(metadata["source"])
                if metadata["confidence"] != "confirmed":
                    self.assertTrue(metadata["validation_need"])

    def test_indexed_wiki_references_are_revision_pinned(self):
        for entry in self.manifest["levels"]:
            if "mirusu400.github.io" in entry["reference_url"]:
                self.assertRegex(
                    entry["reference_revision"],
                    r"^mirusu400/wipi-wiki@[0-9a-f]{40}$",
                )


if __name__ == "__main__":
    unittest.main()
