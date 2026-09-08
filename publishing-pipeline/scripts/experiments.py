from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
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

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for experiment in experiments:
        if not isinstance(experiment, dict):
            raise SourceValidationError("Each experiment must be a mapping")
        run_id = experiment.get("id")
        if not isinstance(run_id, str) or not run_id.strip():
            raise SourceValidationError("Each experiment requires a non-empty id")
        if run_id in seen_ids:
            raise SourceValidationError(f"Duplicate experiment ID: {run_id}")
        seen_ids.add(run_id)

    for experiment in experiments:
        run_id = experiment["id"]
        started_at = _parse_timestamp(
            experiment.get("started_at"),
            source=f"experiments.yaml run {run_id}",
            field="started_at",
        )
        run = deepcopy(experiment)
        run["_started_at"] = started_at
        run["results"] = []
        run["execution_log"] = []
        run["evidence"] = []
        normalized.append(run)

    by_id = {run["id"]: run for run in normalized}
    for filename, rows, target in (
        ("experiment-results.csv", results, "results"),
        ("experiment-execution-log.csv", execution_log, "execution_log"),
    ):
        for row_number, row in enumerate(rows, start=2):
            run_id = row["run_id"]
            if run_id not in by_id:
                raise SourceValidationError(
                    f"{filename} row {row_number} references unknown run_id {run_id}"
                )
            item = dict(row)
            item["sequence"] = _sequence(row, filename=filename, row_number=row_number)
            by_id[run_id][target].append(item)

    for row_number, row in enumerate(evidence, start=2):
        run_id = row["run_id"]
        if run_id not in by_id:
            raise SourceValidationError(
                f"experiment-evidence.csv row {row_number} references unknown run_id {run_id}"
            )
        by_id[run_id]["evidence"].append(dict(row))

    for run in normalized:
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
