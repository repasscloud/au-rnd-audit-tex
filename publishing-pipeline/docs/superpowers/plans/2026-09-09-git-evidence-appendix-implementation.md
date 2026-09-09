# Git Evidence Appendix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish document 04 from validated repository facts and explicit supplier interpretations.

**Architecture:** A focused `git_evidence.py` loader normalizes exported CSV and optional read-only local Git facts, validates them against the existing document graph, and supplies a dedicated template context. The publisher and transactional seven-document build remain unchanged except for loading this model.

**Tech Stack:** Python 3, PyYAML, CSV, Git CLI, Jinja2, LaTeX/Tectonic, unittest.

**Spec:** `docs/superpowers/specs/2026-09-09-git-evidence-appendix-data-contract-design.md`

## Global Constraints

- Work only under `publishing-pipeline/`; do not commit.
- Never mutate supplier inputs or configured repositories.
- No network access during publication.
- Repository facts, supplier assertions and interpretations remain distinct.
- Existing experiment and overview sources retain ownership.
- Every Tectonic warning is a publication failure.

---

### Task 1: Define repository contracts and validation

**Files:** Create `tests/test_git_evidence.py`, fixtures, templates, and `scripts/git_evidence.py`.

**Interfaces:** Produce `load_git_evidence(input_dir, overview, experiments, claim_mapping) -> dict`.

- [ ] Write failing tests for valid exported records, IDs, required fields, duplicates, placeholders and graph references.
- [ ] Run the focused tests and confirm failure because the loader is absent.
- [ ] Implement the minimal YAML/CSV loader and normalizer.
- [ ] Run focused tests to green, then refactor shared validation helpers only where necessary.

### Task 2: Add identity, interpretation and lifecycle rules

**Files:** Modify `tests/test_git_evidence.py` and `scripts/git_evidence.py`.

**Interfaces:** Extend the normalized model with explicit identity mappings, interpretations, limitations and reverse indexes.

- [ ] Add failing tests for ambiguous mappings, orphan links, contradictions, combined/split exclusivity and template exclusion.
- [ ] Confirm the failures describe missing behavior.
- [ ] Implement validation and deterministic ordering.
- [ ] Run focused tests to green.

### Task 3: Add safe local Git inspection

**Files:** Modify `tests/test_git_evidence.py` and `scripts/git_evidence.py`.

**Interfaces:** Local acquisition returns the same normalized fact shape as exported CSV rows.

- [ ] Add failing temporary-repository tests for commits, merges/reverts, expected HEAD, dirty/detached/shallow state and non-mutation.
- [ ] Implement read-only, no-network inspection with explicit paths and pinned state.
- [ ] Run focused tests and verify repository state is unchanged.

### Task 4: Integrate and render document 04

**Files:** Modify `scripts/publisher.py`, `templates/04_git_evidence_appendix.tex`, `tests/test_publisher.py`; create active example inputs.

**Interfaces:** Add `sources["git_evidence"]` for Jinja rendering.

- [ ] Add failing integration tests for dynamic text, chronology and forbidden legacy content.
- [ ] Load the Git evidence model after documents 01--03 sources are normalized.
- [ ] Replace the static template with concise dynamic sections.
- [ ] Run focused and complete unit tests.

### Task 5: Add operating documentation

**Files:** Create the four files under `docs/04-git-evidence-appendix/`; modify `README.md`.

- [ ] Document exact fields, examples, acquisition modes, lifecycle and hard gates.
- [ ] Add the AI protocol and reusable prompt with explicit non-inference rules.
- [ ] Scan documentation and active inputs for unlabeled examples or placeholders.

### Task 6: Publish and verify

**Files:** Generated and output files are transactionally replaced by the publisher.

- [ ] Run the full test suite.
- [ ] Publish all seven PDFs and confirm zero Tectonic warnings.
- [ ] Compare two unchanged renders for substantive TeX determinism.
- [ ] Extract document-04 text and reject old instructional/placeholder content.
- [ ] Visually inspect every document-04 page and compare IDs/classifications with documents 01--03.
- [ ] Run `git diff --check` and review the complete scoped diff without committing.
