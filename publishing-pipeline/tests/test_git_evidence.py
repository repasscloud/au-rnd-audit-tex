from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT / "scripts"))

from git_evidence import load_git_evidence
from validation import SourceValidationError


EVENT_HEADER = (
    "record_id,repository_ref,record_type,immutable_identifier,occurred_at,"
    "authored_at,committed_at,author_name,author_email_sha256,committer_name,"
    "committer_email_sha256,subject,parent_identifiers,ref_names,"
    "related_record_ids,source_evidence_ref,status,raw_record_sha256\n"
)
HASH = "0123456789abcdef0123456789abcdef01234567"
PARENT = "89abcdef0123456789abcdef0123456789abcdef"
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


class GitEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temp.name)
        self.overview = {
            "program": {"scope": {"period_start": "2026-07-01", "period_end": "2027-06-30"}},
            "projects": [{"id": "RND-2026-01"}],
            "uncertainties": [{"id": "UT-01"}],
            "activities": [{"id": "ACT-2026-001", "project_refs": ["RND-2026-01"], "uncertainty_refs": ["UT-01"], "experiment_refs": ["RUN-2026-001"]}],
            "people": [{"id": "P-001", "name": "Example Person"}],
            "program_evidence": [{"evidence_id": "EV-0100"}],
        }
        self.experiments = [{"id": "RUN-2026-001", "project_ref": "RND-2026-01", "uncertainty_refs": ["UT-01"], "_started_at": __import__("datetime").datetime.fromisoformat("2026-07-14T09:30:00+09:30"), "evidence": [{"evidence_id": "EV-0001"}]}]
        self.claim_mapping = {"reviews": [{"id": "REV-2026-001"}]}
        self.write_valid_exported_sources()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_valid_exported_sources(self) -> None:
        config = {
            "repository_evidence": {
                "state": "applicable",
                "coverage_statement": "Example only - application repository coverage.",
                "repositories": [{
                    "id": "REPO-001", "name": "Example only - C360 application repository",
                    "project_refs": ["RND-2026-01"], "period_start": "2026-07-01", "period_end": "2027-06-30",
                    "acquisition": {"mode": "exported"}, "expected_head": HASH,
                    "history": {"completeness": "complete", "limitation": {"state": "no_data"}},
                    "identity_mappings": [{
                        "id": "GITID-0001", "git_name_exact": "Example Author",
                        "git_email_sha256": DIGEST_A, "person_ref": "P-001",
                        "basis": "Example only - confirmed by the record owner.",
                        "evidence_refs": ["EV-0100"], "review_ref": "REV-2026-001", "status": "confirmed",
                    }],
                }],
            }
        }
        (self.input_dir / "repositories.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        row = (
            f"GITREC-2026-000001,REPO-001,commit,{HASH},,2026-07-14T09:48:00+09:30,"
            f"2026-07-14T09:50:00+09:30,Example Author,{DIGEST_A},Example Committer,{DIGEST_B},"
            f"Record recovery experiment,{PARENT},refs/heads/example,,,recorded,{DIGEST_C}\n"
        )
        (self.input_dir / "repository-events.csv").write_text(EVENT_HEADER + row, encoding="utf-8")
        interpretations = {"interpretations": [{
            "id": "GITINT-2026-0001", "repository_ref": "REPO-001",
            "record_refs": ["GITREC-2026-000001"], "materiality": "material",
            "engineering_context": ["candidate_experimental_support"],
            "interpretation": "Example only - source change used by the referenced run; not an eligibility conclusion.",
            "interpretation_owner": "P-001", "project_refs": ["RND-2026-01"],
            "uncertainty_refs": ["UT-01"], "activity_refs": ["ACT-2026-001"],
            "experiment_refs": ["RUN-2026-001"], "person_refs": [],
            "evidence_refs": ["EV-0001"], "review_refs": ["REV-2026-001"],
            "recorded_at": "2026-07-14T13:00:00+09:30",
        }]}
        (self.input_dir / "repository-interpretations.yaml").write_text(yaml.safe_dump(interpretations, sort_keys=False), encoding="utf-8")

    def load(self):
        return load_git_evidence(self.input_dir, self.overview, self.experiments, self.claim_mapping)

    def test_loads_exported_facts_and_keeps_interpretation_separate(self) -> None:
        result = self.load()
        self.assertEqual(result["repositories"][0]["id"], "REPO-001")
        self.assertEqual(result["events"][0]["full_hash"], HASH)
        self.assertEqual(result["events"][0]["author_person_ref"], "P-001")
        self.assertEqual(result["events"][0]["committer_person_ref"], "")
        self.assertEqual(result["interpretations"][0]["experiment_refs"], ["RUN-2026-001"])

    def test_rejects_duplicate_immutable_commit(self) -> None:
        path = self.input_dir / "repository-events.csv"
        duplicate = path.read_text(encoding="utf-8").splitlines()[1].replace(
            "GITREC-2026-000001", "GITREC-2026-000002", 1
        )
        path.write_text(path.read_text(encoding="utf-8") + duplicate + "\n", encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "Duplicate immutable identifier"):
            self.load()

    def test_rejects_interpretation_that_contradicts_activity_project(self) -> None:
        text = (self.input_dir / "repository-interpretations.yaml").read_text(encoding="utf-8")
        (self.input_dir / "repository-interpretations.yaml").write_text(text.replace("RND-2026-01", "RND-2026-99"), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "unknown project"):
            self.load()

    def test_rejects_ambiguous_confirmed_identity_mapping(self) -> None:
        config = yaml.safe_load((self.input_dir / "repositories.yaml").read_text(encoding="utf-8"))
        duplicate = dict(config["repository_evidence"]["repositories"][0]["identity_mappings"][0])
        duplicate["id"] = "GITID-0002"
        duplicate["person_ref"] = "P-002"
        self.overview["people"].append({"id": "P-002", "name": "Other Person"})
        config["repository_evidence"]["repositories"][0]["identity_mappings"].append(duplicate)
        (self.input_dir / "repositories.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        with self.assertRaisesRegex(SourceValidationError, "ambiguous identity"):
            self.load()

    def test_local_inspection_is_pinned_and_does_not_mutate_repository(self) -> None:
        repo = self.input_dir / "local-repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Local Author"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "local@example.invalid"], cwd=repo, check=True)
        (repo / "record.txt").write_text("immutable\n", encoding="utf-8")
        subprocess.run(["git", "add", "record.txt"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "Capture experiment record"], cwd=repo, check=True)
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        before = subprocess.check_output(["git", "status", "--porcelain=v2", "--branch"], cwd=repo, text=True)
        config = yaml.safe_load((self.input_dir / "repositories.yaml").read_text(encoding="utf-8"))
        repository = config["repository_evidence"]["repositories"][0]
        repository["acquisition"] = {"mode": "local", "local_path": str(repo.resolve()), "allowed_paths": [str(repo.resolve())]}
        repository["expected_head"] = head
        repository["identity_mappings"] = []
        (self.input_dir / "repositories.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        (self.input_dir / "repository-events.csv").write_text(EVENT_HEADER, encoding="utf-8")
        (self.input_dir / "repository-interpretations.yaml").write_text("interpretations: []\n", encoding="utf-8")
        result = self.load()
        after = subprocess.check_output(["git", "status", "--porcelain=v2", "--branch"], cwd=repo, text=True)
        self.assertEqual(result["events"][0]["immutable_identifier"], head)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
