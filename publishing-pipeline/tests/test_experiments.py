from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

import yaml

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT / "scripts"))

from experiments import load_experiment_sources
from validation import SourceValidationError


class ExperimentSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temporary_directory.name) / "input"
        self.input_dir.mkdir()
        for source in (PIPELINE_ROOT / "tests" / "fixtures").glob("valid-experiment*"):
            shutil.copy2(source, self.input_dir / source.name.removeprefix("valid-"))

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _restore_yaml(self) -> dict[str, Any]:
        source = PIPELINE_ROOT / "tests" / "fixtures" / "valid-experiments.yaml"
        target = self.input_dir / "experiments.yaml"
        shutil.copy2(source, target)
        return yaml.load(target.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    def _mutate_yaml(self, change: Callable[[dict[str, Any]], None]) -> None:
        document = self._restore_yaml()
        change(document)
        (self.input_dir / "experiments.yaml").write_text(
            yaml.safe_dump(document, sort_keys=False),
            encoding="utf-8",
        )

    def _run(self, run_id: str = "RUN-2026-001") -> dict[str, Any]:
        document = self._restore_yaml()
        return next(run for run in document["experiments"] if run["id"] == run_id)

    def _write_run_change(
        self,
        change: Callable[[dict[str, Any]], None],
        run_id: str = "RUN-2026-001",
    ) -> None:
        def apply(document: dict[str, Any]) -> None:
            run = next(item for item in document["experiments"] if item["id"] == run_id)
            change(run)

        self._mutate_yaml(apply)

    def test_normalizes_runs_in_chronological_order(self) -> None:
        runs = load_experiment_sources(self.input_dir)

        self.assertEqual([run["id"] for run in runs], ["RUN-2026-001", "RUN-2026-002"])
        self.assertEqual(runs[0]["results"][0]["metric"], "provider submissions")
        self.assertEqual(runs[1]["results"][0]["kind"], "qualitative")

    def test_rejects_missing_required_run_fields(self) -> None:
        removers = {
            "title": lambda run: run.pop("title"),
            "project_ref": lambda run: run.pop("project_ref"),
            "uncertainty_refs": lambda run: run.pop("uncertainty_refs"),
            "started_at": lambda run: run.pop("started_at"),
            "engineers": lambda run: run.pop("engineers"),
            "objective": lambda run: run.pop("objective"),
            "background.summary": lambda run: run["background"].pop("summary"),
            "hypothesis.statement": lambda run: run["hypothesis"].pop("statement"),
            "hypothesis.formed_at": lambda run: run["hypothesis"].pop("formed_at"),
            "design": lambda run: run.pop("design"),
            "method": lambda run: run.pop("method"),
            "evaluation": lambda run: run.pop("evaluation"),
            "status": lambda run: run.pop("status"),
        }
        for field_path, remove in removers.items():
            with self.subTest(field_path=field_path):
                self._write_run_change(remove)
                with self.assertRaisesRegex(
                    SourceValidationError,
                    rf"RUN-2026-001 requires {field_path.replace('.', r'\.')}",
                ):
                    load_experiment_sources(self.input_dir)

    def test_completed_run_requires_end_and_conclusion(self) -> None:
        for field in ("ended_at", "conclusion"):
            with self.subTest(field=field):
                self._write_run_change(lambda run, name=field: run.pop(name))
                with self.assertRaisesRegex(SourceValidationError, rf"requires {field}"):
                    load_experiment_sources(self.input_dir)

    def test_ongoing_run_requires_interim_conclusion_and_next_action(self) -> None:
        for field in ("interim_conclusion", "next_actions"):
            with self.subTest(field=field):
                self._write_run_change(
                    lambda run, name=field: run.pop(name),
                    run_id="RUN-2026-002",
                )
                with self.assertRaisesRegex(SourceValidationError, rf"requires {field}"):
                    load_experiment_sources(self.input_dir)

    def test_ongoing_run_rejects_final_end_timestamp(self) -> None:
        self._write_run_change(
            lambda run: run.__setitem__("ended_at", "2026-07-15T10:00:00+09:30"),
            run_id="RUN-2026-002",
        )

        with self.assertRaisesRegex(SourceValidationError, "ongoing forbids ended_at"):
            load_experiment_sources(self.input_dir)

    def test_rejects_unknown_status(self) -> None:
        self._write_run_change(lambda run: run.__setitem__("status", "successful"))

        with self.assertRaisesRegex(SourceValidationError, "status must be"):
            load_experiment_sources(self.input_dir)

    def test_rejects_invalid_run_chronology(self) -> None:
        changes = {
            "ended_at must not precede started_at": lambda run: run.__setitem__(
                "ended_at", "2026-07-14T08:00:00+09:30"
            ),
            "hypothesis.formed_at must not follow started_at": lambda run: run[
                "hypothesis"
            ].__setitem__("formed_at", "2026-07-14T10:00:00+09:30"),
        }
        for message, change in changes.items():
            with self.subTest(message=message):
                self._write_run_change(change)
                with self.assertRaisesRegex(SourceValidationError, message.replace(".", r"\.")):
                    load_experiment_sources(self.input_dir)

    def test_rejects_execution_outside_completed_run(self) -> None:
        path = self.input_dir / "experiment-execution-log.csv"
        text = path.read_text(encoding="utf-8").replace(
            "2026-07-14T10:00:00+09:30", "2026-07-14T13:00:00+09:30"
        )
        path.write_text(text, encoding="utf-8")

        with self.assertRaisesRegex(SourceValidationError, "outside the run period"):
            load_experiment_sources(self.input_dir)

    def test_rejects_duplicate_sequences(self) -> None:
        path = self.input_dir / "experiment-results.csv"
        with path.open("a", encoding="utf-8") as stream:
            stream.write(
                "RUN-2026-001,1,quantitative,recovery duration,0,18,seconds,"
                "Measured duration,EV-0010\n"
            )

        with self.assertRaisesRegex(SourceValidationError, "duplicate sequence 1"):
            load_experiment_sources(self.input_dir)

    def test_rejects_orphan_rows_and_cross_run_evidence(self) -> None:
        result_path = self.input_dir / "experiment-results.csv"
        original = result_path.read_text(encoding="utf-8")
        result_path.write_text(original.replace("RUN-2026-001,1", "RUN-2026-099,1"), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "unknown run_id RUN-2026-099"):
            load_experiment_sources(self.input_dir)

        shutil.copy2(
            PIPELINE_ROOT / "tests" / "fixtures" / "valid-experiment-results.csv",
            result_path,
        )
        result_path.write_text(original.replace("EV-0010", "EV-0020"), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "evidence_ref EV-0020 belongs to RUN-2026-002"):
            load_experiment_sources(self.input_dir)

    def test_requires_each_child_collection(self) -> None:
        filenames = (
            "experiment-results.csv",
            "experiment-execution-log.csv",
            "experiment-evidence.csv",
        )
        for filename in filenames:
            with self.subTest(filename=filename):
                source = PIPELINE_ROOT / "tests" / "fixtures" / f"valid-{filename}"
                target = self.input_dir / filename
                shutil.copy2(source, target)
                header = target.read_text(encoding="utf-8").splitlines()[0]
                rows = target.read_text(encoding="utf-8").splitlines()[1:]
                target.write_text(
                    header + "\n" + "\n".join(row for row in rows if not row.startswith("RUN-2026-001,") and ",RUN-2026-001," not in row) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(SourceValidationError, "RUN-2026-001 requires at least one"):
                    load_experiment_sources(self.input_dir)

    def test_validates_result_shape(self) -> None:
        path = self.input_dir / "experiment-results.csv"
        cases = {
            "kind must be quantitative or qualitative": (",quantitative,", ",estimated,"),
            "unit is required for quantitative results": (",count,No duplicate", ",,No duplicate"),
            "baseline_value not_applicable requires explanatory notes": (
                "1,1,count,No duplicate in measured interruption windows,EV-0010",
                "not_applicable,1,count,,EV-0010",
            ),
        }
        for message, (before, after) in cases.items():
            with self.subTest(message=message):
                shutil.copy2(
                    PIPELINE_ROOT / "tests" / "fixtures" / "valid-experiment-results.csv",
                    path,
                )
                path.write_text(path.read_text(encoding="utf-8").replace(before, after), encoding="utf-8")
                with self.assertRaisesRegex(SourceValidationError, message):
                    load_experiment_sources(self.input_dir)

    def test_normalizes_missing_optional_block_to_no_data(self) -> None:
        self._write_run_change(lambda run: run.pop("unexpected_behaviour"))

        runs = load_experiment_sources(self.input_dir)

        self.assertEqual(runs[0]["unexpected_behaviour"], {"state": "no_data"})

    def test_rejects_invalid_optional_block(self) -> None:
        cases = (
            ({"state": "provided"}, "state provided requires content"),
            ({"state": "no_data", "content": "hidden"}, "state no_data forbids content"),
            ({"state": "disabled"}, "state must be provided or no_data"),
        )
        for value, message in cases:
            with self.subTest(value=value):
                self._write_run_change(lambda run, item=value: run.__setitem__("unexpected_behaviour", item))
                with self.assertRaisesRegex(SourceValidationError, message):
                    load_experiment_sources(self.input_dir)

    def test_rejects_placeholder_values(self) -> None:
        for value in ("[Experiment title]", "xxx", "TBD"):
            with self.subTest(value=value):
                self._write_run_change(lambda run, item=value: run.__setitem__("title", item))
                with self.assertRaisesRegex(SourceValidationError, "contains placeholder text"):
                    load_experiment_sources(self.input_dir)


if __name__ == "__main__":
    unittest.main()
