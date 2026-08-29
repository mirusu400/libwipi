from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_readme_exposes_the_usable_triple_and_verifiers(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in (
            "1.2.1/lgt-raptor/aram-raptor",
            "1.2.1/lgt-raptor/aram-wie-raptor",
            "1.2.1/ktf-samsung/aram-ktf",
            "docs/getting-started.md",
            "tools/verify_aram.py --build-probe",
            "tools/verify_wie.py --prepare",
            "tools/verify_aram_ktf.py",
            "SKT is not an alias for `ktf-samsung`",
            "SK Telecom SK-VM is a Java runtime",
            "no real-device claim",
        ):
            self.assertIn(required, readme)
        self.assertIn("100 public veneers", readme)
        self.assertIn("examples\\sdk-lab-aram.json", readme)
        self.assertNotIn("numbered-import veneers are a later milestone", readme)

    def test_getting_started_covers_a_copyable_application(self):
        guide = (ROOT / "docs/getting-started.md").read_text(encoding="utf-8")
        for required in (
            "include $(LIBWIPI_ROOT)/mk/application.mk",
            "APP_RESOURCES",
            "void startClet",
            "MC_GETDPTR",
            "make -C examples/my-app clean package inspect",
            "spec/evidence/emulator-conformance.json",
            "not `real-device verified`",
        ):
            self.assertIn(required, guide)

    def test_korean_usage_guide_is_linked_and_avoids_em_dash(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/usage.ko.md", readme)

        guide = (ROOT / "docs/usage.ko.md").read_text(encoding="utf-8")
        for required in (
            "1.2.1/lgt-raptor/aram-wie-raptor",
            "1.2.1/ktf-samsung/aram-ktf",
            "include $(LIBWIPI_ROOT)/mk/application.mk",
            "make -C examples/my-app clean package inspect",
            "MC_GETDPTR",
            "tools/verify_aram.py --suite platformer --build-probe",
            "tools/verify_aram_ktf.py",
            "실기기 검증",
        ):
            self.assertIn(required, guide)
        self.assertNotIn("\u2014", guide)


if __name__ == "__main__":
    unittest.main()
