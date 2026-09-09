# Git Evidence Appendix Data Contract Design

**Status:** Approved on 2026-09-09.

**Scope:** `publishing-pipeline/` only. Document 04 becomes a concise repository chronology and evidence index. Repository activity supports the technical record but does not prove experimental character or legal R&D eligibility.

## Architecture and source ownership

The appendix reuses the normalized project, uncertainty, activity, experiment,
person, evidence, and review graph used by documents 01--03. Three new inputs
own information that cannot safely be derived:

- `repositories.yaml` owns repository scope, acquisition configuration,
  limitations, and explicit Git-identity mappings.
- `repository-events.csv` owns exported immutable repository and engineering
  facts. Optional local Git inspection produces the same fact model in memory.
- `repository-interpretations.yaml`, or mutually exclusive split
  `repository-interpretations/interpretation.GITINT-YYYY-NNNN.yaml` files, owns
  supplier-authored materiality explanations and typed links.

Template files are ignored. Inputs and inspected repositories are never mutated.
Ordinary publication performs no network access. Local inspection is limited to
explicit absolute paths, checks expected HEAD, range and repository identity,
disables optional locks, and never fetches, checks out, cleans, runs hooks, or
updates submodules.

## Identifiers

Repositories use `REPO-NNN`, event rows `GITREC-YYYY-NNNNNN`, interpretations
`GITINT-YYYY-NNNN`, and identity mappings `GITID-NNNN`. Commits retain their full
object hashes scoped by repository. Existing `RND-YYYY-NN`, `UT-NN`,
`ACT-YYYY-NNN`, `RUN-YYYY-NNN`, `P-NNN`, `EV-NNNN`, and `REV-YYYY-NNN` IDs remain
authoritative.

## Evidence boundary

Immutable facts preserve exact identifiers, timestamps, author and committer
roles, subjects, parents and captured digests. Curated interpretations are
visibly separate supplier assertions. A Git identity links to a person only
through an explicit active mapping; matching names or email digests never creates
a relationship. Commit messages are displayed as recorded and are not treated as
complete statements of purpose.

Ordinary engineering, maintenance, refactoring, administration, outside-boundary
work, failed approaches, reverts, abandoned work and contradictory evidence stay
visible where captured or interpreted. Counts, code volume, test results, builds,
deployments and repository activity never establish eligibility or labour/cost
attribution.

## Sections and presence

Required sections are purpose/boundary, repository coverage, acquisition
integrity and limitations, chronology for each available repository, coverage
notes, and document control. Material interpretations, hosted records and
identity mappings are conditional. Repositories, facts, mappings,
interpretations and limitations repeat. Display hashes, reverse indexes,
chronology and coverage summaries are derived.

`No data provided.` is limited to optional notes, additional engineering records,
interpretations, supplementary evidence and identity mappings when no person
attribution is claimed. `Not applicable` requires a reason and is limited to the
whole appendix when source control did not apply, absent remotes, range starts at
repository inception, absent submodules and first-version supersession.

Publication fails for missing applicable repositories or facts; placeholders;
malformed or duplicate IDs/hashes; unknown, orphaned or contradictory links;
conflicting identities; sensitive remotes; local paths outside the configured
allow-list; expected-state mismatch; falsely declared complete shallow/partial
history; or unavailable history lacking both a limitation and accountable review.

## Ordering and transactional behavior

Repositories sort by period start then ID. Commits sort by committed timestamp,
authored timestamp and full hash. Other events sort by occurrence timestamp,
type, immutable identifier and record ID. Interpretations sort by earliest linked
event then ID. Identity mappings sort by repository, case-folded exact name,
email digest and ID. Experiment-derived material remains ordered by `started_at`
then run ID.

All sources validate before rendering. The existing staging build replaces
generated TeX and PDFs only after all seven documents compile without any
Tectonic warning.

## Verification

Tests cover exported and local modes, template exclusion, combined/split
interpretations, duplicates, orphans, contradictions, identities, merge/revert
history, dirty/detached/shallow states, expected-state changes, deterministic
ordering, non-mutation and transactional failure. Acceptance requires the full
suite, seven warning-free PDFs, text and visual inspection of document 04,
cross-document comparison, placeholder removal and substantively deterministic
TeX for unchanged inputs and repository state.
