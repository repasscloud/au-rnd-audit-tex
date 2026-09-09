# 03 Claim Mapping Register authoring guide

## Purpose

Document 03 is a concise traceability matrix. It connects supplier-authored
activity classifications to projects, uncertainties, experiment runs, people,
observations, evidence, recorded effort, infrastructure/tooling, exclusions, and
accountable review. It does not determine legal R&D eligibility and does not
repeat the narratives in documents 01 or 02.

## Exact mappings

| Output | Source fields |
| --- | --- |
| Project index | project `id`, `name`, `uncertainty_refs`, `experiment_refs` |
| Experimental activities | activity identity, classification, description, rationale, uncertainty/run/person/evidence refs |
| Supporting activities | activity fields plus `supports_activity_refs` and `supports_experiment_refs` |
| Experiment trace | experiment project, uncertainty, engineers, results sequence, evidence and status; activity run refs |
| Recorded effort | enhanced timesheet CSV fields |
| Infrastructure/tooling | enhanced infrastructure CSV fields |
| Exclusions | `ordinary_engineering` and `outside_rnd_boundary` activities |
| Human review | review identity, type, question, owner, status, subjects and evidence |

Enhanced timesheet header:

```csv
timesheet_id,person_ref,date,project_ref,activity_ref,run_ref,category,hours,description
```

Enhanced infrastructure header:

```csv
cost_id,month,service,provider,total_cost,rnd_percent,eligible_amount,allocation_basis,activity_refs,evidence_ref
```

Use semicolons inside `activity_refs` when a cost record has multiple explicitly
supplied activity links. This does not apportion its amount between those
activities.

Supporting example (example only, not evidence):

```yaml
- id: ACT-2026-003
  classification: candidate_supporting
  rationale: "Example only - the isolated fixtures directly enabled the declared interruption run."
  project_refs: [RND-2026-01]
  uncertainty_refs: [UT-01]
  experiment_refs: [RUN-2026-001]
  supports_activity_refs: [ACT-2026-001]
  supports_experiment_refs: [RUN-2026-001]
  person_refs: [P-002]
  evidence_refs: [EV-0101]
```

## Presence rules

- Required: complete project-to-uncertainty-to-experiment and candidate activity
  paths, with resolvable people and evidence.
- Conditional: supporting activities, effort, infrastructure, exclusions, and
  human review.
- Optional: documented explanatory notes only.
- Repeating: records are rendered once each.
- Derived: reverse links, observation IDs, ordering, and matrix rows.

`No data provided.` is permitted only for optional notes. `Not applicable`
requires a reason and is limited to a genuinely absent conditional category.
Missing required content stops publication.

## Hard publication requirements

All IDs and references resolve; duplicate IDs/references are rejected; support
targets are candidate experimental records; activity/run/project paths agree;
applicable resource rows name activities; cost evidence resolves; review lifecycle
is valid; active placeholders are rejected; templates are ignored; and all seven
PDFs compile without warnings before prior outputs are replaced.

Publication success confirms structural consistency only. It does not confirm
facts, evidence sufficiency, legal eligibility, dominant purpose, or allocation
reasonableness.
