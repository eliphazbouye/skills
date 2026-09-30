# Build plan — <Feature name>

- **Status:** draft <!-- draft | in-progress | done | shipped (committed by land just before the merge, so it's true on the base branch) -->
- **Created:** YYYY-MM-DD · **Updated:** YYYY-MM-DD
- **PR:** — <!-- set by the ship skill; merged or not is read from the platform (gh pr view) -->
- **Branch:** `feat/<slug>` · **Worktree:** `../<repo>.worktrees/<slug>` · **Ports:** app — · db — <!-- set when the worktree is created (feature / endurance); see feature/worktrees.md -->
- **Depends on:** — <!-- feat/<other> when stacked on a feature still in flight (see feature/worktrees.md) -->
- **Spec:** [spec.md](spec.md) · **ADRs:** ADR-NNNN · **Lessons applied:** L-NNN

<!-- Small features without spec.md: add a short "## Spec" section here (summary, acceptance criteria, decisions). -->

## Resume here

<!-- Written by `remember` when working in this feature's worktree: where to resume, blockers, next action. Replaces memory.md's *Resume here* for this feature, so parallel features don't collide. -->

## Code context

<!-- Files and modules this feature touches or builds on, with one line on why. -->
- `path/to/file` — 

## Steps

- [ ] **S1.** <What to do> — files: `…` — satisfies: AC-1 — verify: <test / command / manual check>
- [ ] **S2.** 

## Review findings

<!-- Written by the `review` skill (R items) and the `verify` skill (V items). The status can't be `done` while a 🔴/🟡 item is open.
     States: [ ] open · [~] fixed, awaiting confirmation (build writes it, with the fix commit) · [x] confirmed fixed (review confirms R, verify confirms V) · ~~struck~~ won't fix / accepted, with the reason — the user's decision, ignored by every gate. -->
<!-- > Last review: round N · YYYY-MM-DD · base `<sha>` · HEAD `<sha>` (+ uncommitted: yes/no) · verdict: … -->
<!-- - [ ] **R1-1** 🔴 <short title> — `file:line` -->

## Acceptance run

<!-- Written by the `verify` skill; replaced on each run. Failures are added above as V<run>-<n> findings. -->
<!-- > Run: run N · YYYY-MM-DD · HEAD `<sha>` (+ uncommitted: yes/no) · n pass · n fail · n manual (n confirmed, n pending) -->
<!-- - S-1 / UC-1 — pass | fail | manual — confirmed YYYY-MM-DD | manual — pending — <what was done, what was observed> -->

## Timeline

<!-- Written by `land` at the close-out, from `wt.py metrics <slug> --markdown`: lead time, time per stage (active / waiting on the user / runs), quality counters. Read by endurance's retros. -->

## Follow-up

<!-- Written by the `land` skill after the merge: the success check from the brief — what, where, when. -->

## Open questions

- <Question> — unblocked by: <who/what>
