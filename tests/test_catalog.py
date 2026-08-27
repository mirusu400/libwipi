import csv
import json
from collections import Counter
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "spec/wipi-1.2.1/api.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_inventory_and_confidence(self):
        self.assertEqual(len(self.rows), 239)
        self.assertEqual([int(row["ordinal"]) for row in self.rows], list(range(1, 240)))
        self.assertEqual(len({row["name"] for row in self.rows}), 239)
        confidence = Counter(row["ktf_samsung_confidence"] for row in self.rows)
        self.assertEqual(confidence, {"confirmed": 229, "candidate": 10})

    def test_candidates_are_local_cstdlib(self):
        candidates = [
            row for row in self.rows if row["ktf_samsung_confidence"] == "candidate"
        ]
        self.assertTrue(candidates)
        self.assertTrue(
            all(
                row["family"] == "CSTDLIB" and row["implementation"] == "local"
                for row in candidates
            )
        )

    def test_special_abi_rows(self):
        by_name = {row["name"]: row for row in self.rows}
        self.assertEqual(by_name["MC_knlSetTimer"]["ktf_samsung_slot"], "+0x68")
        self.assertEqual(
            by_name["MC_knlSetTimer"]["abi_class"], "aapcs-to-packed-i64"
        )
        for name in ("MC_knlPrintk", "MC_knlSprintk", "MC_knlExecute"):
            self.assertEqual(by_name[name]["abi_class"], "variadic-unverified")

    def test_profile_boundaries(self):
        ktf = json.loads((ROOT / "spec/profiles/ktf-samsung.json").read_text())
        lgt = json.loads((ROOT / "spec/profiles/lgt-raptor.json").read_text())
        self.assertEqual(ktf["shared_buffer_slots"]["MC_knlDestroySharedBuf"], "0x4c")
        self.assertEqual(ktf["master_vector_getter"]["slot"], "0x84")
        self.assertEqual(ktf["layouts"]["MC_GrpContext"], 60)
        self.assertEqual(lgt["layouts"]["MC_GrpContext"], 56)
        self.assertEqual(lgt["import_module"], "0x1fb")


if __name__ == "__main__":
    unittest.main()
