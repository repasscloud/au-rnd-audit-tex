# Reusable AI-agent task for document 03

Work only within `publishing-pipeline/`. Inspect the current working tree and
preserve unrelated changes.

Build or update the Claim Mapping Register only from verified supplier-authored
sources. First classify each work item as candidate experimental, candidate
supporting, ordinary engineering, outside the R&D boundary, human review required,
or insufficiently supported. Explain the evidence for the classification but do
not determine legal R&D eligibility.

Reuse project, uncertainty, activity, person, experiment, result, evidence,
timesheet, infrastructure, and review IDs. Never create a separate mapping record
that restates existing relationships. Never infer labour or infrastructure
attribution from commits, roles, participation, project membership, or timing.

Preserve failed, rejected, mixed, inconclusive, ongoing, ordinary, and excluded
work. Separate verified facts, supplier assertions, and inference. Ask accountable
humans about missing legal, ownership, evidentiary, technical, classification,
supporting-purpose, dominant-purpose, or allocation decisions.

Use YAML for narrative/structured records and CSV only for high-volume rows.
Ignore templates as evidence, do not rewrite supplier inputs to make validation
pass, and do not edit generated TeX or PDFs. Missing required audit content must
stop publication.

Run the focused and complete tests, publish all seven PDFs with zero Tectonic
warnings, inspect document 03 text and every rendered page, compare its IDs and
statuses with documents 01 and 02, scan for placeholders/instructions, and verify
deterministic generated TeX. Report exact changes, checks, and limitations.
