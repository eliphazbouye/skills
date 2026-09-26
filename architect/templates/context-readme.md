# Project context

> Written for agents and humans. Read this first, then `project/`, then the feature folder you're working in.

## Layout

```
context/
├── README.md              ← this file
├── project/               ← what holds for the whole project
│   ├── architecture.md    ← modules, layers, boundaries, key dependencies
│   ├── memory.md          ← session memory (skill: remember)
│   ├── ui-registry.md     ← canonical UI patterns (skill: imprint)
│   ├── lessons.md         ← recurring mistakes found in reviews (skill: review)
│   └── adr/               ← one file per significant decision (skill: architect)
└── features/              ← one folder per feature (skill: architect)
    └── <feature-slug>/
        ├── use-cases.md   ← who does what, in which scenario
        ├── spec.md        ← what it must do + acceptance criteria
        ├── build-plan.md  ← how it's built, step by step, with status
        └── review.md      ← review rounds and finding status (skill: review)
```

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
