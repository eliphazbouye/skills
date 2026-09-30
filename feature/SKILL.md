---
name: feature
description: Drive one feature end to end — from a fuzzy request to a merged, closed-out PR — in its own branch and git worktree (so several features can run in parallel, one session each), by chaining the other skills (scope → architect → build → review → verify → ship → land) without the user having to know which comes next. Reads the feature's state from context/ (brief, build plan, review findings, acceptance run, PR) to find the current stage, runs that stage's skill, moves on automatically, and stops only at the moments that are the user's to decide: interview answers, plan approval, unplanned decisions, which findings to fix, the manual checks, the PR text, pushes and the merge. Resumable at any point in any session. Use when the user wants to take a feature all the way, asks "what's next on this feature", or says "feature", "take it end to end", "de bout en bout", "pilote la feature", "amène-la jusqu'au merge", or "continue la feature X".
---

# Feature

The failure this prevents: the skills exist, but using them well means knowing the order, remembering where you left off, and typing the next command each time. So steps get skipped — the review before shipping, the check in the running app, the re-review after fixes — or the user drives the agent step by step and becomes the scheduler. This skill is the scheduler: it knows the pipeline, reads where the feature stands, and keeps it moving, handing control back only when a human decision is needed.

The goal is not to remove the user. The goal is **every stage done, in order, none skipped — with the user's attention spent only on the decisions that are theirs.**

## The pipeline

```
scope ──▶ architect ──▶ build ──▶ review ──▶ verify ──▶ ship ──▶ land
  ▲           ▲           ▲  ◀── 🔴/🟡 ──┘      │                   │
  │           │           └──◀── failures ──────┘                   │
  │           └── the plan is wrong / a new decision ◀── any stage  │
  └── the need itself changed ◀── any stage                         ▼
                                                               shipped
```

Each stage is its own skill, followed as written. This skill adds the routing between them, and the workspace: **every feature lives on its own branch, in its own git worktree**, so several can move in parallel (one session per worktree, or all of them coordinated by `endurance`). The mechanics — creating and bootstrapping worktrees, finding features, running the app in isolation, staleness, syncing with the base — are in `worktrees.md` next to this file.

## The rules

1. **One worktree, one feature, one session.** Work only inside the feature's worktree; never edit another worktree's files. Project-wide files edited on this branch (`lessons.md`, ADRs, `architecture.md`) reach the base through the merge, with the sync rules of `worktrees.md`.
2. **The state lives in context/, not in this conversation.** Always derive the stage from the files (the table below), read in the feature's worktree, never from memory of what was done earlier in the session. That's what makes `/feature <name>` resumable from any session, after any interruption.
3. **Move on by itself; stop for the user's decisions.** Between stages, don't ask "run X next?" — when a stage's skill ends with its hand-off question and the recommended option *is* the pipeline's next stage, take it without asking and say so in one line. Ask when the recommended option is something else, and always at the **decision points** each skill already has:
   - `scope` — the interview answers, the brief playback;
   - `architect` — the design questions, the plan approval;
   - `build` — an unmade decision, a plan amendment;
   - `review` — which findings to fix, which lessons to record;
   - `verify` — the manual checklist confirmation (never taken automatically);
   - `ship` — gate overrides, the PR text, the push;
   - `land` — the fixes and replies to post, the push, the merge.
4. **Never skip a stage silently.** A stage is skipped only when its own skill says it isn't needed (`scope`'s fast exit, `verify` on a change with nothing user-visible) or when the user explicitly says to — and a skipped stage is stated, and recorded in the PR by `ship`.
5. **Always leave a trace.** When `architect` finds the task trivial, it still writes a Small `build-plan.md` under this pipeline — otherwise the state table would send every resume back to `architect`.
6. **Loops go back, not around.** Review findings go back to `build`, then a re-review. Verify failures go back to `build`, then `review` of the fix, then `verify` again. A wrong plan goes back to `architect`; a changed need to `scope`. Never patch forward to keep the pipeline moving.
7. **Stuck means stop.** A stage that fails the same way twice, or a `build` that suggests `/recover`, stops the pipeline: follow `recover`, and resume with this skill once it's resolved.

## Where the feature stands

Read `context/features/<slug>/` **in the feature's worktree** (and `context/project/brief.md` for a project's first feature) and pick the **first** row that matches.

Terms: an item is **open** if it's `[ ]` or `[~]` (fixed, not yet confirmed); struck items (won't fix / accepted) are ignored. **Stale** is defined in `worktrees.md` → *Stale* (the code the feature touches changed since the recorded HEAD). **Ready** means: no open 🔴/🟡, and the last review isn't stale. **Passed** means: no failing scenario, no `manual — pending` item, and the run isn't stale.

| State in context/ | Stage |
|---|---|
| no folder, or no brief and no build plan | `scope` (its fast exit hands over to `architect` if the need is already clear) |
| `brief.md` with `Status: draft` | `scope` — resume the interview |
| brief final, no `build-plan.md` | `architect` |
| plan `draft`, or unticked steps | `build` |
| `[ ]` 🔴/🟡 items under *Review findings* (R or V) | `build` — fix them |
| all steps ticked but `Status:` isn't `done` | `build` — its finish step |
| `[~]` R items, or no review, or the last review is stale | `review` (a re-review if a *Last review* header exists) |
| ready, and no *Acceptance run*, or it's stale, or `[~]` V items, or `manual — pending` items | `verify` (skipped only if the change has nothing a user can see or trigger — say so) |
| ready and passed (or verify skipped), no `PR:` | `ship` |
| `PR:` set, not merged | `land` |
| `PR:` merged (`gh pr view`) but `Status:` isn't `shipped` | `land` — its close-out |
| `Status: shipped` (on the base branch) | done — report the *Follow-up* success check, if any |

**A bug fix** (`context/fixes/<slug>.md`) follows the same table from the `build` rows on, with `fix` as its first stage (no record yet → `fix`).

Check the git state against it (the worktree's branch, uncommitted work, unpushed commits). If they disagree — the plan says `done` but there's uncommitted code, the branch is gone — report it and ask before choosing a stage.

## Process

### 1. Pick the feature and its worktree

Find every feature in flight (`worktrees.md` → *Finding every feature in flight*) — across all worktrees and `feat/*` / `fix/*` branches, not just the current checkout.

- **The user names it or describes it** → match it on slug and on brief/spec titles.
  - It has a worktree, and this session is in it → continue.
  - It has a worktree elsewhere → move there (`worktrees.md` → *Entering*): this session moves in, or — if another session may already be working there, or this session drives something else — give the user the command for a new session and stop.
  - It has a branch but no worktree → recreate the worktree on that branch and bootstrap it.
- **A new request** → agree on the slug in one line (short kebab-case, English, no date — `scope` and `architect` keep it). Then, **before `scope` writes anything**: make sure the recipe exists (`worktrees.md` → *The recipe*), create and bootstrap its worktree on `feat/<slug>` with its ports (*Create and bootstrap*), and enter it (*Entering*) — from then on, the worktree is the working root. `wt.py create <slug>` makes the worktree and assigns the ports. If a feature it depends on is still in flight, stack it (`--from feat/<other>`, `worktrees.md` → *Stacked features*). A bug → `fix/<slug>` in `fix-<slug>`, and the `fix` stage.
- **No name** → list the features that aren't `shipped`, each with its worktree and stage, and ask with AskUserQuestion which one to drive (recommend the one this worktree is on). With several in flight, mention `/endurance` for the whole picture.

### 2. Announce, log and run

Show one line with where the feature is:

```
export-csv   scope ✓ · architect ✓ · build ✓ · review ✓ · ▶ verify · ship · land
```

Then log it (`wt.py event <slug> <stage> start`, see `worktrees.md` → *Flow log*; `wait` / `resume` around each question the stage puts to the user, `end` when it finishes) and follow the stage's skill in full. When it ends, re-read the state (rule 2), show the updated line, and go to the next stage.

### 3. Keep the session healthy

A whole feature in one session is long. At a stage boundary — typically after `build`, which uses the most context — if the conversation has grown heavy, offer: "Save with `/remember`, then continue in a fresh session in this worktree with `/feature <slug>` (Recommended)" / "Continue here". Everything the next stage needs is already in context/, so nothing is lost.

Under `endurance`, this skill isn't driving: endurance runs the stages and its workers follow `endurance/worker-prompt.md`.

### 4. Finish

When the table says `shipped`: show its numbers (`wt.py metrics <slug>` — lead time, where the time went, quality). `land` has already offered to remove the worktree (`worktrees.md` → *Removing*). Report in a few lines what was built, the PR, the decisions recorded (ADRs), the lessons added, and the *Follow-up* success check with its date. Suggest `/remember` if the session goes on with something else.

If the user stops at any point, say which stage the feature is at and that `/feature <slug>` resumes it; suggest `/remember`.
