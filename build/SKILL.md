---
name: build
description: Implement a feature by executing its build plan (context/features/<slug>/build-plan.md) step by step — test first from the acceptance criteria, verify, tick, and stop to ask whenever a decision the plan didn't make shows up. Also fixes open review findings (regression test first). Resumable across sessions: the plan's checkboxes are the state. Use after `architect` has written a plan, to continue an interrupted implementation, to fix findings picked in a review, or whenever the user says "build", "implement the plan", "continue the build", "implémente", "code la feature", "reprends l'implémentation", or "corrige les findings".
---

# Build

The failure this prevents: the plan was agreed, then the implementation quietly drifted from it. A step got ticked because it "should work", a test was written after the code to match whatever the code did, a decision nobody made got baked in because stopping to ask felt slow, and when the session ended mid-way nobody knew which half was really done. This skill executes the plan as a contract: one step at a time, proven before it's ticked, and every unplanned decision handed back to the user.

The goal is not to write code fast. The goal is **code that does what the spec says, with evidence, in a state any session can resume from.**

## The rules

1. **The plan is the contract.** Build what `build-plan.md` says, in order. Something needed that isn't in the plan — a missing step, a wrong premise, extra scope — is not improvised: stop, say so, and amend the plan with the user (step 4).
2. **Test first, from the acceptance criteria.** For a step that satisfies an `AC-n`, write the test that encodes it, run it, **see it fail for the right reason**, then implement. A test written after the code tends to test what the code does, not what the spec asks.
3. **Tick only on evidence.** A step is ticked when its *verify* check has actually run and passed in this session — not when it "should work". If a check can't run, the step stays unticked and you say why.
4. **Stop on unmade decisions.** When the code needs a choice the spec, the ADRs and the conventions don't settle, stop coding and ask with AskUserQuestion — one question, recommended option first with "(Recommended)", grounded in this codebase. Record the answer before continuing (step 4).
5. **Stay inside the lines.** Respect `architecture.md`, accepted ADRs, `ui-registry.md` for UI work, and the active lessons in `lessons.md`. Code that would break one of them is a decision (rule 4), not an implementation detail.

## Process

### 1. Find the plan

- If the user names a feature, use `context/features/<slug>/build-plan.md`. Findings on a fix live in its fix record (`context/fixes/<slug>.md`, written by `fix`): it plays the role of the plan — fix its open *Review findings* the same way.
- Otherwise look for plans with `Status: in-progress` (and check *Resume here* in `context/project/memory.md`). One → use it. Several → ask which with AskUserQuestion. None → list the `draft` plans and ask.
- **No plan at all?** A bug in existing behavior → follow `/fix` instead. For a trivial change, just do it — this skill isn't needed. For anything with open decisions, suggest `/architect` first rather than building on guesses.

### 2. Load the context

Read, before touching code:

- the plan, then `spec.md` and `use-cases.md` in the same folder;
- the ADRs the plan and spec cite, and `context/project/architecture.md`;
- the active entries of `context/project/lessons.md` — note which apply to which steps;
- `context/project/ui-registry.md` if any step touches UI;
- `CLAUDE.md`, for the project's test/lint/build commands and conventions;
- the files listed under the plan's *Code context*.

### 3. Prepare the ground

- **Git state.** Run `git status` and note the branch. Uncommitted changes that aren't part of this plan → ask what to do with them before starting. On the default branch → ask with AskUserQuestion: "Create branch `feat/<slug>` (Recommended)" / "Stay on <branch>".
- **Under `feature` or `endurance`** (the pipeline is driving): don't ask these two — you're already on the feature's branch in its worktree (if you're on the default branch, stop: the worktree step was skipped); commit after each verified step, unless CLAUDE.md or memory says otherwise; say so in one line.
- **Commit policy** — ask once, unless CLAUDE.md or memory already answers it: "Commit after each verified step (Recommended)" / "One commit at the end" / "I'll commit myself". Per-step commits make the history match the plan and give `review` a clean base.
- **Baseline.** Run the test suite (and typecheck/lint if cheap) before changing anything, and note what already fails. Those failures are not yours — don't fix them silently, and don't let them hide new ones.
- **No test setup in the project?** Ask: "Set up a minimal test harness first (Recommended)" / "Verify steps manually" — and if manual, each *verify* is a concrete command or check you run and report.
- Set the plan's `Status:` to `in-progress` and update its `Updated:` date.

### 4. Execute, one step at a time

**Order:** open (`[ ]`) 🔴/🟡 items under *Review findings* first (they're about code that already exists), then the first unticked step, in order.

For each step:

1. **Announce it** in one line: the step, the files, the `AC-n` it satisfies, and any lesson (`L-NNN`) that applies.
2. **Test first** (rule 2) — for a review finding, a regression test that reproduces it. Run it; confirm it fails, and fails because the behavior is missing, not because of a typo or setup error.
3. **Implement** the smallest change that makes it pass, following the conventions of the surrounding code.
4. **Verify** — run the step's *verify* check, the new test, and the tests around the code you touched. Compare against the baseline: anything newly failing is yours to fix now.
5. **Tick** the step (`- [x]`). A review finding is **not** ticked by you — you're its author: mark it `- [~]` with the fix commit (`(fix: <sha>)`), and add `file:line` if it had none (a `V` finding from `verify` cites a scenario). `review` confirms `R` items and `verify` confirms `V` items. Update `Updated:`.
6. **Commit**, if that's the policy, with a message naming the step (`S3: …`) or finding (`R1-2: …`).

**When something doesn't fit the plan, stop the loop:**

- **Unmade decision** (rule 4) → ask, then record the answer: in the feature's `spec.md` (*Decisions*, and a line in *Revisions*), or — if it's hard to reverse, cross-cutting, or sets a convention — as a new ADR in `context/project/adr/` from `architect`'s `templates/adr.md`, next number, citing this feature. Then continue.
- **A step, or the whole plan, is ticked but `Status:` wasn't set to `done`** (a session stopped before step 5) → run step 5 now.
- **The plan is wrong** — a step is impossible, a premise was false, a step is missing → explain what you found, propose the amendment (added, changed or reordered steps), and ask: "Amend the plan as proposed (Recommended)" / "Change the approach" / "Stop here". Edit `build-plan.md` only after approval. If the change touches the spec's behavior or an ADR, suggest `/architect` instead.
- **A check keeps failing** after two honest attempts at the same step → stop guessing; suggest `/recover` and leave the step unticked.

Keep the user informed with one line per finished step — no running commentary.

### 5. Finish

When every step is ticked:

- Run the full checks — tests, typecheck, lint, build — and compare with the baseline.
- Walk the spec's acceptance criteria: each `AC-n` → the test that proves it, or "not covered" with the reason.
- Set `Status: done` (the `review` skill sets it back to `in-progress` if it finds 🔴/🟡 issues).

Report briefly: what was built, the AC → test mapping, decisions made during the build and where they're recorded, plan amendments, anything left failing from the baseline. Then ask with AskUserQuestion:

- "Run `/review` now (Recommended)" — a fresh reviewer, since you are the author;
- "Commit and push" (if not already done per the policy);
- "Stop here" — and suggest `/remember` so the next session resumes cleanly.

After fixing review findings — `R` from a review or `V` from an acceptance run — recommend a re-review instead: "Re-review the fixes (Recommended)"; after it, `/verify` runs again for `V` findings.

**Stopping mid-way** is fine — the ticked steps are the state. Just make sure every ticked step is really done, the unticked ones aren't half-written without a note, and suggest `/remember`.
