from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT / "scripts"))

from experiments import load_experiment_sources
from overview import load_overview_sources
from validation import SourceValidationError


class OverviewSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temporary_directory.name) / "input"
        shutil.copytree(PIPELINE_ROOT / "tests" / "fixtures" / "overview-valid", self.input_dir)
        for source in (PIPELINE_ROOT / "tests" / "fixtures").glob("valid-experiment*"):
            shutil.copy2(source, self.input_dir / source.name.removeprefix("valid-"))
        self.experiments = load_experiment_sources(self.input_dir)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_loads_and_orders_overview_records(self) -> None:
        overview = load_overview_sources(self.input_dir, self.experiments)

        self.assertEqual([person["id"] for person in overview["people"]], ["P-001", "P-002"])
        self.assertEqual([activity["id"] for activity in overview["activities"]], ["ACT-2026-002", "ACT-2026-001"])
        self.assertEqual([item["evidence_id"] for item in overview["program_evidence"]], ["EV-0100", "EV-0101"])
        self.assertEqual([run["id"] for run in overview["experiment_summaries"]], ["RUN-2026-001", "RUN-2026-002"])
        self.assertEqual(overview["experiment_summaries"][0]["conclusion_text"], self.experiments[0]["conclusion_text"])

    def test_loads_split_collections_and_ignores_templates(self) -> None:
        for plural, singular, prefix in (
            ("projects", "project", "project"),
            ("uncertainties", "uncertainty", "uncertainty"),
            ("people", "person", "person"),
            ("activities", "activity", "activity"),
        ):
            import yaml
            path = self.input_dir / f"{plural}.yaml"
            document = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
            path.unlink()
            split_dir = self.input_dir / plural
            split_dir.mkdir()
            for record in document[plural]:
                (split_dir / f"{prefix}.{record['id']}.yaml").write_text(
                    yaml.safe_dump({singular: record}, sort_keys=False), encoding="utf-8"
                )
            (split_dir / f"{prefix}.EXAMPLE.template.yaml").write_text("ignored: true\n", encoding="utf-8")

        overview = load_overview_sources(self.input_dir, self.experiments)
        self.assertEqual(overview["projects"][0]["id"], "RND-2026-01")

    def test_rejects_unknown_project_reference_from_experiment(self) -> None:
        self.experiments[0]["project_ref"] = "RND-2026-99"
        with self.assertRaisesRegex(SourceValidationError, "unknown project_ref RND-2026-99"):
            load_overview_sources(self.input_dir, self.experiments)

    def test_rejects_project_experiment_disagreement(self) -> None:
        path = self.input_dir / "projects.yaml"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "experiment_refs: [RUN-2026-001, RUN-2026-002]", "experiment_refs: [RUN-2026-001]"
        ), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "experiment_refs must match"):
            load_overview_sources(self.input_dir, self.experiments)

    def test_rejects_global_evidence_id_collision(self) -> None:
        path = self.input_dir / "program-evidence.csv"
        path.write_text(path.read_text(encoding="utf-8").replace("EV-0100", "EV-0010"), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "Duplicate evidence ID: EV-0010"):
            load_overview_sources(self.input_dir, self.experiments)

    def test_rejects_placeholder_anywhere_in_active_overview_sources(self) -> None:
        path = self.input_dir / "program.yaml"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "Example only - a multi-tenant travel operations platform.", "\"[Describe platform]\""
        ), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "placeholder text"):
            load_overview_sources(self.input_dir, self.experiments)

    def test_rejects_mixed_collection_modes(self) -> None:
        split_dir = self.input_dir / "projects"
        split_dir.mkdir()
        (split_dir / "project.RND-2026-01.yaml").write_text(
            "project:\n  id: RND-2026-01\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(SourceValidationError, "cannot use both projects.yaml and split project files"):
            load_overview_sources(self.input_dir, self.experiments)

    def test_not_applicable_resource_summary_requires_reason(self) -> None:
        path = self.input_dir / "program.yaml"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "labour_summary: {state: applicable}", "labour_summary: {state: not_applicable}"
        ), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "labour_summary not_applicable requires reason"):
            load_overview_sources(self.input_dir, self.experiments)


if __name__ == "__main__":
    unittest.main()
