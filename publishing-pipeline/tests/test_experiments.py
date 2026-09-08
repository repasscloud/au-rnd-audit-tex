from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT / "scripts"))

from experiments import load_experiment_sources


class ExperimentSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temporary_directory.name) / "input"
        self.input_dir.mkdir()
        for source in (PIPELINE_ROOT / "tests" / "fixtures").glob("valid-experiment*"):
            shutil.copy2(source, self.input_dir / source.name.removeprefix("valid-"))

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_normalizes_runs_in_chronological_order(self) -> None:
        runs = load_experiment_sources(self.input_dir)

        self.assertEqual([run["id"] for run in runs], ["RUN-2026-001", "RUN-2026-002"])
        self.assertEqual(runs[0]["results"][0]["metric"], "provider submissions")
        self.assertEqual(runs[1]["results"][0]["kind"], "qualitative")


if __name__ == "__main__":
    unittest.main()
