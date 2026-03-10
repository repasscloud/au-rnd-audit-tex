# R&D audit TeX pack

[![Build TeX with Tectonic](https://github.com/repasscloud/au-rnd-audit-tex/actions/workflows/build-tex.yml/badge.svg)](https://github.com/repasscloud/au-rnd-audit-tex/actions/workflows/build-tex.yml)

Files in this pack:

- `01_overview_of_all_work.tex` - annual overview / master narrative
- `02_experiment_notebook.tex` - audit-grade experiment run notebook
- `03_claim_mapping_register.tex` - core/supporting activity mapping register
- `04_git_evidence_appendix.tex` - git import appendix with automatic file inclusion
- `05_engineer_weekly_timesheets.tex` - weekly labour allocation pack
- `06_infrastructure_cost_worksheets.tex` - monthly infrastructure/tooling apportionment
- `07_annual_claim_pack.tex` - full annual claim summary structure
- `rd_audit_style.sty` - shared visual style and utility macros
- `git_log_export.sh` - helper to export git logs into plain text for inclusion

Suggested build order:

1. Fill the overview document.
2. Create experiment notebook entries for each independent run.
3. Complete the claim mapping register.
4. Export repository logs and compile the git appendix.
5. Complete weekly timesheets and monthly infrastructure sheets.
6. Assemble the annual claim pack and cross-reference the supporting documents.
