import csv
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GenerationTests(unittest.TestCase):
    def test_checked_in_outputs_are_current(self):
        subprocess.run(
            [sys.executable, "tools/generate.py", "--check"],
            cwd=ROOT,
            check=True,
        )

    def test_veneer_boundary(self):
        assembly = (ROOT / "src/abi/ktf/generated_veneer.S").read_text()
        globals_ = [
            line.removeprefix(".global ")
            for line in assembly.splitlines()
            if line.startswith(".global MC_")
        ]
        self.assertEqual(len(globals_), 205)
        self.assertNotIn("MC_knlPrintk", globals_)
        self.assertNotIn("MC_knlSprintk", globals_)
        self.assertNotIn("MC_knlExecute", globals_)
        self.assertIn("MC_knlSetTimer", globals_)

    def test_aram_wie_lgt_veneer_boundary(self):
        assembly = (ROOT / "src/abi/lgt/generated_veneer.S").read_text()
        globals_ = [
            line.removeprefix(".global ")
            for line in assembly.splitlines()
            if line.startswith(".global MC_")
        ]
        install = json.loads(
            (ROOT / "spec/install/aram-wie-raptor.json").read_text()
        )
        confirmed = install["imports"]["confirmed_public_methods"]
        self.assertEqual(set(globals_), set(confirmed))
        self.assertEqual(len(globals_), 59)
        self.assertNotIn("MC_knlPrintk", globals_)
        self.assertNotIn("MC_knlSprintk", globals_)
        self.assertIn("MC_knlSetTimer", globals_)
        self.assertIn("MC_grpDrawString", globals_)
        for name, aram_method in install["imports"][
            "aram_method_overrides"
        ].items():
            start = assembly.index(f"{name}:")
            end = assembly.index(f".size {name}", start)
            veneer = assembly[start:end]
            self.assertIn("__wipi_lgt_environment", veneer)
            self.assertIn(aram_method, veneer)
            self.assertIn(confirmed[name], veneer)
        display_start = assembly.index("MC_grpGetDisplayInfo:")
        display_end = assembly.index(
            ".size MC_grpGetDisplayInfo", display_start
        )
        display_info = assembly[display_start:display_end]
        self.assertIn("WIE provider success 1", display_info)
        self.assertIn("__wipi_lgt_environment", display_info)
        self.assertIn("cmp r0, #1", display_info)
        self.assertIn("movs r0, #0", display_info)
        self.assertIn("MC_mdaPlay", globals_)

    def test_every_catalog_declaration_is_emitted(self):
        with (ROOT / "spec/wipi-1.2.1/api.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            rows = list(csv.DictReader(stream))
        declaration_headers = list((ROOT / "include/wipi/generated").glob("*.h"))
        declaration_headers.extend(
            ROOT / "include" / name
            for name in ("string.h", "stdlib.h", "time.h")
        )
        generated = "\n".join(path.read_text() for path in declaration_headers)
        for row in rows:
            self.assertIn(row["prototype"], generated)


if __name__ == "__main__":
    unittest.main()
