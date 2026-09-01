import csv
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ID = "skt-samsung-sch-w830-dl21"


class SktSchW830ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads(
            (ROOT / "spec/profiles" / f"{PROFILE_ID}.json").read_text(
                encoding="utf-8"
            )
        )
        with (ROOT / cls.profile["bindings"]).open(
            encoding="utf-8", newline=""
        ) as stream:
            cls.bindings = list(csv.DictReader(stream))
        with (ROOT / "spec/wipi-1.2.1/api.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            cls.catalog = list(csv.DictReader(stream))

    def test_profile_is_exactly_scoped(self):
        profile = self.profile
        self.assertEqual(profile["id"], PROFILE_ID)
        self.assertEqual(profile["carrier"], "SKT")
        self.assertEqual(profile["oem"], "Samsung")
        self.assertEqual(profile["device"], "SCH-W830")
        self.assertEqual(profile["firmware"], "DL21")
        self.assertEqual(profile["process_import_pointer"], "0x01001000")
        self.assertEqual(
            profile["direct_root_fields"],
            {"MC_KNL": "0x00", "MC_GRP": "0x04", "MC_FS": "0x0c", "MC_NET": "0x14"},
        )
        mapping = profile["api_level_mappings"]["1.2.1"]
        self.assertTrue(mapping["target_build"])
        self.assertEqual(
            mapping["install_profiles"],
            ["none"],
        )
        self.assertFalse(profile["claims"]["package"])
        self.assertFalse(profile["claims"]["loads"])
        self.assertFalse(profile["claims"]["real_device"])

    def test_only_direct_sch_bindings_are_admitted(self):
        self.assertEqual(len(self.bindings), 71)
        self.assertEqual(len({row["name"] for row in self.bindings}), 71)
        by_name = {row["name"]: row for row in self.catalog}
        allowed_fields = self.profile["direct_root_fields"]
        for binding in self.bindings:
            self.assertEqual(binding["confidence"], "confirmed")
            self.assertIn(binding["family"], allowed_fields)
            self.assertEqual(binding["root_field"], allowed_fields[binding["family"]])
            catalog = by_name[binding["name"]]
            self.assertEqual(binding["ordinal"], catalog["ordinal"])
            self.assertEqual(binding["family"], catalog["family"])
            self.assertEqual(binding["slot"], catalog["ktf_samsung_slot"])
            self.assertEqual(catalog["implementation"], "table")
            self.assertTrue(binding["evidence"].startswith("anycall_magichole@"))

    def test_unverified_methods_are_not_promoted(self):
        names = {row["name"] for row in self.bindings}
        self.assertEqual(
            {name for name in names if name in {"MC_knlPrintk", "MC_knlSprintk", "MC_knlExecute"}},
            {"MC_knlPrintk", "MC_knlSprintk"},
        )
        for provider_only in (
            "MC_grpPutPixel",
            "MC_fsSetMode",
            "MC_netSocketAccept",
            "MC_knlExecute",
            "MC_uicCreateApplicationContext",
            "MC_mdaClipCreate",
        ):
            self.assertNotIn(provider_only, names)
        self.assertEqual(self.profile["coverage"]["confirmed_table_bindings"], 71)
        self.assertEqual(self.profile["coverage"]["generated_table_veneers"], 69)
        self.assertEqual(self.profile["coverage"]["local_cstdlib_symbols"], 31)
        self.assertEqual(self.profile["coverage"]["linkable_public_symbols"], 100)


if __name__ == "__main__":
    unittest.main()
