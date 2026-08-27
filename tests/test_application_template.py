from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ApplicationTemplateTests(unittest.TestCase):
    def test_template_uses_the_shared_application_build(self):
        makefile = (ROOT / "examples/template/Makefile").read_text(
            encoding="utf-8"
        )
        self.assertIn("mk/application.mk", makefile)
        for forbidden in ("-mcpu", "-mthumb", "-mfloat-abi", "-nostdlib"):
            self.assertNotIn(forbidden, makefile)

    def test_external_application_dry_run_is_complete(self):
        if shutil.which("make") is None:
            self.skipTest("GNU make is exercised by the Docker target gate")
        result = subprocess.run(
            ["make", "-n", "-B", "--no-print-directory", "package"],
            cwd=ROOT / "examples/template",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        output = result.stdout.replace("\\", "/")
        self.assertIn("-mcpu=arm7tdmi", output)
        self.assertIn("ld/raptor.ld", output)
        self.assertIn("tools/package_raptor.py", output)
        self.assertIn("libwipi-starter.zip", output)


if __name__ == "__main__":
    unittest.main()
