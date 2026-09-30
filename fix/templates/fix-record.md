# Fix — <short title of the bug>

- **Status:** in-progress <!-- in-progress | done | shipped — same meaning as in a build plan -->
- **Created:** YYYY-MM-DD · **Updated:** YYYY-MM-DD
- **PR:** — <!-- set by ship -->
- **Branch:** `fix/<slug>` · **Worktree:** — <!-- if it has one --> · **Ports:** — <!-- app / db, assigned per worktrees.md -->
- **Area:** `context/features/<slug>/` (the feature whose code this touches, if any) · **Lessons:** L-NNN

<!-- Written by the `fix` skill. It plays the role of a build plan for review, verify, ship and land. -->

## Resume here

<!-- Where the fix stands if it's interrupted: the step (reproduce / cause / fix / record), what's known, next action. -->

## Report

- **Symptom:** 
- **Expected:** 
- **Where:** <environment, version or commit, role, data>
- **How to trigger:** 
- **Since:** <always | date / release — regression>

## Cause

<!-- Two or three sentences: what happens, why, since when. For a regression, the breaking commit. -->

## Fix

- **Change:** `file:line` — 
- **Regression test:** `path::name`
- **Other occurrences:** <none | `file:line` — fixed here / reported>

## Review findings

<!-- Same format as a build plan. Written by review; [~] by the fixing agent, confirmed by review or verify. -->

## Acceptance run

<!-- Written by verify, if the bug is visible to users. -->
