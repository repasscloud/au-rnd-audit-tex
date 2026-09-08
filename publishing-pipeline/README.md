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
- `input/experiments.yaml`: required experiment narratives, designs, evaluations, and conclusions.
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

The experiment notebook is generated as one annual PDF. Its index and complete run sections are sorted by `started_at`, then run ID. Result metrics are supplied by data and can differ for every experiment; the template does not assume latency, throughput, error-rate, or resource metrics.

Use the four `*.template.yaml` and `*.template.csv` files as structural examples. The publisher reads only the exact active filenames, so template examples cannot appear in a PDF accidentally.

Authoring workflow:

1. Copy the relevant structure from `experiments.template.yaml` into `experiments.yaml` and replace all examples with actual records.
2. Give each run a stable `RUN-YYYY-NNN` ID and use it in all three CSV files.
3. Record the hypothesis and its evidence before the experiment begins.
4. Append execution, observation/result, and evidence rows while the activity occurs.
5. Complete the evaluation honestly. For a finished run, set a completed status, `ended_at`, and `conclusion`. For an unfinished run, use `ongoing`, an `interim_conclusion`, and at least one `next_actions` item.
6. Run the publisher and correct every reported source error.
7. Never edit files in `generated/` or `output/`; they are replaced during publication.

### Experiment status

Allowed values are `confirmed`, `rejected`, `mixed`, `inconclusive`, and `ongoing`. These describe how the supplied observations relate to the hypothesis. They do not determine R&D eligibility.

### Missing and inapplicable data

| Content type | Supplier behavior | Publisher behavior |
|---|---|---|
| Required | Supply complete content | Missing content stops publication |
| Conditional and applicable | Supply complete content | Missing content stops publication |
| Conditional and not applicable | Supply `state: not_applicable` and a non-empty reason where the schema permits it | The PDF prints `Not applicable` and the reason |
| Optional | Supply content or use/omit the documented `no_data` state | The PDF prints `No data provided.` when empty |
| Repeating | Add one row/item per record | The publisher sorts and renders every item |
| Derived | Supply valid source records and references | The publisher builds the index and grouped sections |

`No data provided.` cannot be selected for a hypothesis, method, execution log, results/observations, evaluation, conclusion or interim conclusion, or evidence collection. Those records are hard requirements for every published run.

### CSV rules

- `sequence` is a positive integer and must be unique within a run and CSV type.
- Timestamps use ISO 8601 and include a UTC offset, for example `2026-07-14T09:30:00+09:30`.
- A result `kind` is `quantitative` or `qualitative`.
- Quantitative results require a unit.
- `baseline_value` can be `not_applicable` only when the notes explain why comparison is not relevant.
- Every result and execution row references evidence owned by the same run.
- Evidence IDs are unique across the notebook.

### Validation boundary

The publisher verifies required structure, timestamps, ordering, identifier formats, internal experiment/evidence references, absence states, and placeholder-looking values. Until the program and people source contracts are implemented, project, uncertainty, and person IDs are checked for the documented format but cannot yet be resolved to an authoritative record.

The publisher does not determine legal eligibility, factual truth, scientific adequacy, or whether a record is sufficient for a particular review. Those remain supplier and professional-review responsibilities.

## Remaining baseline

The overview, claim-mapping register, git appendix, weekly timesheets, infrastructure worksheets, and annual claim pack still contain instructional placeholders. Their proposed data contracts and conversion sequence are documented in `docs/superpowers/specs/2026-09-08-published-pdf-data-contract-design.md`.
