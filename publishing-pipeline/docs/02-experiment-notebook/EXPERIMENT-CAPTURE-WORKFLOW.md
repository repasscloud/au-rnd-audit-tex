# Experiment test and capture workflow

## Purpose

This workflow defines when an AI agent and responsible human should create or update Experiment Notebook records. It prevents retrospective hypotheses, undocumented execution, inferred measurements, and conclusions unsupported by evidence.

Use it with [AI-AGENT-PROTOCOL.md](AI-AGENT-PROTOCOL.md) and the field-level rules in [README.md](README.md).

## Lifecycle overview

| Stage | Timing | Primary records | Permitted outcome |
| --- | --- | --- | --- |
| Screen | Before declaring an experiment | Classification notes and background sources | Candidate, ordinary engineering, supporting candidate, insufficient information, or human review |
| Plan | Before execution | Draft experiment YAML | Testable pre-run design |
| Start | When execution actually begins | Active YAML and first execution/evidence rows | `ongoing` |
| Observe | During execution | Execution, results, and evidence CSV rows | Contemporaneous record |
| Evaluate | After observations are available | YAML evaluation and interim/final conclusion | Evidence-based interpretation |
| Close or continue | At the declared boundary | Status, `ended_at` or next actions | Completed state or continuing `ongoing` state |
| Publish | After source validation | Generated TeX and PDF | Reproducible notebook output |

## Stage 1: screen the proposed work

The agent should inspect available issue descriptions, design notes, ADRs, source code, prior tests, technical research, and expert correspondence. It should not treat the absence of information in the immediate conversation as proof that knowledge does not exist.

Capture or request:

- The technical hurdle.
- The specific outcome that is not known.
- The current technical baseline.
- Research already performed.
- Existing methods and why they do not resolve the outcome.
- The competent professionals involved.
- The new knowledge sought.
- The relationship to a defined project and uncertainty.

Stop without creating an active experiment when:

- The outcome follows from documentation or established practice.
- The activity merely confirms that an implementation meets known requirements.
- The unknown is commercial, managerial, legal, or administrative.
- No pre-run hypothesis can be identified.
- Trial and error is proposed without causal criteria.
- The user asks the AI to manufacture justification for work already completed.

## Stage 2: write the pre-run test plan

Create a draft split record named `input/experiments/drafts/experiment.RUN-YYYY-NNN.plan.yaml`. Use a singular `experiment` mapping. The publisher does not scan the `drafts/` subdirectory. Do not place a `.plan.yaml` directly in `input/experiments/`, and do not add execution, result, or evidence CSV rows for future events.

The pre-run record must define:

### Identity

- Stable `id` selected from current repository records.
- Meaningful `title` describing what is tested.
- `project_ref`.
- One or more `uncertainty_refs`.
- Expected participants and roles.

### Technical basis

- `objective`: the precise technical question.
- `background.summary`: known state, research, knowledge gap, and why execution is required.
- `background.research_refs`: identifiers for actual background evidence.
- `hypothesis.statement`: expected causal or technical result.
- `hypothesis.formed_at`: actual time the hypothesis was settled.
- `hypothesis.basis_refs`: evidence supporting the hypothesis.

### Experimental design

- `independent_variables`: what will deliberately change.
- `controlled_variables`: what will remain fixed.
- `observed_variables`: what will be measured or observed.
- `acceptance_criteria`: predeclared conditions supporting the hypothesis.
- `failure_triggers`: conditions rejecting or limiting it.
- `method`: reproducible procedure, environment, build, data, instrumentation, repetitions, and analysis method.

The agent must not create a measurement threshold merely to fill the schema. Thresholds must come from the responsible technical owner and be justified by the technical objective.

## Test structure

The experiment may use automated tests, scripts, benchmarks, fault injection, simulations, controlled deployments, or manual technical procedures. Those are instruments within the experiment; their existence does not by itself make the activity experimental R&D.

For each test case, capture in the method or an associated evidence file:

- Test-case identifier.
- Exact proposition or condition tested.
- Application and dependency versions.
- Environment and configuration relevant to the result.
- Initial state and test data.
- Variable changed.
- Conditions held constant.
- Instrumentation and collection method.
- Execution steps.
- Expected observation under the hypothesis.
- Acceptance and failure criteria.
- Number of planned repetitions, where meaningful.
- Known limitations and invalid-run conditions.

An automated assertion should test an observable consequence of the hypothesis, not merely mirror the implementation. Record both passing and failing assertions. Preserve raw output as evidence rather than pasting large logs into YAML.

## Stage 3: start the run

When execution actually begins:

1. Confirm that the hypothesis and criteria were established before the first experimental action.
2. Set `started_at` to the actual start timestamp with UTC offset.
3. Set `status: ongoing`.
4. Move and rename the plan file to the active form `input/experiments/experiment.RUN-YYYY-NNN.yaml`.
5. Add the first evidence record representing the plan, background material, environment snapshot, or execution output actually available.
6. Add the first execution-log row when the corresponding action occurs.

Do not activate a plan file merely to reserve an ID. An active ongoing run cannot publish until it has at least one execution row, result row, and evidence row plus an interim evaluation and next action.

## Stage 4: capture execution events

Append one row to `input/experiment-execution-log.csv` for each material experimental event:

```csv
run_id,sequence,occurred_at,actor,tool,action,observation,evidence_ref
```

### Field rules

| Field | Capture rule |
| --- | --- |
| `run_id` | Exact YAML experiment ID |
| `sequence` | Next positive integer for this run in this CSV; do not renumber existing history casually |
| `occurred_at` | Actual ISO 8601 time with UTC offset |
| `actor` | Stable person reference or accurately identified executing agent/system |
| `tool` | Tool used, or `not_applicable` only when no tool applies |
| `action` | What was actually done, with enough specificity to distinguish it from the planned method |
| `observation` | Immediate factual observation, not the later overall evaluation |
| `evidence_ref` | Evidence ID owned by this run that substantiates the event |

Add or update an execution row when the underlying event is known. Do not prepopulate future actions as if they occurred. If a correction is necessary, preserve the reason in the evidence trail or change record rather than silently changing history.

Material events commonly include:

- Capturing the starting environment.
- Applying the independent variable.
- Beginning a test case or repetition.
- Triggering a controlled failure.
- Collecting a measurement.
- Discovering an invalid run.
- Restoring the controlled state.
- Ending the planned procedure.

Routine command noise need not become a row. The record should allow a reviewer to reconstruct the experimental progression without becoming an indiscriminate terminal transcript.

## Stage 5: register evidence

Add evidence to `input/experiment-evidence.csv` before another source references it:

```csv
evidence_id,run_id,type,title,location,captured_at,notes
```

### Field rules

| Field | Capture rule |
| --- | --- |
| `evidence_id` | Next unique `EV-NNNN` identifier resolved from current sources |
| `run_id` | Run that owns the evidence |
| `type` | Meaningful category such as `test-plan`, `test-report`, `raw-log`, `metrics-export`, `screenshot`, `research-note`, or `environment-record` |
| `title` | Human-readable description |
| `location` | Stable repository or controlled evidence-repository location |
| `captured_at` | Actual capture time with UTC offset |
| `notes` | What the evidence contains, relevant limitations, or scope |

Evidence should include, where applicable:

- Background research and expert analysis.
- Pre-run plan and hypothesis record.
- Source revision or commit identifier.
- Environment and dependency versions.
- Configuration with secrets removed.
- Input dataset identity and integrity information.
- Test scripts and test-case definitions.
- Raw command output and machine-readable results.
- Logs, traces, screenshots, metrics exports, and provider records.
- Analysis worksheets or notebooks.
- Review or decision records.

The CSV location is a catalogue entry, not proof that the evidence exists. The agent must not claim the evidence was verified unless it opened or otherwise checked the referenced record.

Do not store credentials, private keys, tokens, payment-card data, or prohibited personal data merely to strengthen an evidence record. Redact or use controlled references consistent with the applicable security policy.

## Stage 6: capture results and observations

Append each material observation to `input/experiment-results.csv`:

```csv
run_id,sequence,kind,metric,baseline_value,observed_value,unit,notes,evidence_ref
```

### Field rules

| Field | Capture rule |
| --- | --- |
| `run_id` | Exact YAML experiment ID |
| `sequence` | Next positive integer for this run in this CSV |
| `kind` | `quantitative` or `qualitative` |
| `metric` | What was measured or observed; metrics are experiment-specific |
| `baseline_value` | Declared comparison value, or `not_applicable` with explanatory notes |
| `observed_value` | Actual supplied result; never an expected or desired value |
| `unit` | Required for quantitative results; use `not_applicable` for qualitative results without a unit |
| `notes` | Context, method, limitations, invalidation, or comparison explanation |
| `evidence_ref` | Evidence ID owned by this run that contains or substantiates the observation |

Record individual material observations rather than compressing conflicting measurements into a favourable average. When aggregation is part of the declared analysis, retain raw data as evidence and explain the aggregation method.

Use a qualitative result when the observation is categorical or descriptive. Do not invent a number to make a qualitative observation appear more scientific.

## Stage 7: evaluate without rewriting history

Update `evaluation` only after relevant observations exist. It must:

- Refer to the declared acceptance criteria and failure triggers.
- Explain how varied and controlled conditions relate to observations.
- Separate measurement from inference.
- Address contradictory or unexpected evidence.
- Identify invalid runs, limitations, and unresolved questions.
- Avoid claiming causation that the design cannot support.

If work continues, update `interim_conclusion` and `next_actions`. Keep `status: ongoing` and omit `ended_at`.

An interim conclusion should say:

- What is supported so far.
- What is contradicted so far.
- What cannot yet be concluded.
- What evidence or execution remains necessary.

## Stage 8: close the run

Close a run only when its declared execution boundary has been reached and the available observations have been evaluated.

1. Record the actual `ended_at` timestamp.
2. Select `confirmed`, `rejected`, `mixed`, or `inconclusive` from the evidence—not from the desired commercial outcome.
3. Replace `interim_conclusion` with a final `conclusion`.
4. Explain the relationship between observations and hypothesis.
5. Retain useful `next_actions`, especially for rejected, mixed, or inconclusive runs.
6. Record unexpected behaviour as `provided`, or use `state: no_data` when none was recorded.

Do not close an experiment merely because implementation work ended, a deadline arrived, or tests passed. An `inconclusive` result is appropriate when the evidence cannot resolve the hypothesis.

## Stage 9: start a follow-up run

Create a new run rather than rewriting the old run when:

- The hypothesis changes.
- A new technical mechanism is proposed.
- Acceptance criteria or failure triggers materially change.
- A different environment or scale changes the technical question.
- The prior conclusion produces a new uncertainty.
- New instrumentation is needed to resolve an inconclusive result.

Reference the preceding run in narrative text or supporting evidence until explicit previous/next-run schema fields are added. Never change the preceding run's conclusion to reflect knowledge learned later.

## Stage 10: validate and publish

Before publication, check:

- Exactly one YAML input mode is active.
- Filename ID and `experiment.id` match in split mode.
- Every run has matching rows in all three CSV files.
- Every evidence reference exists and belongs to the same run.
- Sequences are unique positive integers within the run and CSV.
- Hypothesis time does not follow start time.
- Completed execution events fall within the run period.
- Status, conclusion fields, and `ended_at` agree.
- No required field uses an absence marker.
- No example or placeholder values remain.

Run:

```zsh
./publish.zsh
```

Publication success means only that the source contract passed and the PDFs compiled without warnings. It is not a determination of factual sufficiency or R&D eligibility.
