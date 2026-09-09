from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Any

from validation import SourceValidationError, load_yaml_mapping

TIMESHEET_ID = re.compile(r"TS-\d{4}-\d{4}")
COST_ID = re.compile(r"COST-\d{4}-\d{4}")
REVIEW_ID = re.compile(r"REV-\d{4}-\d{3}")
REVIEW_TYPES = {"legal", "technical", "evidentiary", "ownership", "classification", "allocation"}
PLACEHOLDER = re.compile(r"(?:\[[^\]]+\]|xxx|tbd)", re.IGNORECASE)


def load_reviews(input_dir: Path) -> list[dict[str, Any]]:
    combined = input_dir / "reviews.yaml"
    directory = input_dir / "reviews"
    split = [path for path in sorted(directory.glob("review.*.yaml")) if not path.name.endswith(".template.yaml")] if directory.is_dir() else []
    if combined.is_file() and split:
        raise SourceValidationError("cannot use both reviews.yaml and split review files")
    if not combined.is_file() and not split:
        return []
    if combined.is_file():
        records = load_yaml_mapping(combined).get("reviews")
        if not isinstance(records, list):
            raise SourceValidationError("reviews.yaml requires a reviews list")
    else:
        records = []
        pattern = re.compile(r"review\.(REV-\d{4}-\d{3})\.yaml")
        for path in split:
            match = pattern.fullmatch(path.name)
            if not match:
                raise SourceValidationError(f"invalid split review filename: {path.name}")
            record = load_yaml_mapping(path).get("review")
            if not isinstance(record, dict) or record.get("id") != match.group(1):
                raise SourceValidationError(f"{path.name} filename ID must match review.id")
            records.append(record)
    seen: set[str] = set()
    for record in records:
        review_id = record.get("id")
        if not isinstance(review_id, str) or not REVIEW_ID.fullmatch(review_id):
            raise SourceValidationError(f"review has invalid id: {review_id}")
        if review_id in seen:
            raise SourceValidationError(f"Duplicate review ID: {review_id}")
        seen.add(review_id)
    return records


def build_claim_mapping(
    overview: dict[str, Any], experiments: list[dict[str, Any]],
    timesheets: list[dict[str, str]], infrastructure_costs: list[dict[str, str]],
    reviews: list[dict[str, Any]],
) -> dict[str, Any]:
    projects = {item["id"]: item for item in overview["projects"]}
    uncertainties = {item["id"]: item for item in overview["uncertainties"]}
    activities = {item["id"]: item for item in overview["activities"]}
    people = {item["id"]: item for item in overview["people"]}
    runs = {item["id"]: item for item in experiments}
    evidence = {item["evidence_id"] for item in overview["program_evidence"]}
    evidence.update(item["evidence_id"] for run in experiments for item in run["evidence"])
    for activity in activities.values():
        activity["classification_label"] = activity["classification"].replace("_", " ").title()

    seen_timesheets: set[str] = set()
    category_map = {"candidate_experimental": "core", "candidate_supporting": "supporting", "ordinary_engineering": "non-rnd", "outside_rnd_boundary": "non-rnd"}
    for number, row in enumerate(timesheets, 2):
        if "timesheet_id" not in row:
            if timesheets:
                raise SourceValidationError("populated legacy timesheets.csv cannot provide activity traceability")
            continue
        row_id = row["timesheet_id"].strip()
        if not TIMESHEET_ID.fullmatch(row_id) or row_id in seen_timesheets:
            raise SourceValidationError(f"timesheets.csv row {number} has invalid or duplicate timesheet_id {row_id}")
        seen_timesheets.add(row_id)
        person_ref, project_ref, activity_ref, run_ref = (row[key].strip() for key in ("person_ref", "project_ref", "activity_ref", "run_ref"))
        if person_ref not in people: raise SourceValidationError(f"timesheets.csv row {number} references unknown person_ref {person_ref}")
        if project_ref not in projects: raise SourceValidationError(f"timesheets.csv row {number} references unknown project_ref {project_ref}")
        if activity_ref not in activities: raise SourceValidationError(f"timesheets.csv row {number} references unknown activity_ref {activity_ref}")
        activity = activities[activity_ref]
        if project_ref not in activity["project_refs"]: raise SourceValidationError(f"timesheets.csv row {number} activity_ref contradicts project_ref")
        expected = category_map.get(activity["classification"])
        if expected and row["category"] != expected: raise SourceValidationError(f"timesheets.csv row {number} category {row['category']} contradicts activity {activity_ref} classification")
        if activity["classification"] == "human_review_required" and row["category"] != "review-required": raise SourceValidationError(f"timesheets.csv row {number} human-review activity requires review-required category")
        if run_ref and (run_ref not in runs or run_ref not in activity["experiment_refs"] or runs[run_ref]["project_ref"] != project_ref):
            raise SourceValidationError(f"timesheets.csv row {number} run_ref contradicts activity or project")

    seen_costs: set[str] = set()
    for number, row in enumerate(infrastructure_costs, 2):
        if "cost_id" not in row:
            if infrastructure_costs:
                raise SourceValidationError("populated legacy infrastructure-costs.csv cannot provide activity traceability")
            continue
        cost_id = row["cost_id"].strip()
        if not COST_ID.fullmatch(cost_id) or cost_id in seen_costs:
            raise SourceValidationError(f"infrastructure-costs.csv row {number} has invalid or duplicate cost_id {cost_id}")
        seen_costs.add(cost_id)
        refs = [value.strip() for value in row["activity_refs"].split(";") if value.strip()]
        if not refs or len(refs) != len(set(refs)): raise SourceValidationError(f"infrastructure-costs.csv row {number} requires unique activity_refs")
        for ref in refs:
            if ref not in activities: raise SourceValidationError(f"infrastructure-costs.csv row {number} references unknown activity_ref {ref}")
        if row["evidence_ref"].strip() not in evidence: raise SourceValidationError(f"infrastructure-costs.csv row {number} references unknown evidence_ref {row['evidence_ref'].strip()}")
        row["activity_ref_list"] = refs

    review_ids = {item["id"] for item in reviews}
    for activity in activities.values():
        for ref in activity["review_refs"]:
            if ref not in review_ids: raise SourceValidationError(f"activity {activity['id']} references unknown review_ref {ref}")
        if activity["classification"] == "human_review_required" and not activity["review_refs"]:
            raise SourceValidationError(f"activity {activity['id']} human_review_required requires review_refs")
    state_order = {"open": 0, "resolved": 1, "superseded": 2}
    reviews.sort(key=lambda item: (state_order.get(item.get("status"), 9), item.get("raised_at", ""), item["id"]))
    for review in reviews:
        question = review.get("question")
        if not isinstance(question, str) or not question.strip() or PLACEHOLDER.fullmatch(question.strip()):
            raise SourceValidationError(f"review {review['id']} requires non-placeholder question")
        if review.get("decision_type") not in REVIEW_TYPES or review.get("status") not in state_order:
            raise SourceValidationError(f"review {review['id']} has invalid decision_type or status")
        if review.get("owner_person_ref") not in people: raise SourceValidationError(f"review {review['id']} references unknown owner_person_ref")
        try: datetime.fromisoformat(review.get("raised_at", ""))
        except ValueError as error: raise SourceValidationError(f"review {review['id']} requires ISO raised_at") from error
        subjects = review.get("subject_refs")
        if not isinstance(subjects, dict) or not any(subjects.values()): raise SourceValidationError(f"review {review['id']} requires subject_refs")
        subject_indexes = {"projects": projects, "uncertainties": uncertainties, "activities": activities, "experiments": runs, "people": people, "evidence": {item: True for item in evidence}}
        for kind, refs in subjects.items():
            if kind not in subject_indexes or not isinstance(refs, list) or not refs or len(refs) != len(set(refs)):
                raise SourceValidationError(f"review {review['id']} has invalid {kind} subject_refs")
            for ref in refs:
                if ref not in subject_indexes[kind]: raise SourceValidationError(f"review {review['id']} references unknown {kind} subject {ref}")
        evidence_refs = review.get("evidence_refs", [])
        if not isinstance(evidence_refs, list) or len(evidence_refs) != len(set(evidence_refs)):
            raise SourceValidationError(f"review {review['id']} evidence_refs must be a list without duplicates")
        for ref in evidence_refs:
            if ref not in evidence: raise SourceValidationError(f"review {review['id']} references unknown evidence_ref {ref}")
        if review["status"] == "resolved" and (not review.get("resolved_at") or not review.get("resolution")): raise SourceValidationError(f"review {review['id']} resolved requires resolved_at and resolution")
        if review["status"] == "superseded" and review.get("superseded_by_ref") not in review_ids: raise SourceValidationError(f"review {review['id']} superseded requires valid superseded_by_ref")
        if review["status"] == "open" and (review.get("resolved_at") or review.get("resolution")): raise SourceValidationError(f"review {review['id']} open forbids resolution")

    experiment_rows = []
    for run in experiments:
        experiment_rows.append({
            "id": run["id"], "title": run["title"], "started_date": run["started_date"],
            "project_ref": run["project_ref"], "uncertainty_refs": run["uncertainty_refs"],
            "activity_refs": [item["id"] for item in overview["activities"] if run["id"] in item["experiment_refs"]],
            "person_refs": [item["person_ref"] for item in run["engineers"]],
            "observation_refs": [f"{run['id']}/RESULT-{item['sequence']:03d}" for item in run["results"]],
            "evidence_refs": [item["evidence_id"] for item in run["evidence"]], "status_label": run["status_label"],
        })
    return {
        "program": overview["program"],
        "projects": overview["projects"],
        "experimental_activities": [item for item in overview["activities"] if item["classification"] == "candidate_experimental"],
        "supporting_activities": [item for item in overview["activities"] if item["classification"] == "candidate_supporting"],
        "excluded_activities": [item for item in overview["activities"] if item["classification"] in {"ordinary_engineering", "outside_rnd_boundary"}],
        "review_activities": [item for item in overview["activities"] if item["classification"] == "human_review_required"],
        "experiments": experiment_rows, "people": overview["people"],
        "timesheets": sorted(timesheets, key=lambda row: (row.get("date", ""), row.get("person_ref", row.get("person", "")).casefold(), row.get("timesheet_id", ""))),
        "infrastructure_costs": sorted(infrastructure_costs, key=lambda row: (row["month"], row["service"].casefold(), row.get("cost_id", ""))),
        "reviews": reviews,
    }
