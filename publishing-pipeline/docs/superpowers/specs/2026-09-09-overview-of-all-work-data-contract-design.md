# Overview of All Work Data Contract Design

**Status:** Approved on 2026-09-09.

**Scope:** All changes remain under `publishing-pipeline/`. This design converts
`01_overview_of_all_work.pdf` into the annual technical narrative and navigation
record for the existing seven-document pack.

## Purpose and boundary

Document 01 must give an auditor a coherent annual account of the company, claim
period, platform, technical objective, baseline knowledge, unresolved technical
questions, projects, experimental progression, outcomes, people, evidence, and
work outside the R&D boundary. It summarises and connects authoritative records;
it does not reproduce experiments in full or determine legal eligibility.

The publisher validates structure, chronology, identifiers, relationships, and
absence states. It never invents facts, rewrites supplier records, treats
generated files as evidence, or turns a candidate classification into an
eligibility conclusion.

## Source ownership

| Source | Responsibility | Form |
|---|---|---|
| `claim.yaml` | Company, period, program, ownership and document control | YAML |
| `program.yaml` | Product, objective, scope, baseline, annual synthesis and applicability | YAML |
| `projects.yaml` or `projects/project.<ID>.yaml` | Project narratives and relationships | Combined or split YAML |
| `uncertainties.yaml` or `uncertainties/uncertainty.<ID>.yaml` | Technical knowledge gaps and year state | Combined or split YAML |
| `people.yaml` or `people/person.<ID>.yaml` | People, roles and technical responsibilities | Combined or split YAML |
| `activities.yaml` or `activities/activity.<ID>.yaml` | Candidate, supporting, ordinary and outside-boundary work | Combined or split YAML |
| `program-evidence.csv` | Program-level evidence catalogue | CSV |
| Existing experiment YAML and three CSV files | Authoritative experiment records | Unchanged |
| Existing timesheet and infrastructure CSV files | High-volume resource records | Unchanged |

Combined and split forms for a record type are mutually exclusive. Split files
have a singular top-level mapping, filename IDs must equal internal IDs, template
files and nested draft directories are ignored, and records are merged only in
memory. `program.yaml` is singular and has no split form.

## Stable identifiers

- Project: `RND-YYYY-NN`
- Uncertainty: `UT-NN`
- Experiment: `RUN-YYYY-NNN`
- Person: `P-NNN`
- Evidence: `EV-NNNN`, globally unique across program and experiment catalogues
- Activity: `ACT-YYYY-NNN`

Activity identifiers are classification-neutral. The supplied classification is
one of `candidate_experimental`, `candidate_supporting`, `ordinary_engineering`,
`outside_rnd_boundary`, or `human_review_required`.

## Published sections

| Section | Audit function | State |
|---|---|---|
| Purpose and scope | Defines the overview role and validation/legal boundary | Required controlled copy plus required scope data |
| Company and claim period | Establishes entity, period and document ownership | Required |
| Product or platform | Defines what was developed | Required |
| Technical objective | States capability and new knowledge sought | Required |
| Commercial context | Supplies context without substituting commercial uncertainty | Conditional; reasoned not-applicable allowed |
| Technical baseline and research | Shows prior state, accessible knowledge and approach limitations | Required; optional subcollections explicit |
| Technical uncertainty register | States specific knowledge gaps and their evidence | Repeating; at least one required |
| Project register and narratives | Connects workstreams to uncertainty, experiments, people and evidence | Repeating; at least one required |
| Systematic experimental progression | Chronologically summarises existing experiment records | Derived; at least one required |
| Annual outcomes | Preserves supported, rejected, mixed, inconclusive and ongoing results | Required synthesis plus derived run outcomes |
| Personnel and roles | Resolves every participant to an authoritative person | Repeating; referenced records required |
| Activity and R&D boundary | Separates candidate experiments from routine and excluded work | Required, including explicit outside-boundary content |
| Evidence index | Locates program and experiment evidence | Derived; both catalogues validated |
| Resource-attribution overview | Summarises recorded labour and infrastructure without deciding eligibility | Conditional and derived |
| Limitations and unresolved matters | Prevents the annual record implying false completeness | Required |
| Document control | Identifies owner, review date, evidence repository and version | Required |

The old project template, uncertainty wording prompt, blank checklists, zero-value
cost examples, and instructional copy do not belong in the published PDF.

## Required source mappings

`program.yaml` has a top-level `program` mapping containing:

- `product.name`, `product.description`, `product.development_context`
- `technical_objective.statement`, `technical_objective.new_knowledge_sought`
- `commercial_context`: `provided/content` or `not_applicable/reason`
- `scope.period_start`, `scope.period_end`, `scope.repositories`,
  `scope.included_work_summary`, `scope.outside_boundary_summary`
- `baseline.summary`, `baseline.existing_knowledge`,
  `baseline.approaches_reviewed`, `baseline.prior_internal_work`, and
  `baseline.standards_and_constraints`
- `annual_synthesis.progression_summary`, `knowledge_outcome`,
  `unresolved_matters`, and `limitations`
- `applicability.labour_summary`, `infrastructure_summary`, and
  `contractor_summary`

Every project contains its ID, name, dates, lead, technical focus, business
objective state, technical problem, uncertainty/experiment/activity/contributor/
evidence references, repositories, experimental strategy, annual outcome, and
unresolved matters.

Every uncertainty contains its ID, title, area, statement, reason the outcome
could not be determined, competent-professional basis, new knowledge sought,
background evidence, project references, status, year outcome, and unresolved
aspects.

Every person contains its ID, name, role, engagement type, technical
responsibilities, project/activity references, and optional evidence references.

Every activity contains its ID, title, supplied classification and classification
owner, dates, description, rationale, and project/uncertainty/experiment/person/
evidence references.

`program-evidence.csv` headers are exactly:

```csv
evidence_id,type,title,location,captured_at,period_start,period_end,notes
```

All columns except `notes` are required. Evidence locations are catalogued, not
asserted by the publisher to exist or prove a proposition.

## Experiment summary derivation

Document 01 consumes the normalized result of the existing experiment loader.
It renders ID, title, start date, project, uncertainty references, supplied
status, observation count/kinds, exact conclusion or interim conclusion, notebook
reference, and owned evidence references. It never creates another experiment
summary source, paraphrases conclusions, or reproduces complete methods, designs,
execution logs, or result tables.

Experiment summaries and project child runs sort by parsed `started_at`, then run
ID. Explicit project experiment references must exactly match experiment-owned
project references.

## Absence semantics

`No data provided.` is allowed only for optional prior internal work, additional
standards/constraints, person evidence notes, evidence notes, and supplementary
repository or explanatory notes.

`Not applicable` is allowed only with a non-placeholder reason for commercial
context, a separate project business objective, reviewed absence of prior
internal work or material standards, contractors, labour, or infrastructure.

It is never allowed for the entity/period, product, objective, baseline,
uncertainties, project technical narratives, experimental progression, annual
outcomes, limitations, boundary statement, or required evidence.

## Fail-closed validation

Publication fails before replacing generated TeX or PDFs for missing or
placeholder content, malformed dates/timestamps/IDs, mixed source modes, filename
ID mismatch, duplicate IDs, unknown/orphan/cross-owner references, inconsistent
forward and reverse links, out-of-period records without an explanation, missing
people, missing program evidence, invalid classifications or absence states,
candidate experimental activities without uncertainty and run links, candidate
supporting activities without a linked candidate experiment/run, outside-boundary
activities linked as experiments, undefined template data, any TeX warning, or
forbidden placeholder text in the resulting PDF.

Source validation is structural. It does not verify legal eligibility, factual
truth, evidence sufficiency, or whether the classification owner had authority.

## Deterministic order

- Projects: `period_start`, then ID.
- Uncertainties: first linked project order, then ID.
- Experiments: `started_at`, then run ID.
- People: case-folded name, then ID.
- Activities: `period_start`, then ID.
- Program evidence: `period_start`, `captured_at`, then ID.
- Experiment evidence: experiment order, `captured_at`, then ID.
- Resolved child references: global record order.
- Narrative lists: supplier order.

## Transactional publication

The publisher first validates every source. The shell entrypoints then render and
compile all seven documents in temporary sibling directories. Generated TeX and
PDF destinations are replaced only after every compile succeeds without warnings.
Supplier inputs are never rewritten.

## Documentation and verification

Agent-facing documentation lives under `docs/01-overview-of-all-work/` and
contains a human guide, AI protocol, lifecycle workflow, and reusable task prompt.
All C360 examples are labelled examples and never loaded as evidence.

Automated coverage includes valid combined/split modes, invalid fixtures,
absence states, placeholders, duplicates, chronology, every reference direction,
experiment-summary preservation and order, transactional failure, and dynamic
rendering. Acceptance additionally requires all tests, seven warning-free PDFs,
PDF text checks, and visual inspection of document 01.
