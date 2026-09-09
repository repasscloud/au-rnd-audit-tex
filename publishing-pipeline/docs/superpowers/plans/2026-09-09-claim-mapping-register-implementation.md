# Claim Mapping Register Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate document 03 as a concise, validated traceability matrix over existing technical records and explicitly supplied activity-level resource relationships.

**Architecture:** Add a focused `claim_mapping.py` composer over normalized overview, experiment, resource, and review records. Extend only the natural source owners for missing edges, keep templates presentation-only, and retain transactional publication.

**Tech Stack:** Python 3, PyYAML, CSV, Jinja2, unittest, Tectonic, Poppler PDF tools.

**Spec:** `publishing-pipeline/docs/superpowers/specs/2026-09-09-claim-mapping-register-data-contract-design.md`

## Global Constraints

- Work only under `publishing-pipeline/` and preserve user-authored changes.
- Never infer eligibility, people, dates, measurements, evidence, conclusions, approvals, expenditure, percentages, or relationships.
- Never rewrite supplier inputs or edit generated TeX/PDF directly.
- Experiment records remain authoritative and chronological by `started_at`, then run ID.
- Template files are never active evidence.
- Missing required audit content and every Tectonic warning stop publication.
- Failed publication preserves prior generated files and PDFs.
- Do not commit without explicit instruction.

---

### Task 1: Define the derived traceability interface

**Files:** Create `tests/test_claim_mapping.py`, create `scripts/claim_mapping.py`, add focused fixtures.

**Interfaces:** `build_claim_mapping(overview, experiments, timesheets, infrastructure_costs, reviews) -> dict`.

- [ ] Write a failing test for project/uncertainty/experiment/activity/person/evidence composition and deterministic ordering.
- [ ] Run the focused test and confirm failure because the module/interface is absent.
- [ ] Implement the smallest index and composition helpers.
- [ ] Run the focused test and complete suite.

### Task 2: Validate activity support and review relationships

**Files:** Modify `scripts/overview.py`, `scripts/claim_mapping.py`, `tests/test_claim_mapping.py`, and overview fixtures.

- [ ] Add failing tests for required supporting targets, non-experimental targets, cross-project runs, forbidden support fields, missing review links, duplicates, and orphans.
- [ ] Confirm each test fails for the intended missing behavior.
- [ ] Implement relationship validation without deciding eligibility.
- [ ] Run focused and complete tests.

### Task 3: Add enhanced resource contracts

**Files:** Modify `scripts/publisher.py`, `scripts/claim_mapping.py`, `tests/test_publisher.py`, `tests/test_claim_mapping.py`, and CSV fixtures/templates.

- [ ] Add failing tests for enhanced timesheet/cost rows and legacy compatibility.
- [ ] Add failures for invalid IDs, orphans, run/activity disagreement, unresolved evidence, missing applicable attribution, and category/classification contradictions.
- [ ] Implement dual exact-header loading and normalized row identities.
- [ ] Run focused and complete tests.

### Task 4: Add review source loading and lifecycle validation

**Files:** Modify `scripts/claim_mapping.py`, create review fixtures/templates, modify `tests/test_claim_mapping.py`.

- [ ] Add failing tests for combined and split modes, template exclusion, filename mismatch, duplicate IDs, subject orphans, and each lifecycle state.
- [ ] Implement deterministic combined/split loading and validation.
- [ ] Run focused and complete tests.

### Task 5: Integrate and render document 03

**Files:** Modify `scripts/publisher.py`, `templates/03_claim_mapping_register.tex`, and rendering tests.

- [ ] Add failing assertions for every section and all five classifications.
- [ ] Add forbidden-copy assertions for old instructions, sample IDs, brackets, and eligibility language.
- [ ] Integrate `sources["claim_mapping"]` only after every source validates.
- [ ] Replace document 03 with compact dynamic tables and explicit applicability states.
- [ ] Run rendering tests and the complete suite.

### Task 6: Add authoring and agent documentation

**Files:** Create `docs/03-claim-mapping-register/README.md`, `AI-AGENT-PROTOCOL.md`, `CLAIM-MAPPING-CAPTURE-WORKFLOW.md`, `AI-AGENT-TASK-TEMPLATE.md`; update relevant READMEs.

- [ ] Document exact YAML/CSV mappings, examples, presence policy, hard gates, and lifecycle.
- [ ] Label every C360 example as example rather than evidence.
- [ ] Require fact/assertion/inference separation and accountable-human escalation.
- [ ] Scan documentation for placeholders and contradictions.

### Task 7: Publish and verify

**Files:** Generated and output artifacts only through the publication commands.

- [ ] Run the complete test suite with zero failures.
- [ ] Publish all seven PDFs and confirm zero Tectonic warnings.
- [ ] Extract documents 01, 02, and 03 text; confirm consistent IDs/statuses and no old instructions or placeholders.
- [ ] Render every document-03 page and inspect clipping, overflow, table readability, page breaks, headers, and footers.
- [ ] Republish unchanged inputs and compare normalized generated TeX after removing the generated date line if necessary.
- [ ] Run scoped placeholder scans, `git diff --check`, and review the full scoped diff.
