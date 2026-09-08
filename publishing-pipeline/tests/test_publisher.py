from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT / "scripts"))

from publisher import SourceValidationError, latex_escape, load_sources, render_documents


class PublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_dir = PIPELINE_ROOT / "tests" / "fixtures"
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temporary_directory.name) / "input"
        self.input_dir.mkdir()
        for source in self.fixture_dir.glob("valid-*"):
            target_name = source.name.removeprefix("valid-")
            shutil.copy2(source, self.input_dir / target_name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_loads_valid_yaml_and_csv_sources(self) -> None:
        sources = load_sources(self.input_dir)

        self.assertEqual(sources["document"]["company"], "Example Research Pty Ltd")
        self.assertEqual(sources["experiments"][0]["id"], "RUN-001")
        self.assertEqual(sources["timesheets"][0]["category"], "core")
        self.assertEqual(sources["infrastructure_costs"][0]["eligible_amount"], "50.00")

    def test_rejects_missing_required_document_field(self) -> None:
        claim_path = self.input_dir / "claim.yaml"
        claim_text = claim_path.read_text(encoding="utf-8")
        claim_path.write_text(
            claim_text.replace("  financial_year: 2025-2026\n", ""),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(SourceValidationError, "financial_year"):
            load_sources(self.input_dir)

    def test_rejects_duplicate_experiment_ids(self) -> None:
        experiments_path = self.input_dir / "experiments.yaml"
        experiments_path.write_text(
            "experiments:\n  - id: RUN-001\n    title: First\n"
            "  - id: RUN-001\n    title: Second\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(SourceValidationError, "Duplicate experiment ID: RUN-001"):
            load_sources(self.input_dir)

    def test_rejects_invalid_timesheet_headers(self) -> None:
        (self.input_dir / "timesheets.csv").write_text("person,date,hours\n", encoding="utf-8")

        with self.assertRaisesRegex(SourceValidationError, "timesheets.csv headers"):
            load_sources(self.input_dir)

    def test_rejects_invalid_timesheet_category(self) -> None:
        timesheet_path = self.input_dir / "timesheets.csv"
        timesheet_path.write_text(
            "person,date,project_ref,run_ref,category,hours,description\n"
            "Engineer,2026-01-12,RND-01,RUN-001,maybe,8,Investigation\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(SourceValidationError, "timesheets.csv row 2 category"):
            load_sources(self.input_dir)

    def test_rejects_inconsistent_infrastructure_cost(self) -> None:
        cost_path = self.input_dir / "infrastructure-costs.csv"
        cost_path.write_text(
            "month,service,provider,total_cost,rnd_percent,eligible_amount,allocation_basis,evidence_ref\n"
            "2026-01,Compute,Cloud,100.00,50,75.00,Tagged usage,invoice-001\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(SourceValidationError, "eligible_amount must equal 50.00"):
            load_sources(self.input_dir)

    def test_escapes_latex_control_characters(self) -> None:
        escaped = latex_escape("R&D_50% #1 {draft} ~ ^ \\")

        self.assertEqual(
            escaped,
            r"R\&D\_50\% \#1 \{draft\} \textasciitilde{} \textasciicircum{} \textbackslash{}",
        )

    def test_renders_all_seven_documents_with_source_metadata(self) -> None:
        sources = load_sources(self.input_dir)
        output_dir = Path(self.temporary_directory.name) / "generated"

        rendered = render_documents(PIPELINE_ROOT / "templates", output_dir, sources)

        self.assertEqual(len(rendered), 7)
        overview = (output_dir / "01_overview_of_all_work.tex").read_text(encoding="utf-8")
        style = (output_dir / "rd_audit_style.sty").read_text(encoding="utf-8")
        self.assertIn("Example Research Pty Ltd", overview)
        self.assertIn("Evidence Pipeline Research", style)
        self.assertIn("GENERATED FILE", overview)
        self.assertTrue((output_dir / "rd_audit_style.sty").is_file())


if __name__ == "__main__":
    unittest.main()
