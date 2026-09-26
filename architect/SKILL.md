---
name: architect
description: Run the architecture conversation that should happen before building any serious feature. Reads the project's context/ folder (initializing its standard structure on a new project), surfaces the decisions that haven't been made yet (auth, data model, error handling, boundaries…), asks focused questions ONE AT A TIME with a recommended option, presents a plan for approval, then writes the feature's use cases, spec, build plan and ADRs into context/ and hands off to the `build` skill. Use before implementing a non-trivial feature, when a task has unstated design decisions, or whenever the user says "architect", "plan this feature", "let's design X before building", "conçois", "planifie cette feature", or "réfléchissons à l'archi avant de coder".
---

# Architect

The failure this prevents: you ask an agent to build a feature, it silently guesses at decisions you never made — what authentication to use, how to shape the data, what happens on error — and you discover the wrong guess only after it's built, then refactor. This skill forces that conversation *first*, and writes its outcome down so no later session has to guess again.

The goal is not to produce paperwork. The goal is to **make the implicit decisions explicit, let the user decide them, and record them where the next session and the `review` skill will find them.**

## The rules

1. **Every question goes through AskUserQuestion — one question per call.** Never dump a list of questions in prose, and never put several questions in one AskUserQuestion call. Ask one, wait, let the answer shape the next. A wall of questions gets skimmed and half-answered — exactly the guessing this skill exists to stop.
2. **Always recommend.** Every question has a recommended option: listed first, its label ending in "(Recommended)", its description saying why — grounded in this codebase ("matches the session auth already in `src/auth/session.ts`"), not generic best practice. The other options state their trade-off. For genuinely open questions, still offer your best 2–4 concrete candidates; the user can always pick "Other".
3. **Surface decisions, don't make them.** When you spot a fork the user hasn't decided, name it and ask. If the user answers "you decide" / "je ne sais pas", take the recommended option and record it as **defaulted** — so it's visibly revisitable later.
4. **Only ask what matters.** Skip decisions already settled by the context files, an existing ADR, or an obvious convention in this codebase. Don't manufacture questions to look thorough. If you pass ~6 questions, batch the remaining minor decisions into one "here are my defaults for X, Y, Z" question.
5. **Flag contradictions, never overwrite silently.** If an answer contradicts an accepted ADR, `architecture.md`, or what the code actually does — or if the context files and the code disagree with each other — say so and ask which one wins.
6. **Nothing is built before the plan is confirmed.** This skill plans and writes the plan down; the `build` skill implements it, and stops to ask on any decision the plan didn't make.

## The context/ structure

This skill owns and maintains this layout. Other skills (`remember`, `imprint`, `review`) read and write inside it.

```
context/
├── README.md                     ← how this folder is organized (for humans and agents)
├── project/                      ← what holds for the WHOLE project
│   ├── architecture.md           ← modules, layers, boundaries, key dependencies
│   ├── memory.md                 ← session memory (written by `remember`)
│   ├── ui-registry.md            ← UI patterns (written by `imprint`)
│   ├── lessons.md                ← recurring mistakes found in reviews (written by `review`)
│   └── adr/
│       └── 0001-<decision>.md    ← one file per significant decision
└── features/                     ← one folder per feature, stable name, no date
    └── <feature-slug>/
        ├── use-cases.md
        ├── spec.md
        └── build-plan.md         ← steps + open review findings (findings written by `review`)
```

Templates for every file live in this skill's `templates/` directory. Write generated files in the language the user is speaking with you (or the language of the project's existing docs, if they have one).

## Process

### 0. Initialize or migrate the structure

Check `context/` before anything else:

- **No `context/`, but the repo already has substantial code:** the architecture should be mapped from the code before planning on top of it. Ask with AskUserQuestion: "Map the codebase first with `/map` (Recommended)" / "Minimal init and continue". On the first, follow the `map` skill, then come back to this feature.
- **No `context/` (new project):** create `context/README.md` (from `templates/context-readme.md`), `context/project/architecture.md` (from `templates/architecture.md`, filled with what the repo actually shows — or, on an empty repo, with what this conversation establishes), and the empty `context/project/adr/` and `context/features/` folders (with a `.gitkeep` each). Then make sure the project's `CLAUDE.md` (create it if missing) contains the pointer from `templates/context-readme.md`'s "CLAUDE.md pointer" section. Tell the user in one line what you created.
- **Old flat layout:** if `context/memory.md` or `context/ui-registry.md` exist at the root, move them into `context/project/` (use `git mv` if the repo is tracked), update any `CLAUDE.md` line pointing to the old path, and create whatever else is missing from the structure above. Tell the user what moved.
- **Project already keeps ADRs elsewhere** (e.g. `docs/adr/`, `doc/architecture/decisions/`): keep using that folder and its numbering/format instead of `context/project/adr/`, and note its location in `context/README.md`.

### 1. Read the context

Read, in this order:

1. `context/README.md`, then everything in `context/project/` — `architecture.md`, `memory.md`, `ui-registry.md`, `lessons.md`, and every ADR (at least the title and status of each; read in full the ones related to this feature).
2. `context/features/` — list the folders. **If the request extends or changes an existing feature, work in its folder** and read its three files; don't create a second folder for the same feature.
3. `./docs/` if it exists, plus `CLAUDE.md` and the README.
4. The existing code this feature will touch, so questions and recommendations are grounded in what's actually there.

Treat accepted ADRs and `architecture.md` as ground truth — they answer some questions for you. Treat the active entries of `lessons.md` as constraints on the plan: when a lesson applies to this feature, build it into the relevant step (and its verification) and cite it (`L-NNN`) — so the mistake is designed out, not just remembered.

### 2. Size the feature and surface the unmade decisions

From the request + context, build a private list of the decisions this feature requires. Walk these categories and flag the ones that are genuinely open:

- **Boundaries & scope** — what's in vs explicitly out? What's the smallest version that's still useful?
- **Actors & use cases** — who uses this, through which scenarios?
- **Authentication & authorization** — who can do this? How is identity established and checked?
- **Data model** — entities, fields, relationships? Where does state live? Migrations?
- **Interfaces & contracts** — API shape, function signatures, events. What calls this, what does it call?
- **Error & edge behavior** — failure, empty, concurrent, partial input? Retries, timeouts, idempotency?
- **Dependencies & integration** — new libraries or services? How does it fit existing modules?
- **Non-functional** — performance, scale, security, observability.
- **Testing & rollout** — how is correctness verified? Feature flag? Migration/backfill path?

Then size it:

- **Trivial** (a fix, a rename, no open decision): say so in one line, and ask via AskUserQuestion whether to skip straight to implementation (recommended) or plan anyway. No files are written for a trivial task.
- **Small** (one scenario, no significant decision): `build-plan.md` only, with a short "Spec" section inside it.
- **Medium**: `spec.md` (use cases written inline) + `build-plan.md`.
- **Large** (several actors or flows, cross-cutting decisions): `use-cases.md` + `spec.md` + `build-plan.md`.
- **At any size**, each *significant* decision gets its own ADR (see step 5).

### 3. Ask, one at a time

Lead with the decision that most constrains the rest (usually scope or data model). For each, one AskUserQuestion call:

- The question states the decision plainly and why it matters for this feature.
- 2–4 options, recommended first with "(Recommended)", each description giving the trade-off.
- Use `preview` when options are concrete artifacts worth comparing side by side (API shapes, schemas, folder layouts).
- Wait. Use the answer to prune or reshape the remaining questions.

Stop when nothing material is left to decide. Don't pad the conversation.

### 4. Present the plan and confirm

Present the plan in the conversation — it is what the files will contain, condensed:

- **Feature** — one paragraph: what's being built and why. Folder: `context/features/<slug>/`.
- **Use cases** — actor + scenario, one line each (`UC-1`, `UC-2`…).
- **Decisions** — every decision made in this conversation, with the chosen option, a one-line rationale, and whether it was *decided* or *defaulted*. Mark the ones that will become ADRs. This is the most important section: it's the record that stops the re-guessing.
- **Out of scope** — what was explicitly excluded.
- **Implementation steps** — ordered, concrete, referencing real files/modules, each with how it's verified.
- **Open questions** — anything deferred, with who/what unblocks it.
- **Files to write** — which files this will create or update, per the sizing in step 2.

Then confirm with AskUserQuestion: "Approve and write the files (Recommended)" / "Change a decision" / "Change scope or file set". On a change, adjust and show the plan again. If the session is in plan mode, present the plan through ExitPlanMode instead; files are written once it's approved.

### 5. Write the files

Only after explicit approval, and before writing any code:

- **`context/features/<slug>/`** — write `use-cases.md`, `spec.md`, `build-plan.md` from the templates, per the sizing. The slug is short kebab-case, no date (`auth-login`, `export-pdf`). If the folder already exists, update the files in place and add a line to the spec's *Revisions* section.
- **ADRs** — a decision gets an ADR when it is hard to reverse, cross-cutting, or sets a convention other features will follow (auth scheme, database, API error format, a new core dependency). Feature-local choices (a field name, a local UI choice) stay in `spec.md`. Number ADRs sequentially after the highest existing one (`0001`, `0002`…), from `templates/adr.md`. When a decision replaces an older ADR, set the old one's status to `Superseded by ADR-NNNN` — never delete or rewrite its body.
- **`context/project/architecture.md`** — update only if the feature adds or changes a module, a layer boundary, an external service, or a core dependency.

**One source per fact.** Files reference each other instead of copying: the spec cites `UC-n` and `ADR-NNNN`, the build plan cites `AC-n`. Something that changes should only need editing in one place.

### 6. Hand off to build

This skill stops once the files are written — implementing the plan is the `build` skill's job, and keeping it separate means an interrupted implementation can resume from the plan without re-running this conversation.

Report in one line what was written where, then ask with AskUserQuestion: "Start building now with `/build` (Recommended)" / "Stop here — build later". On the first, follow the `build` skill for this feature. On the second, suggest `/remember` so the next session knows the plan is ready.
