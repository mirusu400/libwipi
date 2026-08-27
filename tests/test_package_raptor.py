import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "tools/package_raptor.py"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


class RaptorPackageTests(unittest.TestCase):
    def package(self, directory: Path, output_name: str = "app.zip") -> Path:
        binary = directory / "binary.mod"
        binary.write_bytes(b"\x7fELF" + bytes(range(32)))
        resource = directory / "fixture.bin"
        resource.write_bytes(b"resource-data")
        output = directory / output_name
        subprocess.run(
            [
                sys.executable,
                str(PACKAGER),
                "--binary",
                str(binary),
                "--output",
                str(output),
                "--aid",
                "libwipi-test",
                "--name",
                "libwipi test",
                "--resource",
                f"{resource}=res/fixture.bin",
            ],
            cwd=ROOT,
            check=True,
        )
        return output

    def test_package_is_deterministic_and_round_trips(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            first = self.package(directory, "first.zip")
            second = self.package(directory, "second.zip")
            self.assertEqual(first.read_bytes(), second.read_bytes())

            with zipfile.ZipFile(first) as outer:
                self.assertEqual(
                    outer.namelist(), ["app_info", "libwipi-test.jar"]
                )
                self.assertTrue(all(info.date_time == FIXED_TIME for info in outer.infolist()))
                descriptor = outer.read("app_info").decode("ascii")
                self.assertIn("AID:libwipi-test\r\n", descriptor)
                self.assertIn("MClass:Clet\r\n", descriptor)
                with zipfile.ZipFile(
                    io.BytesIO(outer.read("libwipi-test.jar"))
                ) as inner:
                    self.assertEqual(
                        inner.namelist(),
                        ["META-INF/MANIFEST.MF", "binary.mod", "res/fixture.bin"],
                    )
                    self.assertTrue(
                        all(info.date_time == FIXED_TIME for info in inner.infolist())
                    )
                    self.assertEqual(inner.read("binary.mod")[:4], b"\x7fELF")
                    self.assertEqual(inner.read("res/fixture.bin"), b"resource-data")

            inspected = subprocess.run(
                [sys.executable, str(PACKAGER), "--inspect", str(first)],
                cwd=ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            report = json.loads(inspected.stdout)
            self.assertEqual(report["aid"], "libwipi-test")
            self.assertEqual(report["module"], "binary.mod")
            self.assertEqual(report["resources"], ["res/fixture.bin"])

    def test_unsafe_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            binary = directory / "binary.mod"
            binary.write_bytes(b"\x7fELF" + bytes(32))
            resource = directory / "fixture.bin"
            resource.write_bytes(b"fixture")
            for arguments in (
                ("--aid", "../escape"),
                ("--aid", "safe", "--resource", f"{resource}=../escape.bin"),
                ("--aid", "safe", "--resource", f"{resource}=C:/escape.bin"),
            ):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(PACKAGER),
                        "--binary",
                        str(binary),
                        "--output",
                        str(directory / "bad.zip"),
                        *arguments,
                    ],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("unsafe", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
