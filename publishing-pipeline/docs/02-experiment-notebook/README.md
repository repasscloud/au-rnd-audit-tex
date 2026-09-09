# 02 Experiment Notebook authoring guide

The Experiment Notebook is one annual PDF containing every supplied experimental run. It is intended to preserve the chronological progression from a pre-run hypothesis through method, execution, observation, evaluation, and conclusion.

The publisher can verify that required records exist, that timestamps and references are internally consistent, and that the generated notebook is ordered deterministically. It cannot determine R&D eligibility, factual accuracy, scientific adequacy, or whether the evidence will satisfy a particular auditor. Those remain supplier and professional-review responsibilities.

## AI-assisted experiment capture

Use these instructions when Codex, ChatGPT, Claude, or another AI agent will help classify, plan, or maintain an experimental record:

- [AI agent protocol](AI-AGENT-PROTOCOL.md) — mandatory authority, classification, evidence, lifecycle, and safe-editing rules.
- [Experiment test and capture workflow](EXPERIMENT-CAPTURE-WORKFLOW.md) — what to record before, during, and after execution and how to map it into YAML and CSV.
- [Reusable AI agent task](AI-AGENT-TASK-TEMPLATE.md) — a prompt that can be supplied directly to an agent for a particular proposed experiment.

The agent assists with evidence-grounded classification and record construction. It must not manufacture a retrospective experiment, rewrite unsuccessful results, or determine legal R&D eligibility.

## Source files

Three active CSV files and one of two YAML input modes produce `output/02_experiment_notebook.pdf`:

| Source | Purpose |
| --- | --- |
| `input/experiments.yaml` | Combined mode: all run narratives in one file |
| `input/experiments/experiment.RUN-YYYY-NNN.yaml` | Split mode: one run narrative per file |
| `input/experiment-results.csv` | Quantitative and qualitative observations |
| `input/experiment-execution-log.csv` | Timestamped actions and observations |
| `input/experiment-evidence.csv` | Evidence catalogue and locations |

The corresponding `.template.yaml` and `.template.csv` files are structural examples only. The publisher never reads template files directly. Copy their structures into active files and replace every example with contemporaneous supplier records.

Copying YAML alone is not enough. Every run also requires matching results, execution-log entries, and evidence in the three active CSV files. If required data is missing, publication stops and any previously generated PDF remains unchanged.

## Choose one YAML input mode

The publisher supports either a single combined YAML file or a directory containing one YAML file per experiment. Do not use both modes at the same time.

### Combined-file mode

Use `input/experiments.yaml` with a top-level `experiments` list:

```yaml
experiments:
  - id: RUN-2026-001
    # Complete first run record
  - id: RUN-2026-002
    # Complete second run record
```

This mode is convenient for a small number of experiments.

### Split-file mode

Do not provide `input/experiments.yaml`. Instead, create one file per run in `input/experiments/`:

```text
input/experiments/
├── experiment.RUN-2026-001.yaml
├── experiment.RUN-2026-002.yaml
└── experiment.RUN-2026-003.yaml
```

Each file has a singular top-level `experiment` mapping:

```yaml
experiment:
  id: RUN-2026-001
  title: Example experiment
  # Remaining run fields
```

The ID in the filename must exactly match `experiment.id`. For example, `experiment.RUN-2026-001.yaml` must contain `id: RUN-2026-001`. Invalid filenames and mismatched identifiers stop publication.

Files ending in `.template.yaml` are ignored. Use `input/experiments/experiment.RUN-2026-001.template.yaml` as the split-file structural example: copy it to an active filename, then change both filename and internal ID for the real run.

The publisher combines split records in memory. It does not create or overwrite `experiments.yaml`. It reads filenames deterministically, validates the combined records, and orders the final PDF by `started_at`, then `id`. Run-number order does not override the recorded chronology.

If both `input/experiments.yaml` and any active split experiment files exist, publication stops with an ambiguity error. Remove or rename the inactive source before publishing.

## How experiments become one notebook

In combined mode, `experiments.yaml` contains an `experiments` list. In split mode, the in-memory result is equivalent to that list. Each item is one independently identifiable run:

```yaml
experiments:
  - id: RUN-2026-001
    # Complete run record
  - id: RUN-2026-002
    # Complete run record
```

The notebook may contain any number of runs. The publisher sorts them by `started_at`, then by `id` when start times are equal. It creates one chronological index and one complete section for each run. An empty experiment list is not publishable.

The template demonstrates two lifecycle states:

- `RUN-2026-001` shows a completed experiment.
- `RUN-2026-002` shows an experiment still in progress.

## Experiment identity and traceability

```yaml
id: RUN-2026-001
title: Recovery behaviour after queue-worker interruption
project_ref: RND-2026-01
uncertainty_refs:
  - UT-01
```

### `id`

A permanent, unique identifier for the run. It should remain unchanged after publication and must match the `run_id` used by that experiment's rows in all three CSV files.

Use the form `RUN-YYYY-NNN`, for example `RUN-2026-014`.

### `title`

A concise description of what was tested. It should distinguish the run from other experiments; a generic title such as `Experiment 14` does not explain the work.

### `project_ref`

The stable project or activity identifier to which the run belongs, for example `RND-2026-01`. The notebook records and displays this reference. Other documents can later use it to connect the run to the claim overview and mapping register.

### `uncertainty_refs`

One or more stable technical-uncertainty identifiers addressed by the run, for example `UT-01`. These references demonstrate why the experiment was undertaken and connect it to a defined technical uncertainty rather than merely documenting ordinary development work.

Until authoritative program and people sources are implemented, project, uncertainty, and person references are format-checked but cannot be resolved against master records.

## Timing and status

```yaml
started_at: 2026-07-14T09:30:00+09:30
ended_at: 2026-07-14T12:10:00+09:30
status: mixed
```

### `started_at`

The date and time the experimental run began. Supply a complete ISO 8601 timestamp with a UTC offset. The publisher uses this field to order the notebook.

### `ended_at`

The date and time observation and evaluation for a completed run ended.

- It is required for completed runs.
- It is forbidden when `status` is `ongoing`.
- It cannot precede `started_at`.
- Every execution-log event for a completed run must fall between `started_at` and `ended_at`.

### `status`

Status describes how the supplied observations relate to the hypothesis. It does not determine whether the activity is eligible R&D.

| Value | Meaning |
| --- | --- |
| `confirmed` | The observations supported the hypothesis |
| `rejected` | The observations contradicted the hypothesis |
| `mixed` | Some parts were supported and others were not |
| `inconclusive` | The evidence did not resolve the hypothesis |
| `ongoing` | The run has not reached a final conclusion |

Failed, rejected, mixed, and inconclusive experiments should be recorded honestly. They can demonstrate the actual systematic progression and should not be rewritten as successful outcomes.

## People involved

```yaml
engineers:
  - person_ref: P-001
    role: experiment lead
  - person_ref: P-004
    role: test environment operator
```

`engineers` identifies who performed or observed the work and their role in this run. At least one entry is required. Each entry requires a stable `person_ref` and a meaningful `role`.

Participation in an experiment does not automatically mean all of that person's time is eligible expenditure.

## Technical objective

```yaml
objective: Determine whether queued deliveries can resume after worker interruption without losing or duplicating accepted messages.
```

The objective states the specific technical question investigated by this run. It should be narrower than the overall project objective and framed so the experiment can produce a meaningful result. A generic statement such as `test the system` is insufficient.

This is required and cannot be replaced by `No data provided.`

## Background

```yaml
background:
  summary: Existing recovery documentation described queue persistence, but it did not establish whether an interruption between provider acceptance and local acknowledgement could cause duplicate delivery.
  research_refs:
    - EV-0141
    - EV-0142
```

### `background.summary`

Describe what was already known, what research or prior work had been performed, what remained technically uncertain, and why the result could not simply be determined in advance. This should distinguish technical uncertainty from a missing business requirement, routine configuration question, or ordinary implementation task.

### `background.research_refs`

List the evidence identifiers supporting the background. Every identifier must exist as an `evidence_id` in `experiment-evidence.csv` and must belong to the same run.

The background summary and at least one research reference are required.

## Pre-run hypothesis

```yaml
hypothesis:
  statement: If each delivery is durably persisted before submission, restarting the worker at any tested interruption point will resume processing without losing a delivery.
  formed_at: 2026-07-13T16:20:00+09:30
  basis_refs:
    - EV-0141
```

### `hypothesis.statement`

State the expected technical result before conducting the experiment. It must be specific, testable, and capable of being confirmed, rejected, or left unresolved by the recorded observations.

The objective asks a question. The hypothesis records the expected answer.

### `hypothesis.formed_at`

Record when the hypothesis was formed. It cannot be later than `started_at`; this prevents the source from presenting a retrospectively written explanation as a pre-run hypothesis.

### `hypothesis.basis_refs`

List the evidence used to form the hypothesis. Every identifier must exist in `experiment-evidence.csv` and belong to this run.

The complete hypothesis block is required and cannot use `No data provided.`

## Experimental design

```yaml
design:
  independent_variables:
    - Worker interruption point
    - Duration between provider submission and worker restart
  controlled_variables:
    - Application build
    - Queue configuration
    - Test message payload
  observed_variables:
    - Whether every queued message reached a terminal state
    - Number of duplicate provider submissions
  acceptance_criteria:
    - Every queued message reaches a terminal state after recovery
    - No message is submitted to the provider more than once
  failure_triggers:
    - Any queued message becomes permanently unreachable
    - Any interruption point produces more than one provider submission
```

The design records how the hypothesis will be tested before results are evaluated.

### `independent_variables`

What the run deliberately changes, such as an interruption point, input condition, algorithm, configuration, or test treatment.

### `controlled_variables`

What remains constant so that an observed outcome can reasonably be connected to the tested change, such as the application build, environment, test payload, or instrumentation.

### `observed_variables`

What will be measured or observed. Metrics are not fixed by the template. Depending on the hypothesis, they may include correctness, recovery behaviour, duplicate count, accuracy, memory use, response time, or a qualitative observation. Actual observations belong in `experiment-results.csv`.

### `acceptance_criteria`

The criteria established before execution for deciding whether observations support the hypothesis. Do not rewrite these after seeing the results.

### `failure_triggers`

The conditions that would contradict or materially limit the hypothesis. These demonstrate that the experiment was capable of disproving the proposed approach.

The overall design block is required. Where a particular design category genuinely does not apply, use the explicit conditional form and explain why:

```yaml
controlled_variables:
  state: not_applicable
  reason: This was a static algorithm analysis with no comparative execution environment.
```

An unexplained blank value is not acceptable.

## Method

```yaml
method: Deploy build 2026.07.14.3 to the isolated test environment, enqueue 100 uniquely identified messages, interrupt the worker at each defined recovery point, restart it after 30 seconds, and reconcile local delivery records against provider submissions.
```

Describe exactly how the experiment was conducted. Where relevant, identify the build, environment, starting conditions, test data, tools, instrumentation, procedure, run sequence, and method used to collect and compare results.

The method should be detailed enough for another competent person to understand and, where practical, reproduce the run. Timestamped steps actually performed belong in `experiment-execution-log.csv`.

The method is required and cannot use `No data provided.`

## Evaluation

```yaml
evaluation: All persisted messages resumed processing, satisfying the recovery criterion. One interruption window produced an ambiguous provider state, so the absence of duplicate delivery could not be established for that window.
```

Interpret the supplied results by comparing observations with acceptance criteria, identifying any failure triggers, distinguishing measured facts from inference, and explaining limitations, ambiguity, or conflicting observations. Results belong in the results CSV; the evaluation explains what those results mean.

Evaluation is required for completed and ongoing runs and cannot use `No data provided.`

## Completed-run conclusion

```yaml
conclusion: The hypothesis was partly supported. Durable queue recovery prevented message loss, but duplicate prevention could not be established when provider acceptance occurred before interruption.
```

A completed run requires a logical `conclusion` that answers the original hypothesis using the recorded observations and evaluation. It must agree with `status`; for example, a `mixed` run should not claim without qualification that the hypothesis was completely confirmed.

Completed statuses also require `ended_at`. They must not use `interim_conclusion` as a substitute for a final conclusion.

## Ongoing-run interim conclusion

```yaml
status: ongoing
interim_conclusion: Recovery has succeeded at two interruption points, but the provider-acceptance window has not yet been tested and no final conclusion can be made.
```

An ongoing run requires `interim_conclusion` instead of `conclusion`. State what has been observed so far, what those observations tentatively indicate, what remains unresolved, and why no final conclusion can yet be made.

An ongoing run must not contain `ended_at`.

## Next actions

```yaml
next_actions:
  - Add provider-side acceptance reconciliation to the instrumentation.
  - Repeat the run at the unresolved interruption point.
```

Record how the experimental progression continues. Actions should identify a specific follow-up run, design change, instrumentation need, or technical decision—not a vague instruction such as `investigate further`.

At least one next action is required for an ongoing run. Next actions are optional for a completed run but are particularly useful after a rejected, mixed, or inconclusive outcome.

## Unexpected behaviour

When unexpected behaviour occurred, supply it explicitly:

```yaml
unexpected_behaviour:
  state: provided
  content: The provider accepted the message but returned no operation identifier before the connection was interrupted.
```

When no unexpected behaviour was recorded, use:

```yaml
unexpected_behaviour:
  state: no_data
```

`provided` requires non-empty `content`. `no_data` forbids `content` and causes the PDF to display `No data provided.` This absence state is permitted because a run may genuinely have no unexpected behaviour; it is not permitted for required experimental records.

## CSV relationships

The YAML run ID joins one experiment to its CSV records. For example, this YAML identifier:

```yaml
id: RUN-2026-001
```

requires CSV rows whose `run_id` is the same:

```csv
run_id,sequence,...
RUN-2026-001,1,...
```

Every run requires at least one record in each CSV collection:

- One result or observation.
- One execution-log entry.
- One evidence record.

Every result and execution row must reference evidence owned by the same run. Background and hypothesis evidence references must also resolve to evidence owned by that run. Orphan rows, cross-run references, and unknown evidence identifiers stop publication.

### Result records

Result metrics are dynamic. Each experiment may measure entirely different things, and quantitative and qualitative records can coexist.

- `sequence` controls row order within the run and must be a unique positive integer.
- `kind` is `quantitative` or `qualitative`.
- Quantitative results require a unit.
- `baseline_value` may be `not_applicable` only when `notes` explains why comparison is irrelevant.
- `evidence_ref` must identify evidence belonging to the same run.

### Execution-log records

Execution entries record what actually occurred, in order, rather than restating the planned method.

- `sequence` controls entry order and must be a unique positive integer within the run.
- `occurred_at` must be an ISO 8601 timestamp with a UTC offset.
- For completed runs, it must fall between `started_at` and `ended_at`.
- `evidence_ref` must identify evidence belonging to the same run.

### Evidence records

Evidence records catalogue material supporting the background, hypothesis, execution, and observations. Evidence IDs must be unique throughout the notebook, and each record must belong to exactly one run.

The evidence location should be stable and meaningful to an authorised reviewer. The publisher records the location but does not verify that the file exists, is accessible, or proves the associated assertion.

## Absence and applicability rules

| Content type | Author action | Publication behaviour |
| --- | --- | --- |
| Required | Supply complete content | Missing content stops publication |
| Conditional and applicable | Supply complete content | Missing content stops publication |
| Conditional and inapplicable | Use `state: not_applicable` with a non-empty reason where permitted | PDF prints `Not applicable` and the reason |
| Optional | Supply content or use the documented `no_data` state | PDF prints `No data provided.` |
| Repeating | Add one item or row per record | Publisher sorts and renders every record |
| Derived | Supply valid records and references | Publisher generates indexes and grouped sections |

`No data provided.` cannot be selected for the hypothesis, method, execution log, results or observations, evaluation, conclusion or interim conclusion, or evidence collection. These are hard requirements for every published run.

## Publication workflow

1. Choose combined-file mode or split-file mode; do not provide active YAML files for both.
2. Copy `experiments.template.yaml` for combined mode, or copy the split template under `input/experiments/` once for each run.
3. Copy the three CSV template structures into their corresponding active CSV files.
4. Replace every example with actual contemporaneous supplier records.
5. Assign each run a stable `RUN-YYYY-NNN` identifier and use it consistently in its filename, YAML, and all three CSV files.
6. Record the hypothesis and its basis evidence before the run starts.
7. Append execution, result, and evidence records while the activity occurs.
8. For a completed run, supply a completed status, `ended_at`, and `conclusion`.
9. For an unfinished run, use `ongoing`, omit `ended_at`, and supply an `interim_conclusion` and at least one next action.
10. Run `./publish.zsh` on macOS or `./publish.sh` on Linux.
11. Correct every reported source error and run the publisher again.
12. Review the generated notebook and its referenced evidence before relying on it.

Do not edit `generated/` or `output/`. If validation fails, the publisher does not replace the existing generated files or PDF. Always confirm that the publication command completed successfully before reviewing the output.

## Hard publication requirements

Publication stops if any run lacks:

- A unique run ID and meaningful title.
- Project and uncertainty references.
- A valid start time and lifecycle-consistent status.
- At least one engineer.
- A technical objective.
- Background and supporting evidence references.
- A pre-run hypothesis, formation time, and basis evidence.
- An experimental design.
- A reproducible method.
- At least one execution-log entry.
- At least one result or observation.
- An evaluation.
- A conclusion for a completed run or interim conclusion for an ongoing run.
- At least one evidence record.

The publisher also rejects mixed YAML input modes, invalid split filenames, filename-to-record ID mismatches, malformed timestamps, duplicate or invalid identifiers, duplicate sequences, invalid statuses, placeholder-looking values, invalid absence states, orphan CSV rows, unknown evidence references, cross-run evidence references, and execution events outside a completed run's time range.
