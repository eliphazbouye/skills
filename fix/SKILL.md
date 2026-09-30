---
name: fix
description: Fix a bug properly, recording it in context/fixes/<slug>.md — one reported by a user, seen in production, or found by hand, outside any feature being built. Captures the report precisely, reproduces it before touching anything (a failing test at the lowest level that shows it), finds the root cause rather than the symptom (git bisect for regressions), checks whether the same mistake exists elsewhere, applies the smallest fix that makes the test pass without breaking the rest, corrects the spec if it was wrong or silent, and turns the cause into a lesson when it could happen again. Hands off to `review` and `ship`. Use when something that used to work is broken, a bug report comes in, or whenever the user says "fix", "il y a un bug", "ça marche plus", "corrige ce bug", "this is broken", "bug report", or "regression". Not for review findings on a feature in progress (that's `build`) or a session going in circles (that's `recover`).
---

# Fix

The failure this prevents: a bug comes in, the agent reads the error, changes the line that threw, and says "fixed". It wasn't reproduced, so nobody knows the change addresses *this* bug. It fixed the symptom — the null check — not the cause — the record that should never have been saved without an owner. The same mistake sits in two other handlers. There's no test, so it comes back in three months. This skill makes a fix a proven one.

The goal is not a fast patch. The goal is **the bug reproduced, its cause understood, a test that would have caught it, and the smallest fix that makes that test pass — with the mistake designed out if it could happen again.**

## The rules

1. **No fix without a reproduction.** Before changing code, the bug is reproduced: ideally a failing automated test, at least a script or exact steps that show it every time. Can't reproduce → stop and say so; don't fix blind.
2. **Cause, not symptom.** Explain *why* the bug happens before fixing it. A fix that only stops the crash (a null check, a try/catch, a default value) is acceptable only if the cause is understood and that really is the right place to handle it.
3. **Smallest fix, no drive-by changes.** Fix the bug, nothing else. Refactoring and cleanup noticed on the way go in the report as suggestions.
4. **A fix can reveal a decision.** If the correct behavior isn't obvious — the spec is silent, or it says something else — that's the user's call: ask with AskUserQuestion, then record the answer in the spec.
5. **Two failed fixes → `recover`.** If two sound fixes for the same cause don't work, the understanding is wrong: stop and follow `recover`.

## Process

### 1. Capture the report

From what the user gave, pin down: **the symptom** (what happens, error message, screenshot), **the expected behavior**, **where** (environment, version or commit, user role, data), **how to trigger it**, and **since when** (always, or since a date or release — a regression). Look for the logs or traces the project keeps. Ask only for what's missing and needed to reproduce — one AskUserQuestion at a time, recommended answer first.

**Write the fix record now** — `context/fixes/<slug>.md` from `templates/fix-record.md`, with the *Report* filled and `Status: in-progress` (in the fix's worktree if it has one; commit it as `chore(context): fix record for <slug>` under `feature` / `endurance`). An interrupted fix then leaves its state on disk; the steps below fill in the rest.

Read what the project knows about this area: the `context/features/` folder the code belongs to (its spec and *Edge cases*), `architecture.md`, the relevant ADRs, and `lessons.md` — the bug may be a lesson that wasn't followed.

### 2. Reproduce

- Run the test suite first to know the baseline.
- Write a **failing test at the lowest level that shows the bug** — a unit test if the cause is local, an integration test if it's in the wiring. Run it; it must fail for the reported reason, not for a setup mistake.
- Can't write a test yet (you don't know where the bug is) → reproduce by hand or with a script first, then narrow down until a test is possible.
- **Not reproducible** after an honest attempt → report exactly what was tried (environments, data, steps) and ask for what would help: logs, the exact data, a recording. Stop there.

### 3. Find the root cause

- Trace from the symptom to the cause: read the code path, add temporary logging if needed (removed before the fix is done).
- **Regression** (it used to work) → find the commit that broke it: `git log` on the files involved, or `git bisect run <the failing test>` between a known good and the current commit. The breaking commit often tells you the cause *and* the intent the fix must preserve.
- State the cause in two or three sentences: what happens, why, and since when.
- **Same mistake elsewhere?** Search the codebase for the same pattern (the same unchecked call, the same missing guard, the same copy-pasted block). Each occurrence is either fixed here (if it's the same bug, reachable) or listed in the report.

### 4. Fix

- Implement the smallest change that makes the failing test pass, in the place where the cause lives, respecting `architecture.md`, the ADRs and the active lessons.
- Run the new test, the tests around the change, then the full suite, typecheck and lint — compare with the baseline. Nothing newly failing.
- Remove any temporary logging or scripts.
- Commit on a branch (`fix/<slug>`, unless the user or CLAUDE.md says otherwise), with a message naming the symptom and the cause. When other work is in flight in this checkout, or under `feature` / `endurance`, do the fix in its own worktree (`../feature/worktrees.md` → *Create and bootstrap*) — created before step 2, so the reproduction runs there too.

### 5. Record

- **The fix record** — complete `context/fixes/<slug>.md` (slug: short kebab-case naming the bug, no date): cause, fix, test, `Status: done`. It's what `review`, `verify`, `ship` and `land` read and write — the fix report must not live only in the conversation. Commit it with the fix (or on its own as `chore(context): …`).
- **Spec wrong or silent** — if the feature has a `spec.md`, add the case to *Edge cases & errors* (and an `AC-n` if it's a real requirement) and a line in *Revisions*, after the user approves the wording.
- **Lesson** — if the cause is a pattern a future agent could repeat on different code (not a one-off typo), propose it as a lesson candidate in `review`'s format (`context/project/lessons.md`, `L-NNN`, *Seen:* `fix YYYY-MM-DD <slug>`). If an existing lesson covers it, it *recurred*: add a *Seen* line and consider escalating it to a lint rule or a test. The user picks what's recorded.
- **Tooling gap** — if the bug could have been caught automatically (a type, a lint rule, a missing test in CI), say how.

### 6. Report and hand off

Present: the symptom, the root cause (and the breaking commit for a regression), the fix (`file:line`), the test that proves it, other occurrences found and what was done with them, and what was recorded. Then ask with AskUserQuestion:

- "Have it reviewed with `/review` (Recommended)" — a fresh reviewer, since you wrote the fix;
- "Check it in the running app with `/verify`" — when the bug is visible to users, after the review;
- "Ship it with `/ship`" — for a fix small enough that the user will review the PR themselves;
- "Stop here".

`review`, `verify`, `ship` and `land` treat the fix record as the build plan: findings, the acceptance run, `PR:` and the `shipped` status go there — never into the feature folder of the code it touches, which may already be `shipped`.
