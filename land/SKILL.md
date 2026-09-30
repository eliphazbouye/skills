---
name: land
description: Take an open pull request from "opened" to "merged and closed out". Watches the CI and fixes what fails (reproduced locally, regression test first), triages every human review comment into fix / reply / question and drafts the answers, pushes and posts only after the user approves, merges only when the user explicitly asks and the PR is green and approved, after syncing with the base and renumbering colliding ADRs/lessons, commits the close-out on the branch just before the merge — build plan marked shipped, success check scheduled from the brief, lessons drawn from what reviewers caught — then removes the feature's worktree and branch. Use after `ship` has opened a PR, when CI fails on a PR, when review comments come in, or whenever the user says "land", "suis la PR", "la CI est rouge", "traite les commentaires de la PR", "merge it", "on peut merger", or "close out the feature".
---

# Land

The failure this prevents: the PR is open, so the feature feels done — and then it sits. CI went red on a flaky-looking test nobody looked at, a reviewer's comment about a missing permission check got a "will fix" and was forgotten, the branch got merged with a stale approval, and `context/` still says the feature is `done`-but-not-shipped three weeks later. This skill carries the PR the last mile and makes the record say what actually happened.

The goal is not to get to "merged" fast. The goal is **a merge the reviewers actually agreed to, with every comment answered, and a context/ that knows the feature is live.**

## The rules

1. **Nothing outward-facing without approval.** Pushing commits, posting a reply or a review comment, resolving a thread, merging: each happens only after the user has seen exactly what will be sent. Drafting is free; publishing is the user's call.
2. **Merge only when asked.** Merging happens on the user's explicit request, and only when the checks are green and the required approvals are current. A merge the user wants despite a red check or a missing approval is their explicit override, stated back to them first.
3. **Every comment gets an outcome.** Fixed (with the commit), answered (with the reply), or declined (with the reason) — none left silently pending. A reviewer's point is never dismissed without the user deciding to.
4. **CI failures are bugs until proven otherwise.** Reproduce locally before fixing. "Flaky" is a conclusion reached with evidence (it passes on retry without any change, and the failure is unrelated to the diff), not a way to move on. A test is never skipped or deleted to go green.
5. **Fixes follow `build`.** A code change for CI or for a comment gets a regression test first, stays inside the plan and the ADRs, and stops to ask on an unmade decision.

## Process

### 1. Find the PR

The `PR:` field of the feature's `build-plan.md` (or of a fix record `context/fixes/<slug>.md`), the PR for the current branch (`gh pr view`), or the one the user names. No `gh` (or the platform's CLI) → ask the user to paste the CI status and the comments, and work from that.

### 2. Read its state

- **Checks** — `gh pr checks`. Still running → wait for them in the background (`gh pr checks --watch`), and meanwhile go to comments.
- **Reviews and comments** — `gh pr view --comments`, and the inline review threads (`gh api repos/{owner}/{repo}/pulls/{n}/comments`, and the review states). Note which threads are unresolved and which reviews request changes.
- **Mergeability** — conflicts with the base, the base moving ahead, required approvals missing.

Show a short status: checks ✅/❌/⏳, approvals, unresolved threads, conflicts.

### 3. Fix what CI caught

For each failing check: read the failing log (`gh run view <id> --log-failed`), reproduce it locally with the same command, and classify:

- **Caused by the change** → fix it following `build` (regression test first when it's a behavior failure; direct fix for lint/type/format).
- **Environment difference** (a version, an env var, a service the CI doesn't have) → fix the code or the CI config if it's the project's to fix, or report it — and if the local docs or CLAUDE.md missed it, note it.
- **Flaky** (rule 4 evidence) → report it with the evidence; rerunning (`gh run rerun --failed`) is the user's call; propose a lesson or an issue so it gets fixed properly.

### 4. Triage the review comments

For each unresolved thread or change request, classify and draft:

- **Fix** — the reviewer is right: the change to make, the file, and a one-line reply naming the commit once done.
- **Reply** — it's a question or a misunderstanding: the answer, citing the spec, an ADR or the code (`file:line`).
- **Disagree** — you think the code is right: the reason, grounded in the record. The user decides whether to argue or to change it.
- **Out of scope** — valid but not for this PR: a reply proposing a follow-up, and where it gets recorded (a *Deferred* line in the brief, an open question in the plan, an issue).

A comment that reveals a decision the plan never made (a new permission rule, a changed behavior) → it's a decision: ask with AskUserQuestion, record it in the spec or an ADR, then fix.

Present the triage table, then ask with AskUserQuestion (multiSelect): which fixes to make and which replies to post as drafted. Apply only the picked ones.

### 5. Push and answer

After the fixes: run the full checks locally, then show the commits and the replies to be posted. Ask: "Push and post the replies (Recommended)" / "Push only" / "Edit first". On approval, push, post the replies on their threads, and resolve only the threads the user agreed to resolve. If the fixes touched more than a few lines of logic, recommend a `/review` of the delta before pushing — the fixing agent is the author again. If they changed behavior a user can see, recommend `/verify` again too.

Then back to step 2 until the checks are green, the threads are answered, and the approvals are in.

### 6. Sync, close out, then merge — on request

When the user asks to merge:

1. **Sync with the base** (`../feature/worktrees.md` → *Sync with the base*): bring the base in, resolve conflicts, renumber ADRs and lessons that collide with ones merged meanwhile. If the sync touched the feature's files, the review and acceptance run are now stale: say so, and recommend `/review` (and `/verify`) before merging.
2. **Close out on the branch, before the merge.** The base branch is usually checked out in another worktree, so the close-out can't be committed there. Instead, commit it on the feature branch now — it reaches the base only through the merge, so on the base it is true by construction:
   - **Build plan** (or fix record) — `Status: shipped`.
   - **Success check** — if the brief defines success (a metric, a behavior, a date), fill the plan's *Follow-up*: what to check, where, and when ("check the export is used by ≥ 3 accountants — analytics dashboard — 2026-11-15"). A fix record has no brief: skip it.
   - **Lessons** — comments the reviewers had to make that a future agent could avoid on a different feature (a pattern, not a one-off) → propose them as lesson candidates, in `review`'s format (`context/project/lessons.md`, `L-NNN`), with the user picking which to record. A CI failure caused by a local/CI difference → a line in CLAUDE.md or the docs, so the next agent runs what CI runs.
   - **Deferred items** — out-of-scope follow-ups agreed in the comments are in the brief's *Deferred* or the plan's *Open questions*, with an owner.

   - **Timeline** — log `wt.py event <slug> land shipped` (`../feature/scripts/wt.py`), then fill the plan's *Timeline* with `wt.py metrics <slug> --markdown` (lead time, time per stage, quality counters); under `endurance`, it runs the retro from it.

   Commit it on its own (`chore(context): close out <slug>`) and push it with the user's approval. If the base branch's protection dismisses approvals on new commits (`gh api repos/{owner}/{repo}/branches/<base>/protection`), say so first: the close-out push will need a fresh approval — or choose the fallback below.
3. **Merge.** Re-check that checks are green, approvals are current, and there's no conflict. Use the repository's merge method (the one its recent merged PRs used, or its settings). Show the method and the final commit message, and merge after the user confirms. If the merge is abandoned, revert the close-out commit.

**Already merged elsewhere, or the fallback** (close-out after the merge): create a temporary detached worktree on the base (`git worktree add --detach <tmp> origin/<base>` — allowed even while the base is checked out elsewhere), make the close-out edits there, commit, and publish it the way the repository accepts changes to the base — a direct push (`git push origin HEAD:<base>`) only if that's allowed and the user approves, otherwise a small PR. Then remove the temporary worktree.

### 7. Clean up

- **Leave the feature's worktree** (a session can't remove the one it stands in): move to the main worktree, and pull the base there if its working tree is clean.
- **Remove the worktree and branch** (`../feature/worktrees.md` → *Removing*): its processes and isolated resources (ports, containers, databases), `git worktree remove`, the local and remote branch — asking before each deletion.
- **Resume pointers** — if `context/project/memory.md` on the base points to this feature, it will be updated by the next `/remember` in the main worktree; mention it.

After the merge, if another feature is stacked on this one (its plan says `**Depends on:** feat/<this>`), it must be rebased onto the base and its PR retargeted (`../feature/worktrees.md` → *Stacked features*) — say so, or let `endurance` do it. Release the ports: `wt.py ports release <slug>`.

Report in one line: merged, where the success check is scheduled, what was recorded, and which worktree was removed. If other features are in flight, suggest `/endurance` so they're synced with the new base. Suggest `/remember` if the session continues on something else.
