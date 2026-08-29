import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "tools/package_ktf.py"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


class KTFPackageTests(unittest.TestCase):
    def package(self, directory: Path, output_name: str = "app.zip") -> Path:
        client = directory / "client.bin"
        client.write_bytes(b"\x00\x48\x70\x47" + bytes(range(32)))
        resource = directory / "fixture.bin"
        resource.write_bytes(b"resource-data")
        output = directory / output_name
        subprocess.run(
            [
                sys.executable,
                str(PACKAGER),
                "--client",
                str(client),
                "--bss-size",
                "4096",
                "--output",
                str(output),
                "--aid",
                "01020304",
                "--pid",
                "PD000001",
                "--name",
                "libwipi test",
                "--display-size",
                "240x320",
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
                self.assertEqual(outer.namelist(), ["__adf__", "01020304.jar"])
                self.assertTrue(all(info.date_time == FIXED_TIME for info in outer.infolist()))
                descriptor = outer.read("__adf__").decode("ascii")
                self.assertIn("AID:01020304\r\n", descriptor)
                self.assertIn("PID:PD000001\r\n", descriptor)
                self.assertIn("MClass:LibwipiClet\r\n", descriptor)
                self.assertIn("DisplaySize:240*320\r\n", descriptor)
                with zipfile.ZipFile(io.BytesIO(outer.read("01020304.jar"))) as inner:
                    self.assertEqual(
                        inner.namelist(),
                        [
                            "META-INF/MANIFEST.MF",
                            "client.bin4096",
                            "res/fixture.bin",
                        ],
                    )
                    self.assertTrue(
                        all(info.date_time == FIXED_TIME for info in inner.infolist())
                    )
                    self.assertEqual(inner.read("client.bin4096")[:4], b"\x00\x48\x70\x47")
                    self.assertEqual(inner.read("res/fixture.bin"), b"resource-data")

            inspected = subprocess.run(
                [sys.executable, str(PACKAGER), "--inspect", str(first)],
                cwd=ROOT,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )
            report = json.loads(inspected.stdout)
            self.assertEqual(report["aid"], "01020304")
            self.assertEqual(report["pid"], "PD000001")
            self.assertEqual(report["main_class"], "LibwipiClet")
            self.assertEqual(report["client"], "client.bin4096")
            self.assertEqual(report["bss_size"], 4096)
            self.assertEqual(report["display_size"], [240, 320])
            self.assertEqual(report["resources"], ["res/fixture.bin"])

    def test_unsafe_names_and_invalid_bss_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            client = directory / "client.bin"
            client.write_bytes(b"\x70\x47")
            resource = directory / "fixture.bin"
            resource.write_bytes(b"fixture")
            for arguments in (
                ("--aid", "../escape", "--bss-size", "1"),
                ("--aid", "safe", "--bss-size", "-1"),
                (
                    "--aid",
                    "safe",
                    "--bss-size",
                    "1",
                    "--resource",
                    f"{resource}=../escape.bin",
                ),
            ):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(PACKAGER),
                        "--client",
                        str(client),
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


if __name__ == "__main__":
    unittest.main()
