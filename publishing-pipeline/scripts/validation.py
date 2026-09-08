from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import yaml


class SourceValidationError(ValueError):
    """Raised when publishing input does not satisfy the source contract."""


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SourceValidationError(f"Missing required source file: {path.name}")
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise SourceValidationError(f"Cannot read {path.name}: {error}") from error
    if not isinstance(value, dict):
        raise SourceValidationError(f"{path.name} must contain a YAML mapping")
    return value


def load_strict_csv(path: Path, required_headers: tuple[str, ...]) -> list[dict[str, str]]:
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
