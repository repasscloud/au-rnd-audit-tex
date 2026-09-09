from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
import re
from typing import Any

from validation import SourceValidationError, load_strict_csv, load_yaml_mapping

PROJECT_ID = re.compile(r"RND-\d{4}-\d{2}")
UNCERTAINTY_ID = re.compile(r"UT-\d{2}")
PERSON_ID = re.compile(r"P-\d{3}")
ACTIVITY_ID = re.compile(r"ACT-\d{4}-\d{3}")
EVIDENCE_ID = re.compile(r"EV-\d{4}")
PLACEHOLDER = re.compile(r"(?:\[[^\]]+\]|xxx|tbd)", re.IGNORECASE)
PROGRAM_EVIDENCE_HEADERS = ("evidence_id", "type", "title", "location", "captured_at", "period_start", "period_end", "notes")
COLLECTIONS = {
    "projects": ("project", PROJECT_ID),
    "uncertainties": ("uncertainty", UNCERTAINTY_ID),
    "people": ("person", PERSON_ID),
    "activities": ("activity", ACTIVITY_ID),
}


def _scan(value: Any, source: str, path: str = "") -> None:
    if isinstance(value, str) and PLACEHOLDER.fullmatch(value.strip()):
        raise SourceValidationError(f"{source} contains placeholder text at {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            _scan(item, source, f"{path}.{key}".strip("."))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan(item, source, f"{path}[{index}]")


def _value(record: dict[str, Any], path: str) -> Any:
    value: Any = record
    for part in path.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def _text(record: dict[str, Any], field: str, source: str) -> str:
    value = _value(record, field)
    if not isinstance(value, str) or not value.strip():
        raise SourceValidationError(f"{source} requires {field}")
    if PLACEHOLDER.fullmatch(value.strip()):
        raise SourceValidationError(f"{source} contains placeholder text at {field}")
    return value.strip()


def _list(record: dict[str, Any], field: str, source: str, required: bool = True) -> list[Any]:
    value = record.get(field)
    if not isinstance(value, list) or (required and not value):
        raise SourceValidationError(f"{source} requires {field} list")
    return value


def _parse_date(value: Any, source: str, field: str) -> date:
    if not isinstance(value, str):
        raise SourceValidationError(f"{source} requires {field}")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise SourceValidationError(f"{source} {field} must use YYYY-MM-DD") from error


def _parse_timestamp(value: Any, source: str, field: str) -> datetime:
    if not isinstance(value, str):
        raise SourceValidationError(f"{source} requires {field}")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise SourceValidationError(f"{source} {field} must be an ISO 8601 timestamp") from error
    if parsed.tzinfo is None:
        raise SourceValidationError(f"{source} {field} must include a UTC offset")
    return parsed


def _state(value: Any, source: str, field: str, allow_no_data: bool = False) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SourceValidationError(f"{source} requires {field} state mapping")
    state = value.get("state")
    allowed = {"provided", "not_applicable"} | ({"no_data"} if allow_no_data else set())
    if state not in allowed:
        raise SourceValidationError(f"{source} {field} has invalid state")
    key = "content" if state == "provided" else "reason" if state == "not_applicable" else None
    if state == "provided" and "items" in value:
        items = value["items"]
        if not isinstance(items, list) or not items:
            raise SourceValidationError(f"{source} {field} requires items")
        key = None
    if key:
        _text(value, key, f"{source} {field}")
    permitted = ({key} if key else set()) | ({"items"} if state == "provided" and "items" in value else set())
    for forbidden in {"content", "reason", "items"} - permitted:
        if forbidden in value:
            raise SourceValidationError(f"{source} {field} state {state} has invalid content")
    result = deepcopy(value)
    result["has_data"] = state == "provided"
    result["is_not_applicable"] = state == "not_applicable"
    return result


def _load_collection(input_dir: Path, plural: str) -> list[dict[str, Any]]:
    singular, id_pattern = COLLECTIONS[plural]
    combined = input_dir / f"{plural}.yaml"
    directory = input_dir / plural
    split = [p for p in sorted(directory.glob(f"{singular}.*.yaml")) if not p.name.endswith(".template.yaml")] if directory.is_dir() else []
    if combined.is_file() and split:
        raise SourceValidationError(f"cannot use both {plural}.yaml and split {singular} files")
    if combined.is_file():
        records = load_yaml_mapping(combined).get(plural)
        if not isinstance(records, list) or not records:
            raise SourceValidationError(f"{plural}.yaml requires a non-empty {plural} list")
        return records
    if not split:
        raise SourceValidationError(f"Missing {plural} source")
    matcher = re.compile(rf"{singular}\.({id_pattern.pattern})\.yaml")
    records = []
    for path in split:
        match = matcher.fullmatch(path.name)
        if not match:
            raise SourceValidationError(f"invalid split {singular} filename: {path.name}")
        record = load_yaml_mapping(path).get(singular)
        if not isinstance(record, dict):
            raise SourceValidationError(f"{path.name} requires a {singular} mapping")
        if record.get("id") != match.group(1):
            raise SourceValidationError(f"{path.name} filename ID must match {singular}.id")
        records.append(record)
    return records


def _index(records: list[dict[str, Any]], name: str, pattern: re.Pattern[str]) -> dict[str, dict[str, Any]]:
    indexed = {}
    for record in records:
        record_id = record.get("id")
        if not isinstance(record_id, str) or not pattern.fullmatch(record_id):
            raise SourceValidationError(f"{name} has invalid id: {record_id}")
        if record_id in indexed:
            raise SourceValidationError(f"Duplicate {name} ID: {record_id}")
        indexed[record_id] = record
    return indexed


def _refs(values: Any, known: dict[str, Any], source: str, field: str, required: bool = True) -> list[str]:
    if not isinstance(values, list) or (required and not values):
        raise SourceValidationError(f"{source} requires {field} list")
    if len(values) != len(set(values)):
        raise SourceValidationError(f"{source} {field} contains duplicate references")
    label = field.removesuffix("s")
    for value in values:
        if value not in known:
            raise SourceValidationError(f"{source} references unknown {label} {value}")
    return values


def load_overview_sources(input_dir: Path, experiments: list[dict[str, Any]]) -> dict[str, Any]:
    document = load_yaml_mapping(input_dir / "program.yaml")
    program = document.get("program")
    if not isinstance(program, dict):
        raise SourceValidationError("program.yaml requires a program mapping")
    _scan(document, "program.yaml")
    for field in ("product.name", "product.description", "product.development_context", "technical_objective.statement", "technical_objective.new_knowledge_sought", "scope.period_start", "scope.period_end", "scope.included_work_summary", "scope.outside_boundary_summary", "baseline.summary", "annual_synthesis.progression_summary", "annual_synthesis.knowledge_outcome"):
        _text(program, field, "program.yaml")
    program["commercial_context"] = _state(program.get("commercial_context"), "program.yaml", "commercial_context")
    scope_start = _parse_date(program["scope"]["period_start"], "program.yaml", "scope.period_start")
    scope_end = _parse_date(program["scope"]["period_end"], "program.yaml", "scope.period_end")
    if scope_end < scope_start:
        raise SourceValidationError("program.yaml scope period_end must not precede period_start")
    _list(program["scope"], "repositories", "program.yaml scope")
    for field in ("existing_knowledge", "approaches_reviewed"):
        _list(program["baseline"], field, "program.yaml baseline")
    program["baseline"]["prior_internal_work"] = _state(program["baseline"].get("prior_internal_work"), "program.yaml", "baseline.prior_internal_work", True)
    program["baseline"]["standards_and_constraints"] = _state(program["baseline"].get("standards_and_constraints"), "program.yaml", "baseline.standards_and_constraints", True)
    _list(program["annual_synthesis"], "unresolved_matters", "program.yaml annual_synthesis")
    _list(program["annual_synthesis"], "limitations", "program.yaml annual_synthesis")
    applicability = program.get("applicability")
    if not isinstance(applicability, dict):
        raise SourceValidationError("program.yaml requires applicability")
    for field in ("labour_summary", "infrastructure_summary"):
        value = applicability.get(field)
        if not isinstance(value, dict) or value.get("state") not in {"applicable", "not_applicable"}:
            raise SourceValidationError(f"program.yaml applicability.{field} has invalid state")
        if value["state"] == "not_applicable":
            reason = value.get("reason")
            if not isinstance(reason, str) or not reason.strip() or PLACEHOLDER.fullmatch(reason.strip()):
                raise SourceValidationError(f"program.yaml applicability.{field} not_applicable requires reason")
        elif "reason" in value:
            raise SourceValidationError(f"program.yaml applicability.{field} applicable forbids reason")
    applicability["contractor_summary"] = _state(applicability.get("contractor_summary"), "program.yaml", "applicability.contractor_summary")

    projects = deepcopy(_load_collection(input_dir, "projects")); uncertainties = deepcopy(_load_collection(input_dir, "uncertainties"))
    people = deepcopy(_load_collection(input_dir, "people")); activities = deepcopy(_load_collection(input_dir, "activities"))
    for name, records in (("projects", projects), ("uncertainties", uncertainties), ("people", people), ("activities", activities)):
        for record in records: _scan(record, f"{name}.yaml")
    project_ids = _index(projects, "project", PROJECT_ID); uncertainty_ids = _index(uncertainties, "uncertainty", UNCERTAINTY_ID)
    person_ids = _index(people, "person", PERSON_ID); activity_ids = _index(activities, "activity", ACTIVITY_ID)
    experiment_ids = {run["id"]: run for run in experiments}

    program_evidence = []; evidence_ids: dict[str, Any] = {}
    for number, row in enumerate(load_strict_csv(input_dir / "program-evidence.csv", PROGRAM_EVIDENCE_HEADERS), 2):
        source = f"program-evidence.csv row {number}"
        for field in PROGRAM_EVIDENCE_HEADERS[:-1]: _text(row, field, source)
        _scan(row, source)
        evidence_id = row["evidence_id"].strip()
        if not EVIDENCE_ID.fullmatch(evidence_id): raise SourceValidationError(f"{source} evidence_id has invalid format")
        if evidence_id in evidence_ids: raise SourceValidationError(f"Duplicate evidence ID: {evidence_id}")
        start = _parse_date(row["period_start"], source, "period_start"); end = _parse_date(row["period_end"], source, "period_end")
        captured = _parse_timestamp(row["captured_at"], source, "captured_at")
        if end < start: raise SourceValidationError(f"{source} period_end must not precede period_start")
        item = dict(row, _period_start=start, _captured_at=captured)
        evidence_ids[evidence_id] = item; program_evidence.append(item)
    for run in experiments:
        for evidence in run["evidence"]:
            evidence_id = evidence["evidence_id"]
            if evidence_id in evidence_ids: raise SourceValidationError(f"Duplicate evidence ID: {evidence_id}")
            evidence_ids[evidence_id] = evidence

    for project in projects:
        source = f"project {project['id']}"
        for field in ("name", "technical_focus", "technical_problem", "experimental_strategy", "annual_outcome"): _text(project, field, source)
        start = _parse_date(project.get("period_start"), source, "period_start"); end = _parse_date(project.get("period_end"), source, "period_end")
        if start < scope_start or end > scope_end or end < start: raise SourceValidationError(f"{source} period must fall within program scope")
        project["_period_start"] = start
        if project.get("lead_person_ref") not in person_ids: raise SourceValidationError(f"{source} references unknown lead_person_ref {project.get('lead_person_ref')}")
        project["business_objective"] = _state(project.get("business_objective"), source, "business_objective")
        _refs(project.get("uncertainty_refs"), uncertainty_ids, source, "uncertainty_refs"); _refs(project.get("experiment_refs"), experiment_ids, source, "experiment_refs")
        _refs(project.get("activity_refs"), activity_ids, source, "activity_refs"); _refs(project.get("contributor_refs"), person_ids, source, "contributor_refs")
        _refs(project.get("evidence_refs"), evidence_ids, source, "evidence_refs"); _list(project, "repositories", source); _list(project, "unresolved_matters", source)

    for uncertainty in uncertainties:
        source = f"uncertainty {uncertainty['id']}"
        for field in ("title", "area", "statement", "outcome_not_determinable_reason", "competent_professional_basis", "new_knowledge_sought", "year_outcome"): _text(uncertainty, field, source)
        if uncertainty.get("status") not in {"open", "partly_resolved", "resolved", "superseded"}: raise SourceValidationError(f"{source} has invalid status")
        _refs(uncertainty.get("project_refs"), project_ids, source, "project_refs"); _refs(uncertainty.get("background_evidence_refs"), evidence_ids, source, "background_evidence_refs")
        _list(uncertainty, "unresolved_aspects", source)
        if set(uncertainty["project_refs"]) != {p["id"] for p in projects if uncertainty["id"] in p["uncertainty_refs"]}: raise SourceValidationError(f"{source} project_refs must match project uncertainty_refs")

    for person in people:
        source = f"person {person['id']}"
        for field in ("name", "role", "engagement_type"): _text(person, field, source)
        _list(person, "technical_responsibilities", source); _refs(person.get("project_refs"), project_ids, source, "project_refs"); _refs(person.get("activity_refs"), activity_ids, source, "activity_refs")
        if isinstance(person.get("evidence_refs"), dict): person["evidence_refs"] = _state(person["evidence_refs"], source, "evidence_refs", True)
        else: _refs(person.get("evidence_refs"), evidence_ids, source, "evidence_refs", False)

    classifications = {"candidate_experimental", "candidate_supporting", "ordinary_engineering", "outside_rnd_boundary", "human_review_required"}
    for activity in activities:
        source = f"activity {activity['id']}"
        for field in ("title", "description", "rationale"): _text(activity, field, source)
        if activity.get("classification") not in classifications: raise SourceValidationError(f"{source} has invalid classification")
        if activity.get("classification_owner") not in person_ids: raise SourceValidationError(f"{source} references unknown classification_owner {activity.get('classification_owner')}")
        start = _parse_date(activity.get("period_start"), source, "period_start"); end = _parse_date(activity.get("period_end"), source, "period_end")
        if end < start: raise SourceValidationError(f"{source} period_end must not precede period_start")
        activity["_period_start"] = start
        _refs(activity.get("project_refs"), project_ids, source, "project_refs"); uncertainty_refs = _refs(activity.get("uncertainty_refs"), uncertainty_ids, source, "uncertainty_refs", False)
        experiment_refs = _refs(activity.get("experiment_refs"), experiment_ids, source, "experiment_refs", False); _refs(activity.get("person_refs"), person_ids, source, "person_refs")
        if isinstance(activity.get("evidence_refs"), dict): activity["evidence_refs"] = _state(activity["evidence_refs"], source, "evidence_refs", True)
        else: _refs(activity.get("evidence_refs"), evidence_ids, source, "evidence_refs", False)
        if activity["classification"] == "candidate_experimental" and (not uncertainty_refs or not experiment_refs): raise SourceValidationError(f"{source} candidate_experimental requires uncertainty and experiment references")
        if activity["classification"] == "outside_rnd_boundary" and experiment_refs: raise SourceValidationError(f"{source} outside_rnd_boundary must not reference experiments")
        supports_activities = _refs(activity.get("supports_activity_refs", []), activity_ids, source, "supports_activity_refs", False)
        supports_experiments = _refs(activity.get("supports_experiment_refs", []), experiment_ids, source, "supports_experiment_refs", False)
        review_refs = activity.get("review_refs", [])
        if not isinstance(review_refs, list) or len(review_refs) != len(set(review_refs)):
            raise SourceValidationError(f"{source} review_refs must be a list without duplicates")
        if activity["classification"] == "candidate_supporting":
            if not supports_activities and not supports_experiments:
                raise SourceValidationError(f"{source} candidate_supporting requires a support target")
            for target in supports_activities:
                if activity_ids[target].get("classification") != "candidate_experimental":
                    raise SourceValidationError(f"{source} support target {target} must be candidate_experimental")
            for target in supports_experiments:
                if experiment_ids[target]["project_ref"] in project_ids and experiment_ids[target]["project_ref"] not in activity["project_refs"]:
                    raise SourceValidationError(f"{source} support experiment {target} must belong to a referenced project")
        elif supports_activities or supports_experiments:
            raise SourceValidationError(f"{source} support targets require candidate_supporting classification")
        activity["supports_activity_refs"] = supports_activities
        activity["supports_experiment_refs"] = supports_experiments
        activity["review_refs"] = review_refs

    for run in experiments:
        if run["project_ref"] not in project_ids: raise SourceValidationError(f"experiment {run['id']} references unknown project_ref {run['project_ref']}")
        for ref in run["uncertainty_refs"]:
            if ref not in uncertainty_ids: raise SourceValidationError(f"experiment {run['id']} references unknown uncertainty_ref {ref}")
        for engineer in run["engineers"]:
            if engineer["person_ref"] not in person_ids: raise SourceValidationError(f"experiment {run['id']} references unknown person_ref {engineer['person_ref']}")
    for project in projects:
        owned = {run["id"] for run in experiments if run["project_ref"] == project["id"]}
        if set(project["experiment_refs"]) != owned: raise SourceValidationError(f"project {project['id']} experiment_refs must match experiment project_ref values")
        linked_activities = {activity["id"] for activity in activities if project["id"] in activity["project_refs"]}
        if set(project["activity_refs"]) != linked_activities: raise SourceValidationError(f"project {project['id']} activity_refs must match activity project_refs")

    projects.sort(key=lambda x: (x["_period_start"], x["id"])); project_order = {p["id"]: i for i, p in enumerate(projects)}
    uncertainties.sort(key=lambda x: (min(project_order[r] for r in x["project_refs"]), x["id"])); people.sort(key=lambda x: (x["name"].casefold(), x["id"]))
    activities.sort(key=lambda x: (x["_period_start"], x["id"])); program_evidence.sort(key=lambda x: (x["_period_start"], x["_captured_at"], x["evidence_id"]))
    summaries = [{"id": r["id"], "title": r["title"], "started_date": r["started_date"], "project_ref": r["project_ref"], "uncertainty_refs": r["uncertainty_refs"], "status_label": r["status_label"], "conclusion_label": r["conclusion_label"], "conclusion_text": r["conclusion_text"], "result_count": len(r["results"]), "result_kinds": sorted({v["kind_label"] for v in r["results"]}), "evidence_refs": [e["evidence_id"] for e in r["evidence"]]} for r in experiments]
    return {"program": program, "projects": projects, "uncertainties": uncertainties, "people": people, "activities": activities, "program_evidence": program_evidence, "experiment_summaries": summaries}
