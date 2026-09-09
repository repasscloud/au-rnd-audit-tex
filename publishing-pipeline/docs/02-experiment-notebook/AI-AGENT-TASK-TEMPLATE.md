# Reusable AI agent task for experiment capture

## How to use this prompt

Copy the task below into Codex, ChatGPT, Claude, or another capable AI agent. Replace the bracketed task context with the real work under consideration. Give the agent read access to the relevant repository and evidence sources, but do not provide secrets or prohibited personal information.

The prompt intentionally prevents the agent from manufacturing a retrospective R&D narrative. It asks the agent to assist with classification and record keeping while leaving legal eligibility and evidence ownership with accountable humans.

## Agent task

```text
You are assisting with an Australian R&D Experiment Notebook record.

Read and follow these repository instructions before taking action:

1. publishing-pipeline/docs/02-experiment-notebook/AI-AGENT-PROTOCOL.md
2. publishing-pipeline/docs/02-experiment-notebook/EXPERIMENT-CAPTURE-WORKFLOW.md
3. publishing-pipeline/docs/02-experiment-notebook/README.md

Scope:

- Work only within the repository paths explicitly provided by the user.
- For publication data, modify only the selected experiment YAML source and the three experiment CSV files unless the user expands the scope.
- Never edit publishing-pipeline/generated or publishing-pipeline/output directly.

Proposed technical work:

[Describe the technical hurdle, proposed work, relevant project, and available evidence here.]

Your first task is classification, not file creation.

Classify the work as exactly one of:

- candidate_experiment
- ordinary_engineering
- supporting_candidate
- insufficient_information
- human_review_required

For a candidate experiment, establish from available records:

- the precise technical outcome that cannot be known or determined in advance;
- why reasonably accessible knowledge, information, experience, documentation, or standard professional practice cannot determine it;
- the new technical knowledge sought;
- the background research and evidence supporting the knowledge gap;
- the pre-run testable hypothesis;
- the independent, controlled, and observed variables;
- the acceptance criteria and failure triggers;
- the reproducible method;
- what result could reject or materially limit the hypothesis.

Do not treat complexity, novelty to the team, implementation difficulty, defects, passing tests, commercial uncertainty, or lack of immediate documentation as proof of experimental R&D. Do not decide legal R&D eligibility.

Before writing files, report:

1. Your classification and evidence-based rationale.
2. Facts you verified and their sources.
3. Assumptions or inferences.
4. Missing facts.
5. Questions requiring the technical owner, evidence owner, or R&D adviser.
6. Whether the work is pre-run, ongoing, or already completed.

If the work is ordinary engineering, supporting only, or insufficiently supported, do not create a completed experiment record. Explain what is missing or why it is not an experiment.

If a candidate experiment is approved for capture, inspect all current experiment YAML and CSV sources before selecting identifiers. Preserve unrelated user changes.

Prefer split-file mode:

publishing-pipeline/input/experiments/experiment.RUN-YYYY-NNN.yaml

The file must use:

experiment:
  id: RUN-YYYY-NNN

The filename ID and internal ID must match. Never use split mode while publishing-pipeline/input/experiments.yaml is active.

Before execution:

- Draft the identity, technical objective, background, evidence references, hypothesis, hypothesis formation time, experimental design, method, engineers, and intended observations.
- Obtain human confirmation of the knowledge gap, hypothesis, criteria, method, participants, timestamps, and evidence.
- Do not invent thresholds, actions, evidence, or timestamps.
- Keep a not-yet-started draft under publishing-pipeline/input/experiments/drafts/ using experiment.RUN-YYYY-NNN.plan.yaml. Never put a .plan.yaml directly in the active experiments directory.

When execution actually begins:

- Rename the approved plan to experiment.RUN-YYYY-NNN.yaml.
- Set the actual started_at timestamp and status: ongoing.
- Add only actions that actually occurred to experiment-execution-log.csv.
- Register actual evidence in experiment-evidence.csv before referencing it.
- Add actual quantitative or qualitative observations to experiment-results.csv.

Structure tests and procedures so the record identifies:

- test-case identifier;
- source revision and relevant versions;
- environment and initial state;
- test data;
- deliberately changed variable;
- controlled conditions;
- instrumentation;
- exact procedure;
- expected observation under the hypothesis;
- acceptance and failure criteria;
- repetitions, limitations, and invalid-run conditions.

For every material execution event, append:

run_id,sequence,occurred_at,actor,tool,action,observation,evidence_ref

For every material result, append:

run_id,sequence,kind,metric,baseline_value,observed_value,unit,notes,evidence_ref

For every evidence item, append:

evidence_id,run_id,type,title,location,captured_at,notes

Resolve the next IDs and sequence numbers by reading current sources. Do not guess them from memory. Every result and execution row must reference evidence owned by the same run.

During an ongoing run:

- Update evaluation only from observations already captured.
- Maintain interim_conclusion stating what can and cannot yet be concluded.
- Maintain at least one specific next_actions item.
- Do not add ended_at.

When execution and evaluation are complete:

- Add the actual ended_at timestamp.
- Select confirmed, rejected, mixed, or inconclusive from the evidence.
- Replace interim_conclusion with a logical final conclusion.
- Preserve failures, contradictory evidence, limitations, and unexpected behaviour.
- Start a new run instead of rewriting history when the hypothesis or material design changes.

After editing:

- Re-read every changed record.
- Check IDs, chronology, sequences, evidence ownership, required fields, and lifecycle rules.
- Run publishing-pipeline/publish.zsh when the environment supports it.
- If publication succeeds, inspect 02_experiment_notebook.pdf for the run ID, title, observations, evaluation, and conclusion.
- Report exact validation failures rather than hiding or working around them.

Your final report must state:

- classification;
- run ID and status;
- files and rows changed;
- evidence referenced;
- facts not verified;
- human decisions still required;
- test or publication result;
- whether the PDF was inspected.

Never claim that the agent, the pipeline, or a passing build has established legal R&D eligibility.
```

## Suggested human input block

Providing this block with the task reduces speculation:

```text
Technical owner:
Project reference:
Uncertainty reference:
Proposed technical question:
Known technical baseline:
Background research locations:
Why existing knowledge cannot determine the outcome:
New knowledge sought:
Proposed hypothesis:
Proposed method:
Variables to change:
Conditions to control:
Observations to collect:
Acceptance criteria:
Failure triggers:
Expected participants and roles:
Evidence repository:
Intended start time and timezone:
```

Leave an item blank when it is unknown. The agent should ask for missing material rather than infer an answer.
