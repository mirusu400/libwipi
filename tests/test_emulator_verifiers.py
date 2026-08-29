import unittest

from tools.verify_aram import (
    suite_package as aram_suite_package,
    validate_interactive,
    validate_performance,
    validate_platformer,
)
from tools.verify_aram_ktf import validate_report as validate_ktf_report
from tools.verify_wie import suite_config


class EmulatorVerifierTests(unittest.TestCase):
    def test_aram_platformer_suite_selects_the_example_package(self):
        package = aram_suite_package("platformer")
        self.assertEqual(package.name, "libwipi-sky-hopper.zip")
        self.assertIn("examples/platformer/build", package.as_posix())

    def test_aram_platformer_contract(self):
        report = {
            "status": "ok_frame",
            "level": "interactive",
            "format": "raptor-wipi-c",
            "profile_id": "wipi-1.2.1/lgt/raptor",
            "image": {"mode": "Thumb"},
            "wipi": {
                "api_calls": 100,
                "implemented_calls": 100,
                "unimplemented_calls": 0,
                "observed_apis": 13,
            },
            "input_events": 4,
            "frame_changes": 4,
        }
        validate_platformer(report)
        report["frame_changes"] = 1
        with self.assertRaisesRegex(ValueError, "frame changes"):
            validate_platformer(report)

    def test_wie_platformer_suite_has_an_independent_harness_and_package(self):
        harness, package = suite_config("platformer")
        self.assertEqual(harness.name, "libwipi_platformer.rs")
        self.assertEqual(package.name, "libwipi-sky-hopper.zip")
        self.assertIn("examples/platformer/build", package.as_posix())

    def test_wie_rejects_an_unknown_suite(self):
        with self.assertRaisesRegex(ValueError, "unknown WIE suite"):
            suite_config("missing")

    def test_aram_interactive_contract(self):
        report = {
            "status": "ok_frame",
            "level": "interactive",
            "format": "raptor-wipi-c",
            "profile_id": "wipi-1.2.1/lgt/raptor",
            "image": {"mode": "Thumb"},
            "wipi": {
                "api_calls": 100,
                "implemented_calls": 100,
                "unimplemented_calls": 0,
                "observed_apis": 24,
            },
            "input_events": 2,
            "frame_changes": 3,
        }
        validate_interactive(report)
        report["wipi"]["unimplemented_calls"] = 1
        with self.assertRaisesRegex(ValueError, "unimplemented"):
            validate_interactive(report)

    def test_aram_audio_contract(self):
        audio = {
            "chunks": 2,
            "frames": 100,
            "sample_rate": 44100,
            "channels": 2,
            "generation_changes": 0,
            "discontinuities": 0,
            "missing_frames": 0,
            "overlapping_frames": 0,
            "format_changes": 0,
            "invalid_chunks": 0,
            "published_dropped_samples": 0,
            "media_dropped_samples": 0,
        }
        report = {
            "status": "ok_frame",
            "level": "performance",
            "performance": {"audio": audio},
        }
        validate_performance(report)
        audio["missing_frames"] = 1
        with self.assertRaisesRegex(ValueError, "missing_frames"):
            validate_performance(report)

    def test_ktf_first_frame_contract_stays_below_interactive(self):
        report = {
            "status": "ok_frame",
            "level": "boots",
            "format": "ktf-wipi",
            "profile_id": "wipi-1.2.1/ktf/generic",
            "image": {"mode": "Thumb"},
            "wipi": {
                "present_count": 1,
                "api_calls": 8,
                "implemented_calls": 8,
                "unimplemented_calls": 0,
            },
        }
        validate_ktf_report(report)
        report["wipi"]["unimplemented_calls"] = 1
        with self.assertRaisesRegex(ValueError, "unimplemented"):
            validate_ktf_report(report)


if __name__ == "__main__":
    unittest.main()
