# R&D audit TeX framework

[![Build TeX with Tectonic](https://github.com/repasscloud/au-rnd-audit-tex/actions/workflows/build-tex.yml/badge.svg?branch=main)](https://github.com/repasscloud/au-rnd-audit-tex/actions/workflows/build-tex.yml)

This repository provides two independent publishing paths:

- `static-pack/` preserves the manually populated LaTeX baseline.
- `publishing-pipeline/` validates YAML and CSV data, generates LaTeX, and compiles PDFs.

On macOS:

```zsh
cd publishing-pipeline
./publish.zsh
```

On Linux:

```bash
cd publishing-pipeline
./publish.sh
```

See `docs/publishing-pipeline-design.md` for the architecture and `docs/publishing-pipeline-plan.md` for the implementation baseline.
