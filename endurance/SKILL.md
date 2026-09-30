---
name: endurance
description: Act as the tech lead for several features built in parallel, each in its own git worktree — and make delivery faster over time without lowering quality. From the main worktree, shows a board of every feature in flight (stage, owner, worktree, PR, who's waiting on what), catches conflicts early — between plans before code exists, between branches, and by merging all active branches together and running the tests — decides the merge order (stacking dependent features), keeps work-in-progress limited, starts new features in bootstrapped worktrees, and delegates the code-heavy stages to background worker subagents that talk to each other through a shared message channel and whose decisions it batches and puts to the user. Tracks how long each feature and stage takes (active time, waiting on the user, rework, CI and delivery time) with quality counters beside it, finds the bottleneck and proposes changes that shorten build and delivery. Watches PRs and notifies the user when something needs them. Never decides for the user, never removes a quality gate, never merges unasked. Use when working on several features at once, to see delivery metrics, or whenever the user says "endurance", "tech lead", "orchestre les features", "plusieurs features en parallèle", "où en sont toutes les features", "dashboard des features", "combien de temps pour livrer", or "livrer plus vite".
---

# Endurance

The failure this prevents: three features in three worktrees, three terminals. Each session does its job, none sees the others. Two of them change the same service in incompatible ways and nobody notices until the second merge breaks — or worse, merges cleanly and breaks at runtime, because git only sees conflicting lines, not a renamed function the other branch still calls. Both created `ADR-0006`. One has been waiting on a question for a day because its terminal was buried. Ten features are half-done and none ships. And nobody knows whether shipping takes two days or two weeks, or where the time goes. `/feature` drives one feature well; this skill is the view from above — the one place where the user answers every question, and the one that makes the whole system faster.

The goal is not to build faster by skipping steps. The goal is **several features moving at once, each through the full pipeline, conflicts caught early, the user's attention spent only on decisions — and a lead time that goes down while quality holds.**

## The rules

1. **The user decides; endurance routes.** Every decision a stage raises — from a worker or from a conversation — goes to the user through AskUserQuestion, labelled with the feature's slug. Endurance never answers a worker's question itself, and never takes a "(Recommended)" option on the user's behalf except the pipeline hand-offs `feature` already takes automatically.
2. **Delegate the long work, keep the conversations.** `build`, fixing findings (from `review`, `verify` or `land`), `verify`, a bug fix's steps 2–5 and syncs with the base run in background workers. `scope`, `architect`, `review` (which spawns its own fresh reviewer) and its choices, a fix's report capture, `ship` and `land` run in this session, with the user, against the feature's worktree as the **working root** (`../feature/worktrees.md` → *The working root*) — never against the main worktree.
3. **One agent per worktree.** Never two workers on one feature, never a stage run here in a worktree where a worker is running (the `.endurance-worker` marker).
4. **State on disk, always.** The board is rebuilt from git, the context/ files and the shared state (`wt.py`), never from memory of this conversation. This session can be closed at any time; `/endurance` rebuilds everything.
5. **Nothing outward-facing without approval.** Pushing, PRs, comments, merges, deleting branches or worktrees: only through `ship` and `land`, with their approvals. Workers never push.
6. **Conflicts are decisions.** When two features collide, endurance reports it with the evidence and asks — sequence them, stack one on the other, merge the plans, or re-scope.
7. **Finish before starting.** Work in progress is limited (default **3** features in flight, or the `WIP limit` in CLAUDE.md's `## Worktrees`). Above the limit, recommend finishing one before starting another — every feature that lingers accumulates conflicts with the others.
8. **Faster, never looser.** Speed comes from smaller features, less waiting, less rework and faster tooling — never from skipping `review`, `verify`, a test, or the gate in `ship`. Every flow change is judged on lead time **and** the quality counters together.
9. **Someone else's branch is read-only.** A feature whose commits are by another person (the board's *owner*) is shown, checked for conflicts and messaged — never worked on, synced or delegated to a worker without that person.

## The tooling

`../feature/scripts/wt.py` implements the mechanics in `../feature/worktrees.md` — use it instead of retyping git commands:

| Need | Command |
|---|---|
| Every feature in flight, with facts | `wt.py board` (`--gh` for PR states, `--json` for details) |
| Conflicts between plans and branches | `wt.py overlap` |
| All active branches merged together + tests | `wt.py integrate --test "<the project's test command>"` |
| New worktree, branch and ports | `wt.py create <slug>` (`--fix`, `--from feat/<other>` to stack) |
| Is a review / acceptance run still valid | `wt.py stale <worktree> <recorded HEAD>` |
| ADR / lesson numbers colliding after a sync | `wt.py renumber <worktree>` then `--apply` |
| Messages between workers | `wt.py mail post / read / list` |
| Time per feature and stage | `wt.py event …` (logging), `wt.py metrics` (`--gh` for CI and delivery) |

Run it from the main worktree (`python3 <skills>/feature/scripts/wt.py …`). The shared state (ports, messages, flow log) lives in the repository's git directory — shared by every worktree, never committed.

## Process

### 1. Build the board

Run `wt.py board --gh` and show it, adding what only this session knows: a worker running (launched from here), the question it's waiting on.

- **Stage** — the script's best guess from `feature`'s state table; confirm it against the files when it matters.
- **Waiting on** — *worker running*, *you* (the `asks` column counts pending decisions written in the plans, so they survive a closed session), *CI / reviewers*, *nothing — ready to advance*.
- **⚙ without a worker running here** — a worker was interrupted: show *interrupted?*, look at the uncommitted files (✎), and ask before relaunching.
- **owner** — rule 9.
- **mail** — unread messages for that feature.

Also flag worktrees without a feature branch, branches without a worktree, and merged features whose worktree still exists (removal candidates). If the Artifact tool is available and the user wants it, publish the board as a page they can keep open (load `artifact-design` first) and republish it when it changes.

### 2. Catch conflicts early

Three levels, cheapest first:

- **Plans** — as soon as `architect` writes a plan, run `wt.py overlap`: it compares the files each plan *intends* to touch (its *Code context* and steps) with the other features' plans and changes. An overlap found here costs a conversation, not a rework: propose an order, a stack (step 6), or merging the two plans.
- **Branches** — `wt.py overlap` also reports files changed on both branches, both editing `architecture.md`, and the same new ADR number.
- **Integration** — before each merge, and whenever two active branches share files, run `wt.py integrate --test "<test command>"` (with the database and ports of an unused slot, per the recipe): it merges every active branch into a scratch worktree on top of the base and runs the tests. It catches the conflicts git doesn't flag — a function renamed on one branch and still called on another. A failure is reported to the features involved (message + the board), and fixing it is a decision.

Also check **boundaries** (both touch the same module or external service in `architecture.md`) and **decisions** (ADRs about the same subject on two branches) by reading the plans. Report each risk with evidence and a recommendation; real collisions are decisions (rule 6).

### 3. Decide what moves next

- **Waiting on the user** → the decision queue (step 5).
- **At a delegated stage** with no worker → launch one (step 4).
- **At a conversational stage** → run it with the user in this session, with the feature's worktree as working root, one feature at a time; for a long `scope` or `architect`, offer a dedicated session: `cd <path> && claude "/feature <slug>"`.
- **`review`** → from this session, passing the worktree to the reviewer (per `review`); the findings picked for fixing go to a worker.
- **A new bug** → capture the report with the user (`fix` step 1), `wt.py create <slug> --fix`, write the fix record at once, delegate steps 2–5.
- **Can't-be-isolated resources** (the recipe's list) → never two stages using them at once.
- **New feature requested above the WIP limit** → rule 7: show what's closest to done, and recommend finishing it first. The user decides.

**How many workers.** At most 3 at once by default. Fewer when decisions pile up: with 2 or more decisions waiting on the user, don't launch more workers — they'd only add questions. More only if the user asks.

### 4. Delegate to workers

Launch each worker with the Agent tool (`general-purpose`, in the background — several in one message when starting several). The prompt is **the full content of `worker-prompt.md`**, verbatim, followed by:

```
## Assignment
- Feature: <slug> · worktree: <absolute path> · branch: <branch>
- Stage: <build | build: fix open findings | verify | fix: steps 2–5 | sync with the base> — follow <absolute path to that skill's SKILL.md, or to feature/worktrees.md for a sync>
- Tooling: python3 <absolute path to feature/scripts/wt.py>
- Commit policy: commit after each verified step
- Isolation: ports <app> / <db> from the plan header; env file and database per the Worktrees recipe
- Other features in flight: <slug — one line on what it changes, from its plan>, …
- Language for context/ files: <the user's language>
```

Log the start: `wt.py event <slug> <stage> start`. When a worker reports:

- **done** → `event … end`, re-read the state, update the board, step 3.
- **needs-decision** → `event … wait`, add it to the queue.
- **blocked** → `event … end --note blocked`; propose `/recover` in that worktree. Don't relaunch blindly.
- **verify with manual items** → the app is still running at the URL it gives: put the checklist to the user, then stop the app and record the answers.

After each report, check the main worktree wasn't touched (`../feature/worktrees.md` → *The working root*), and read `wt.py mail list` for messages the report mentions.

### 5. The decision queue

Pending decisions are on disk (*Open questions* entries `— unblocked by: user (pending)`). Before asking:

- **Batch what belongs together.** Decisions from different features about the same subject (the same API, the same convention, the same data) become one question: the answer applies to all of them, and a split answer would build the conflict in.
- **Order** — what blocks the most first (a feature others depend on, the one closest to merging).

Ask with AskUserQuestion — one decision per call, header = the slug (or "orders-export + notif"), the worker's question and options (recommended first). Put the worker's **code excerpt** in the recommended option's `preview`, and each option's **impact** in its description, so the user decides without opening the worktree. After the answer: `wt.py event <slug> <stage> resume`, send it to the worker with SendMessage (it records it and clears the *pending* mark); if the worker is gone, record the answer in the worktree and launch a new worker for the same stage.

### 6. Dependencies and stacking

When feature B needs feature A (a plan cites it, or the project brief orders them):

- **Stack** instead of waiting: create B from A's branch (`wt.py create <b> --from feat/<a>`), note `**Depends on:** feat/<a>` in B's plan header. `ship` opens B's PR against `feat/<a>`, so its diff shows only B.
- **When A merges**: rebase B onto the base, dropping A's commits (`git -C <B> rebase --onto origin/<base> <A's last commit B was built on> feat/<b>`), retarget B's PR (`gh pr edit <n> --base <base>`, with approval), and let the staleness rule re-check B.
- Never merge B before A.

### 7. Merge and resync

A feature reaching `land` merges only on the user's request. Before it, run the integration check (step 2). After a merge:

- For every other active branch that shares files or boundaries with it, sync with the base (`../feature/worktrees.md` → *Sync with the base*, then `wt.py renumber`) — in a worker, but only once no worker is running in that worktree; a conflict comes back as a decision and is redone here with the user. Staleness sends it back to `review` / `verify` if its files were touched.
- Post a message to all (`wt.py mail post --from endurance --to all "<slug> merged: <what changed that others use>"`).
- Offer to remove the merged worktree and branch (*Removing*), and `wt.py ports release <slug>`.

### 8. Watch and notify

While features wait on CI, reviewers or the user, keep watching without being asked each time:

- Offer to run `/loop 15m /endurance watch` (the `loop` skill). In **watch mode**, refresh `wt.py board --gh` and `wt.py mail list`, and act only on changes: CI turned red or new review comments on a PR (→ run `land`'s triage for it, or queue it), a worker finished, a new pending decision, a PR approved and green (→ ready to merge — ask).
- **Notify** when the user is needed — a decision is waiting, a PR is ready to merge, a worker is blocked: use the PushNotification tool if it's available (one short line: the slug and what's needed), otherwise say it at the top of the next message.
- Stay quiet when nothing changed.

### 9. Measure the flow — and shorten it

**Log every stage** (this session and the workers do it): `wt.py event <slug> <stage> start` when a stage begins, `wait` when it stops for the user, `resume` when answered, `end` when it finishes, and `land` logs `shipped` at the merge. That's what `wt.py metrics` turns into:

- **lead time** per feature (first event → shipped), and the median over shipped features;
- **per stage**: active time, time waiting on the user, re-runs (a stage entered twice is rework — a review round, a failed verify);
- **idle** time between stages (nobody moved it on);
- with `--gh`: **CI** duration per workflow on each branch, and the **delivery** workflows on the base (deploy / release) — the time from merge to production;
- **quality counters** beside the speed: review rounds, 🔴 found, verify failures, bugs fixed later in that feature's code (fix records citing it).

`land` writes the feature's own numbers into its plan (*Timeline*, from `wt.py metrics <slug> --markdown`) at the close-out.

**Improve** — after every 3 shipped features, or when the user asks ("combien de temps pour livrer ?", "livrer plus vite"): run `wt.py metrics --gh`, find the stage that takes the largest share, and propose changes targeted at it — each with the expected gain, its cost, and how quality is protected:

| Where the time goes | Typical changes |
|---|---|
| **Waiting on the user** (scope, decisions, manual checks) | fewer, better questions in `scope` so fewer surface later; batching decisions (step 5); notifications (step 8); a checklist ready before the app is up |
| **Build** is long | smaller features (split the plan into shippable slices); a faster local test loop — run only the tests near the change during a step, the full suite at the end; test-suite speed (profile the slowest tests; parallelize) |
| **Rework** (review rounds, verify failures) | the recurring findings as lessons escalated to lint rules or tests; clearer acceptance criteria in `architect`; verify's scenarios run earlier, during build |
| **CI** is long | caching dependencies and builds, parallel jobs, running only affected tests on PRs (full suite on the base), failing fast (lint and typecheck first) |
| **Merge → production** is long | a deploy triggered on merge, smaller and more frequent deploys, migrations decoupled from deploys, a faster build image, a rollback that's one command |
| **Idle** between stages | the watch mode (step 8); the WIP limit (rule 7) so fewer features wait for attention |

Each change the user picks becomes a normal piece of work — a `/spike` if its gain is uncertain ("does caching cut CI below 5 minutes?"), then a feature (`ci-cache`) through the full pipeline, with its expected gain in the brief's *Success*. After it ships, compare the next features' metrics **and** quality counters with before; a gain that costs quality (more 🔴, more verify failures, more bugs after ship) is reverted or reworked — rule 8.

### 10. Retro after each merge

When `land` closes a feature out, read its *Timeline* and the review/verify history, and draft a short retro with the user: what took the longest and why, what was reworked and why, what went well. A cause that could slow another feature (a missing test fixture, an unclear convention, a flaky CI job) becomes a **process lesson** in `context/project/lessons.md` (`L-NNN`, stated as an instruction, *Seen:* `retro YYYY-MM-DD <slug>`), picked by the user — the same way `review` turns code mistakes into lessons.

### 11. Start a new feature

Agree on the slug, check the WIP limit (rule 7), make sure the recipe exists (*The recipe*), `wt.py create <slug>` (or `--from` to stack, step 6), bootstrap with the assigned ports, log `wt.py event <slug> scope start`, check the intent against the board (step 2), then run its `scope` — here, or in a dedicated session.

### 12. Keep this session light

This session sees every feature; it must not carry their details. Workers' reports are short by design; the detail lives in context/. When the conversation grows heavy, offer: "Close this session once the running workers report — `/endurance` rebuilds the board from disk (Recommended)" / "Continue". Closing it stops running workers: what they committed, their pending decisions and the flow log are on disk; a step in progress restarts — the marker shows where.

When the user stops: show the board one last time, with what each feature waits on.
