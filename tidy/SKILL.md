---
name: tidy
description: Audit the project's context/ folder so it keeps telling the truth. Finds broken references (UC/AC/ADR/L ids that don't exist), ADR numbering problems, accepted ADRs the code no longer follows, stale or inconsistent build plans, lessons that are duplicated, already enforced or overdue for escalation, an oversized or stale memory.md, and CLAUDE.md commands that no longer exist. Reports a fix list grouped by file, applies only the fixes the user picks, and routes the rest to the skill that owns it. Never changes the code. Use every few weeks, before a large feature, when agents seem to follow outdated guidance, or whenever the user says "tidy", "clean up the context", "range le contexte", "is the context up to date", or "audit context".
---

# Tidy

The failure this prevents: `context/` is what every agent reads first, so when it's wrong, every agent is wrong in the same way. It rots quietly — a plan left `in-progress` for a feature shipped a month ago, an ADR the code stopped following, a lesson already caught by the linter still taking up attention, a memory file that grew to two hundred lines, a spec pointing at `ADR-0007` which doesn't exist. None of it shows up in a diff. This skill looks at the whole folder at once and finds it.

The goal is not to rewrite the documentation. The goal is **a context/ folder that's accurate, consistent and small — with every correction decided by the user.**

## The rules

1. **Report, then apply only what's picked.** Findings are a fix list. Mechanical fixes (a status line, a broken link, moving a lesson to *Enforced*) are applied only after the user picks them; anything that's a real decision is routed, not decided.
2. **Accepted ADRs are never edited.** An ADR the code no longer follows is either code drift (a fix list for the code) or an outdated decision (a new ADR that supersedes it, via `/architect`). Only an ADR's *Status* line ever changes.
3. **Never touch the code.** Code that breaks the context is reported with `file:line`; fixing it is `/build`'s job.
4. **Route to the owner.** Each file has a skill that owns it — architecture drift goes to `/map`, decisions to `/architect`, session state to `/remember`, UI patterns to `/imprint`. This skill finds problems across all of them; it doesn't take over their judgment.

## Process

### 1. Inventory

List everything under `context/`, plus `CLAUDE.md`, `CLAUDE.local.md`, and the ADR folder if it lives elsewhere (`context/README.md` says where). Note each feature folder and its plan's `Status:` and `Updated:` dates.

### 2. Run the checks

**Structure**
- Files in legacy locations (`context/memory.md`, `context/ui-registry.md` at the root) or outside the layout in `context/README.md`.
- `CLAUDE.md` missing the context pointer, or pointing to paths that don't exist.

**References**
- Every `UC-n`, `AC-n`, `ADR-NNNN`, `L-NNN` and relative link cited in any context file resolves to something that exists.
- ADR numbering: duplicates, and ADRs marked `Superseded by ADR-NNNN` whose successor doesn't exist or doesn't point back.

**ADRs vs code**
- For each accepted ADR with a checkable claim ("all DB access goes through `src/db/`", "we use Zod for validation"), spot-check the code. For many ADRs, fan out read-only `Explore` subagents, a few ADRs each, returning violations with `file:line`.
- Broader drift between `architecture.md` and the code is `/map`'s job (re-map) — suggest it rather than redoing it.

**Features**
- Every step ticked but `Status:` not `done`, or `done` with unticked steps or unticked 🔴/🟡 review findings.
- `in-progress` plans with no recent activity: compare `Updated:` and `git log` on the files the plan touches. Stale → abandoned, blocked, or finished without updating?
- `done` plans with a `PR:` link — is the PR merged? (`gh pr view`, if available.)
- Specs whose acceptance criteria no plan step cites.

**Lessons** (`lessons.md`)
- Duplicate or overlapping lessons.
- Lessons already enforced: search the lint/type/test config for a rule that covers them → candidates for *Enforced*.
- Lessons seen 3+ times, or born from a 🔴, still not escalated to a lint rule, test or CLAUDE.md rule.

**Memory** (`memory.md`)
- Over ~60 lines.
- *Resume here* disagreeing with git (branch, uncommitted work, a feature since finished).
- *Dead ends* whose problem is solved; entries that belong in another file (a decision that deserves an ADR, a convention that belongs in `architecture.md`).

**Commands**
- The commands listed in `CLAUDE.md` still exist (scripts in `package.json`, `Makefile` targets, …). Don't run anything with side effects to check.

### 3. Report

Present the fix list in the conversation, grouped by file, each finding marked:

- **Wrong** — says something false (a broken reference, an ADR the code violates, a status that lies).
- **Stale** — was true, isn't current (an old *Resume here*, a finished plan still `in-progress`).
- **Bloat** — true but costs attention for nothing (duplicates, enforced lessons still active, oversized memory).

For each: the location, what's off, and the proposed fix — marked **mechanical** (this skill can apply it) or **routed** (which skill owns it, and why).

### 4. Apply what's picked

Ask with AskUserQuestion, multiSelect, one option per group of mechanical fixes (e.g. "Fix 4 broken references", "Mark 2 finished plans done", "Move 3 lessons to Enforced", "Trim memory.md to its essentials") — recommend the *Wrong* groups. Apply only those. For memory changes, show the entries to be removed first; never drop one silently.

End with the routed items as a short list of next steps — "`/map` to re-map `src/billing/`", "`/architect` to supersede ADR-0004", "`/build` to fix the 3 ADR violations" — and one line on what was changed.
