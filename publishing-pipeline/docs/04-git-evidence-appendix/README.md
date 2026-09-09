# 04 Git Evidence Appendix authoring guide

## Purpose and authority

Document 04 is a source-control chronology and evidence index. It locates
immutable engineering records and keeps separately supplied interpretations that
connect them to documents 01--03. It does not determine R&D eligibility, labour,
cost, authorship, or causation.

`repositories.yaml` owns repository coverage, acquisition, limitations and
explicit identity mappings. `repository-events.csv` owns high-volume immutable
facts. `repository-interpretations.yaml`, or mutually exclusive split files,
owns supplier interpretations. Existing overview, experiment, evidence and
review sources retain their relationships. Templates are never active evidence.

## Repository YAML

`repository_evidence.state` is `applicable` or `not_applicable`. The latter
requires a reason and forbids repositories. Applicable evidence requires a
coverage statement and repositories with:

| Field | Contract |
|---|---|
| `id` | Unique `REPO-NNN` |
| `name` | Supplier label; categories are not fixed |
| `project_refs` | Existing project IDs |
| `period_start`, `period_end` | Dates inside program scope |
| `acquisition.mode` | `exported` or `local` |
| `expected_head` | Full pinned object hash |
| `history.completeness` | `complete`, `shallow`, `partial`, `unknown`, or `unavailable` |
| `history.limitation` | `no_data`, or content plus accountable review |
| `identity_mappings` | Explicit mappings only; may be empty |

Local mode requires an absolute `local_path` exactly present in `allowed_paths`.
Publication performs read-only inspection without fetching, hooks, checkout,
cleaning or submodule updates.

Identity mappings require `GITID-NNNN`, exact Git name, SHA-256 of the exact
email bytes, existing person, basis, evidence, review and lifecycle status. Names
or email similarity never create a mapping.

## Event CSV

Headers must be exactly:

```csv
record_id,repository_ref,record_type,immutable_identifier,occurred_at,authored_at,committed_at,author_name,author_email_sha256,committer_name,committer_email_sha256,subject,parent_identifiers,ref_names,related_record_ids,source_evidence_ref,status,raw_record_sha256
```

Commit, merge and revert rows require full hashes, offset-aware author/committer
timestamps, separate identities, subject, parents and record digest. Other rows
use `occurred_at` and an immutable provider-scoped ID. Semicolons separate plural
cells. Allowed types are commits, merges, reverts, branch snapshots, tags,
releases, pull/merge requests, issues, tickets, builds, tests, deployments and
other engineering records. Detailed diffs, rename/delete lists and provider logs
belong in existing evidence records referenced by `source_evidence_ref`.

## Interpretation YAML

Use combined `interpretations: [...]` or split
`interpretation.GITINT-YYYY-NNNN.yaml` files with singular `interpretation`.
Filename and internal IDs must match. Each record supplies repository/event
references, materiality, engineering context, narrative, accountable owner,
timestamp and typed project, uncertainty, activity, experiment, person, evidence
and review lists. Empty lists remain unasserted; the pipeline does not infer them.

Contexts cover candidate experimental/supporting support, ordinary engineering,
maintenance, refactoring, administration, outside-boundary work, failed
approaches, reverts, abandoned work, contradictory evidence and human review.
They are supplier assertions and never override document-03 classifications.

## Absence, ordering and gates

`No data provided.` is restricted to optional notes, mappings, interpretations
and supplementary records. Reasoned `Not applicable` is restricted to the whole
appendix and structurally inapplicable repository features. Missing required
facts fail publication.

Repositories sort by start date and ID. Commits sort by committed timestamp,
authored timestamp and full hash. Other events sort by occurrence time, type,
immutable ID and record ID. Experiment material remains ordered by `started_at`,
then run ID.

Publication rejects placeholders, duplicates, orphans, contradictions, ambiguous
identity, sensitive remotes, incomplete history without review, changed local
state and every TeX warning. Inputs and repositories are never rewritten.

All shipped C360 material beginning `Illustrative example only` demonstrates the
contract and is not evidence of actual repositories, commits, identities,
relationships, approvals, classifications, or eligibility.
