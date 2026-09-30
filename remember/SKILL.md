---
name: remember
description: Carry a project's working state across sessions. At the end of a session (save mode), it files what happened into the right place in context/ — ticks finished build-plan steps, adds new conventions to architecture.md, flags decisions that need an ADR — and keeps context/project/memory.md for the rest: where to resume, git state, dead ends, small decisions. At the start of a session (resume mode), it reads it all back and briefs you on where things stand and the next action, handing off to the interrupted skill (a `scope` interview, a `build`). Use when the user says "remember this", "let's wrap up", "save where we are", "on s'arrête là", before stopping work you'll resume later — or, to resume, "where were we", "resume", "où on en était", "reprends".
---

# Remember

The failure this prevents: every session starts from zero. You spend the first ten minutes re-explaining what was decided yesterday, the agent retries the approach that already failed, and sometimes it contradicts a decision it made last time because nothing recorded it. This skill closes a session by putting its durable conclusions where the next session will find them — and opens the next one by reading them back.

Everything stays **project-local**: it lives in the project's `context/`, travels with the repo, and is shared by anyone (or any agent) working in it. Do not write to the global `~/.claude` memory store.

## Two modes

- **Save** — end of a session, or a checkpoint before a long pause or a context compaction. Steps S1–S6.
- **Resume** — start of a session: "where were we", "resume", "où on en était", "reprends". Steps R1–R3.

If it's unclear which one the user means, it's save when there's session work to record and resume when the session has just started.

## Where things go

`memory.md` is the **last resort**, not the default. Each fact goes to the one place designed for it:

| Fact from the session | Goes to | Who writes it |
|---|---|---|
| An interrupted `scope` interview | the draft brief's *Ledger* (`context/features/<slug>/brief.md` or `context/project/brief.md`) — check it reflects the last answers; *Resume here* just points to it | `scope` writes it as it goes; this skill checks it |
| Progress on a planned feature | tick the steps in `context/features/<slug>/build-plan.md` | this skill (after checking the code) |
| A new project-wide convention ("handlers return Result, never throw") | *Conventions* in `context/project/architecture.md` | this skill, with the user's OK |
| A new UI pattern | `context/project/ui-registry.md` | suggest `/imprint` |
| A significant decision — hard to reverse, cross-cutting, sets a convention | an ADR in `context/project/adr/` | suggest `/architect` |
| A decision specific to one feature | that feature's `spec.md` (*Decisions*) | this skill, with the user's OK |
| A mistake found in a review | `context/project/lessons.md` | `review` — not this skill |
| A personal preference of the user ("reply in French", "small commits") | `CLAUDE.local.md` (not committed) | this skill, with the user's OK |
| Where to resume, git state, blockers — in a feature's worktree | *Resume here* in that feature's `build-plan.md` (or its brief, before a plan exists) | this skill |
| Where to resume, git state, blockers — in the main worktree | *Resume here* in `memory.md` | this skill |
| An approach tried and ruled out | *Dead ends* in `memory.md` | this skill |
| A small project decision with no better home | *Small decisions* in `memory.md` | this skill |
| A rule for everyone on this project | *Project constraints* in `memory.md` | this skill |

Never write the same fact in two places. If it's already recorded in its proper home, memory at most points to it.

Do **not** record: anything the code, git history, or CLAUDE.md already says; things that only mattered inside this conversation; vague summaries ("worked on the app"). If a fresh agent could re-derive it by reading the repo, it isn't worth writing.

## Save mode

### S1. Review the session

Scan what actually happened. Pull out the few conclusions that outlive it and sort each into the table above. Most sessions yield a handful of facts, not ten.

Look hard for **dead ends** — approaches tried and abandoned, with the reason. They're the most expensive thing to lose: without them, the next session retries the same thing.

### S2. Establish the ground truth

- Run `git status` and note the current branch; unpushed commits: `git log @{u}..HEAD` if the branch has an upstream, otherwise all commits since `origin/<base>` are unpushed.
- For each build-plan step the session worked on, check in the code that it's really done before ticking it.

### S3. Reconcile with what's already written

Read `context/project/memory.md` (and, if it's still at the old location `context/memory.md`, move it to `context/project/` first — `git mv` if the repo is tracked — and update any `CLAUDE.md` line pointing to the old path).

- **Already covered?** Update the entry in place — no near-duplicates.
- **Superseded?** A decision reversed this session makes the old entry stale: rewrite or remove it. Contradictory memories are worse than none.
- **Still true?** Spot-check existing entries that make claims about the code (a constraint, a small decision) against the code as it is now. An entry the code no longer matches is flagged for removal, not silently kept.
- **Solved dead ends** — remove them; the problem is gone.
- **Misplaced entries** — an old *Decisions*/*Patterns*/*Progress* entry from before this layout gets moved to its proper home per the table (or dropped if already recorded there).

### S4. Keep it small

`memory.md` is read at the start of every session, so every line costs context. Keep it under **~60 lines**. Over that, prune: move entries to their proper home, drop what's no longer needed, merge what overlaps. Never grow it into a log. If the whole `context/` seems out of date — not just memory — suggest `/tidy`.

### S5. Confirm, then write

Show the user what you're about to do, grouped by file — additions, updates, **removals** (never remove a memory silently), ticked steps, and anything routed to another skill ("this decision needs an ADR — run `/architect`"). Then ask with AskUserQuestion: "Save as shown (Recommended)" / "Change something" / "Cancel".

On approval, write:

- `context/project/memory.md` — from `templates/memory.md` if it doesn't exist; *Resume here* rewritten every time (it's a snapshot, not a history); only sections with content. Present tense, self-contained bullets; absolute dates. Write in the language the user works in.
- The other files from S1's routing — ticked steps, conventions, feature decisions, `CLAUDE.local.md` preferences. If `CLAUDE.local.md` is created, make sure it's git-ignored.

### S6. Make sure it gets read next time

`memory.md` doesn't load on its own. Check that `CLAUDE.md` (create it if missing) points to it — either directly or through the `context/project/` pointer that `architect` installs. If neither is there, add:

```markdown
- At the start of a session, read `context/project/memory.md` — start with "Resume here".
```

The **first** time you save in a project, offer once (don't insist) to set up a Claude Code hook that reminds the user to run `/remember` before a context compaction or at the end of a session — via the `update-config` skill, in the user's settings, not in the repo.

End with one line: what was saved where, and the next action recorded in *Resume here*.

## Resume mode

### R1. Read the state

- In a feature's worktree (`git worktree list`, the branch is `feat/*` or `fix/*`): that feature's *Resume here* in its build plan first. Otherwise `context/project/memory.md` — *Resume here* first. Then *Dead ends*.
- Other features in flight in other worktrees: one line each, and suggest `/endurance` if there are several.
- Any brief still in `Status: draft` (`context/features/*/brief.md`, `context/project/brief.md`): an interrupted `scope` interview — its open high-impact ledger entries.
- The build plan of the feature in progress: first unticked step, and unticked items under *Review findings*.
- `git status`, the current branch, unpushed commits — and compare with what *Resume here* says. If they disagree (other commits landed, the branch changed, the uncommitted work is gone), that's the first thing to report.
- The active entries of `context/project/lessons.md` that apply to the next step.

### R2. Brief the user

Five lines at most:

- where things stand (feature, step, git state);
- what's blocking, if anything;
- any mismatch between memory and reality;
- the dead ends and lessons relevant to what's next;
- **the proposed next action.**

### R3. Hand over

Ask with AskUserQuestion: "Continue with <next action> (Recommended)" — through `/build` when it's a build-plan step or an open review finding — / "Work on something else" / "Review first (`/review`)" — adapt the options to the state (e.g. `/feature <slug>` routes any feature to its next stage; otherwise recommend resuming `/scope` when a brief is still a draft, `/architect` when a brief is final but the feature has no build plan yet, `/verify` when it's reviewed but not checked in the running app, `/land` when its PR is open, recommend `/review` when a feature's steps are all ticked but it was never reviewed, and `/ship` when it's `done`, reviewed and has no `PR:` yet). Don't start working before the user picks.

## The bar

A good save is one a fresh agent could read cold tomorrow and act on without a follow-up question — and a good resume gets the user back to work in one exchange. If a fact wouldn't change what the next session does, don't write it.
