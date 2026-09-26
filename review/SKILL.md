---
name: review
description: Review a feature an agent just built before you trust it, using a fresh reviewer subagent that never saw the author's reasoning. Runs the project's tests/typecheck/lint, checks the implementation against the plan (spec, acceptance criteria, ADRs), the architecture boundaries and production-readiness, and reports proven issues grouped by severity (critical / important / minor). Tracks open findings in the feature's build plan and turns recurring mistakes into project lessons so future sessions don't repeat them. Never fixes without your choice. Use after an agent finishes a feature, before committing, after fixing review findings ("re-review"), or whenever the user says "review this", "review the feature", or "is this production ready".
---

# Review

The failure this prevents: an agent builds a feature — say 400 lines — you skim it, it looks fine, you commit. Three days later a bug surfaces that a careful read would have caught. And next month, another agent makes the same mistake in another feature, because nothing learned from the first one. This skill is that careful read, done before you commit, by someone other than the author — and the memory that stops the same mistake twice.

"Someone other than the author" is literal: **the review itself runs in a fresh subagent**. The agent that built the feature carries its own reasoning in context — why each shortcut seemed fine, which edge case it decided didn't matter — and reads its code through that lens. A subagent that sees only the intent documents and the diff reads what's actually there. Your job in the main session is to scope the review, hand it off cleanly, relay the result faithfully, and record what it taught.

## The rules

1. **Never fix without the user's choice.** Don't edit, refactor, or "quickly clean up" anything while reviewing. Fixes happen only after the report, on what the user explicitly picks (step 6).
2. **Don't coach the reviewer.** The subagent gets the instructions, the intent documents and the change — never the author's explanations, the session's reasoning, or hints about which parts are "fine". Those are exactly the blind spots the handoff exists to remove.
3. **Relay, don't soften.** You don't drop, downgrade, or explain away a reviewer's finding — even if you (or the author session) disagree. If you think one is wrong, keep it and add your objection next to it, marked as yours. The user decides.
4. **Learn only what generalizes.** A lesson is a rule a future agent would follow on a *different* feature. A one-off bug is fixed and logged, not turned into a lesson.

## Process

### 1. Establish what was supposed to be built

Locate the intent the code will be judged against — as **file paths**, so the reviewer reads the source, not your summary of it:

- **The plan.** If the feature was planned with the `architect` skill, its folder is `context/features/<slug>/`: `spec.md` (behavior and acceptance criteria `AC-n`), `use-cases.md` if present, `build-plan.md` (the steps, and which are ticked). Otherwise a ticket, a PR description, or the request that kicked off the work — if that request is only in this conversation, quote it verbatim; don't paraphrase. If nothing is obvious, ask the user: "what was this feature supposed to do?"
- **The architecture.** `context/project/architecture.md`, the ADRs in `context/project/adr/` (or the project's own ADR folder, e.g. `docs/adr/`), CLAUDE.md, and any docs on boundaries or conventions.
- **The lessons.** `context/project/lessons.md` if it exists — mistakes this project already made.
- **The UI registry.** `context/project/ui-registry.md`, if the change touches UI files.
- **The previous round.** The *Review findings* section of the feature's `build-plan.md`, if it exists. If it has unticked findings and the user is asking after fixes, this is a **re-review** (see step 2).

No plan found? Don't block — the review runs against architecture and production-readiness, and the report says no plan was available.

### 2. Identify the change under review

- **Uncommitted work:** `git diff` + `git diff --staged` + `git status`.
- **Branch or PR:** `git diff <base>...HEAD`.
- **Specific files** the user points at: those plus what they directly touch.
- **Re-review:** only what changed since the last round (from the base/HEAD recorded under *Review findings* in `build-plan.md`), plus the locations of its unticked findings — the reviewer checks each open finding is resolved and that the fixes didn't introduce new problems.

Pin it down as something the reviewer can reproduce — exact git command(s) plus the list of changed files — and check the size with `git diff --stat`.

### 3. Hand off to the reviewer subagent(s)

Launch the review with the Agent tool, `general-purpose` subagent (it must read files and run commands). The prompt is **the full content of `reviewer-prompt.md`** (in this skill's directory), passed verbatim, followed by a section you fill in:

```
## This review
- Change: <git command(s)>; files: <list>
- Intent: <paths — spec, use cases, build plan, ADRs, architecture, lessons, UI registry, CLAUDE.md> | <user request, quoted verbatim> | no plan available
- Scope: <all changed files | this slice: …>
- Re-review of: <build-plan.md path, unticked finding IDs to verify> (only for a re-review)
- Language: write the report in <the user's language>.
```

Nothing else goes in — no summary of the implementation, no opinions (rule 2).

**Size the handoff:**

- **Normal change** (up to roughly 800 changed lines): **one** reviewer.
- **Large change** (bigger, or spanning several modules): split the diff **by module or area** — never by lens, since the worst bugs cross lenses — and launch one reviewer per slice, all in a single message so they run concurrently. Each gets the full intent and all three lenses; only one of them runs the checks (say which in its Scope).
- **Verification (large changes, or any change with 🔴 findings marked *suspected*):** launch one more fresh subagent with the 🔴 findings only, asking it to independently confirm or refute each against the code, read-only. You don't do this check yourself — you are likely the author.

Don't review the code yourself while the subagents work, and don't start fixing anything.

### 4. Consolidate and report

Merge the reviewers' reports into one: deduplicate the same issue found in two slices (keep the higher severity), fold in the verifier's verdicts (a refuted finding stays, marked *refuted* with the verifier's reason — rule 3). Present it in the conversation, in the reviewer's format: checks, acceptance criteria, 🔴 / 🟡 / ⚪ findings with clickable `file:line`, plan gaps, recurred lessons, outside-the-diff, and the one-line verdict.

### 5. Record the round

- **Open findings in the build plan.** If the feature has a folder in `context/features/<slug>/`, update the *Review findings* section of its `build-plan.md` — no separate review log; the full report lives in the chat, and what generalizes goes to `lessons.md`:
  - the header line: date, base and HEAD commits (+ whether uncommitted changes were included), verdict;
  - one checkbox per 🔴/🟡/⚪ finding: `` - [ ] **R<round>-<n>** <sev> <short title> — `file:line` ``;
  - on a re-review: tick fixed items (`(fixed, round N)`), strike through won't-fix items with the reason, mark disputed ones, and add the new round's findings. Remove items ticked in an earlier round, so the section only holds what's open or just resolved.
  - If any 🔴/🟡 box is unticked, set the plan's `Status:` back to `in-progress`.

  No feature folder → the report stays in the chat only.
- **Plan gaps.** For each plan gap, the fix is either in the code or in the plan. Say which you recommend, and if it's the plan — a missing decision, or a deliberate departure from an ADR — suggest `/architect` to record it (a new ADR superseding the old one). Never leave an ADR contradicted silently.

### 6. Learn, then hand the decision back

Draft **lesson candidates** from the findings (rule 4): a finding generalizes if a future agent could make the same mistake on a different feature — a pattern, not a line of code. Also note every finding the reviewer matched to an existing lesson: that lesson *recurred*.

Then ask with **one AskUserQuestion call** holding two questions:

1. **"Which lessons should be recorded?"** (multiSelect) — one option per candidate, the rule as label, the finding it comes from in the description. Recommend the ones from 🔴/🟡 findings. Skip this question if there are no candidates.
2. **"What next?"** — "Fix the 🔴 findings (Recommended)" · "Fix 🔴 + 🟡" · "Pick findings one by one" · "Nothing for now". Adjust the recommendation: no 🔴 → recommend fixing the 🟡; verdict "ready" → recommend "Nothing for now".

Then:

- **Write the chosen lessons** to `context/project/lessons.md` (create it from `templates/lessons.md`): a new `L-NNN` entry, stated as an instruction, with why and where it was seen. A recurred lesson gets a new line under **Seen** instead of a duplicate entry. Add the lesson IDs to the plan's `Lessons applied` line so later rounds know they're covered.
- **Escalate what keeps coming back.** A lesson seen **3 times or more**, or born from a 🔴, is a sign that written advice isn't enough: propose making it automatic — a lint rule, a test, a type constraint — or at least a rule in `CLAUDE.md`. Once it's enforced, move it to the **Enforced** section: agents no longer need to remember it.
- **Fix only what was picked**, following the `build` skill: each picked finding is an item under *Review findings*, fixed regression-test first. Then offer a re-review of the fixes (step 2) — the fixing agent is the author again, so the same handoff applies.

If `context/project/lessons.md` was just created, make sure `CLAUDE.md` points to it. The pointer `architect` installs covers `context/project/`; if there's no such pointer, add: "Before planning or writing code, read `context/project/lessons.md` — mistakes this project already made."
