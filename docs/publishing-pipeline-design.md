# Data-driven publishing pipeline design

## Purpose

This repository provides two deliberately separate ways to produce the Australian R&D audit pack:

1. `static-pack/` is the preserved manual baseline. Its LaTeX documents can be edited and compiled directly without the publishing pipeline.
2. `publishing-pipeline/` is a small local publisher. Users maintain YAML and CSV source data, then run one platform-specific command to validate the data, generate LaTeX, and compile PDFs.

The pipeline is not a web product. It has no server, database, authentication, external API, background worker, or deployment runtime.

## Repository boundaries

```text
static-pack/                 Original standalone LaTeX framework
publishing-pipeline/input/   Human-maintained YAML and CSV records
publishing-pipeline/templates/ Data-aware LaTeX templates
publishing-pipeline/scripts/ Validation and rendering code
publishing-pipeline/tests/   Automated pipeline tests and fixtures
publishing-pipeline/generated/ Disposable generated LaTeX
publishing-pipeline/output/  Disposable generated PDFs
docs/                        Design and implementation records
```

The static pack and publishing pipeline must remain independently runnable. Pipeline templates begin as copies of the static templates so future pipeline work cannot silently alter the baseline.

## Source contract

`input/claim.yaml` is the primary source. The baseline schema covers document metadata and program identity: company name, ABN, financial year, program name, preparer, version, confidentiality, owner, review date, and evidence repository path.

`input/experiments.yaml` establishes the high-volume narrative extension point. It contains an `experiments` list, initially empty.

`input/timesheets.csv` and `input/infrastructure-costs.csv` establish tabular extension points with explicit headers and no invented claim values.

Later iterations can add projects, uncertainties, activities, experiments, evidence, personnel, and financial schedules without changing the publishing entrypoints.

## Processing flow

1. The platform entrypoint verifies that it is running on its intended operating system.
2. It verifies Python and Tectonic are available.
3. It creates or reuses `.venv` and installs the pinned-range Python dependencies.
4. `scripts/publish.py` loads YAML and CSV source files.
5. The publisher validates required keys, scalar types, non-empty values, CSV headers, and duplicate experiment IDs.
6. Every inserted value is escaped for LaTeX before rendering.
7. Seven Jinja templates are rendered into `generated/`.
8. The shared style file is copied into `generated/`.
9. Tectonic compiles each generated document into `output/`.
10. Any validation failure, template failure, compilation error, or Tectonic warning fails the command.

Generation uses custom Jinja delimiters (`<< >>` for values and `<% %>` for blocks) so ordinary LaTeX braces are not interpreted as template syntax.

## Safety and audit properties

- Input files are never modified by a publish run.
- Generated files carry a warning that they must not be edited manually.
- Output directories contain reproducible artefacts and are ignored by Git.
- Unknown source fields are tolerated so the schema can grow, but required baseline fields are enforced.
- Missing or malformed source files fail closed with a concise error.
- LaTeX control characters are escaped before insertion.
- Empty high-volume files are valid when their required header row is present.
- The build fails on warnings instead of hiding them.

## Testing baseline

The Python test suite covers valid input, missing required metadata, invalid CSV headers, duplicate experiment IDs, LaTeX escaping, and seven-document rendering. Platform scripts have syntax checks and explicit operating-system guards. A full macOS publish run verifies the local end-to-end path; Linux uses the same Python publisher and is exercised by GitHub Actions through `publish.sh`.

## Explicit non-goals

- No browser interface or localhost server in the baseline.
- No spreadsheet import beyond CSV.
- No automatic extraction from source-code repositories.
- No claim-eligibility decisions or legal conclusions.
- No silent calculation or invention of missing evidence.
- No attempt to make generated LaTeX the source of truth.
