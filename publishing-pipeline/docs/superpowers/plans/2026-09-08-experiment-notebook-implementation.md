# Experiment Notebook Data Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a single chronological, data-driven experiment notebook whose dynamic run sections use YAML/CSV input and fail closed when audit-critical records are missing.

**Architecture:** Extend the existing source loader with a focused experiment normalization and validation boundary, then pass normalized run records to the existing strict Jinja renderer. Keep narrative records in `experiments.yaml`, place high-volume observations, execution entries, and evidence references in normalized CSV sources, and make the TeX template presentation-only.

**Tech Stack:** Python 3 standard library, PyYAML 6, Jinja2 3, `unittest`, LaTeX/Tectonic, YAML, CSV.

**Spec:** `publishing-pipeline/docs/superpowers/specs/2026-09-08-published-pdf-data-contract-design.md`

## Global Constraints

- Change only files under `publishing-pipeline/`.
- Continue to generate exactly seven `.tex` files and seven PDFs.
- Preserve `input/claim.yaml` as shared document metadata.
- Required experiment sections have no supplier-controlled off switch and no fallback copy.
- Optional absence renders exactly `No data provided.`; conditional non-applicability requires and renders a reason.
- Sort experiments by `started_at`, then `id`; sort child CSV rows by `sequence`.
- Reject active placeholder values such as bracketed prompts, `xxx`, or `TBD`.
- Never infer eligibility, facts, measurements, conclusions, approvals, or evidence.
- Validate all sources before overwriting generated output.
- Use decimal-safe handling if numeric result calculations are added; this slice renders supplied result values without performing scientific calculations.

---

## Target file structure

| File | Responsibility |
|---|---|
| `scripts/publisher.py` | Orchestrate loading, validation, normalization, and rendering; preserve its public error import for compatibility |
| `scripts/validation.py` | Own `SourceValidationError` and reusable strict YAML/CSV loading helpers without importing domain modules |
| `scripts/experiments.py` | Own experiment YAML/CSV schemas, validation, cross-reference checks, state rules, and deterministic sorting |
| `input/experiments.yaml` | Supplier-authored run narratives and structured experimental design |
| `input/experiment-results.csv` | Supplier-authored dynamic observation/result rows |
| `input/experiment-execution-log.csv` | Supplier-authored chronological actions and observations |
| `input/experiment-evidence.csv` | Supplier-authored evidence catalogue linked to runs |
| `templates/02_experiment_notebook.tex` | Render normalized notebook index and run sections only |
| `templates/rd_audit_style.sty` | Provide shared no-data and not-applicable callouts |
| `tests/test_experiments.py` | Unit tests for experiment source and state validation |
| `tests/test_publisher.py` | Integration tests for source assembly and TeX rendering |
| `tests/fixtures/valid-experiments.yaml` | Valid two-run narrative fixture |
| `tests/fixtures/valid-experiment-results.csv` | Valid dynamic metric rows for both runs |
| `tests/fixtures/valid-experiment-execution-log.csv` | Valid execution rows for both runs |
| `tests/fixtures/valid-experiment-evidence.csv` | Valid evidence records for both runs |
| `README.md` | Explain experiment inputs, absence semantics, and publication errors |

## Task 1: Define experiment source interfaces and valid fixtures

**Files:**

- Create: `publishing-pipeline/scripts/experiments.py`
- Create: `publishing-pipeline/scripts/validation.py`
- Create: `publishing-pipeline/tests/test_experiments.py`
- Modify: `publishing-pipeline/tests/fixtures/valid-experiments.yaml`
- Create: `publishing-pipeline/tests/fixtures/valid-experiment-results.csv`
- Create: `publishing-pipeline/tests/fixtures/valid-experiment-execution-log.csv`
- Create: `publishing-pipeline/tests/fixtures/valid-experiment-evidence.csv`

**Interfaces:**

- Produces: `EXPERIMENT_CSV_SCHEMAS: dict[str, tuple[str, ...]]`
- Produces: `load_experiment_sources(input_dir: Path) -> list[dict[str, Any]]`
- Produces: `validate_and_normalize_experiments(experiment_source: dict[str, Any], results: list[dict[str, str]], execution_log: list[dict[str, str]], evidence: list[dict[str, str]]) -> list[dict[str, Any]]`
- Consumes: `SourceValidationError`, `load_yaml_mapping(path: Path) -> dict[str, Any]`, and `load_strict_csv(path: Path, required_headers: tuple[str, ...]) -> list[dict[str, str]]` from `scripts/validation.py`
- Raises: `SourceValidationError` from `scripts/validation.py`; `publisher.py` re-exports the imported name so existing callers remain compatible

- [ ] **Step 1: Write a two-run valid fixture that exercises ordering and different metric types**

Use `RUN-2026-002` before `RUN-2026-001` in YAML so tests prove output ordering comes from `started_at`. Make one completed `mixed` run with a quantitative result and one `ongoing` run with a qualitative result, `interim_conclusion`, and `next_actions`.

- [ ] **Step 2: Write the initial public-interface test**

```python
def test_normalizes_runs_in_chronological_order(self) -> None:
    runs = load_experiment_sources(self.input_dir)

    self.assertEqual([run["id"] for run in runs], ["RUN-2026-001", "RUN-2026-002"])
    self.assertEqual(runs[0]["results"][0]["metric"], "provider submissions")
    self.assertEqual(runs[1]["results"][0]["kind"], "qualitative")
```

- [ ] **Step 3: Run the focused test and verify it fails for the missing module/interface**

Run: `publishing-pipeline/.venv/bin/python -m unittest discover -s publishing-pipeline/tests -p 'test_experiments.py' -v`

Expected: failure because `scripts/experiments.py` or `load_experiment_sources` does not exist.

- [ ] **Step 4: Define exact CSV schemas and minimal file loading**

```python
EXPERIMENT_CSV_SCHEMAS = {
    "experiment-results.csv": (
        "run_id", "sequence", "kind", "metric", "baseline_value",
        "observed_value", "unit", "notes", "evidence_ref",
    ),
    "experiment-execution-log.csv": (
        "run_id", "sequence", "occurred_at", "actor", "tool",
        "action", "observation", "evidence_ref",
    ),
    "experiment-evidence.csv": (
        "evidence_id", "run_id", "type", "title", "location",
        "captured_at", "notes",
    ),
}
```

Move the existing `SourceValidationError`, YAML loader, and strict CSV loader from `publisher.py` into `validation.py`. Rename them to the public interfaces above and import them back into `publisher.py`. Do not accept alternate header order because deterministic human-editable contracts are preferable here.

- [ ] **Step 5: Implement minimal normalization and ordering**

Parse timestamps with `datetime.fromisoformat`, attach CSV child lists by `run_id`, coerce `sequence` to positive integers for sorting, and return new normalized mappings rather than mutating loader output.

- [ ] **Step 6: Run the focused tests and the existing suite**

Run: `publishing-pipeline/.venv/bin/python -m unittest discover -s publishing-pipeline/tests -v`

Expected: all current and new tests pass.

- [ ] **Step 7: Commit the source contract slice**

```bash
git add publishing-pipeline/scripts/validation.py publishing-pipeline/scripts/experiments.py publishing-pipeline/tests/test_experiments.py publishing-pipeline/tests/fixtures/valid-experiments.yaml publishing-pipeline/tests/fixtures/valid-experiment-results.csv publishing-pipeline/tests/fixtures/valid-experiment-execution-log.csv publishing-pipeline/tests/fixtures/valid-experiment-evidence.csv
git commit -m "test: define experiment notebook source contract"
```

## Task 2: Enforce required, conditional, chronology, and reference rules

**Files:**

- Modify: `publishing-pipeline/scripts/experiments.py`
- Modify: `publishing-pipeline/tests/test_experiments.py`

**Interfaces:**

- Consumes: `validate_and_normalize_experiments(...)` from Task 1
- Produces: fully validated normalized run mappings with `results`, `execution_log`, and `evidence` child lists
- Produces: actionable `SourceValidationError` messages containing filename and run ID or CSV row number

- [ ] **Step 1: Add table-driven failures for every hard-required narrative field**

```python
def test_rejects_missing_required_run_fields(self) -> None:
    required_paths = (
        "title", "project_ref", "uncertainty_refs", "started_at", "engineers",
        "objective", "background.summary", "hypothesis.statement",
        "hypothesis.formed_at", "design", "method", "evaluation", "status",
    )
    for field_path in required_paths:
        with self.subTest(field_path=field_path):
            with self.assertRaisesRegex(SourceValidationError, rf"RUN-2026-001 requires {re.escape(field_path)}"):
                self.load_with_field_removed(field_path)
```

- [ ] **Step 2: Add status-state tests**

Test that completed statuses require `ended_at` and `conclusion`; `ongoing` requires `interim_conclusion` and a non-empty `next_actions`, and rejects a final `ended_at`. Test the allowed status set exactly.

- [ ] **Step 3: Add chronology tests**

Reject `ended_at < started_at`, a hypothesis `formed_at` later than `started_at`, child execution timestamps outside a completed run's range, duplicate sequences within a run, and invalid ISO timestamps. `ended_at` represents completion of observation/evaluation for this contract, so a completed run must encompass its execution log.

- [ ] **Step 4: Add cross-reference and cardinality tests**

Reject unknown run IDs in every CSV, duplicate experiment IDs, duplicate evidence IDs, missing evidence references, execution/result references to evidence owned by a different run, zero result rows, zero execution rows, and zero evidence rows. Validate `project_ref`, each `uncertainty_ref`, and each `person_ref` against their documented ID patterns; do not claim those external-domain IDs resolve until their later authoritative sources exist.

- [ ] **Step 5: Add result-shape tests**

Verify `kind` is `quantitative` or `qualitative`; quantitative rows require a unit; qualitative rows may use `not_applicable`; every row requires metric, observed value, notes, and evidence reference; `baseline_value=not_applicable` requires notes explaining the absence.

- [ ] **Step 6: Add optional/conditional state tests**

Use this exact value shape for optional narrative blocks:

```yaml
unexpected_behaviour:
  state: "provided"
  content: "Provider activity arrived after the local state transition."
```

Allowed states are `provided` and `no_data`. `provided` requires content; `no_data` forbids content. Fields designated required never accept this state wrapper. Conditional design values use `{state: not_applicable, reason: "..."}` only where the spec permits it.

- [ ] **Step 7: Add placeholder-value rejection tests**

Reject trimmed values matching bracketed prompts, case-insensitive `xxx`, or case-insensitive `TBD`. Do not reject ordinary prose that merely contains square brackets or those letters as part of another word.

- [ ] **Step 8: Implement the validation rules with small field-specific helpers**

Use focused helpers such as:

```python
def require_text(run: dict[str, Any], path: str) -> str: ...
def parse_timestamp(value: str, *, source: str, field: str) -> datetime: ...
def validate_optional_block(run_id: str, name: str, value: Any) -> dict[str, str]: ...
def validate_references(runs: list[dict[str, Any]]) -> None: ...
```

Keep messages stable enough for tests. Do not put rendering copy in validation functions.

- [ ] **Step 9: Run the experiment tests, then the complete suite**

Run: `publishing-pipeline/.venv/bin/python -m unittest discover -s publishing-pipeline/tests -p 'test_experiments.py' -v`

Run: `publishing-pipeline/.venv/bin/python -m unittest discover -s publishing-pipeline/tests -v`

Expected: all tests pass.

- [ ] **Step 10: Commit fail-closed validation**

```bash
git add publishing-pipeline/scripts/experiments.py publishing-pipeline/tests/test_experiments.py
git commit -m "feat: validate audit-grade experiment records"
```

## Task 3: Integrate experiment sources without partial generated output

**Files:**

- Modify: `publishing-pipeline/scripts/publisher.py`
- Modify: `publishing-pipeline/tests/test_publisher.py`
- Modify: `publishing-pipeline/tests/fixtures/valid-claim.yaml`
- Ensure fixture copy logic maps all `valid-*` experiment CSV files to active names

**Interfaces:**

- Consumes: `load_experiment_sources(input_dir: Path)` from Task 1/2
- Produces: `sources["experiments"]` as validated, sorted, normalized run mappings
- Preserves: `load_sources(input_dir: Path) -> dict[str, Any]`

- [ ] **Step 1: Add an integration test for child source attachment**

```python
def test_loads_normalized_experiment_children(self) -> None:
    sources = load_sources(self.input_dir)

    run = sources["experiments"][0]
    self.assertEqual(run["id"], "RUN-2026-001")
    self.assertGreaterEqual(len(run["results"]), 1)
    self.assertGreaterEqual(len(run["execution_log"]), 1)
    self.assertGreaterEqual(len(run["evidence"]), 1)
```

- [ ] **Step 2: Add a no-overwrite-on-validation-error test**

Create a sentinel generated file, introduce an invalid experiment source, call the top-level generate orchestration after it is extracted into a testable function, and assert the sentinel remains unchanged. This establishes the spec's validate-before-overwrite guarantee.

- [ ] **Step 3: Run the integration tests and observe the expected failures**

Run: `publishing-pipeline/.venv/bin/python -m unittest discover -s publishing-pipeline/tests -p 'test_publisher.py' -v`

Expected: the new tests fail because the publisher still accepts only IDs and loads no experiment CSV files.

- [ ] **Step 4: Replace baseline experiment loading with the validated interface**

Remove the duplicate ID-only loop from `publisher.py`. Import the experiment loader and assign its result to `sources["experiments"]`. Keep generic document and cost/timesheet validation behavior unchanged.

- [ ] **Step 5: Separate validation from generated-directory writes if needed**

The top-level flow must first call all source loaders successfully, then render. Do not delete or truncate existing generated files during source validation.

- [ ] **Step 6: Run the complete suite**

Run: `publishing-pipeline/.venv/bin/python -m unittest discover -s publishing-pipeline/tests -v`

Expected: all tests pass.

- [ ] **Step 7: Commit publisher integration**

```bash
git add publishing-pipeline/scripts/publisher.py publishing-pipeline/tests/test_publisher.py publishing-pipeline/tests/fixtures
git commit -m "feat: load normalized experiment notebook data"
```

## Task 4: Render the dynamic notebook and absence states

**Files:**

- Modify: `publishing-pipeline/templates/02_experiment_notebook.tex`
- Modify: `publishing-pipeline/templates/rd_audit_style.sty`
- Modify: `publishing-pipeline/tests/test_publisher.py`

**Interfaces:**

- Consumes: normalized `experiments` list with child `results`, `execution_log`, and `evidence`
- Produces: `RDNoData` and `RDNotApplicable` LaTeX macros
- Produces: one notebook index and one ordered section per experiment

- [ ] **Step 1: Add rendering assertions for two different experiments**

Assert the generated TeX contains both IDs/titles in chronological order, each result metric supplied by the fixture, the run-specific evaluation and conclusion/interim conclusion, and linked evidence titles.

- [ ] **Step 2: Add assertions that static placeholders are absent**

```python
for forbidden in (
    "Latency & {[value]}",
    "RUN-XXX",
    "Repeatable blank run pages",
    "Duplicate this section",
    "State what this run was intended to determine",
):
    self.assertNotIn(forbidden, notebook)
```

- [ ] **Step 3: Add absence-state rendering tests**

Verify `unexpected_behaviour.state=no_data` renders exactly `No data provided.` and that a permitted conditional value with `state=not_applicable` renders its reason. Validation tests from Task 2 already prove required sections cannot reach these branches.

- [ ] **Step 4: Run rendering tests and observe failures against the static template**

Run: `publishing-pipeline/.venv/bin/python -m unittest discover -s publishing-pipeline/tests -p 'test_publisher.py' -v`

Expected: failures because the notebook still contains one static example and blank form.

- [ ] **Step 5: Add shared absence macros**

```tex
\newcommand{\RDNoData}{\RDCallout{No data provided}{No data provided.}}
\newcommand{\RDNotApplicable}[1]{\RDCallout{Not applicable}{#1}}
```

If visual review shows the repeated title/body in `RDNoData` is awkward, change the macro implementation and test only the exact body copy; do not change its meaning.

- [ ] **Step 6: Replace the notebook template body with data-driven loops**

Use Jinja block syntax already configured by the publisher:

```tex
<% for experiment in experiments %>
\clearpage
\section{<< experiment.id >>: << experiment.title >>}
...
<% for result in experiment.results %>
<< result.metric >> & << result.baseline_value >> & << result.observed_value >> & << result.notes >> \\
<% endfor %>
<% endfor %>
```

Render headings and cells from normalized values only. Keep TeX row delimiters in the template. Use conditionals only for schema-approved optional and conditional states.

- [ ] **Step 7: Remove the blank-run pages and completion instructions from published output**

Retain a short static purpose/audit note if useful to an auditor; remove authoring instructions, sample runs, fixed metrics, and blank writing space.

- [ ] **Step 8: Run all automated tests**

Run: `publishing-pipeline/.venv/bin/python -m unittest discover -s publishing-pipeline/tests -v`

Expected: all tests pass.

- [ ] **Step 9: Generate TeX and scan the notebook for forbidden markers**

Run:

```bash
publishing-pipeline/.venv/bin/python publishing-pipeline/scripts/publisher.py --input publishing-pipeline/tests/fixtures --templates publishing-pipeline/templates --generated /tmp/au-rnd-audit-tex-experiment-generated
rg -n '\[([^]]*(Name|Date|value|ID|Title)[^]]*)\]|xxx|TBD|RUN-XXX|Blank experiment' /tmp/au-rnd-audit-tex-experiment-generated/02_experiment_notebook.tex
```

Expected: generation succeeds and the scan returns no matches.

- [ ] **Step 10: Commit dynamic rendering**

```bash
git add publishing-pipeline/templates/02_experiment_notebook.tex publishing-pipeline/templates/rd_audit_style.sty publishing-pipeline/tests/test_publisher.py
git commit -m "feat: render chronological experiment notebook"
```

## Task 5: Provide supplier templates and operating documentation

**Files:**

- Modify: `publishing-pipeline/input/experiments.yaml`
- Create: `publishing-pipeline/input/experiment-results.csv`
- Create: `publishing-pipeline/input/experiment-execution-log.csv`
- Create: `publishing-pipeline/input/experiment-evidence.csv`
- Create: `publishing-pipeline/input/experiments.template.yaml`
- Create: `publishing-pipeline/input/experiment-results.template.csv`
- Create: `publishing-pipeline/input/experiment-execution-log.template.csv`
- Create: `publishing-pipeline/input/experiment-evidence.template.csv`
- Modify: `publishing-pipeline/README.md`
- Modify: `publishing-pipeline/tests/test_publisher.py`

**Interfaces:**

- Consumes: exact source contracts defined by Tasks 1–2
- Produces: safe reusable templates separate from active data
- Produces: documented supplier workflow and error semantics

- [ ] **Step 1: Add a test that template files are ignored by active loading**

Place valid example content in `*.template.yaml`/`*.template.csv`, load active sources, and assert template run IDs do not appear. The loader must open exact active filenames only.

- [ ] **Step 2: Add active empty-header CSV files and a reusable narrative template**

The reusable YAML template must show every required key, both completed and ongoing state shapes, optional `no_data`, and conditional `not_applicable` with a reason. The active files should contain real supplier data or remain invalid until configured; do not silently publish a fake example as evidence.

- [ ] **Step 3: Document the authoring workflow**

Explain:

1. copy/reference the template structure;
2. assign stable cross-document IDs;
3. write the hypothesis before the run;
4. append execution, result, and evidence rows while work occurs;
5. set the final status and conclusion honestly;
6. publish and correct actionable validation errors;
7. never edit `generated/` or `output/` directly.

- [ ] **Step 4: Document absence semantics and hard failures**

Include a compact table for required, conditional, optional, repeating, and derived content. State plainly that `No data provided.` cannot be selected for hypothesis, method, observations, evaluation, conclusion/interim conclusion, or evidence.

- [ ] **Step 5: Run all tests**

Run: `publishing-pipeline/.venv/bin/python -m unittest discover -s publishing-pipeline/tests -v`

Expected: all tests pass.

- [ ] **Step 6: Commit supplier documentation and templates**

```bash
git add publishing-pipeline/input publishing-pipeline/README.md publishing-pipeline/tests/test_publisher.py
git commit -m "docs: add experiment notebook input guidance"
```

## Task 6: End-to-end compilation and final review

**Files:**

- Modify only if verification exposes a defect: files changed in Tasks 1–5

**Interfaces:**

- Consumes: the complete experiment slice
- Produces: verified generated TeX and all seven PDFs

- [ ] **Step 1: Run the complete test suite from the pipeline environment**

Run: `publishing-pipeline/.venv/bin/python -m unittest discover -s publishing-pipeline/tests -v`

Expected: all tests pass.

- [ ] **Step 2: Publish all seven PDFs**

Run on macOS: `publishing-pipeline/publish.zsh`

Expected: `Published 7 PDFs ... with no warnings.`

- [ ] **Step 3: Inspect generated experiment TeX for chronological order and forbidden content**

Run:

```bash
rg -n 'RUN-2026-|No data provided|Not applicable|RUN-XXX|\{\[|xxx|TBD|Blank experiment' publishing-pipeline/generated/02_experiment_notebook.tex
```

Expected: real run IDs appear in chronological order; approved absence copy may appear; no placeholder/template markers appear.

- [ ] **Step 4: Extract PDF text and check required sections**

Use an available PDF text extractor on `publishing-pipeline/output/02_experiment_notebook.pdf`. Verify each run has objective, background, hypothesis, variables/conditions, method, execution log, results, evaluation, conclusion/interim conclusion, next action where required, and evidence.

- [ ] **Step 5: Visually inspect the PDF**

Check the index, page breaks, repeated long-table headers, long content wrapping, URLs/paths, result rows with different metric types, absence callouts, and document-control pages. No tables may overflow or hide content.

- [ ] **Step 6: Verify no unrelated paths changed**

Run: `git status --short` and `git diff --check -- publishing-pipeline`

Expected: only intended `publishing-pipeline/` files are changed and whitespace checks pass.

- [ ] **Step 7: Commit any verification-only corrections**

If corrections were necessary, commit them with a message naming the observed defect. If none were necessary, do not create an empty commit.

## Completion gate

Do not call this slice complete unless all of the following are evidenced in the same working state:

- experiment unit and integration tests pass;
- existing timesheet/infrastructure/shared-metadata tests still pass;
- all seven TeX files generate;
- all seven PDFs compile without warnings;
- experiment PDF text contains every supplied run in deterministic order;
- dynamic metrics differ across fixture runs without template changes;
- required missing data has negative tests and blocks generation;
- optional/conditional absence copy is visible and truthful;
- generated notebook contains no instructional placeholders or blank forms;
- no file outside `publishing-pipeline/` was changed.
