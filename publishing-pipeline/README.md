# Publishing pipeline

This folder contains the local YAML/CSV-to-LaTeX-to-PDF publisher. The original manual framework remains independently buildable in `../static-pack/`.

## Run on macOS

```zsh
./publish.zsh
```

## Run on Linux

```bash
./publish.sh
```

Each command prepares a local Python virtual environment, installs the two required libraries, runs the automated tests, validates the input files, generates seven LaTeX documents, and compiles seven PDFs. Any validation failure, test failure, Tectonic error, or Tectonic warning stops publication.

## Files people edit

- `input/claim.yaml`: document and claim metadata.
- `input/experiments.yaml`: experiment records; the baseline accepts an empty list.
- `input/timesheets.csv`: high-volume labour allocation rows.
- `input/infrastructure-costs.csv`: high-volume infrastructure and tooling rows.
- `templates/`: data-aware LaTeX templates. Edit these only when changing document structure or presentation.

## Files the pipeline owns

- `generated/`: generated `.tex` files and the generated style package.
- `output/`: compiled PDFs.
- `.venv/`: local Python dependencies.

Do not edit generated files. Change the source YAML, CSV, or templates and publish again.

## Current baseline

The first implementation intentionally fills the common document metadata and establishes validated extension points for experiments, timesheets, and infrastructure costs. It does not yet replace every instructional placeholder in the original templates. Those sections can be converted incrementally as their source fields are agreed from real claim data.
