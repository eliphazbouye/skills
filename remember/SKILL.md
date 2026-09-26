---
name: remember
description: Wrap up a work session by compressing what happened — decisions made, patterns established, progress completed — into the project-local context/project/memory.md so the next session in this project continues without re-explaining. Use at the end of a session, when the user says "remember this", "let's wrap up", "save where we are", or before stopping work you'll resume later.
---

# Remember

The failure this prevents: every session starts from zero. You spend the first ten minutes re-explaining what was decided yesterday, and sometimes the agent contradicts a decision it made last time because nothing recorded it. This skill captures the session's durable conclusions into a single `context/project/memory.md` file so the next session in *this* project opens with continuity instead of amnesia.

This memory is **project-local, not global**. It lives in the project's `context/project/` folder as `memory.md`, travels with the project, and is shared by anyone (or any agent) working in this repo. Do not write to the global `~/.claude` memory store — everything here goes in the project's own `context/project/memory.md`.

## What to capture (and what to skip)

Capture only what a future session would otherwise have to ask about or rediscover:

- **Decisions** — a fork the user resolved, and *why* the chosen option won. ("Using Postgres not SQLite — needs concurrent writes.")
- **Patterns established** — a convention agreed this session that should hold going forward. ("API handlers return Result, never throw.")
- **Progress** — what is now done and what is the next concrete step, so resume doesn't restart. ("Auth flow complete; next is token refresh.")
- **Constraints & preferences** — guidance on how the user wants work done, with the reason.

Do **not** capture: anything the repo, git history, or CLAUDE.md already records; things that only mattered inside this conversation; or vague summaries ("worked on the app"). If it can be re-derived by reading the code, it is not a memory.

**Don't duplicate the `architect` files — point to them.** A significant decision already recorded as an ADR in `context/project/adr/` gets at most a one-line pointer ("Auth uses JWT — ADR-0001"), not a restatement. Progress on a planned feature lives in its `context/features/<slug>/build-plan.md` checkboxes; memory only says which feature is in progress and where to resume ("`auth-login` in progress — resume at S3 in its build-plan"). If a decision made this session is significant (hard to reverse, cross-cutting, sets a convention) and has no ADR yet, suggest running `/architect` to record it rather than burying it in memory.

## Process

### 1. Review the session

Scan what actually happened this session. Pull out the handful of conclusions that outlive it — the decisions, patterns, progress, and constraints above. Most sessions yield 1–4 memories, not ten. Prefer few, sharp facts over many soft ones.

### 2. Read the existing memory.md and reconcile

Look for `context/project/memory.md`. If it exists, read it first. For each candidate fact:

- **Already covered?** Update that entry in place instead of adding a near-duplicate.
- **Now wrong / superseded?** A decision reversed this session means the old entry is stale — rewrite or delete it. Contradictory memories are worse than none; they are exactly what makes the agent contradict itself.
- **Genuinely new?** Add a new entry.

If a `context/memory.md` exists at the old location (the root of `context/`), move it to `context/project/memory.md` first (`git mv` if the repo is tracked) and update any `CLAUDE.md` line that points to the old path.

If `context/project/memory.md` does not exist yet, create it (and the `context/project/` folder if needed).

### 3. Write the facts into memory.md

Keep one file, `context/project/memory.md`, organized by section. Each fact is a bullet, written in the present tense and self-contained, so it reads correctly with no memory of this conversation. Convert relative dates ("yesterday") to absolute ones. Suggested structure:

```markdown
# Project Memory

> Project-local memory for agents. Read this at the start of a session; update it at the end.

## Decisions
- Using Postgres, not SQLite — needs concurrent writes. (2026-06-09)

## Patterns
- API handlers return a Result type, never throw.

## Progress
- Auth flow complete. Next: token refresh.

## Constraints & preferences
- Keep dependencies minimal — user prefers stdlib over new packages. Why: easier audits.
```

Only include sections that have content. Keep the file tight — prune stale bullets as you go rather than letting it grow into a log.

### 4. Make sure it gets read next time

`context/project/memory.md` does not auto-load into context at session start (unlike the global store). On the **first** time you create it, ensure the next session will actually read it: check `CLAUDE.md` at the project root for a line pointing to it — or to `context/project/` as a whole, which `architect` adds when it initializes the structure — and if there isn't one, add:

```markdown
- At the start of a session, read `context/project/memory.md` for project decisions, patterns, and progress.
```

Create `CLAUDE.md` if it doesn't exist. Skip this step if the pointer is already there.

### 5. Confirm

Tell the user, briefly, what you saved into `context/project/memory.md` and what you updated or removed — so they can correct a mischaracterized decision before it carries into the next session.

## The bar

A good memory is one a fresh agent could read cold tomorrow and act on without asking a follow-up. If a candidate fact wouldn't change how the next session behaves, don't write it.
