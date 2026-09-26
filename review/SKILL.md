---
name: review
description: Review a feature an agent just built before you trust it. Checks the implementation against the plan it was supposed to follow, against the project's architecture boundaries, and against production-readiness — then reports issues grouped by severity (critical / important / minor). Never autofixes; you stay in control of what gets changed. Use after an agent finishes a feature, before committing, or whenever the user says "review this", "review the feature", or "is this production ready".
---

# Review

The failure this prevents: an agent builds a feature — say 400 lines — you skim it, it looks fine, you commit. Three days later a bug surfaces that a careful read would have caught. This skill is that careful read, done before you commit, by someone other than the author.

The goal is not to rewrite the code. The goal is to **find what's wrong and hand the decision back to you**. This skill reports; it never autofixes. You decide what to act on.

## The rules

1. **Never autofix.** Do not edit, refactor, or "quickly clean up" anything. Even an obvious one-line fix gets reported, not applied. The moment you start editing, the user stops reviewing — that defeats the skill. The only output is the report.
2. **Severity is honest, not inflated.** A `critical` is something that will break in production or corrupt data. Don't promote a style nit to `important` to look thorough, and don't bury a real data-loss bug under minor noise. If there are no critical issues, say so plainly.
3. **Every issue is concrete.** Each finding names the file and line, says what's wrong, and says why it matters. "Consider improving error handling" is not a finding. "`service.ts:88` swallows the DB error and returns an empty list, so callers can't distinguish 'no rows' from 'query failed'" is — in a real report that file:line is a clickable link.
4. **Review against intent, not taste.** Judge the code against the plan it was meant to follow and the project's own conventions — not against how you'd have written it. A different-but-valid choice is not a finding.

## Process

### 1. Establish what was supposed to be built

Before reading the code, find the intent to judge it against:

- **The plan.** If the feature was planned with the `architect` skill, its folder is `context/features/<slug>/`: read `spec.md` (behavior and acceptance criteria `AC-n`), `use-cases.md` if present, and `build-plan.md` (the steps, and which are ticked as done). Otherwise use a ticket, a PR description, or the prompt that kicked off the work. Ask the user for it if it's not obvious — "what was this feature supposed to do?" is a fair opening question.
- **The architecture.** Read `context/project/architecture.md` and the ADRs in `context/project/adr/` (or the project's own ADR folder, e.g. `docs/adr/`) — accepted ADRs are binding decisions the code must respect. Also read CLAUDE.md and any docs describing module boundaries, layering, or conventions. These define what "respects the architecture" means for this project. If there's no written architecture, infer the boundaries from the surrounding code and say you're doing so.

If you can't find a plan, don't block — review against the architecture and production-readiness, and note in the report that no plan was available to check against.

### 2. Identify the change under review

Determine exactly what to review. Prefer the diff, not the whole repo:

- If it's uncommitted work: `git diff` / `git diff --staged` and `git status`.
- If it's a branch or PR: diff against the base.
- If the user points at specific files, review those plus what they directly touch.

Read the changed code in full, and read enough of the surrounding code to understand how it's called and what it depends on. A 400-line feature is small enough to read every line — do that.

### 3. Review across three lenses

Walk the change against each:

- **Matches the plan.** Does the implementation do what it was supposed to? Look for: missing pieces of the plan, scope that quietly grew beyond it, decisions silently made differently than agreed (in `spec.md` or an ADR), and stubs/TODOs left where real behavior was expected. When a spec exists, check each acceptance criterion (`AC-n`) and say which are met, unmet, or untested — and flag `build-plan.md` steps ticked as done that the code doesn't actually deliver.
- **Respects architecture boundaries.** Does it sit in the right layer and talk to its neighbors the right way? Look for: a layer reaching past its boundary (e.g. a controller hitting the DB directly), leaked abstractions, circular or wrong-direction dependencies, business logic in the wrong place, and conventions the rest of the codebase follows but this code breaks.
- **Production readiness.** Will it survive contact with real traffic and real data? Look for: unhandled errors and swallowed exceptions, missing input validation, race conditions and concurrency hazards, N+1 queries and obvious performance traps, resource leaks, missing-or-misleading logging, secrets in code, auth/authorization gaps, and missing tests for the behavior that matters.

Don't force a finding into every lens. An empty lens is a good result — report it as clean.

### 4. Report by severity

Present the report directly in the conversation — do not write it to a file unless asked. Group findings into three buckets, most severe first:

- **🔴 Critical** — will break in production, lose/corrupt data, or open a security hole. Must be fixed before this ships.
- **🟡 Important** — real bugs, architecture violations, or missing safeguards that should be fixed but aren't catastrophic.
- **⚪ Minor** — style, naming, small cleanups, nice-to-haves. Safe to defer.

For each finding: the file:line link, what's wrong, why it matters, and a suggested direction for the fix (a suggestion — not an applied change). Within each bucket, order by impact.

End with a one-line verdict: is this ready to commit, ready after the critical/important items, or not yet. Then stop — the user decides what to do next.
