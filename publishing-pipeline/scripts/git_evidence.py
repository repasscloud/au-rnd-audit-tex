from __future__ import annotations

import hashlib
import os
import re
import subprocess
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from typing import Any

from validation import SourceValidationError, load_strict_csv, load_yaml_mapping


EVENT_HEADERS = (
    "record_id", "repository_ref", "record_type", "immutable_identifier",
    "occurred_at", "authored_at", "committed_at", "author_name",
    "author_email_sha256", "committer_name", "committer_email_sha256",
    "subject", "parent_identifiers", "ref_names", "related_record_ids",
    "source_evidence_ref", "status", "raw_record_sha256",
)
REPOSITORY_ID = re.compile(r"REPO-\d{3}")
EVENT_ID = re.compile(r"GITREC-\d{4}-\d{6}")
INTERPRETATION_ID = re.compile(r"GITINT-\d{4}-\d{4}")
IDENTITY_ID = re.compile(r"GITID-\d{4}")
HEX_40_PLUS = re.compile(r"[0-9a-f]{40,64}")
HEX_64 = re.compile(r"[0-9a-f]{64}")
PLACEHOLDER = re.compile(r"(?:\[[^]]+]|xxx|tbd)", re.IGNORECASE)
EVENT_TYPES = {
    "commit", "merge_commit", "revert", "branch_snapshot", "tag", "release",
    "pull_request", "merge_request", "issue", "ticket", "build", "test",
    "deployment", "other_engineering_record",
}
CONTEXTS = {
    "candidate_experimental_support", "candidate_supporting_support",
    "ordinary_engineering", "maintenance", "refactoring", "administrative",
    "outside_boundary", "failed_approach", "revert", "abandoned_work",
    "contradictory_evidence", "human_review_required",
}


def _text(value: Any, source: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceValidationError(f"{source} requires {field}")
    value = value.strip()
    if PLACEHOLDER.fullmatch(value):
        raise SourceValidationError(f"{source} contains placeholder text at {field}")
    return value


def _timestamp(value: Any, source: str, field: str) -> datetime:
    value = _text(value, source, field)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise SourceValidationError(f"{source} {field} must be an ISO 8601 timestamp") from error
    if parsed.tzinfo is None:
        raise SourceValidationError(f"{source} {field} must include a UTC offset")
    return parsed


def _date(value: Any, source: str, field: str) -> date:
    value = _text(value, source, field)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise SourceValidationError(f"{source} {field} must use YYYY-MM-DD") from error


def _refs(value: Any, known: set[str], source: str, field: str, required: bool = False) -> list[str]:
    if not isinstance(value, list) or (required and not value):
        raise SourceValidationError(f"{source} requires {field} list")
    if len(value) != len(set(value)):
        raise SourceValidationError(f"{source} {field} contains duplicate references")
    noun = field.removesuffix("_refs").replace("_", " ")
    for ref in value:
        if ref not in known:
            raise SourceValidationError(f"{source} references unknown {noun} {ref}")
    return value


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def _git(path: Path, *args: str) -> str:
    environment = dict(os.environ)
    environment.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"})
    try:
        return subprocess.run(
            ["git", "-C", str(path), *args], check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment,
        ).stdout.rstrip("\n")
    except (OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        raise SourceValidationError(f"cannot inspect configured repository {path}: {detail}") from error


def _inspect_local(repository: dict[str, Any], sequence_start: int) -> tuple[list[dict[str, str]], dict[str, Any]]:
    source = f"repository {repository['id']}"
    acquisition = repository["acquisition"]
    path_text = _text(acquisition.get("local_path"), source, "acquisition.local_path")
    path = Path(path_text)
    if not path.is_absolute() or not path.is_dir():
        raise SourceValidationError(f"{source} local_path must be an existing absolute directory")
    allowed = acquisition.get("allowed_paths")
    if not isinstance(allowed, list) or path.resolve() not in {Path(item).resolve() for item in allowed if isinstance(item, str)}:
        raise SourceValidationError(f"{source} local_path is outside the configured allow-list")
    if _git(path, "rev-parse", "--is-inside-work-tree") != "true":
        raise SourceValidationError(f"{source} local_path is not a Git worktree")
    head = _git(path, "rev-parse", "HEAD")
    if head != repository["expected_head"]:
        raise SourceValidationError(f"{source} expected_head does not match configured repository state")
    shallow = _git(path, "rev-parse", "--is-shallow-repository") == "true"
    completeness = repository["history"]["completeness"]
    if shallow and completeness == "complete":
        raise SourceValidationError(f"{source} shallow history cannot be declared complete")
    status = _git(path, "status", "--porcelain=v2", "--branch")
    detached = "# branch.head (detached)" in status
    dirty = any(line and not line.startswith("#") for line in status.splitlines())
    fmt = "%H%x1f%P%x1f%aI%x1f%cI%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1f%s%x1e"
    raw = _git(path, "log", "--no-show-signature", f"--pretty=format:{fmt}", head)
    rows: list[dict[str, str]] = []
    for offset, record in enumerate(raw.split("\x1e")):
        if not record.strip():
            continue
        fields = record.strip("\n").split("\x1f")
        if len(fields) != 9:
            raise SourceValidationError(f"{source} returned an invalid Git record")
        commit_hash, parents, authored, committed, author_name, author_email, committer_name, committer_email, subject = fields
        record_type = "merge_commit" if len(parents.split()) > 1 else "revert" if subject.casefold().startswith("revert") else "commit"
        raw_digest = hashlib.sha256(record.encode("utf-8")).hexdigest()
        rows.append({
            "record_id": f"GITREC-{committed[:4]}-{sequence_start + offset:06d}",
            "repository_ref": repository["id"], "record_type": record_type,
            "immutable_identifier": commit_hash, "occurred_at": "", "authored_at": authored,
            "committed_at": committed, "author_name": author_name,
            "author_email_sha256": hashlib.sha256(author_email.encode("utf-8")).hexdigest(),
            "committer_name": committer_name,
            "committer_email_sha256": hashlib.sha256(committer_email.encode("utf-8")).hexdigest(),
            "subject": subject, "parent_identifiers": ";".join(parents.split()),
            "ref_names": "", "related_record_ids": "", "source_evidence_ref": "",
            "status": "recorded", "raw_record_sha256": raw_digest,
        })
    return rows, {"head": head, "shallow": shallow, "detached": detached, "dirty": dirty}


def _load_interpretations(input_dir: Path) -> list[dict[str, Any]]:
    combined = input_dir / "repository-interpretations.yaml"
    directory = input_dir / "repository-interpretations"
    split = [path for path in sorted(directory.glob("interpretation.*.yaml")) if not path.name.endswith(".template.yaml")] if directory.is_dir() else []
    if combined.is_file() and split:
        raise SourceValidationError("cannot use both repository-interpretations.yaml and split interpretation files")
    if combined.is_file():
        records = load_yaml_mapping(combined).get("interpretations")
        if not isinstance(records, list):
            raise SourceValidationError("repository-interpretations.yaml requires an interpretations list")
        return records
    records = []
    pattern = re.compile(r"interpretation\.(GITINT-\d{4}-\d{4})\.yaml")
    for path in split:
        match = pattern.fullmatch(path.name)
        record = load_yaml_mapping(path).get("interpretation")
        if not match or not isinstance(record, dict) or record.get("id") != match.group(1):
            raise SourceValidationError(f"{path.name} filename ID must match interpretation.id")
        records.append(record)
    return records


def load_git_evidence(input_dir: Path, overview: dict[str, Any], experiments: list[dict[str, Any]], claim_mapping: dict[str, Any]) -> dict[str, Any]:
    document = load_yaml_mapping(input_dir / "repositories.yaml")
    root = document.get("repository_evidence")
    if not isinstance(root, dict) or root.get("state") not in {"applicable", "not_applicable"}:
        raise SourceValidationError("repositories.yaml requires repository_evidence state")
    if root["state"] == "not_applicable":
        reason = _text(root.get("reason"), "repositories.yaml", "repository_evidence.reason")
        if root.get("repositories"):
            raise SourceValidationError("not_applicable repository evidence forbids repositories")
        return {"is_applicable": False, "reason": reason, "repositories": [], "events": [], "interpretations": [], "identity_mappings": []}
    coverage = _text(root.get("coverage_statement"), "repositories.yaml", "coverage_statement")
    repositories = deepcopy(root.get("repositories"))
    if not isinstance(repositories, list) or not repositories:
        raise SourceValidationError("applicable repository evidence requires repositories")

    project_ids = {item["id"] for item in overview["projects"]}
    uncertainty_ids = {item["id"] for item in overview["uncertainties"]}
    activity_by_id = {item["id"]: item for item in overview["activities"]}
    activity_ids = set(activity_by_id)
    person_ids = {item["id"] for item in overview["people"]}
    run_by_id = {item["id"]: item for item in experiments}
    run_ids = set(run_by_id)
    evidence_ids = {item["evidence_id"] for item in overview["program_evidence"]}
    evidence_ids.update(item["evidence_id"] for run in experiments for item in run["evidence"])
    review_ids = {item["id"] for item in claim_mapping.get("reviews", [])}
    scope_start = date.fromisoformat(str(overview["program"]["scope"]["period_start"]))
    scope_end = date.fromisoformat(str(overview["program"]["scope"]["period_end"]))

    repository_by_id: dict[str, dict[str, Any]] = {}
    identities: list[dict[str, Any]] = []
    identity_keys: dict[tuple[str, str, str], str] = {}
    for repository in repositories:
        repository_id = repository.get("id")
        if not isinstance(repository_id, str) or not REPOSITORY_ID.fullmatch(repository_id) or repository_id in repository_by_id:
            raise SourceValidationError(f"invalid or duplicate repository ID: {repository_id}")
        source = f"repository {repository_id}"
        _text(repository.get("name"), source, "name")
        repository["project_refs"] = _refs(repository.get("project_refs"), project_ids, source, "project_refs", True)
        start = _date(repository.get("period_start"), source, "period_start")
        end = _date(repository.get("period_end"), source, "period_end")
        if end < start or start < scope_start or end > scope_end:
            raise SourceValidationError(f"{source} period must fall within program scope")
        acquisition = repository.get("acquisition")
        if not isinstance(acquisition, dict) or acquisition.get("mode") not in {"exported", "local"}:
            raise SourceValidationError(f"{source} acquisition.mode must be exported or local")
        head = _text(repository.get("expected_head"), source, "expected_head")
        if not HEX_40_PLUS.fullmatch(head):
            raise SourceValidationError(f"{source} expected_head must be a full object hash")
        history = repository.get("history")
        if not isinstance(history, dict) or history.get("completeness") not in {"complete", "shallow", "partial", "unknown", "unavailable"}:
            raise SourceValidationError(f"{source} requires valid history.completeness")
        limitation = history.get("limitation", {"state": "no_data"})
        if not isinstance(limitation, dict) or limitation.get("state") not in {"no_data", "provided"}:
            raise SourceValidationError(f"{source} requires history.limitation state")
        if history["completeness"] != "complete" and limitation.get("state") != "provided":
            raise SourceValidationError(f"{source} incomplete history requires a limitation")
        if limitation.get("state") == "provided":
            _text(limitation.get("content"), source, "history.limitation.content")
            if limitation.get("review_ref") not in review_ids:
                raise SourceValidationError(f"{source} incomplete history requires an accountable review_ref")
        mappings = repository.get("identity_mappings", [])
        if not isinstance(mappings, list):
            raise SourceValidationError(f"{source} identity_mappings must be a list")
        for mapping in mappings:
            mapping_id = mapping.get("id")
            if not isinstance(mapping_id, str) or not IDENTITY_ID.fullmatch(mapping_id) or any(item["id"] == mapping_id for item in identities):
                raise SourceValidationError(f"invalid or duplicate identity mapping ID: {mapping_id}")
            name = _text(mapping.get("git_name_exact"), f"identity {mapping_id}", "git_name_exact")
            digest = _text(mapping.get("git_email_sha256"), f"identity {mapping_id}", "git_email_sha256")
            if not HEX_64.fullmatch(digest):
                raise SourceValidationError(f"identity {mapping_id} git_email_sha256 must be 64 lowercase hex characters")
            person = mapping.get("person_ref")
            if person not in person_ids:
                raise SourceValidationError(f"identity {mapping_id} references unknown person {person}")
            _text(mapping.get("basis"), f"identity {mapping_id}", "basis")
            _refs(mapping.get("evidence_refs", []), evidence_ids, f"identity {mapping_id}", "evidence_refs")
            if mapping.get("review_ref") not in review_ids:
                raise SourceValidationError(f"identity {mapping_id} references unknown review {mapping.get('review_ref')}")
            if mapping.get("status") not in {"confirmed", "disputed", "superseded"}:
                raise SourceValidationError(f"identity {mapping_id} has invalid status")
            key = (repository_id, name, digest)
            if mapping["status"] == "confirmed" and key in identity_keys and identity_keys[key] != person:
                raise SourceValidationError(f"repository {repository_id} has ambiguous identity mapping for {name}")
            if mapping["status"] == "confirmed":
                identity_keys[key] = person
            mapping["repository_ref"] = repository_id
            identities.append(mapping)
        repository["_period_start"] = start
        repository_by_id[repository_id] = repository

    rows = load_strict_csv(input_dir / "repository-events.csv", EVENT_HEADERS)
    local_observations: dict[str, Any] = {}
    for repository in repositories:
        if repository["acquisition"]["mode"] == "local":
            imported, observed = _inspect_local(repository, len(rows) + 1)
            rows.extend(imported)
            local_observations[repository["id"]] = observed

    events: list[dict[str, Any]] = []
    event_by_id: dict[str, dict[str, Any]] = {}
    immutable: set[tuple[str, str]] = set()
    for number, row in enumerate(rows, 2):
        source = f"repository-events.csv row {number}"
        record_id = _text(row.get("record_id"), source, "record_id")
        if not EVENT_ID.fullmatch(record_id) or record_id in event_by_id:
            raise SourceValidationError(f"invalid or duplicate repository event ID: {record_id}")
        repository_ref = _text(row.get("repository_ref"), source, "repository_ref")
        if repository_ref not in repository_by_id:
            raise SourceValidationError(f"{source} references unknown repository {repository_ref}")
        record_type = _text(row.get("record_type"), source, "record_type")
        if record_type not in EVENT_TYPES:
            raise SourceValidationError(f"{source} has invalid record_type")
        identifier = _text(row.get("immutable_identifier"), source, "immutable_identifier")
        key = (repository_ref, identifier)
        if key in immutable:
            raise SourceValidationError(f"Duplicate immutable identifier {identifier} in {repository_ref}")
        immutable.add(key)
        item: dict[str, Any] = dict(row)
        item["is_commit"] = record_type in {"commit", "merge_commit", "revert"}
        if item["is_commit"]:
            if not HEX_40_PLUS.fullmatch(identifier):
                raise SourceValidationError(f"{source} commit requires a full object hash")
            item["_authored_at"] = _timestamp(row["authored_at"], source, "authored_at")
            item["_effective_at"] = _timestamp(row["committed_at"], source, "committed_at")
            for field in ("author_name", "author_email_sha256", "committer_name", "committer_email_sha256", "subject"):
                _text(row[field], source, field)
            for field in ("author_email_sha256", "committer_email_sha256", "raw_record_sha256"):
                if not HEX_64.fullmatch(row[field]):
                    raise SourceValidationError(f"{source} {field} must be 64 lowercase hex characters")
            item["full_hash"] = identifier
            item["display_id"] = identifier[:12]
            item["author_person_ref"] = identity_keys.get((repository_ref, row["author_name"].strip(), row["author_email_sha256"].strip()), "")
            item["committer_person_ref"] = identity_keys.get((repository_ref, row["committer_name"].strip(), row["committer_email_sha256"].strip()), "")
        else:
            item["_effective_at"] = _timestamp(row["occurred_at"], source, "occurred_at")
            item["_authored_at"] = item["_effective_at"]
            item["display_id"] = identifier
            item["author_person_ref"] = item["committer_person_ref"] = ""
        item["effective_display"] = item["_effective_at"].isoformat()
        item["parent_list"] = _split(row["parent_identifiers"])
        item["ref_list"] = _split(row["ref_names"])
        item["related_record_list"] = _split(row["related_record_ids"])
        evidence_ref = row["source_evidence_ref"].strip()
        if evidence_ref and evidence_ref not in evidence_ids:
            raise SourceValidationError(f"{source} references unknown evidence {evidence_ref}")
        event_by_id[record_id] = item
        events.append(item)
    for item in events:
        for ref in item["related_record_list"]:
            if ref not in event_by_id:
                raise SourceValidationError(f"event {item['record_id']} references unknown related record {ref}")
    for repository in repositories:
        owned = [item for item in events if item["repository_ref"] == repository["id"]]
        if not owned and repository["history"]["completeness"] != "unavailable":
            raise SourceValidationError(f"repository {repository['id']} requires repository facts")
        if repository["expected_head"] not in {item["immutable_identifier"] for item in owned}:
            raise SourceValidationError(f"repository {repository['id']} expected_head is absent from repository facts")
        repository["observed"] = local_observations.get(repository["id"], {})

    interpretations = deepcopy(_load_interpretations(input_dir))
    seen_interpretations: set[str] = set()
    for record in interpretations:
        interpretation_id = record.get("id")
        if not isinstance(interpretation_id, str) or not INTERPRETATION_ID.fullmatch(interpretation_id) or interpretation_id in seen_interpretations:
            raise SourceValidationError(f"invalid or duplicate interpretation ID: {interpretation_id}")
        seen_interpretations.add(interpretation_id)
        source = f"interpretation {interpretation_id}"
        repository_ref = record.get("repository_ref")
        if repository_ref not in repository_by_id:
            raise SourceValidationError(f"{source} references unknown repository {repository_ref}")
        record_refs = _refs(record.get("record_refs"), set(event_by_id), source, "record_refs", True)
        if any(event_by_id[ref]["repository_ref"] != repository_ref for ref in record_refs):
            raise SourceValidationError(f"{source} record_refs contradict repository_ref")
        if record.get("materiality") not in {"material", "not_material", "human_review_required"}:
            raise SourceValidationError(f"{source} has invalid materiality")
        contexts = record.get("engineering_context")
        if not isinstance(contexts, list) or not contexts or any(item not in CONTEXTS for item in contexts):
            raise SourceValidationError(f"{source} requires valid engineering_context")
        _text(record.get("interpretation"), source, "interpretation")
        if record.get("interpretation_owner") not in person_ids:
            raise SourceValidationError(f"{source} references unknown interpretation owner")
        record["project_refs"] = _refs(record.get("project_refs", []), project_ids, source, "project_refs")
        record["uncertainty_refs"] = _refs(record.get("uncertainty_refs", []), uncertainty_ids, source, "uncertainty_refs")
        record["activity_refs"] = _refs(record.get("activity_refs", []), activity_ids, source, "activity_refs")
        record["experiment_refs"] = _refs(record.get("experiment_refs", []), run_ids, source, "experiment_refs")
        record["person_refs"] = _refs(record.get("person_refs", []), person_ids, source, "person_refs")
        record["evidence_refs"] = _refs(record.get("evidence_refs", []), evidence_ids, source, "evidence_refs")
        record["review_refs"] = _refs(record.get("review_refs", []), review_ids, source, "review_refs")
        for activity_ref in record["activity_refs"]:
            activity = activity_by_id[activity_ref]
            if not set(record["project_refs"]).issubset(set(activity["project_refs"])):
                raise SourceValidationError(f"{source} project_refs contradict activity {activity_ref}")
            if not set(record["experiment_refs"]).issubset(set(activity.get("experiment_refs", []))):
                raise SourceValidationError(f"{source} experiment_refs contradict activity {activity_ref}")
        record["_recorded_at"] = _timestamp(record.get("recorded_at"), source, "recorded_at")
        record["first_event_at"] = min(event_by_id[ref]["_effective_at"] for ref in record_refs)

    repositories.sort(key=lambda item: (item["_period_start"], item["id"]))
    events.sort(key=lambda item: (item["_effective_at"], 0 if item["is_commit"] else 1, item["immutable_identifier"], item["record_id"]))
    interpretations.sort(key=lambda item: (item["first_event_at"], item["id"]))
    identities.sort(key=lambda item: (item["repository_ref"], item["git_name_exact"].casefold(), item["git_email_sha256"], item["id"]))
    return {
        "is_applicable": True, "coverage_statement": coverage,
        "repositories": repositories, "events": events,
        "interpretations": interpretations, "identity_mappings": identities,
        "has_interpretations": bool(interpretations), "has_identity_mappings": bool(identities),
    }
