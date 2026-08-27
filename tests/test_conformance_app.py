import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ConformanceAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "examples/conformance/main.c").read_text(
            encoding="utf-8"
        )
        cls.coverage = json.loads(
            (ROOT / "examples/conformance/coverage.json").read_text(
                encoding="utf-8"
            )
        )

    def test_observable_categories_are_explicit(self):
        self.assertEqual(
            set(self.coverage["categories"]),
            {"audio", "font", "graphics", "input", "memory", "system", "timer"},
        )
        for category, contract in self.coverage["categories"].items():
            self.assertTrue(contract["apis"], category)
            self.assertTrue(contract["observable"], category)
            for api in contract["apis"]:
                self.assertIn(api, self.source, f"{category}: {api}")

    def test_application_code_has_no_emulator_checks(self):
        for forbidden in (
            "ARAM",
            "WIE",
            "LIBWIPI_INSTALL_",
            "LIBWIPI_PROFILE_",
        ):
            self.assertNotIn(forbidden, self.source)

    def test_known_cross_emulator_exclusions_are_not_hidden(self):
        exclusions = self.coverage["known_exclusions"]
        self.assertIn("storage", exclusions)
        self.assertIn("backlight", exclusions)
        self.assertIn("vibration", exclusions)
        self.assertTrue(all(entry["reason"] for entry in exclusions.values()))

    def test_synthetic_smaf_has_complete_nested_lengths_and_crc(self):
        match = re.search(
            r"static M_Byte test_tone\[\] = \{(.*?)\};",
            self.source,
            re.S,
        )
        self.assertIsNotNone(match)
        tone = bytes(
            int(value, 16)
            for value in re.findall(r"0x([0-9a-fA-F]{2})", match.group(1))
        )
        self.assertEqual(tone[:4], b"MMMD")
        self.assertEqual(int.from_bytes(tone[4:8], "big"), len(tone) - 8)
        self.assertEqual(tone[8:12], b"MTR\0")
        track_size = int.from_bytes(tone[12:16], "big")
        self.assertEqual(16 + track_size, len(tone) - 2)
        self.assertEqual(tone[36:40], b"Mtsq")
        sequence_size = int.from_bytes(tone[40:44], "big")
        self.assertEqual(44 + sequence_size, len(tone) - 2)
        self.assertEqual(tone[-6:-2], b"\x7d\xff\x2f\x00")
        self.assertEqual(tone[-2:], b"\0\0")


if __name__ == "__main__":
    unittest.main()
