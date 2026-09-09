# AI agent protocol for Git evidence

## Authority classes

Always label information as one of:

1. **Immutable repository fact:** captured identifier, timestamp, parent,
   author/committer metadata, ref, subject, or external record identifier.
2. **Supplier assertion:** repository scope, completeness, classification,
   materiality, relationship, identity confirmation, or limitation.
3. **Agent inference:** a proposed observation that is not publishable evidence
   until an accountable human confirms and records it.

Never rewrite repository facts or commit messages. Never manufacture a
retrospective interpretation, relationship, repository event, approval, or
identity mapping.

## Non-inference rules

Do not infer:

- R&D eligibility from any repository activity;
- experimental character from commits, files, branches, tickets, tests or builds;
- activity, experiment, labour or cost attribution from timing or proximity;
- a person from a Git name, email, role, job title or experiment participation;
- purpose from a commit message alone;
- success from passing tests, deployments, coverage, complexity, commit count,
  lines changed or deployment frequency.

Preserve ordinary engineering, maintenance, refactoring, administration,
outside-boundary work, unsuccessful changes, reverts, abandoned branches and
contradictory evidence. Do not curate them away to improve a claim narrative.

## Agent actions

- Inspect only explicitly authorised repositories and paths.
- Perform no fetch, pull, checkout, clean, reset, hook execution or submodule
  update.
- Keep author and committer separate.
- Use full hashes as identity; abbreviations are display-only.
- Preserve time-zone offsets.
- Put high-volume immutable rows in CSV and readable configuration or
  interpretation in YAML.
- Reuse existing project, activity, experiment, person, evidence and review IDs.
- Ask accountable humans about missing legal, ownership, identity,
  evidentiary, technical, classification or relationship decisions.
- Report limitations without presenting absence as proof.

The pipeline may validate structure and contradictions. Neither the agent nor the
pipeline may self-certify legal eligibility.
