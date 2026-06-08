---
name: remember
description: Wrap up a work session by compressing what happened — decisions made, patterns established, progress completed — into the persistent memory store so the next session continues without re-explaining. Use at the end of a session, when the user says "remember this", "let's wrap up", "save where we are", or before stopping work you'll resume later.
---

# Remember

The failure this prevents: every session starts from zero. You spend the first ten minutes re-explaining what was decided yesterday, and sometimes the agent contradicts a decision it made last time because nothing recorded it. This skill captures the session's durable conclusions into memory so the next session opens with continuity instead of amnesia.

The memory store does the loading for you. Files in the memory directory, indexed by `memory.md`, are surfaced into context at the start of each session. Your job here is only the *writing* — turning a messy session into a few clean, durable facts.

## What to capture (and what to skip)

Capture only what a future session would otherwise have to ask about or rediscover:

- **Decisions** — a fork the user resolved, and *why* the chosen option won. ("Using Postgres not SQLite — needs concurrent writes.")
- **Patterns established** — a convention agreed this session that should hold going forward. ("API handlers return Result, never throw.")
- **Progress** — what is now done and what is the next concrete step, so resume doesn't restart. ("Auth flow complete; next is token refresh.")
- **Constraints & preferences** — guidance on how the user wants work done, with the reason.

Do **not** capture: anything the repo, git history, or CLAUDE.md already records; things that only mattered inside this conversation; or vague summaries ("worked on the app"). If it can be re-derived by reading the code, it is not a memory.

## Process

### 1. Review the session

Scan what actually happened this session. Pull out the handful of conclusions that outlive it — the decisions, patterns, progress, and constraints above. Most sessions yield 1–4 memories, not ten. Prefer few, sharp facts over many soft ones.

### 2. Reconcile before writing

For each candidate, check the existing memory directory and `memory.md` first:

- **Already covered?** Update that file instead of creating a near-duplicate.
- **Now wrong / superseded?** A decision reversed this session means the old memory is stale — rewrite or delete it. Contradictory memories are worse than none; they are exactly what makes the agent contradict itself.
- **Genuinely new?** Write a new file.

### 3. Write each memory as one file

One fact per file. Frontmatter:

```markdown
---
name: <short-kebab-case-slug>
description: <one-line summary — used to decide relevance during recall>
metadata:
  type: user | feedback | project | reference
---

<the fact. For feedback and project, follow with **Why:** and **How to apply:** lines.
Link related memories with [[their-name]].>
```

Type guide: `project` — ongoing work, goals, decisions, progress (convert relative dates like "yesterday" to absolute). `feedback` — how the user wants you to work, including the why. `user` — who they are. `reference` — pointers to external resources (URLs, tickets, dashboards). Link liberally with `[[name]]`; a link to a memory that doesn't exist yet is fine — it marks one worth writing later.

Write the fact in the present tense, self-contained, so it reads correctly with no memory of this conversation.

### 4. Update the index

For each new memory, add one line to `MEMORY.md`:

```
- [Title](file.md) — short hook of what it covers
```

Update the existing line if you edited a file; remove it if you deleted one. Never put memory content in `MEMORY.md` itself — it is the index loaded every session, one line per memory.

### 5. Confirm

Tell the user, briefly, what you saved and what you updated or removed — so they can correct a mischaracterized decision before it carries into the next session.

## The bar

A good memory is one a fresh agent could read cold tomorrow and act on without asking a follow-up. If a candidate fact wouldn't change how the next session behaves, don't write it.
