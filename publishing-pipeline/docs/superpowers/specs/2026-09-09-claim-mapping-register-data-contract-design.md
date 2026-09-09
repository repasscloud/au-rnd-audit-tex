# Claim Mapping Register Data Contract Design

**Status:** Approved on 2026-09-09.

**Scope:** All work is confined to `publishing-pipeline/`. This design converts
document 03 into a concise traceability matrix. It does not determine legal R&D
eligibility and does not duplicate the annual narrative in document 01 or the
experimental detail in document 02.

## Purpose

The register lets an authorised reviewer trace projects to technical
uncertainties, uncertainties to experiments, experiments to activities, people,
observations, and evidence, and supplied resource attribution back to activities.
It also preserves ordinary engineering, outside-boundary work, and decisions
requiring accountable human review.

Activity classifications and allocation categories are supplier assertions. The
publisher checks identity, structure, chronology, references, and contradictions;
it does not convert those assertions into eligibility conclusions.

## Architecture

Create `scripts/claim_mapping.py` as a read-only composer over the normalized
overview, experiment, timesheet, infrastructure, and review records. Existing
sources retain ownership. No separate mapping source may restate relationships
already owned by projects, uncertainties, activities, experiments, people, or
evidence.

Three source extensions fill relationships that cannot safely be inferred:

1. Candidate-supporting activities declare the candidate experimental activity
   or experiment they support.
2. Timesheet and infrastructure rows declare activity-level attribution.
3. Review records identify accountable owners and lifecycle states for unresolved
   legal, technical, evidentiary, ownership, classification, or allocation
   decisions.

## Authoritative sources and identifiers

| Record | Source | ID |
| --- | --- | --- |
| Project | project YAML | `RND-YYYY-NN` |
| Uncertainty | uncertainty YAML | `UT-NN` |
| Activity | activity YAML | `ACT-YYYY-NNN` |
| Experiment | existing experiment YAML/CSV | `RUN-YYYY-NNN` |
| Person | people YAML | `P-NNN` |
| Evidence | program/experiment evidence CSV | `EV-NNNN` |
| Observation | derived from run and result sequence | `RUN-YYYY-NNN/RESULT-NNN` |
| Timesheet row | timesheets CSV | `TS-YYYY-NNNN` |
| Cost row | infrastructure CSV | `COST-YYYY-NNNN` |
| Human review | review YAML | `REV-YYYY-NNN` |

Template files are structural examples only and are never loaded. Supplier inputs
are read-only during publication. Generated TeX and PDFs are replaced only after
all validation, tests, and warning-free compilation succeed.

## Source extensions

### Activities

Activity records may contain `supports_activity_refs`,
`supports_experiment_refs`, and `review_refs`. A `candidate_supporting` activity
requires at least one support target. Supported activities must be
`candidate_experimental`; supported experiments must belong to a project named by
the supporting activity. Other classifications forbid support-target fields.
Every `human_review_required` activity requires at least one review reference.

### Timesheets

The enhanced header is:

```csv
timesheet_id,person_ref,date,project_ref,activity_ref,run_ref,category,hours,description
```

Each populated enhanced row requires a unique `TS-YYYY-NNNN` ID and resolvable
person, project, and activity references. `run_ref` may be empty only when no run
attribution was supplied. When present, it must be one of the activity's declared
experiment references and belong to the project. Categories remain
supplier-authored and are checked for structural contradictions with the activity
classification.

The legacy header remains loadable for existing downstream documents. An empty
legacy file is acceptable when labour is declared not applicable. A populated
legacy row cannot satisfy document-03 activity traceability and therefore stops
publication rather than receiving inferred identifiers or relationships.

### Infrastructure and tooling

The enhanced header is:

```csv
cost_id,month,service,provider,total_cost,rnd_percent,eligible_amount,allocation_basis,activity_refs,evidence_ref
```

`cost_id` is unique and matches `COST-YYYY-NNNN`. `activity_refs` is a
semicolon-separated list of explicitly attributed activities. Evidence resolves
against the global evidence catalogue. Existing decimal and arithmetic validation
continues. Linking one cost row to several activities does not divide or duplicate
its amount.

The legacy header remains loadable. It cannot satisfy applicable document-03
activity attribution when populated.

### Human reviews

Reviews use either `input/reviews.yaml` with a top-level `reviews` list or split
`input/reviews/review.REV-YYYY-NNN.yaml` files with a singular top-level `review`
mapping. Modes are mutually exclusive, template files are ignored, filename IDs
must match internal IDs, and records merge only in memory.

Each review requires ID, decision type, question, owner person reference, status,
raised timestamp, and at least one typed subject reference. Allowed decision types
are `legal`, `technical`, `evidentiary`, `ownership`, `classification`, and
`allocation`. Status is `open`, `resolved`, or `superseded`. Resolved reviews
require `resolved_at` and `resolution`; superseded reviews require
`superseded_by_ref`; open reviews forbid a resolution. Optional evidence references
must resolve.

## Document sections

1. **Purpose and interpretation** — explains traceability and the publisher's
   non-eligibility boundary.
2. **Project, uncertainty, and experiment index** — derived navigation across the
   technical record.
3. **Candidate experimental activity matrix** — supplied classification,
   rationale, uncertainty, run, people, and evidence links.
4. **Candidate supporting activity matrix** — explicit supported activity/run and
   supplied relationship rationale.
5. **Experiment trace matrix** — run, project, uncertainties, activities,
   engineers, observation IDs, evidence, and supplied status.
6. **People and recorded effort** — person and stable timesheet rows linked to
   activity/project and optional run.
7. **Infrastructure and tooling attribution** — stable cost rows, activity links,
   allocation basis, and evidence.
8. **Exclusions and boundary record** — ordinary engineering and
   outside-boundary activities with their supplied rationales.
9. **Human review register** — accountable unresolved or superseded decisions.
10. **Coverage and integrity notes** — explicit applicability states and pointers
    to detailed documents.
11. **Document control** — shared claim metadata.

The current instruction section, sample rows, and annual narrative prompts are
removed. Document 03 references document 01 and 02 instead of copying their
content.

## Presence policy

- Required: at least one project, uncertainty, experiment,
  `candidate_experimental` activity, experiment result, and experiment evidence;
  complete and resolvable trace paths.
- Conditional: candidate-supporting activities, labour attribution,
  infrastructure attribution, exclusions, and human-review records.
- Optional: explanatory notes explicitly designated optional.
- Repeating: projects, activities, experiments, effort rows, cost rows,
  exclusions, and reviews.
- Derived: matrix rows, observation IDs, reverse indexes, labels, and coverage
  summaries.

`No data provided.` is permitted only for documented optional notes. It is not
permitted for identities, classifications, rationales, required evidence,
supporting relationships, resource attribution, or review ownership.

`Not applicable` requires a non-placeholder reason and is permitted only when no
supporting activities, labour attribution, infrastructure attribution,
ordinary/outside-boundary activities, or human-review decisions apply.

## Classification boundary

The register displays all five supplier classifications:

- `candidate_experimental`
- `candidate_supporting`
- `ordinary_engineering`
- `outside_rnd_boundary`
- `human_review_required`

Candidate labels never become “eligible” or “claimable.” Ordinary and
outside-boundary work remains visible as exclusions. Human-review-required work
cannot appear in core/supporting resource summaries until the accountable review
records a resolution. Unsuccessful, rejected, mixed, inconclusive, and ongoing
experiments remain visible with their supplied statuses.

## Deterministic ordering

Projects sort by period start then ID; uncertainties by first project then ID;
experiments by `started_at` then run ID; activities by period start then ID;
support targets by activity ID then experiment chronology; people by case-folded
name then ID; timesheets by date, person ID, then timesheet ID; costs by month,
case-folded service, then cost ID; evidence by its existing normalized ordering;
reviews by open/resolved/superseded state, raised timestamp, then review ID.
Supplier-authored narrative-list order is preserved.

## Fail-closed validation

Publication fails for missing required content, placeholders, malformed or
duplicate IDs, duplicate references, orphans, inconsistent reciprocal links,
activity/run/project disagreement, invalid supporting targets, missing supporting
relationships, outside-boundary experiment references, applicable resource rows
without activity attribution, category/classification contradictions, unresolved
cost evidence, invalid review lifecycle, or review-required activities without an
accountable review.

Validation identifies contradictions; it does not judge the truth, sufficiency,
legal character, dominant purpose, or reasonableness of supplier assertions.

## Verification

Implementation uses failing tests first. Fixtures cover every classification,
completed and ongoing runs, valid supporting relationships, attributed and
not-applicable resources, open/resolved/superseded reviews, duplicates,
contradictions, orphans, placeholders, and legacy schemas. Final verification runs
the complete suite, publishes all seven PDFs with zero Tectonic warnings, checks
document-03 text against documents 01 and 02, visually inspects every page, scans
for old placeholder/instructional copy, and verifies substantively deterministic
generated TeX from unchanged inputs.
