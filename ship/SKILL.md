---
name: ship
description: Take a built and reviewed feature to a pull request. Gates on readiness (build plan done, no open critical/important review findings, a review newer than the last code change, full checks green, no debug leftovers), tidies unpushed commits, writes the changelog entry and migration notes, and drafts the PR description from the feature's spec, acceptance criteria, ADRs and review — then pushes and opens the PR only after the user approves the text. Use when a feature is ready to go out, or whenever the user says "ship", "ship it", "open the PR", "prépare la PR", "livre la feature", or "on peut merger ?".
---

# Ship

The failure this prevents: the feature is "done", so it goes out — with a test that was skipped, a `console.log` left in, a new env variable nobody mentioned, commits named "wip", and a PR description that says "adds feature X" while the spec, the decisions and the review that would explain it sit unread in `context/`. This skill is the last gate and the handoff: it checks that the feature is really ready, then writes the PR from what's already been decided and verified.

The goal is not to rush the merge. The goal is **a PR a reviewer can understand and trust without asking — and nothing going out that wasn't checked.**

## The rules

1. **The gate is real.** A blocker (step 2) stops the ship. The user can override it, but only explicitly — and an override is written into the PR description, not hidden.
2. **Nothing outward-facing without approval.** Pushing, opening a PR, or posting anything happens only after the user has seen and approved the exact text. Rewriting commits that are already pushed happens only if the user explicitly asks.
3. **Write from the record, not from memory.** The PR description comes from `spec.md`, the acceptance criteria, the ADRs, the build plan and the review — cited, not paraphrased into something new. If the record is missing something the PR needs, say so; don't invent it.

## Process

### 1. Identify what's shipping

- The feature: named by the user, or the one whose `build-plan.md` is `done` (check *Resume here* in `context/project/memory.md`). Several candidates → ask with AskUserQuestion.
- The branch and its base (the default branch unless the plan or the user says otherwise), and the commits and diff between them.

### 2. Readiness gate

Check each item and show the result as a checklist:

- **Plan complete** — `build-plan.md` has `Status: done` and every step ticked.
- **No open review findings** — no unticked 🔴/🟡 under *Review findings*.
- **Review is current** — a review exists, and its recorded HEAD matches the current HEAD, or the commits since then are only non-code changes. Code changed after the review → blocker: recommend a re-review.
- **Checks green** — run the project's full tests, typecheck, lint and build (commands from CLAUDE.md). Any failure → blocker.
- **Acceptance criteria covered** — every `AC-n` in the spec maps to a test, per the last build or review report. Uncovered ones are listed.
- **No leftovers in the diff** — scan the *added* lines for debug output (`console.log`, `print(`, `dbg!`, `debugger`), focused or skipped tests (`.only`, `.skip`, `xit`, `@Disabled`), new `TODO`/`FIXME`, commented-out code blocks, and anything that looks like a secret or a local path.
- **Clean working tree** — nothing uncommitted that belongs to the feature.

If there are blockers, ask with AskUserQuestion — the recommended option depends on the blocker: "Fix with `/build` (Recommended)", "Re-review with `/review`", or "Ship anyway (recorded in the PR)". Don't continue until every blocker is fixed or explicitly overridden.

### 3. Commit hygiene

Look at the commits between base and HEAD:

- **Not yet pushed and messy** (`wip`, `fix typo`, `oops`, one-line fixups of the previous commit) → propose a cleaner history — squashing fixups, rewording to the repository's own commit style (read `git log` on the base branch) — and ask: "Clean up the commits as shown (Recommended)" / "Keep them as they are".
- **Already pushed** → leave them, unless the user explicitly asks (rule 2).
- **Clean** → say so and move on.

### 4. Release notes

From the diff, detect what someone deploying or upgrading needs to know:

- **Migrations** — new schema migrations, data backfills, and whether they're reversible.
- **Configuration** — new or changed environment variables, config keys, feature flags, with their defaults.
- **Dependencies** — added, removed or major-bumped packages.
- **Breaking changes** — changed public APIs, removed endpoints, changed data formats.

If the project has a `CHANGELOG.md` (or equivalent), draft an entry in *its* existing format and section (usually *Unreleased*). Don't create a changelog the project doesn't keep.

### 5. Draft the PR description

Follow the project's PR template if it has one (`.github/pull_request_template.md` or similar); otherwise:

- **Summary** — from the spec's summary: what and why, two or three sentences.
- **What it does** — use cases (`UC-n`) and acceptance criteria (`AC-n`), each with the test that proves it.
- **Decisions** — the ADRs this feature created or relies on, one line each with a link, and the feature-level decisions from the spec.
- **Deploy notes** — step 4's migrations, config, dependencies and breaking changes. Omit the section if empty.
- **Review** — last review's verdict, findings fixed, findings marked won't-fix (with the reason), and any gate override from step 2.
- **How to test** — the commands, and a manual path through the main use case if it has a UI or an API.
- **Out of scope** — from the spec, so reviewers don't ask for it.

Link to the feature's `context/features/<slug>/` files rather than pasting them. Write in the language the project's PRs use (look at recent merged PRs if possible); default to the user's language.

### 6. Approve, then publish

Show the final PR title, description, changelog entry and the target branch. Then ask with AskUserQuestion: "Push and open the PR (Recommended)" / "Edit the description" / "Push only" / "Stop here".

On approval, commit the changelog entry if there is one, push the branch, and open the PR with `gh pr create` (or the platform's CLI). No CLI available → give the user the title and description to paste.

### 7. Record

- Add a `PR:` line with the link to the header of `build-plan.md`.
- Report the PR link in one line, and suggest `/remember` so the next session knows the feature is out for review.
