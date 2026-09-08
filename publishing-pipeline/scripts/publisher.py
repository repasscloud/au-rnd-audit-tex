from __future__ import annotations

import argparse
import csv
import re
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined


class SourceValidationError(ValueError):
    """Raised when publishing input does not satisfy the baseline contract."""


REQUIRED_DOCUMENT_FIELDS = (
    "company",
    "abn",
    "financial_year",
    "program",
    "prepared_by",
    "version",
    "confidentiality",
    "owner",
    "review_date",
    "evidence_repository",
)

CSV_SCHEMAS = {
    "timesheets.csv": (
        "person",
        "date",
        "project_ref",
        "run_ref",
        "category",
        "hours",
        "description",
    ),
    "infrastructure-costs.csv": (
        "month",
        "service",
        "provider",
        "total_cost",
        "rnd_percent",
        "eligible_amount",
        "allocation_basis",
        "evidence_ref",
    ),
}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SourceValidationError(f"Missing required source file: {path.name}")
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise SourceValidationError(f"Cannot read {path.name}: {error}") from error
    if not isinstance(value, dict):
        raise SourceValidationError(f"{path.name} must contain a YAML mapping")
    return value


def _load_csv(path: Path, required_headers: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.is_file():
        raise SourceValidationError(f"Missing required source file: {path.name}")
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            actual_headers = tuple(reader.fieldnames or ())
            if actual_headers != required_headers:
                raise SourceValidationError(
                    f"Invalid {path.name} headers. Expected: {','.join(required_headers)}"
                )
            return list(reader)
    except (OSError, UnicodeError, csv.Error) as error:
        raise SourceValidationError(f"Cannot read {path.name}: {error}") from error


def _required_row_values(filename: str, row_number: int, row: dict[str, str]) -> None:
    for field, value in row.items():
        if not value.strip():
            raise SourceValidationError(f"{filename} row {row_number} requires {field}")


def _validate_timesheets(rows: list[dict[str, str]]) -> None:
    allowed_categories = {"core", "supporting", "non-rnd"}
    for row_number, row in enumerate(rows, start=2):
        _required_row_values("timesheets.csv", row_number, row)
        try:
            date.fromisoformat(row["date"])
        except ValueError as error:
            raise SourceValidationError(
                f"timesheets.csv row {row_number} date must use YYYY-MM-DD"
            ) from error
        if row["category"] not in allowed_categories:
            raise SourceValidationError(
                f"timesheets.csv row {row_number} category must be core, supporting, or non-rnd"
            )
        try:
            hours = Decimal(row["hours"])
        except InvalidOperation as error:
            raise SourceValidationError(f"timesheets.csv row {row_number} hours must be numeric") from error
        if hours <= 0 or hours > 24:
            raise SourceValidationError(f"timesheets.csv row {row_number} hours must be greater than 0 and at most 24")


def _validate_infrastructure_costs(rows: list[dict[str, str]]) -> None:
    cents = Decimal("0.01")
    for row_number, row in enumerate(rows, start=2):
        _required_row_values("infrastructure-costs.csv", row_number, row)
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", row["month"]):
            raise SourceValidationError(
                f"infrastructure-costs.csv row {row_number} month must use YYYY-MM"
            )
        try:
            total = Decimal(row["total_cost"])
            percentage = Decimal(row["rnd_percent"])
            eligible = Decimal(row["eligible_amount"])
        except InvalidOperation as error:
            raise SourceValidationError(
                f"infrastructure-costs.csv row {row_number} costs and percentage must be numeric"
            ) from error
        if total < 0 or eligible < 0:
            raise SourceValidationError(f"infrastructure-costs.csv row {row_number} costs cannot be negative")
        if percentage < 0 or percentage > 100:
            raise SourceValidationError(f"infrastructure-costs.csv row {row_number} rnd_percent must be 0 to 100")
        expected = (total * percentage / Decimal("100")).quantize(cents, rounding=ROUND_HALF_UP)
        if eligible.quantize(cents, rounding=ROUND_HALF_UP) != expected:
            raise SourceValidationError(
                f"infrastructure-costs.csv row {row_number} eligible_amount must equal {expected}"
            )


def load_sources(input_dir: Path) -> dict[str, Any]:
    claim = _load_yaml(input_dir / "claim.yaml")
    document = claim.get("document")
    if not isinstance(document, dict):
        raise SourceValidationError("claim.yaml requires a document mapping")
    for field in REQUIRED_DOCUMENT_FIELDS:
        value = document.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SourceValidationError(f"Missing required document field: {field}")

    experiment_source = _load_yaml(input_dir / "experiments.yaml")
    experiments = experiment_source.get("experiments")
    if not isinstance(experiments, list):
        raise SourceValidationError("experiments.yaml requires an experiments list")
    seen_ids: set[str] = set()
    for experiment in experiments:
        if not isinstance(experiment, dict):
            raise SourceValidationError("Each experiment must be a mapping")
        experiment_id = experiment.get("id")
        if not isinstance(experiment_id, str) or not experiment_id.strip():
            raise SourceValidationError("Each experiment requires a non-empty id")
        if experiment_id in seen_ids:
            raise SourceValidationError(f"Duplicate experiment ID: {experiment_id}")
        seen_ids.add(experiment_id)

    sources: dict[str, Any] = dict(claim)
    sources["experiments"] = experiments
    timesheets = _load_csv(input_dir / "timesheets.csv", CSV_SCHEMAS["timesheets.csv"])
    infrastructure_costs = _load_csv(
        input_dir / "infrastructure-costs.csv",
        CSV_SCHEMAS["infrastructure-costs.csv"],
    )
    _validate_timesheets(timesheets)
    _validate_infrastructure_costs(infrastructure_costs)
    sources["timesheets"] = timesheets
    sources["infrastructure_costs"] = infrastructure_costs
    return sources


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in value)


def _escape_tree(value: Any) -> Any:
    if isinstance(value, str):
        return latex_escape(value)
    if isinstance(value, list):
        return [_escape_tree(item) for item in value]
    if isinstance(value, dict):
        return {key: _escape_tree(item) for key, item in value.items()}
    return value


def render_documents(template_dir: Path, generated_dir: Path, sources: dict[str, Any]) -> list[Path]:
    generated_dir.mkdir(parents=True, exist_ok=True)
    environment = Environment(
        loader=FileSystemLoader(template_dir),
        undefined=StrictUndefined,
        autoescape=False,
        variable_start_string="<<",
        variable_end_string=">>",
        block_start_string="<%",
        block_end_string="%>",
        comment_start_string="<#",
        comment_end_string="#>",
        keep_trailing_newline=True,
    )
    context = _escape_tree(sources)
    rendered: list[Path] = []
    marker = "% GENERATED FILE - edit input YAML/CSV files, then publish again.\n"
    for template_path in sorted(template_dir.glob("*.tex")):
        output_path = generated_dir / template_path.name
        output_path.write_text(marker + environment.get_template(template_path.name).render(**context), encoding="utf-8")
        rendered.append(output_path)

    style_name = "rd_audit_style.sty"
    if not (template_dir / style_name).is_file():
        raise SourceValidationError("Missing pipeline template: rd_audit_style.sty")
    (generated_dir / style_name).write_text(
        marker + environment.get_template(style_name).render(**context),
        encoding="utf-8",
    )
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source data and generate the R&D audit LaTeX pack.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--templates", type=Path, required=True)
    parser.add_argument("--generated", type=Path, required=True)
    args = parser.parse_args()
    try:
        sources = load_sources(args.input)
        rendered = render_documents(args.templates, args.generated, sources)
    except SourceValidationError as error:
        parser.exit(1, f"Source validation failed: {error}\n")
    print(f"Generated {len(rendered)} LaTeX documents in {args.generated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
