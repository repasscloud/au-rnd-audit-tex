# Overview of All Work authoring guide

## Purpose

`01_overview_of_all_work.pdf` is the annual technical narrative and navigation
record. It connects the entity and claim period to the platform, technical
objective, baseline, uncertainties, projects, experimental progression, people,
evidence, and work outside the R&D boundary. It summarises experiments; document
02 retains their complete methods, execution, observations, evaluation, and
conclusions.

The publisher checks structure and consistency. It does not decide legal R&D
eligibility, factual truth, evidence sufficiency, or the authority of an approver.

## Files and exact mappings

| File | Top-level key / headers | Content |
|---|---|---|
| `claim.yaml` | `document` | company, ABN, financial year, program, preparer, version, confidentiality, owner, review date, evidence repository |
| `program.yaml` | `program` | `product`, `technical_objective`, `commercial_context`, `scope`, `baseline`, `annual_synthesis`, `applicability` |
| `projects.yaml` | `projects` | project records and all cross-references |
| `uncertainties.yaml` | `uncertainties` | technical uncertainty records |
| `people.yaml` | `people` | people and technical roles |
| `activities.yaml` | `activities` | activity boundary records |
| `program-evidence.csv` | `evidence_id,type,title,location,captured_at,period_start,period_end,notes` | program evidence catalogue |
| Existing experiment sources | existing contract | authoritative run details used for derived summaries |

Projects, uncertainties, people, and activities support either one combined YAML
file or one record per file. The split filenames are respectively
`project.RND-YYYY-NN.yaml`, `uncertainty.UT-NN.yaml`, `person.P-NNN.yaml`, and
`activity.ACT-YYYY-NNN.yaml`, with singular top-level mappings. Combined and split
modes are mutually exclusive. Filename and internal ID must match. Template files
and nested drafts are not loaded.

## Identifiers and references

- Projects: `RND-YYYY-NN`
- Uncertainties: `UT-NN`
- Experiments: `RUN-YYYY-NNN`
- People: `P-NNN`
- Evidence: `EV-NNNN`, unique across program and experiment evidence
- Activities: `ACT-YYYY-NNN`

Every reference must resolve. Project experiment lists must equal the runs that
name that project. Uncertainty/project links must agree in both directions. Every
experiment engineer and activity classification owner must resolve to a person.

## Content states

| State | Rule |
|---|---|
| Required | Missing, empty, malformed, or placeholder content stops publication |
| Conditional | Supply content, or `state: not_applicable` with a reason where documented |
| Optional | Supply content or the documented `state: no_data`; the PDF prints `No data provided.` |
| Repeating | Add one complete record; the publisher applies deterministic ordering |
| Derived | Supply valid underlying records; never type the derived summary separately |

`No data provided.` is limited to optional prior work, standards/constraints,
person evidence, and evidence notes. It is forbidden for identity, scope,
baseline, uncertainties, projects, experimental progression, outcomes, boundary,
or limitations.

`Not applicable` is allowed only with a reason for commercial context, a separate
business objective, reviewed absence of prior internal work or material
standards, contractor participation, labour, or infrastructure.

## Experiment summaries

Summaries come directly from the existing normalized experiment sources, ordered
by `started_at` then run ID. The overview preserves the supplied status and exact
conclusion or interim conclusion. It does not duplicate complete designs,
methods, execution logs, result rows, or evidence metadata.

## Deterministic ordering

Projects sort by start date then ID; uncertainties by first project then ID;
people by case-folded name then ID; activities by start date then ID; program
evidence by period start, capture time, then ID. Supplier narrative-list order is
preserved.

## Example warning

The active C360 material included with this implementation is explicitly marked
`Illustrative example only`. It demonstrates the contract and is not evidence,
an eligibility conclusion, or a completed claim record. Replace it only with
verified supplier records and accountable-human decisions.

Run `./publish.zsh` on macOS or `./publish.sh` on Linux. Publication validates all
sources, runs all tests, compiles all seven PDFs, and rejects every Tectonic
warning. Never edit `generated/` or `output/` directly.
