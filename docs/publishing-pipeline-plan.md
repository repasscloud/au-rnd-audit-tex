# Data-driven Publishing Pipeline Implementation Plan

**Goal:** Preserve the static LaTeX baseline and add a tested local YAML/CSV-to-LaTeX-to-PDF publishing pipeline.

**Architecture:** A small Python publisher validates human-maintained YAML and CSV files, escapes source values, renders seven Jinja-based LaTeX templates, and invokes Tectonic through operating-system-specific shell entrypoints. The static pack and generated pipeline remain independent.

**Tech stack:** Python 3, PyYAML, Jinja2, `unittest`, LaTeX, Tectonic, Bash on Linux, zsh on macOS.

**Spec:** `docs/publishing-pipeline-design.md`

## Global constraints

- Preserve the existing static documents and their warning-free builds.
- Keep generated `.tex` and `.pdf` artefacts out of Git.
- Do not introduce a server, database, container, JavaScript toolchain, or external service.
- Fail on invalid source data and on every Tectonic warning or error.
- Do not invent claim facts or eligibility conclusions.

## Task 1: Preserve the static baseline

- [ ] Move the seven LaTeX files, style package, Git export helper, and platform build scripts into `static-pack/`.
- [ ] Keep the baseline build commands working from that directory.
- [ ] Update the root documentation and Linux workflow paths.
- [ ] Run both shell syntax checks and the macOS baseline build.

## Task 2: Establish the source-data contract

- [ ] Add readable sample `claim.yaml` and `experiments.yaml` files.
- [ ] Add header-only timesheet and infrastructure-cost CSV files.
- [ ] Add valid and invalid fixtures for automated tests.
- [ ] Test required metadata, CSV headers, and unique experiment identifiers.

## Task 3: Implement safe rendering

- [ ] Add tests for LaTeX escaping and seven-document generation.
- [ ] Implement focused loading, validation, escaping, and rendering modules.
- [ ] Copy the baseline templates into the pipeline and replace baseline metadata placeholders with data bindings.
- [ ] Mark generated LaTeX as disposable output.

## Task 4: Add platform-specific publishing commands

- [ ] Add `publish.sh` with a Linux-only guard.
- [ ] Add `publish.zsh` with a macOS-only guard.
- [ ] Have both commands prepare dependencies, run tests, generate LaTeX, compile PDFs, and reject warnings.
- [ ] Add shell syntax and wrong-platform guard tests.

## Task 5: Verify and document the framework

- [ ] Run the Python test suite.
- [ ] Run the static macOS build.
- [ ] Run the end-to-end macOS pipeline.
- [ ] Inspect a representative generated PDF visually.
- [ ] Run `git diff --check` and document exact usage and extension points.
