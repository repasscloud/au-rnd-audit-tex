# AI agent protocol for experiment records

## Purpose

This protocol instructs Codex, ChatGPT, Claude, and other AI agents how to assist with an Experiment Notebook record. It applies only to the experiment sources used to publish `02_experiment_notebook.pdf`.

The agent may help identify a candidate technical experiment, structure a pre-run plan, capture supplied observations, maintain source files, and check internal consistency. The agent must not decide that an activity is legally eligible for the Australian R&D Tax Incentive.

Australian Government guidance requires a core R&D activity to address an outcome that cannot be known or determined in advance and can only be determined through a systematic progression of hypothesis, experiment, observation, evaluation, and logical conclusion. Consult current professional advice and authoritative guidance before relying on a record for a claim:

- [Software development sector guide](https://business.gov.au/grants-and-programs/research-and-development-tax-incentive/sector-guides-for-r-and-d-tax-incentive-applicants/software-development)
- [Conducting core R&D activities](https://business.gov.au/grants-and-programs/research-and-development-tax-incentive/check-if-you-are-eligible-for-the-randd-tax-incentive/conducting-core-activities)
- [R&D Tax Incentive record keeping](https://business.gov.au/grants-and-programs/research-and-development-tax-incentive/check-if-you-are-eligible-for-the-randd-tax-incentive/record-keeping-for-the-rd-tax-incentive)

## Authority and evidence rules

The human-supplied record and referenced evidence are authoritative. The AI agent is an assistant, not an evidence source or claim approver.

The agent must:

- Preserve the distinction between known facts, supplied assertions, observations, and inference.
- Use exact timestamps from the underlying activity or evidence where available.
- State when a timestamp is unknown; never estimate one to satisfy the schema.
- Preserve failed, rejected, mixed, inconclusive, and unexpected outcomes.
- Keep the hypothesis and pre-run criteria separate from results learned later.
- Link every result and execution event to evidence owned by the same run.
- Use stable repository paths, report identifiers, log locations, or controlled evidence-repository locations.
- Identify missing information and ask the responsible human rather than complete it speculatively.
- Treat current source files and evidence as potentially incomplete until checked.
- Run the publisher after changes and report validation failures exactly.

The agent must never:

- Declare that an activity qualifies for an R&D tax claim.
- Create a technical uncertainty merely because work was difficult, new to the team, or commercially novel.
- Present routine implementation, configuration, testing, debugging, refactoring, deployment, compliance, or UAT as an experiment without a genuine technical knowledge gap.
- Invent background research, expert opinion, experimental actions, measurements, evidence, people, dates, durations, costs, or conclusions.
- Backdate a hypothesis or rewrite acceptance criteria after results are known.
- Change an unsuccessful result to make the experiment appear successful.
- Use passing automated tests as proof that the underlying activity was experimental.
- Treat generated TeX or PDF text as primary evidence of what occurred.
- overwrite user-authored data without first inspecting and preserving unrelated records.

## Initial classification

Before creating an experiment record, the agent must classify the proposed work as one of:

| Classification | Meaning | Agent action |
| --- | --- | --- |
| `candidate_experiment` | A specific technical outcome may be indeterminable in advance and a hypothesis-led test is possible | Prepare a pre-run plan, clearly subject to human and professional review |
| `ordinary_engineering` | The outcome can be determined using established knowledge, documentation, standard testing, or normal professional skill | Do not create an experiment record; explain the engineering classification |
| `supporting_candidate` | The work directly supports a separately identified candidate experiment but is not itself the experiment | Record the relationship for later claim mapping; do not mislabel it as a run |
| `insufficient_information` | The agent cannot establish the uncertainty, chronology, method, or evidence boundary | Ask targeted questions and do not create a completed record |
| `human_review_required` | Legal eligibility, ownership, evidence sufficiency, or claim scope requires accountable human judgment | Preserve facts and escalate the decision |

The agent must answer these questions before using `candidate_experiment`:

1. What precise technical outcome is unknown?
2. Why could a competent professional not determine that outcome in advance using reasonably accessible knowledge, information, or experience?
3. What background research supports the claimed knowledge gap?
4. What new technical knowledge is the activity intended to generate?
5. What testable hypothesis existed or will exist before execution?
6. What procedure changes one or more defined variables while controlling relevant conditions?
7. What will be observed or measured?
8. What result could reject or materially limit the hypothesis?

If the answers only establish uncertainty about schedules, cost, customer preference, commercial success, legal approval, supplier selection, implementation effort, or whether ordinary code contains defects, classify the work as `ordinary_engineering` or `human_review_required`.

## Experiment boundary

Define one run narrowly enough that it has:

- One stable run ID.
- One pre-run hypothesis or a tightly related set of statements.
- One declared method and controlled context.
- A bounded execution period.
- Observations that can be evaluated together.
- One conclusion or interim conclusion.

Do not combine unrelated technical questions into one run. Create a later run when the first run changes the hypothesis, method, important variables, acceptance criteria, or evidence needed to reach a conclusion.

A repeated execution using the same hypothesis and method may be another result or execution event in the same run when it is part of the planned procedure. It should become a new run when it tests a revised technical proposition or materially different experimental design.

## File ownership

Use one YAML input mode only:

- Combined mode: `input/experiments.yaml` with an `experiments` list.
- Split mode: `input/experiments/experiment.RUN-YYYY-NNN.yaml` with one `experiment` mapping per file.

Split mode is preferred for agent-maintained records because it limits each change to one experimental run. The filename ID must exactly match `experiment.id`.

The agent may update only these experiment sources unless the user expands the scope:

- The selected experiment YAML source.
- `input/experiment-results.csv`.
- `input/experiment-execution-log.csv`.
- `input/experiment-evidence.csv`.

The agent must not edit `generated/` or `output/` directly.

## Record states

### Planned but not started

Create the YAML record only after the required pre-run information is supported. Do not add execution or result rows for work that has not occurred. The current pipeline has no `planned` status, so do not publish a planned-only run as though it were ongoing.

If a planned record must be retained before execution, keep it in the non-active drafts subdirectory, for example:

```text
input/experiments/drafts/experiment.RUN-2026-014.plan.yaml
```

The publisher does not scan that subdirectory. Move and rename the file to `input/experiments/experiment.RUN-2026-014.yaml` when execution begins and the active run has the required CSV records. A `.plan.yaml` placed directly in `input/experiments/` is rejected as an invalid active filename.

### Ongoing

Use `status: ongoing` only after experimental execution has begun. An ongoing published run requires:

- At least one execution entry.
- At least one result or observation.
- At least one evidence record.
- An evaluation of the observations available so far.
- An `interim_conclusion` explaining what is and is not established.
- At least one specific `next_actions` item.
- No `ended_at`.

### Completed

Use `confirmed`, `rejected`, `mixed`, or `inconclusive` only after the declared execution and evaluation are complete. A completed run requires `ended_at` and `conclusion`.

Status describes the relationship between observations and hypothesis:

- `confirmed`: supplied observations support the hypothesis within the declared scope.
- `rejected`: supplied observations contradict it.
- `mixed`: different observations support and contradict material parts.
- `inconclusive`: available observations cannot resolve it.

## Safe update rules

Before every write, the agent must:

1. Read the current YAML record and all CSV rows for the run.
2. Inspect repository status and preserve unrelated user changes.
3. Resolve the next unused run ID, evidence ID, and per-file sequence number from current sources; never guess from memory.
4. Check that referenced evidence exists or will be added in the same change.
5. Explain any inference and obtain human confirmation when it materially affects the record.

After every write, the agent must:

1. Re-read the changed YAML and CSV rows.
2. Confirm IDs, sequences, timestamps, and evidence references match.
3. Run the pipeline tests or publication command appropriate to the request.
4. Report whether publication succeeded, failed, or was not run.
5. Never claim that a new PDF contains the changes unless the publication command succeeded and the PDF content was checked.

## Required agent report

At the end of an experiment-capture task, report:

- Classification and rationale.
- Human/professional decisions still required.
- Run ID and lifecycle status.
- YAML file created or updated.
- CSV rows added or updated in each file.
- Evidence identifiers and locations referenced.
- Missing or unverified facts.
- Validation or publication result.
- Whether the PDF content was checked.
