# Published PDF Data Contract Design

**Status:** Design approved. The experiment-notebook slice was implemented after separate approval; the other six document conversions remain planned work.

**Scope:** Everything described here lives under `publishing-pipeline/`. The seven PDFs retain their existing names. This document defines their responsibilities, proposed input ownership, rendering rules, and validation boundaries.

## 1. Objective

Replace instructional prose, sample rows, blank forms, and bracketed placeholders in the seven generated PDFs with traceable supplier data, derived values, or an explicit and honest absence statement. The publisher must never make a missing required record look complete.

The experiment notebook is the first implementation slice. The remaining six outputs are documented here so their future data contracts remain compatible with it.

## 2. Evidence basis and boundary

Current Australian Government guidance says R&D records should be created while activities occur, link activities to expenditure, and show what was done, how and when it was done, who did it, and what resources were used. For core activity, the systematic progression comprises hypothesis, experiment, observation, evaluation, and logical conclusions. This pipeline can validate the presence, structure, chronology, and cross-references of records; it cannot determine legal eligibility or whether a narrative is factually sufficient.

Authoritative references used for this design:

- [Record keeping for the R&D Tax Incentive](https://business.gov.au/grants-and-programs/research-and-development-tax-incentive/check-if-you-are-eligible-for-the-randd-tax-incentive/record-keeping-for-the-rd-tax-incentive)
- [Conducting core R&D activities](https://business.gov.au/grants-and-programs/research-and-development-tax-incentive/check-if-you-are-eligible-for-the-randd-tax-incentive/conducting-core-activities)
- [Helping you get R&D claims right](https://www.ato.gov.au/Business/Research-and-development-tax-incentive/Helping-you-get-R-D-claims-right/)

The required/optional classifications below are publication-integrity rules for this document set. They are not a legal opinion that a field alone proves eligibility.

## 3. Common publication model

### 3.1 Source ownership

`input/claim.yaml` remains the authoritative source for document-level identity and control metadata shared across all outputs. Each PDF also gets one authoritative domain source, with CSV used for high-volume rows and YAML used for narratives, policy, relationships, and configuration.

| Source | Primary owner | Main consumers |
|---|---|---|
| `input/claim.yaml` | Shared document identity and control | All seven PDFs |
| `input/program.yaml` | Program, project, uncertainty, people, and program evidence narratives | 01, 07 |
| `input/experiments.yaml` | Experiment narratives, chronology, conditions, analysis, and conclusions | 01, 02, 03, 07 |
| `input/experiment-results.csv` | Repeatable result/observation summary rows | 02 |
| `input/experiment-execution-log.csv` | Repeatable chronological execution entries | 02 |
| `input/experiment-evidence.csv` | Evidence references linked to runs | 02, 03, 04, 07 |
| `input/activities.yaml` | Core, supporting, and excluded activity narratives | 03, 07 |
| `input/activity-evidence.csv` | Cross-reference rows between activity, experiment, people, cost, and evidence records | 03, 07 |
| `input/repositories.yaml` | Repository identity, scope, period, and import configuration | 04 |
| `input/commit-evidence.csv` | Curated material commit interpretations | 04 |
| `input/people.yaml` | Roles, engagement type, approvals, and cost schedule references | 01, 05, 07 |
| `input/timesheets.csv` | High-volume labour activity rows | 01, 03, 05, 07 |
| `input/cost-allocation.yaml` | Allocation methods, cost pools, preparers, and review data | 06, 07 |
| `input/infrastructure-costs.csv` | High-volume infrastructure and tooling cost rows | 01, 03, 06, 07 |
| `input/claim-pack.yaml` | Annual summaries, registration/governance statements, contractor and other-cost schedules, declarations | 07 |

This is the target map, not a requirement to introduce every file in the experiment slice.

### 3.2 Section-state contract

The renderer must use a central section policy rather than scattered template-specific booleans.

| Policy | Missing/empty input | PDF behavior |
|---|---|---|
| `required` | Publication fails with source path and field name | No PDF is produced |
| `conditional` + `applicable` | Publication fails if content is empty | Content is rendered |
| `conditional` + `not_applicable` | A non-empty reason is required | `Not applicable — <reason>` is rendered |
| `optional` | Accepted | `No data provided.` is rendered |
| `repeating` | Depends on the collection's requiredness | One generated block per item |
| `derived` | Source values or links are invalid | Publication fails rather than displaying an invented total or index |

Hard lines:

- A required section cannot expose a supplier-controlled off switch.
- A section is never silently omitted.
- `not_applicable` is allowed only for fields declared conditional by the schema and requires an explanation.
- `No data provided.` means applicable but no optional information was supplied. It must not be used for a required field.
- Placeholder-looking active values such as `[Name]`, `[Date]`, `xxx`, or `TBD` fail final publication validation.
- The renderer must not infer facts, eligibility, causal explanations, measurements, approvals, or evidence that the sources do not state.
- Empty collections that would falsely imply no relevant activity fail if their parent document requires at least one record.

### 3.3 Cross-document identifiers

Stable IDs are the join contract:

- project: `RND-YYYY-NN`
- uncertainty: `UT-NN`
- experiment: `RUN-YYYY-NNN`
- core activity: `CORE-NN`
- supporting activity: `SUP-NN`
- evidence: `EV-NNNN`
- person: a stable internal `person_id`, not the display name
- cost row: `COST-YYYY-NNNN`

The validator checks uniqueness and that every reference resolves. Display names may change; identifiers may not be reused within a claim period.

### 3.4 Deterministic output

- Dates use ISO `YYYY-MM-DD`; timestamps include an offset.
- Experiments sort by `started_at`, then `id`.
- Execution log entries sort by timestamp, then sequence.
- Timesheets sort by person, week, date, then source order.
- Costs sort by month, category, then stable ID.
- Derived totals use decimal arithmetic and declared rounding rules.
- Rebuilding unchanged inputs produces substantively identical TeX. A separately displayed generation timestamp is permitted but is not source evidence.

## 4. PDF responsibilities and data needs

### 4.1 `01_overview_of_all_work.pdf`

**Purpose:** The annual technical narrative and navigational overview. It explains the program baseline, uncertainties, project structure, high-level experiment outcomes, people, evidence, and expenditure attribution without duplicating the detailed supporting records.

**Required:** product/platform description; technical program objective; pre-program technical baseline/background research; at least one uncertainty; at least one project; each project's technical problem, hypothesis/strategy, and year outcome; experiment summary derived from valid runs; evidence index; boundary/exclusion statement; resolvable project/uncertainty/run references.

**Conditional:** commercial context may be marked not applicable only with a reason; personnel and expenditure summaries are required when the annual pack declares those categories; contractor sections appear as not applicable with a reason when no contractors were used.

**Optional:** additional standards, third-party constraints, prior prototypes, and explanatory evidence notes. Empty optional content renders `No data provided.`

**Derived/repeating:** uncertainty register, project register and narratives, annual experiment register, people allocation summary, expenditure summaries, and evidence index.

**Example:** a project record identifies `RND-2026-01`, links `UT-01`, describes the baseline, and references runs `RUN-2026-001` through `RUN-2026-004`. The overview renders one project narrative and a concise outcome row for each run.

### 4.2 `02_experiment_notebook.pdf`

**Purpose:** The chronological, audit-readable record of independent experimental runs. It demonstrates the actual progression from hypothesis through method, observation, evaluation, conclusion, and next action without rewriting failed or mixed outcomes.

**Document behavior:** Generate one notebook index followed by one complete run chapter per experiment. Remove the current instructional template and blank pages from the published PDF. Instructional material belongs in source documentation, not the evidence output.

**Required for every run:** stable ID; title; start date/time; engineers; project and uncertainty references; technical objective; pre-run background and basis; a pre-run testable hypothesis; experimental design/conditions; exact method; at least one execution entry; at least one observation/result; evaluation/interpretation; status; and evidence references. A completed run also requires a logical conclusion. An ongoing run requires an interim evaluation and an explicit statement of what remains unresolved.

**Conditional:** end date for completed runs; baseline/control when the method relies on comparison; unexpected behavior; repository, branch, environment, ticket, and next-run link. Each conditional item can be marked not applicable only where the schema permits and with a reason.

**Optional:** supplementary notes and additional attachments. Their absence is displayed explicitly.

**Dynamic results:** metric names are never fixed. A run can record latency, accuracy, memory, recovery behavior, correctness, a qualitative observation, or any other measurement relevant to its hypothesis. Each row identifies its kind, observed value, unit where meaningful, comparison/control where applicable, interpretation note, and evidence reference. The table must adapt to the supplied metrics rather than render the example latency/throughput rows.

**Chronology:** runs sort by `started_at`, then ID. The generated index uses the same order. `previous_run_id` and `next_run_id` links express the investigative chain but do not override chronological order.

**Example YAML narrative:**

```yaml
experiments:
  - id: "RUN-2026-001"
    title: "Evaluate queue recovery after worker interruption"
    project_ref: "RND-2026-01"
    uncertainty_refs: ["UT-01"]
    started_at: "2026-07-14T09:30:00+09:30"
    ended_at: "2026-07-14T12:10:00+09:30"
    status: "mixed"
    engineers:
      - person_ref: "P-001"
        role: "experiment lead"
    objective: "Determine whether interrupted deliveries resume without duplication."
    background:
      summary: "The prototype persisted work state but recovery behavior under process loss was unknown."
      research_refs: ["EV-0001"]
    hypothesis:
      statement: "Persisting the operation identifier before dispatch will allow restart without creating a second provider submission."
      formed_at: "2026-07-13T16:20:00+09:30"
      basis_refs: ["EV-0001", "EV-0002"]
    design:
      independent_variables: ["worker interruption point"]
      controlled_variables: ["build version 2026.07.14.1", "single test tenant"]
      observed_variables: ["submission count", "terminal state", "recovery duration"]
      acceptance_criteria: ["one provider submission", "durable terminal state"]
      failure_triggers: ["duplicate submission", "lost queued record"]
    method: "Run each defined interruption point against an isolated test queue and reconcile persisted and provider states."
    evaluation: "Recovery preserved queued work, but one interruption window remained ambiguous because the provider exposed no idempotent acceptance key."
    conclusion: "The hypothesis was only partly supported; durable recovery worked, but duplicate-prevention could not be established for the ambiguous window."
    next_actions:
      - "Test a provider with idempotent acceptance semantics."
    unexpected_behaviour:
      state: "provided"
      content: "Provider activity lagged the local terminal state by up to 40 seconds."
```

**Example result rows:**

```csv
run_id,sequence,kind,metric,baseline_value,observed_value,unit,notes,evidence_ref
RUN-2026-001,1,quantitative,provider submissions,1,1,count,No duplicate in measured interruption windows,EV-0010
RUN-2026-001,2,quantitative,recovery duration,not_applicable,18,seconds,No historical control existed; acceptance threshold was 30 seconds,EV-0011
RUN-2026-001,3,qualitative,ambiguous acceptance window,absent,present,state,Provider capability prevented a definitive negative inference,EV-0012
```

### 4.3 `03_claim_mapping_register.pdf`

**Purpose:** The traceability matrix between claimed core/supporting activities and uncertainties, experiments, engineering evidence, people, costs, and explicitly excluded work.

**Required:** at least one core activity; core activity description and rationale; uncertainty and notebook references; supporting activity relationship/rationale when supporting activities are claimed; cross-reference rows; core/supporting boundary narrative; every referenced item resolves.

**Conditional:** supporting activities and their dominant-purpose explanation when applicable; exclusion/reduction rows when such work occurred. If no supporting activities are claimed, render `Not applicable` with the supplied reason rather than a blank table.

**Optional:** extra comments on cross-reference rows. Missing comments render `No data provided.` only in the notes cell.

**Derived/repeating:** one row per core activity, supporting activity, exclusion, and cross-reference.

**Example:** `CORE-01` links `UT-01`, runs `RUN-2026-001` and `RUN-2026-002`, engineers `P-001/P-002`, and evidence `EV-0010`. `SUP-01` links directly to `CORE-01` and explains why its test-data preparation was required for those runs.

### 4.4 `04_git_evidence_appendix.pdf`

**Purpose:** A repository chronology and curated interpretation appendix. It supports, but never substitutes for, the experiment notebook and other evidence.

**Required:** at least one repository when source-code evidence is claimed; repository identity, scope, reporting period, resolved evidence import or structured commit rows, and a clear link from material commits to project/run references.

**Conditional:** repositories that do not exist are not rendered as four hard-coded missing imports; repository kinds are data-driven. A repository configured as expected must have its evidence file or publication fails. A genuinely inapplicable repository type is simply absent from the repeating collection, with a document-level statement explaining repository coverage.

**Optional:** curated material-commit commentary beyond the imported chronology. If none is supplied, render `No data provided.`

**Derived/repeating:** one repository section per configured repository; one material-commit row per curated record.

**Example:** repository `repo-main` points to a generated evidence file and declares project scope `RND-2026-01`; commit `a1b2c3d` links to `RUN-2026-001` with an explanation of why the change materially relates to the experiment.

### 4.5 `05_engineer_weekly_timesheets.pdf`

**Purpose:** A generated weekly labour-allocation record grouped by person and week, including eligible and non-eligible work and approval status.

**Required:** every row has person, date, project/run reference where applicable, category, positive hours, and a specific work description; every person resolves to role/engagement metadata; category totals are derived; claimed weeks require an approval state.

**Conditional:** a project/run reference may be not applicable for non-R&D rows with a reason; manager approval may be pending in a draft publication but blocks final publication for claimed weeks.

**Optional:** weekly notes. Missing notes render `No data provided.`

**Derived/repeating:** one weekly sheet per person per week; sorted daily entries; core/supporting/non-R&D totals; total hours; approval display. Remove the blank Week 1/Week 2 forms from published output.

**Example:** five rows for `P-001` in week commencing `2026-07-13` generate one sheet, category totals, and the approver recorded in `people.yaml` or a dedicated weekly approval record.

### 4.6 `06_infrastructure_cost_worksheets.pdf`

**Purpose:** Reproducible monthly infrastructure/tool cost allocation, the rationale and evidence supporting apportionment, and a derived annual roll-up.

**Required:** allocation method statement; stable cost row ID; month; item/category; provider; total cost; allocation percentage; calculated eligible amount; allocation basis; evidence reference; preparer; and internally consistent arithmetic.

**Conditional:** shared-tooling section when licences/tools exist; a zero percent row is permitted but must retain its allocation reasoning. A configured cost pool requires its source evidence.

**Optional:** additional notes. Empty notes render `No data provided.`

**Derived/repeating:** monthly sections, rows, category totals, and annual totals. Input `eligible_amount` should ultimately become derived rather than independently trusted; until that migration, validation must require it to equal the calculation.

**Example:** a July cloud invoice is split into tagged experimental compute and non-R&D production rows, each linking the invoice and tag export used for the percentage.

### 4.7 `07_annual_claim_pack.pdf`

**Purpose:** The annual assembly and management-review pack. It summarizes and cross-references validated content from the other six outputs plus annual governance and expenditure sources.

**Required:** company/program summary; uncertainties and knowledge gained; claim period and governance; at least one project; detailed project narratives derived from program/experiment sources; core activity summary; exclusion boundary; annual evidence index; cost roll-up; technical and finance review records; final approval for final publication.

**Conditional:** supporting activities, employees, contractors, infrastructure/software, and other eligible cost categories appear when declared applicable. An absent category renders `Not applicable — <reason>`, never a fabricated zero row. Draft publication can show a clearly labelled pending approval; final publication cannot.

**Optional:** supplementary executive narrative and evidence notes. Missing values render `No data provided.`

**Derived/repeating:** project portfolio and detail sections, experiment knowledge summary, personnel and cost schedules, expenditure totals, evidence index, and cross-document references. Derived totals must reconcile to their source schedules before publication.

**Example:** `RND-2026-01` is rendered from `program.yaml`; its experiment summary is derived from runs linked to the project; employee totals derive from approved timesheets and cost inputs; infrastructure totals derive from document 06's validated rows.

## 5. Experiment-notebook target contract

### 5.1 Initial source files

The first implementation keeps narrative ownership in the existing `input/experiments.yaml` and adds three normalized CSV files:

1. `input/experiments.yaml` — one complete narrative record per run.
2. `input/experiment-results.csv` — dynamic quantitative or qualitative observations.
3. `input/experiment-execution-log.csv` — timestamped or sequenced actions/observations.
4. `input/experiment-evidence.csv` — typed evidence references and locations.

Splitting each run into a separate YAML file is deferred until file volume demonstrates a need. One source avoids manifest ordering, duplicate notebook configuration, and cross-file partial records while still supporting many experiments.

### 5.2 Requiredness by notebook section

| PDF section | Policy | Source |
|---|---|---|
| How to use this notebook | Static guidance, shortened | Template |
| Notebook index | Derived and required | All valid experiments |
| Administrative details | Required | Experiment YAML |
| Technical objective | Required | Experiment YAML |
| Background | Required | Experiment YAML |
| Hypothesis | Required | Experiment YAML |
| Variables and conditions | Required as a design block; individual lists may be conditionally not applicable with reasons | Experiment YAML |
| Method | Required | Experiment YAML |
| Execution log | Required repeating, at least one row | Execution CSV |
| Results/observations | Required repeating, at least one row | Results CSV |
| Unexpected behavior/failure modes | Optional explicit state | Experiment YAML |
| Interpretation/evaluation | Required | Experiment YAML |
| Conclusion | Required for completed runs; interim conclusion required for ongoing runs | Experiment YAML |
| Next action | Conditional; required for ongoing/unresolved runs | Experiment YAML |
| Evidence attachments | Required repeating, at least one resolvable reference | Evidence CSV |
| Blank run pages | Removed | Not applicable |

### 5.3 Status model

Allowed `status` values are `confirmed`, `rejected`, `mixed`, `inconclusive`, and `ongoing`. This status describes the relationship between observations and hypothesis; it is not an R&D eligibility decision. Completed states require `ended_at` and `conclusion`. `ongoing` forbids a final `ended_at`, requires `interim_conclusion`, and requires at least one next action.

### 5.4 CSV contracts

`experiment-results.csv` headers:

```text
run_id,sequence,kind,metric,baseline_value,observed_value,unit,notes,evidence_ref
```

`kind` is `quantitative` or `qualitative`. `metric`, `observed_value`, and `evidence_ref` are required. `baseline_value` may be `not_applicable` only when notes explain why no comparison is relevant. `unit` is required for quantitative rows and may be `not_applicable` for qualitative rows.

`experiment-execution-log.csv` headers:

```text
run_id,sequence,occurred_at,actor,tool,action,observation,evidence_ref
```

`run_id`, positive integer `sequence`, `occurred_at`, `actor`, `action`, and `observation` are required. `tool` may be `not_applicable`; `evidence_ref` is required so the row remains traceable.

`experiment-evidence.csv` headers:

```text
evidence_id,run_id,type,title,location,captured_at,notes
```

All fields except `notes` are required. Locations are references, not automatically trusted proof that remote resources exist. Local paths declared as locally verifiable should be checked for existence; remote references should be structurally validated and clearly labeled as not content-verified.

### 5.5 Validation and messages

Validation happens before any generated file is overwritten. Errors include the source filename, run ID or row number, and field. Examples:

- `experiments.yaml run RUN-2026-001 requires hypothesis.statement`
- `experiment-results.csv row 4 references unknown run_id RUN-2026-099`
- `experiment-execution-log.csv run RUN-2026-001 requires at least one row`
- `experiments.yaml run RUN-2026-002 status ongoing requires interim_conclusion`
- `experiment-evidence.csv row 3 references duplicate evidence_id EV-0010`

Final-mode validation rejects instructional placeholders. Draft-mode support is not part of the first implementation because the current command publishes audit-facing PDFs; adding draft output later must use unmistakable watermarking and must never weaken final rules.

### 5.6 Rendering behavior

- The notebook index is generated from the same normalized experiment records as the run sections.
- Each run begins on a new page and uses its ID and title in the heading.
- Long tables use `xltabular` and repeat headers across page breaks.
- Empty optional text uses one shared `RDNoData` macro with the exact copy `No data provided.`
- Conditional non-applicability uses one shared `RDNotApplicable{reason}` macro.
- Required content is rendered only after validation, so templates do not contain fallback text for it.
- Supplier strings remain LaTeX-escaped. Controlled renderer fragments such as table row separators are built by templates, never accepted from source input.

## 6. Delivery sequence

1. Implement and verify the experiment notebook contract without changing the other six PDF bodies.
2. Convert the overview and claim-mapping register together because they share project, uncertainty, run, and activity references.
3. Convert timesheets and infrastructure worksheets, including derived totals and approval/allocation validation.
4. Convert the git appendix and evidence resolution model.
5. Convert the annual claim pack last so it assembles validated data instead of duplicating independent narratives.
6. Remove obsolete placeholder macros and static instructional rows only after all consumers migrate.

Each slice must preserve the seven-output build, add negative validation tests, compile all PDFs without Tectonic warnings, and scan generated TeX/PDF text for forbidden placeholder markers.

## 7. Acceptance criteria for the experiment slice

- Two or more experiments produce one index and one chronologically ordered section per run.
- Different runs can use completely different metrics without template changes.
- Required missing hypothesis, method, observations, evaluation, conclusion/interim conclusion, or evidence blocks publication.
- Optional missing content renders `No data provided.`
- Conditional non-applicability renders a reason and cannot be used on required sections.
- No example metric rows, blank-run pages, bracketed prompts, or instructional completion prose remain in `02_experiment_notebook.pdf`.
- Unknown/duplicate IDs, invalid chronology, invalid statuses, orphan CSV rows, and malformed timestamps fail with actionable messages.
- Evidence IDs resolve within the experiment slice. Project, uncertainty, and person references are syntax-checked in this slice and become resolution-checked when their authoritative sources are implemented.
- All supplier content is LaTeX-safe.
- Existing shared metadata still appears.
- All automated tests pass and all seven PDFs compile without warnings.

## 8. Explicitly deferred decisions

These choices do not block the experiment implementation plan:

- Whether a later version supports visibly watermarked draft PDFs.
- Whether high-volume projects eventually split one YAML file into one file per run.
- Whether remote evidence locations are verified through authenticated connectors.
- The authoritative project, uncertainty, and people source schemas; until those later slices exist, experiment references to those domains are validated by ID shape rather than lookup.
- The legal or tax review that determines whether supplied facts substantiate an actual R&DTI claim.
