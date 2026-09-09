# Overview of All Work Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate document 01 from validated annual program records while deriving concise experiment and resource summaries from their existing authoritative sources.

**Architecture:** Add a focused overview loader that owns the new YAML/CSV contracts and validates their reference graph against normalized experiments. Keep the template presentation-only, retain existing experiment ownership, and stage all generated and PDF output transactionally.

**Tech Stack:** Python 3, PyYAML, CSV, Jinja2, unittest, Tectonic, Poppler PDF tools.

**Spec:** `publishing-pipeline/docs/superpowers/specs/2026-09-09-overview-of-all-work-data-contract-design.md`

## Global Constraints

- Work only under `publishing-pipeline/` and preserve existing user changes.
- Never rewrite supplier inputs during publication.
- Never edit generated TeX or PDFs directly.
- Never infer eligibility, facts, people, dates, evidence, conclusions, approvals, measurements, or expenditure.
- Existing experiment YAML/CSV sources remain authoritative and sort by `started_at`, then run ID.
- Active templates are ignored as evidence and placeholder-looking active content fails.
- Validation or compilation failure preserves previous generated files and PDFs.
- Every Tectonic warning is a publication failure.
- Do not commit without explicit instruction.

---

### Task 1: Define overview fixtures and loader interface

**Files:** Create `tests/fixtures/overview-valid/` sources, create
`tests/test_overview.py`, create `scripts/overview.py`.

**Interfaces:** `load_overview_sources(input_dir: Path, experiments: list[dict]) -> dict`.

- [ ] Write representative C360-labelled-example valid sources and tests for normalized ordering and derived experiment summaries.
- [ ] Run the focused tests and observe failure because the interface is absent.
- [ ] Implement strict combined/split loading, field normalization, and deterministic ordering.
- [ ] Run the focused tests and complete suite.

### Task 2: Enforce graph, absence, placeholder, and chronology rules

**Files:** Modify `scripts/overview.py`, `scripts/validation.py`, and
`tests/test_overview.py`; add invalid fixture mutations through test helpers.

**Interfaces:** Shared `is_placeholder`, required text/date/timestamp, and state
helpers; overview graph validation with actionable source/record/field errors.

- [ ] Add failing tests for required fields, IDs, source mode conflicts, template exclusion, filename mismatch, duplicate IDs, global evidence collisions, dates, enum/state shapes, and placeholders.
- [ ] Add failing tests for every project, uncertainty, experiment, person, activity, and evidence orphan or inconsistent reverse relationship.
- [ ] Implement the minimum validation required by each failure.
- [ ] Run focused tests and the complete suite after each red-green group.

### Task 3: Integrate overview and transactional publication

**Files:** Modify `scripts/publisher.py`, `publish.sh`, `publish.zsh`,
`tests/test_publisher.py`; add a script-level transaction test where practical.

**Interfaces:** `sources["overview"]`; staged generated/PDF directories promoted
only after all validation and all seven warning-free compilations.

- [ ] Write failing integration tests proving overview data is loaded and invalid sources preserve existing generated content.
- [ ] Integrate the overview loader after experiments are normalized.
- [ ] Write a failing regression test or controlled script check proving a late compilation failure preserves both destination sets.
- [ ] Implement sibling-directory staging and atomic per-set promotion with rollback-safe ordering.
- [ ] Run the complete suite.

### Task 4: Render the annual overview

**Files:** Modify `templates/01_overview_of_all_work.tex` and
`tests/test_publisher.py`.

**Interfaces:** Presentation-only use of `overview` normalized collections and
existing shared absence macros.

- [ ] Add failing rendering assertions for every section, ordered runs, failed/ongoing outcomes, boundary work, evidence, and resource summaries.
- [ ] Add forbidden-copy assertions for the current instructional template and placeholders.
- [ ] Replace the body with dynamic sections and compact tables/narratives.
- [ ] Run rendering tests, the complete suite, and fixture TeX placeholder scans.

### Task 5: Add active templates, examples, and operating documentation

**Files:** Add new `input/*.template.*` sources, add active source records needed
for publication, create `docs/01-overview-of-all-work/{README.md,AI-AGENT-PROTOCOL.md,OVERVIEW-CAPTURE-WORKFLOW.md,AI-AGENT-TASK-TEMPLATE.md}`, and update `README.md`.

- [ ] Add tests proving every template is ignored.
- [ ] Add exact mappings, required/conditional/optional/repeating/derived rules, and clearly labelled C360 examples.
- [ ] Document classification, verified-fact/inference separation, lifecycle, annual rollover, and accountable-human escalation.
- [ ] Supply active non-placeholder example data explicitly labelled as example data, without changing experiment sources.
- [ ] Run documentation placeholder checks and the complete suite.

### Task 6: Publish and inspect all outputs

**Files:** Generated/output artifacts only through publication commands.

- [ ] Run the complete unit-test suite and confirm zero failures.
- [ ] Run `publish.zsh` and confirm seven PDFs compile with zero warnings.
- [ ] Extract document-01 text and confirm active data is present and old instructional/placeholder copy absent.
- [ ] Inspect rendered pages for overflow, clipping, orphan headings, unreadable tables, and poor page breaks.
- [ ] Re-run publication from unchanged inputs and compare substantively deterministic generated TeX.
- [ ] Run `git diff --check` and review the complete scoped diff.
