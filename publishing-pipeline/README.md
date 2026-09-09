# Publishing pipeline

This folder contains the local YAML/CSV-to-LaTeX-to-PDF publisher. The original manual framework remains independently buildable in `../static-pack/`.

## Run on macOS

```zsh
./publish.zsh
```

## Run on Linux

```bash
./publish.sh
```

Each command prepares a local Python virtual environment, installs the two required libraries, runs the automated tests, validates the input files, generates seven LaTeX documents, and compiles seven PDFs. Any validation failure, test failure, Tectonic error, or Tectonic warning stops publication.

## Files people edit

- `input/claim.yaml`: document and claim metadata.
- `input/experiments.yaml`: combined-file mode for experiment narratives, designs, evaluations, and conclusions.
- `input/experiments/experiment.RUN-YYYY-NNN.yaml`: split-file mode with one experiment per YAML file.
- `input/experiment-results.csv`: dynamic quantitative or qualitative observations linked to runs.
- `input/experiment-execution-log.csv`: chronological actions and observations linked to runs.
- `input/experiment-evidence.csv`: evidence catalogue linked to runs.
- `input/timesheets.csv`: high-volume labour allocation rows.
- `input/infrastructure-costs.csv`: high-volume infrastructure and tooling rows.
- `templates/`: data-aware LaTeX templates. Edit these only when changing document structure or presentation.

## Files the pipeline owns

- `generated/`: generated `.tex` files and the generated style package.
- `output/`: compiled PDFs.
- `.venv/`: local Python dependencies.

Do not edit generated files. Change the source YAML, CSV, or templates and publish again.

## Experiment notebook authoring

The Experiment Notebook is generated as one annual PDF containing all supplied runs in chronological order. Its result metrics are dynamic and can differ for every experiment.

See the [02 Experiment Notebook authoring guide](docs/02-experiment-notebook/README.md) for:

- A field-by-field explanation of `experiments.template.yaml`.
- Completed and ongoing experiment rules.
- Examples of what each section should demonstrate.
- YAML-to-CSV relationships and evidence references.
- Missing-data, applicability, validation, and publication rules.

## Overview of all work authoring

Document 01 is generated from `program.yaml`, the project, uncertainty, people,
activity, and program-evidence sources, plus derived summaries from the existing
experiment, timesheet, and infrastructure sources. See the
[01 Overview of All Work authoring guide](docs/01-overview-of-all-work/README.md)
for the exact mappings, combined/split YAML rules, lifecycle, validation boundary,
and AI-agent protocol.

## Remaining baseline

The overview, claim-mapping register, git appendix, weekly timesheets, infrastructure worksheets, and annual claim pack still contain instructional placeholders. Their proposed data contracts and conversion sequence are documented in `docs/superpowers/specs/2026-09-08-published-pdf-data-contract-design.md`.
