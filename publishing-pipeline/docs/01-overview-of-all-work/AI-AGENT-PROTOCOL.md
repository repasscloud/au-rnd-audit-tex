# AI agent protocol for the annual overview

An AI agent may organise verified source material, maintain cross-references,
identify missing records, and run validation. It is not an evidence source, legal
adviser, technical owner, or claim approver.

Before linking work to an uncertainty or experiment, classify it as
`candidate_experimental`, `candidate_supporting`, `ordinary_engineering`,
`outside_rnd_boundary`, `human_review_required`, or insufficiently supported.
Difficulty, novelty to the team, defects, configuration, routine testing,
refactoring, deployment, compliance, and commercial uncertainty do not establish
experimental work.

The agent must:

- Preserve verified facts, supplied assertions, and inference as distinct things.
- Cite the source used for every factual addition and state when it was checked.
- Preserve rejected, mixed, inconclusive, unsuccessful, and ongoing work.
- Derive experiment summaries from existing experiment sources without rewriting them.
- Inspect current files and preserve unrelated user changes before editing.
- Ask accountable humans about legal classification, ownership, technical
  conclusions, evidence sufficiency, approvals, and material contradictions.
- Report validation and PDF inspection results exactly.

The agent must never:

- Self-certify R&D eligibility or present a candidate classification as eligible.
- Manufacture retrospective hypotheses, chronology, research, evidence,
  measurements, people, dates, conclusions, approvals, or expenditure.
- Convert ordinary engineering into experimental work to improve a narrative.
- Remove or soften unsuccessful evidence.
- Load `*.template.*`, generated TeX, or PDFs as active evidence.
- Rewrite supplier-authored input merely to make publication pass.
- Edit generated TeX or PDFs directly.

If required audit content is not supported, publication must remain failed. An
agent must not substitute `No data provided.` or `Not applicable` where the
contract requires evidence or accountable judgment.
