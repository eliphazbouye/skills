# Project context

> Written for agents and humans. Read this first, then `project/`, then the feature folder you're working in.

## Layout

```
context/
├── README.md              ← this file
├── project/               ← what holds for the whole project
│   ├── brief.md           ← what & why of the whole project, if scoped (skill: scope)
│   ├── architecture.md    ← modules, layers, boundaries, key dependencies (skills: architect, map)
│   ├── memory.md          ← session memory (skill: remember)
│   ├── ui-registry.md     ← canonical UI patterns (skill: imprint)
│   ├── lessons.md         ← recurring mistakes found in reviews (skill: review)
│   └── adr/               ← one file per significant decision (skill: architect)
├── fixes/                 ← one record per bug fix, playing the build plan's role (skill: fix)
└── features/              ← one folder per feature (skill: architect)
    └── <feature-slug>/
        ├── brief.md       ← what & why, settled by interview (skill: scope)
        ├── use-cases.md   ← who does what, in which scenario
        ├── spec.md        ← what it must do + acceptance criteria
        └── build-plan.md  ← how it's built, step by step, with status, open review findings and PR link (skills: build, review, ship)
```

## Parallel work

Each feature lives on its own branch (`feat/<slug>`, `fix/<slug>`) in its own git worktree, so its files here are committed on that branch. The base branch's `context/features/` holds what has merged; features in flight are found with `git worktree list`. See the `feature` skill's `worktrees.md`.

## Rules

- **Accepted ADRs are binding.** Changing one means writing a new ADR that supersedes it — never edit an accepted ADR's decision.
- **One source per fact.** Files reference each other (`UC-1`, `AC-2`, `ADR-0003`) instead of copying.
- **Lessons are rules.** Read the active entries of `project/lessons.md` before planning or writing code; they are mistakes this project already made.
- **One folder per feature, stable name.** Revisiting a feature updates its folder; it doesn't create a new one.
- ADR location: `context/project/adr/` <!-- or the project's existing ADR folder, e.g. docs/adr/ -->

## CLAUDE.md pointer

Add this to the project's `CLAUDE.md` so every session reads the context:

```markdown
## Project context
- At the start of a session, read `context/README.md`, then `context/project/` (architecture, memory, lessons, ADRs).
- Before planning or writing code, re-read `context/project/lessons.md` — mistakes this project already made.
- Before working on a feature, read its folder in `context/features/<slug>/` and follow its `build-plan.md`.
```
