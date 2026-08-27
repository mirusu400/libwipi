import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "import_anycall_catalog", ROOT / "tools/import_anycall_catalog.py"
)
assert SPEC is not None and SPEC.loader is not None
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


class ImportCatalogTests(unittest.TestCase):
    def test_selector_confidence_is_closed_and_explicit(self):
        self.assertEqual(
            IMPORTER.selector_confidence("confirmed_firmware_selector"),
            "confirmed",
        )
        self.assertEqual(
            IMPORTER.selector_confidence("candidate_selector"),
            "candidate",
        )
        with self.assertRaisesRegex(ValueError, "unknown selector_state"):
            IMPORTER.selector_confidence("unreviewed_guess")


if __name__ == "__main__":
    unittest.main()
