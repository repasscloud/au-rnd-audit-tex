from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
import re
from typing import Any

from validation import SourceValidationError, load_strict_csv, load_yaml_mapping


EXPERIMENT_CSV_SCHEMAS = {
    "experiment-results.csv": (
        "run_id",
        "sequence",
        "kind",
        "metric",
        "baseline_value",
        "observed_value",
        "unit",
        "notes",
        "evidence_ref",
    ),
    "experiment-execution-log.csv": (
        "run_id",
        "sequence",
        "occurred_at",
        "actor",
        "tool",
        "action",
        "observation",
        "evidence_ref",
    ),
    "experiment-evidence.csv": (
        "evidence_id",
        "run_id",
        "type",
        "title",
        "location",
        "captured_at",
        "notes",
    ),
}

COMPLETED_STATUSES = {"confirmed", "rejected", "mixed", "inconclusive"}
ALLOWED_STATUSES = COMPLETED_STATUSES | {"ongoing"}
DESIGN_FIELDS = (
    "independent_variables",
    "controlled_variables",
    "observed_variables",
    "acceptance_criteria",
    "failure_triggers",
)
DESIGN_LABELS = {
    "independent_variables": "Independent variables",
    "controlled_variables": "Controlled variables",
    "observed_variables": "Observed variables",
    "acceptance_criteria": "Acceptance criteria",
    "failure_triggers": "Failure triggers",
}
PLACEHOLDER_PATTERN = re.compile(r"(?:\[[^\]]+\]|xxx|tbd)", re.IGNORECASE)
RUN_ID_PATTERN = re.compile(r"RUN-\d{4}-\d{3}")
PROJECT_ID_PATTERN = re.compile(r"RND-\d{4}-\d{2}")
UNCERTAINTY_ID_PATTERN = re.compile(r"UT-\d{2}")
PERSON_ID_PATTERN = re.compile(r"P-\d{3}")


def _is_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_PATTERN.fullmatch(value.strip()))


def _parse_timestamp(value: Any, *, source: str, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise SourceValidationError(f"{source} requires {field}")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise SourceValidationError(f"{source} {field} must be an ISO 8601 timestamp") from error
    if parsed.tzinfo is None:
        raise SourceValidationError(f"{source} {field} must include a UTC offset")
    return parsed


def _display_timestamp(value: datetime) -> str:
    offset = value.strftime("%z")
    if offset:
        offset = f"{offset[:3]}:{offset[3:]}"
    return f"{value.strftime('%d %b %Y, %H:%M')} {offset}".strip()


def _nested_value(mapping: dict[str, Any], path: str) -> Any:
    value: Any = mapping
    for segment in path.split("."):
        if not isinstance(value, dict) or segment not in value:
            return None
        value = value[segment]
    return value


def _require_text(run: dict[str, Any], path: str) -> str:
    run_id = run.get("id", "<unknown>")
    value = _nested_value(run, path)
    if not isinstance(value, str) or not value.strip():
        raise SourceValidationError(f"experiments.yaml run {run_id} requires {path}")
    if _is_placeholder(value):
        raise SourceValidationError(
            f"experiments.yaml run {run_id} contains placeholder text at {path}"
        )
    return value.strip()


def _require_text_list(run: dict[str, Any], path: str) -> list[str]:
    run_id = run.get("id", "<unknown>")
    value = _nested_value(run, path)
    if not isinstance(value, list) or not value:
        raise SourceValidationError(f"experiments.yaml run {run_id} requires {path}")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise SourceValidationError(f"experiments.yaml run {run_id} requires {path}")
        if _is_placeholder(item):
            raise SourceValidationError(
                f"experiments.yaml run {run_id} contains placeholder text at {path}"
            )
    return [item.strip() for item in value]


def _validate_id(value: str, pattern: re.Pattern[str], *, source: str, field: str) -> None:
    if not pattern.fullmatch(value):
        raise SourceValidationError(f"{source} {field} has invalid ID format: {value}")


def _validate_optional_block(run_id: str, name: str, value: Any) -> dict[str, str]:
    if value is None:
        return {"state": "no_data"}
    if not isinstance(value, dict):
        raise SourceValidationError(f"experiments.yaml run {run_id} {name} must be a mapping")
    state = value.get("state")
    content = value.get("content")
    if state not in {"provided", "no_data"}:
        raise SourceValidationError(
            f"experiments.yaml run {run_id} {name} state must be provided or no_data"
        )
    if state == "provided":
        if not isinstance(content, str) or not content.strip():
            raise SourceValidationError(
                f"experiments.yaml run {run_id} {name} state provided requires content"
            )
        if _is_placeholder(content):
            raise SourceValidationError(
                f"experiments.yaml run {run_id} contains placeholder text at {name}.content"
            )
        return {"state": "provided", "content": content.strip()}
    if content is not None:
        raise SourceValidationError(
            f"experiments.yaml run {run_id} {name} state no_data forbids content"
        )
    return {"state": "no_data"}


def _validate_design(run: dict[str, Any]) -> None:
    run_id = run["id"]
    design = run.get("design")
    if not isinstance(design, dict):
        raise SourceValidationError(f"experiments.yaml run {run_id} requires design")
    for field in DESIGN_FIELDS:
        value = design.get(field)
        if isinstance(value, list) and value:
            for item in value:
                if not isinstance(item, str) or not item.strip():
                    raise SourceValidationError(
                        f"experiments.yaml run {run_id} requires design.{field}"
                    )
                if _is_placeholder(item):
                    raise SourceValidationError(
                        f"experiments.yaml run {run_id} contains placeholder text at design.{field}"
                    )
            continue
        if isinstance(value, dict) and value.get("state") == "not_applicable":
            reason = value.get("reason")
            if isinstance(reason, str) and reason.strip() and not _is_placeholder(reason):
                continue
        raise SourceValidationError(
            f"experiments.yaml run {run_id} requires design.{field} content or a not_applicable reason"
        )


def _required_row_text(
    filename: str,
    row_number: int,
    row: dict[str, str],
    field: str,
) -> str:
    value = row[field]
    if not value.strip():
        raise SourceValidationError(f"{filename} row {row_number} requires {field}")
    if _is_placeholder(value):
        raise SourceValidationError(
            f"{filename} row {row_number} contains placeholder text at {field}"
        )
    return value.strip()


def _sequence(row: dict[str, str], *, filename: str, row_number: int) -> int:
    try:
        sequence = int(row["sequence"])
    except ValueError as error:
        raise SourceValidationError(
            f"{filename} row {row_number} sequence must be a positive integer"
        ) from error
    if sequence <= 0:
        raise SourceValidationError(
            f"{filename} row {row_number} sequence must be a positive integer"
        )
    return sequence


def validate_and_normalize_experiments(
    experiment_source: dict[str, Any],
    results: list[dict[str, str]],
    execution_log: list[dict[str, str]],
    evidence: list[dict[str, str]],
) -> list[dict[str, Any]]:
    experiments = experiment_source.get("experiments")
    if not isinstance(experiments, list):
        raise SourceValidationError("experiments.yaml requires an experiments list")

    if not experiments:
        raise SourceValidationError("experiments.yaml requires at least one experiment")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for experiment in experiments:
        if not isinstance(experiment, dict):
            raise SourceValidationError("Each experiment must be a mapping")
        run_id = experiment.get("id")
        if not isinstance(run_id, str) or not run_id.strip():
            raise SourceValidationError("Each experiment requires a non-empty id")
        _validate_id(
            run_id,
            RUN_ID_PATTERN,
            source=f"experiments.yaml run {run_id}",
            field="id",
        )
        if run_id in seen_ids:
            raise SourceValidationError(f"Duplicate experiment ID: {run_id}")
        seen_ids.add(run_id)

    for experiment in experiments:
        run_id = experiment["id"]
        for field in ("title", "project_ref", "objective", "method", "evaluation", "status"):
            _require_text(experiment, field)
        _validate_id(
            experiment["project_ref"],
            PROJECT_ID_PATTERN,
            source=f"experiments.yaml run {run_id}",
            field="project_ref",
        )
        uncertainty_refs = _require_text_list(experiment, "uncertainty_refs")
        for reference in uncertainty_refs:
            _validate_id(
                reference,
                UNCERTAINTY_ID_PATTERN,
                source=f"experiments.yaml run {run_id}",
                field="uncertainty_refs",
            )
        engineers = experiment.get("engineers")
        if not isinstance(engineers, list) or not engineers:
            raise SourceValidationError(f"experiments.yaml run {run_id} requires engineers")
        for engineer in engineers:
            if not isinstance(engineer, dict):
                raise SourceValidationError(f"experiments.yaml run {run_id} requires engineers")
            person_ref = engineer.get("person_ref")
            role = engineer.get("role")
            if not isinstance(person_ref, str) or not person_ref.strip() or not isinstance(role, str) or not role.strip():
                raise SourceValidationError(
                    f"experiments.yaml run {run_id} engineers require person_ref and role"
                )
            _validate_id(
                person_ref,
                PERSON_ID_PATTERN,
                source=f"experiments.yaml run {run_id}",
                field="engineers.person_ref",
            )
            if _is_placeholder(role):
                raise SourceValidationError(
                    f"experiments.yaml run {run_id} contains placeholder text at engineers.role"
                )
        if not isinstance(experiment.get("background"), dict):
            raise SourceValidationError(f"experiments.yaml run {run_id} requires background.summary")
        _require_text(experiment, "background.summary")
        _require_text_list(experiment, "background.research_refs")
        if not isinstance(experiment.get("hypothesis"), dict):
            raise SourceValidationError(f"experiments.yaml run {run_id} requires hypothesis.statement")
        _require_text(experiment, "hypothesis.statement")
        _require_text(experiment, "hypothesis.formed_at")
        _require_text_list(experiment, "hypothesis.basis_refs")
        _validate_design(experiment)

        started_at = _parse_timestamp(
            experiment.get("started_at"),
            source=f"experiments.yaml run {run_id}",
            field="started_at",
        )
        formed_at = _parse_timestamp(
            experiment["hypothesis"]["formed_at"],
            source=f"experiments.yaml run {run_id}",
            field="hypothesis.formed_at",
        )
        if formed_at > started_at:
            raise SourceValidationError(
                f"experiments.yaml run {run_id} hypothesis.formed_at must not follow started_at"
            )
        status = experiment["status"]
        if status not in ALLOWED_STATUSES:
            choices = ", ".join(sorted(ALLOWED_STATUSES))
            raise SourceValidationError(
                f"experiments.yaml run {run_id} status must be {choices}"
            )
        ended_at: datetime | None = None
        if status in COMPLETED_STATUSES:
            _require_text(experiment, "ended_at")
            _require_text(experiment, "conclusion")
            ended_at = _parse_timestamp(
                experiment["ended_at"],
                source=f"experiments.yaml run {run_id}",
                field="ended_at",
            )
            if ended_at < started_at:
                raise SourceValidationError(
                    f"experiments.yaml run {run_id} ended_at must not precede started_at"
                )
        else:
            if experiment.get("ended_at") is not None:
                raise SourceValidationError(
                    f"experiments.yaml run {run_id} status ongoing forbids ended_at"
                )
            _require_text(experiment, "interim_conclusion")
            _require_text_list(experiment, "next_actions")

        run = deepcopy(experiment)
        run["_started_at"] = started_at
        run["_ended_at"] = ended_at
        run["started_date"] = experiment["started_at"].split("T", 1)[0]
        run["started_display"] = _display_timestamp(started_at)
        run["ended_display"] = _display_timestamp(ended_at) if ended_at else "Ongoing"
        run["hypothesis"]["formed_at_display"] = _display_timestamp(formed_at)
        run["is_ongoing"] = status == "ongoing"
        run["status_label"] = status.replace("_", " ").title()
        run["conclusion_label"] = "Interim conclusion" if status == "ongoing" else "Conclusion"
        run["conclusion_text"] = (
            experiment["interim_conclusion"] if status == "ongoing" else experiment["conclusion"]
        )
        run["design_sections"] = []
        for field in DESIGN_FIELDS:
            design_value = experiment["design"][field]
            if isinstance(design_value, list):
                run["design_sections"].append(
                    {
                        "label": DESIGN_LABELS[field],
                        "is_not_applicable": False,
                        "items": design_value,
                    }
                )
            else:
                run["design_sections"].append(
                    {
                        "label": DESIGN_LABELS[field],
                        "is_not_applicable": True,
                        "reason": design_value["reason"],
                    }
                )
        optional_block = _validate_optional_block(
            run_id,
            "unexpected_behaviour",
            experiment.get("unexpected_behaviour"),
        )
        optional_block["has_data"] = optional_block["state"] == "provided"
        run["unexpected_behaviour"] = optional_block
        run["results"] = []
        run["execution_log"] = []
        run["evidence"] = []
        normalized.append(run)

    by_id = {run["id"]: run for run in normalized}
    evidence_index: dict[str, tuple[str, int]] = {}
    for row_number, row in enumerate(evidence, start=2):
        filename = "experiment-evidence.csv"
        evidence_id = _required_row_text(filename, row_number, row, "evidence_id")
        run_id = _required_row_text(filename, row_number, row, "run_id")
        if run_id not in by_id:
            raise SourceValidationError(
                f"experiment-evidence.csv row {row_number} references unknown run_id {run_id}"
            )
        if evidence_id in evidence_index:
            raise SourceValidationError(f"Duplicate evidence ID: {evidence_id}")
        for field in ("type", "title", "location", "captured_at"):
            _required_row_text(filename, row_number, row, field)
        captured_at = _parse_timestamp(
            row["captured_at"],
            source=f"{filename} row {row_number}",
            field="captured_at",
        )
        item = dict(row)
        item["captured_at_display"] = _display_timestamp(captured_at)
        item["notes"] = row["notes"].strip()
        by_id[run_id]["evidence"].append(item)
        evidence_index[evidence_id] = (run_id, row_number)

    seen_sequences: dict[tuple[str, str], set[int]] = {}
    for filename, rows, target in (
        ("experiment-results.csv", results, "results"),
        ("experiment-execution-log.csv", execution_log, "execution_log"),
    ):
        for row_number, row in enumerate(rows, start=2):
            run_id = _required_row_text(filename, row_number, row, "run_id")
            if run_id not in by_id:
                raise SourceValidationError(
                    f"{filename} row {row_number} references unknown run_id {run_id}"
                )
            sequence = _sequence(row, filename=filename, row_number=row_number)
            sequence_key = (run_id, target)
            if sequence in seen_sequences.setdefault(sequence_key, set()):
                raise SourceValidationError(
                    f"{filename} run {run_id} has duplicate sequence {sequence}"
                )
            seen_sequences[sequence_key].add(sequence)
            evidence_ref = _required_row_text(filename, row_number, row, "evidence_ref")
            if evidence_ref not in evidence_index:
                raise SourceValidationError(
                    f"{filename} row {row_number} references unknown evidence_ref {evidence_ref}"
                )
            evidence_owner = evidence_index[evidence_ref][0]
            if evidence_owner != run_id:
                raise SourceValidationError(
                    f"{filename} row {row_number} evidence_ref {evidence_ref} belongs to {evidence_owner}"
                )
            item: dict[str, Any] = dict(row)
            item["sequence"] = sequence
            if target == "results":
                kind = _required_row_text(filename, row_number, row, "kind")
                if kind not in {"quantitative", "qualitative"}:
                    raise SourceValidationError(
                        f"{filename} row {row_number} kind must be quantitative or qualitative"
                    )
                for field in ("metric", "baseline_value", "observed_value"):
                    _required_row_text(filename, row_number, row, field)
                unit = row["unit"].strip()
                if kind == "quantitative" and not unit:
                    raise SourceValidationError(
                        f"{filename} row {row_number} unit is required for quantitative results"
                    )
                if kind == "qualitative" and not unit:
                    item["unit"] = "not_applicable"
                if row["baseline_value"].strip() == "not_applicable" and not row["notes"].strip():
                    raise SourceValidationError(
                        f"{filename} row {row_number} baseline_value not_applicable requires explanatory notes"
                    )
                _required_row_text(filename, row_number, row, "notes")
                item["kind_label"] = kind.title()
                item["baseline_label"] = (
                    "Not applicable"
                    if row["baseline_value"].strip() == "not_applicable"
                    else row["baseline_value"].strip()
                )
                item["unit_label"] = (
                    "Not applicable"
                    if item["unit"].strip() == "not_applicable"
                    else item["unit"].strip()
                )
            else:
                for field in ("occurred_at", "actor", "action", "observation"):
                    _required_row_text(filename, row_number, row, field)
                tool = row["tool"].strip()
                if not tool:
                    raise SourceValidationError(
                        f"{filename} row {row_number} tool must be a value or not_applicable"
                    )
                item["tool_label"] = "Not applicable" if tool == "not_applicable" else tool
                occurred_at = _parse_timestamp(
                    row["occurred_at"],
                    source=f"{filename} row {row_number}",
                    field="occurred_at",
                )
                run = by_id[run_id]
                item["occurred_at_display"] = _display_timestamp(occurred_at)
                if occurred_at < run["_started_at"] or (
                    run["_ended_at"] is not None and occurred_at > run["_ended_at"]
                ):
                    raise SourceValidationError(
                        f"{filename} row {row_number} occurred_at is outside the run period"
                    )
            by_id[run_id][target].append(item)

    for run in normalized:
        for collection in ("results", "execution_log", "evidence"):
            if not run[collection]:
                raise SourceValidationError(
                    f"experiments.yaml run {run['id']} requires at least one {collection} record"
                )
        referenced_evidence = (
            run["background"]["research_refs"] + run["hypothesis"]["basis_refs"]
        )
        for evidence_ref in referenced_evidence:
            if evidence_ref not in evidence_index:
                raise SourceValidationError(
                    f"experiments.yaml run {run['id']} references unknown evidence_ref {evidence_ref}"
                )
            evidence_owner = evidence_index[evidence_ref][0]
            if evidence_owner != run["id"]:
                raise SourceValidationError(
                    f"experiments.yaml run {run['id']} evidence_ref {evidence_ref} belongs to {evidence_owner}"
                )
        run["results"].sort(key=lambda row: row["sequence"])
        run["execution_log"].sort(key=lambda row: row["sequence"])

    normalized.sort(key=lambda run: (run["_started_at"], run["id"]))
    return normalized


def load_experiment_sources(input_dir: Path) -> list[dict[str, Any]]:
    experiment_source = load_yaml_mapping(input_dir / "experiments.yaml")
    results = load_strict_csv(
        input_dir / "experiment-results.csv",
        EXPERIMENT_CSV_SCHEMAS["experiment-results.csv"],
    )
    execution_log = load_strict_csv(
        input_dir / "experiment-execution-log.csv",
        EXPERIMENT_CSV_SCHEMAS["experiment-execution-log.csv"],
    )
    evidence = load_strict_csv(
        input_dir / "experiment-evidence.csv",
        EXPERIMENT_CSV_SCHEMAS["experiment-evidence.csv"],
    )
    return validate_and_normalize_experiments(
        experiment_source,
        results,
        execution_log,
        evidence,
    )
