from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT / "scripts"))

from publisher import load_sources
from validation import SourceValidationError


class ClaimMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temporary_directory.name) / "input"
        self.input_dir.mkdir()
        fixtures = PIPELINE_ROOT / "tests" / "fixtures"
        for source in fixtures.glob("valid-*"):
            if source.is_file():
                shutil.copy2(source, self.input_dir / source.name.removeprefix("valid-"))
        for source in (fixtures / "overview-valid").iterdir():
            if source.is_file():
                shutil.copy2(source, self.input_dir / source.name)
        shutil.copy2(fixtures / "valid-reviews.yaml", self.input_dir / "reviews.yaml")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_builds_complete_traceability_model(self) -> None:
        sources = load_sources(self.input_dir)
        mapping = sources["claim_mapping"]

        self.assertEqual(mapping["projects"][0]["id"], "RND-2026-01")
        self.assertEqual(mapping["experimental_activities"][0]["id"], "ACT-2026-001")
        self.assertEqual(mapping["supporting_activities"][0]["id"], "ACT-2026-003")
        self.assertEqual(mapping["supporting_activities"][0]["supports_activity_refs"], ["ACT-2026-001"])
        self.assertEqual(mapping["experiments"][0]["observation_refs"], ["RUN-2026-001/RESULT-001"])
        self.assertEqual([row["timesheet_id"] for row in mapping["timesheets"]], ["TS-2026-0002", "TS-2026-0001"])
        self.assertEqual(mapping["infrastructure_costs"][0]["cost_id"], "COST-2026-0001")
        self.assertEqual(mapping["reviews"][0]["id"], "REV-2026-001")

    def test_rejects_supporting_activity_without_target(self) -> None:
        path = self.input_dir / "activities.yaml"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "    supports_activity_refs: [ACT-2026-001]\n", ""
        ).replace("    supports_experiment_refs: [RUN-2026-001]\n", ""), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "candidate_supporting requires a support target"):
            load_sources(self.input_dir)

    def test_rejects_timesheet_activity_mismatch(self) -> None:
        path = self.input_dir / "timesheets.csv"
        path.write_text(path.read_text(encoding="utf-8").replace("ACT-2026-001", "ACT-2026-002"), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "category core contradicts"):
            load_sources(self.input_dir)

    def test_rejects_cost_evidence_orphan(self) -> None:
        path = self.input_dir / "infrastructure-costs.csv"
        path.write_text(path.read_text(encoding="utf-8").replace("EV-0101", "EV-9999"), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "unknown evidence_ref EV-9999"):
            load_sources(self.input_dir)

    def test_renders_without_old_instructional_copy(self) -> None:
        from publisher import render_documents
        sources = load_sources(self.input_dir)
        generated = Path(self.temporary_directory.name) / "generated"
        render_documents(PIPELINE_ROOT / "templates", generated, sources)
        text = (generated / "03_claim_mapping_register.tex").read_text(encoding="utf-8")
        for expected in ("ACT-2026-001", "ACT-2026-003", "TS-2026-0001", "COST-2026-0001", "RUN-2026-001/RESULT-001", "REV-2026-001"):
            self.assertIn(expected, text)
        for forbidden in ("CORE-01", "SUP-01", "Use one row per claimed", "Summarise the principal"):
            self.assertNotIn(forbidden, text)

    def test_rejects_unknown_review_subject(self) -> None:
        path = self.input_dir / "reviews.yaml"
        path.write_text(path.read_text(encoding="utf-8").replace("UT-01", "UT-99"), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "unknown uncertainties subject UT-99"):
            load_sources(self.input_dir)

    def test_ignores_review_template_files(self) -> None:
        (self.input_dir / "reviews.template.yaml").write_text("reviews:\n  - id: REV-2099-999\n", encoding="utf-8")
        self.assertNotIn("REV-2099-999", {item["id"] for item in load_sources(self.input_dir)["reviews"]})

    def test_rejects_missing_or_placeholder_review_question(self) -> None:
        path = self.input_dir / "reviews.yaml"
        original = path.read_text(encoding="utf-8")
        for replacement in ("", '    question: "[Decision]"\n'):
            with self.subTest(replacement=replacement):
                path.write_text(original.replace(
                    "    question: Example only - determine whether the unresolved external acceptance state requires another run.\n",
                    replacement,
                ), encoding="utf-8")
                with self.assertRaisesRegex(SourceValidationError, "review REV-2026-001 requires non-placeholder question"):
                    load_sources(self.input_dir)
        path.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
