---
name: map
description: Bring an existing codebase into the context/ system by mapping what's actually there. Fans out read-only subagents over the code (structure and boundaries, data and integrations, conventions, tooling), then writes context/project/architecture.md from evidence, proposes retroactive ADRs for the decisions visible in the code, turns inconsistencies (two error-handling styles, two HTTP clients…) into questions for the user, and records the project's commands in CLAUDE.md. Re-run later to find where the code has drifted from architecture.md. Never changes the code. Use when adopting architect/build/review on a project that already has code, when context/ is empty or stale, or whenever the user says "map", "map the codebase", "cartographie le projet", "document the architecture", or "onboard this repo".
---

# Map

The failure this prevents: you bring the `architect` / `build` / `review` workflow to a project with two years of code, and `context/` is empty. `architect` has no architecture to ground its recommendations in, `review` has no boundaries to check against, and every agent re-derives the same picture from whatever files it happens to open — each time slightly differently. This skill builds that picture once, from evidence, and writes it where every other skill will read it.

The goal is not to judge or fix the code. The goal is to **make the existing architecture explicit — the structure, the decisions it embodies, the conventions it follows — and let the user confirm what's intended and what's accidental.**

## The rules

1. **Describe what is, not what should be.** Record the architecture the code actually has, not the one you'd design. Don't invent layers, rename modules to be tidier, or import conventions from elsewhere.
2. **Every claim has evidence.** Each module, boundary, convention and decision in the output points to real paths (`src/api/`, `lib/db.ts:12`). A claim you can't point to doesn't get written.
3. **Inferred is not decided.** The code shows *what* was chosen, rarely *why*. A retroactive ADR is a proposal until the user confirms it; its rationale is either what the user tells you or explicitly "not recorded".
4. **Inconsistencies are questions, not fixes.** Two ways of doing the same thing is a fork the user resolves: which one is canonical? Ask, with the dominant or most recent pattern recommended. Never refactor the code — the divergent places go on a list.
5. **Right depth.** Map modules, boundaries, data flow and conventions — not every file. `architecture.md` should be readable in a few minutes (aim for under ~150 lines); a deeper need is a feature for `architect`, not a bigger map.
6. **Read-only on the code.** This skill writes only inside `context/` and `CLAUDE.md`.

## Process

### 1. Check the starting point

- **No `context/`, or no `context/project/architecture.md`** → this is a **first map**. Create the structure the `architect` skill defines (its step 0, using its `templates/`: `context/README.md`, `context/project/`, `context/project/adr/`, `context/features/`), then map.
- **`architecture.md` already exists** → this is a **re-map**: the job is to find drift between the document and the code (step 5), not to rewrite it from scratch.
- **ADRs already kept elsewhere** (`docs/adr/`, `doc/architecture/decisions/`…) → read them and keep using that folder and its numbering.

### 2. Survey (yourself, quickly)

Before fanning out, get the lay of the land — cheaply, without reading code in depth:

- the top-level tree (two or three levels), languages, and package manifests (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`…), including workspaces/monorepo packages;
- entry points (main files, servers, CLIs, workers), CI config, Dockerfiles, deploy config;
- README, `docs/`, `CLAUDE.md`, any existing architecture notes or ADRs;
- `git log` recency per top-level directory — which parts are alive, which are legacy.

From this, decide the fan-out: the four dimensions below, plus — for a monorepo or a very large codebase — one extra subagent per major package or service.

### 3. Fan out

Launch read-only `Explore` subagents in parallel, all in a single message, thoroughness "very thorough". Each prompt is self-contained: the repo root, the survey facts it needs, its dimension, rules 1–2 above, and the report format below.

- **Structure & boundaries** — modules and layers, what each is responsible for, entry points, and the **dependency direction** between modules (who imports whom). Flag cycles and layer skips (e.g. UI code importing the DB layer).
- **Data & integrations** — databases and ORM, schema and migrations, where state lives, caches and queues, external services and SDKs, authentication and authorization mechanism.
- **Conventions** — error handling, logging, configuration and secrets, input validation, API style, naming, file organization, testing style. For each: the **dominant pattern with a count and 2–3 example paths**, and the **outliers** with their paths.
- **Tooling & operations** — the exact commands to install, run, test, typecheck, lint, format and build; CI steps; environments and how config differs between them.

Report format for every subagent:

```
## Findings
- <claim> — evidence: `path`, `path:line` — confidence: high | medium | low
## Inconsistencies
- <topic>: pattern A (n uses, e.g. `path`) vs pattern B (m uses, e.g. `path`) — newer: A | B | unclear
## Decisions visible in the code
- <choice, e.g. "Postgres via Prisma"> — evidence: `path` — alternatives visibly rejected, if any
## Unknowns
- <what the code can't tell>
```

You only need the extracted findings back, not file dumps.

### 4. Synthesize and ask

Merge the reports into four piles:

- **Architecture draft** — overview, modules and layers table, boundaries and rules, external services and core dependencies, conventions — shaped by `architect`'s `templates/architecture.md`.
- **ADR candidates** — decisions visible in the code that are significant: hard to reverse, cross-cutting, or setting a convention (the language/framework, the database and ORM, the auth scheme, the API style, the error format, the deployment model). Not every library is an ADR.
- **Inconsistencies** — each one a fork (rule 4).
- **Unknowns** — things only the user can answer (usually *why*).

Then resolve them with the user, through AskUserQuestion:

1. **Inconsistencies first**, one question per call — "Error handling: which pattern is canonical?" — options: the dominant/newer pattern "(Recommended)" with its count and example path in the description, the other pattern, "Both are intended (explain)". Low-stakes ones can be batched into a single "here are my defaults for X, Y, Z" question.
2. **ADR candidates** — list them in the conversation with their evidence, then confirm with multiSelect questions (up to 4 candidates per question, several questions per call): "Which of these should be recorded as ADRs?" For each confirmed one, if the user knows the reason, take it; otherwise the rationale is "not recorded — inferred from the code".
3. **Unknowns** — only the ones that change how the next agent would work; skip the merely curious.

### 5. Re-map: find the drift

On a re-map, compare the existing `architecture.md` and ADRs with the fresh findings, and sort every difference:

- **The code evolved** — a new module, a changed boundary, a replaced dependency, used coherently → propose updating the document (and, for a replaced ADR decision, a new ADR that supersedes the old one).
- **The code drifted** — a few places break a documented rule → the document stands; the places go on the drift list.
- **Unclear** → ask, as in step 4.

### 6. Write

After the user's answers, write:

- **`context/project/architecture.md`** — from the template, with evidence paths, the confirmed canonical conventions, and `Last updated:` set. On a re-map, edit in place.
- **ADRs** in `context/project/adr/` from `architect`'s `templates/adr.md`, numbered after the highest existing one, with **Status:** Accepted, **Origin:** project-wide, **Decided by:** "retroactive — inferred from the code, confirmed by the user on YYYY-MM-DD", and the evidence paths in *Context*.
- **`CLAUDE.md`** — the context pointer from `architect`'s `templates/context-readme.md` if it's missing, and a **Commands** section with the exact install/run/test/typecheck/lint/build commands if CLAUDE.md doesn't already list them. `build` and `review` rely on these.
- **`context/README.md`** — the ADR folder location, if it's not the default.

Write in the language the user works in.

### 7. Report

Present in the conversation:

- what was written: files, the number of ADRs, the conventions made canonical;
- **the drift / inconsistency list** — for each resolved fork, the places that follow the non-canonical pattern, with `file:line` links — reported, not fixed (rule 4). If the list is long, suggest planning the cleanup as a feature with `/architect`;
- open unknowns left unanswered.

Then suggest the next step: `/imprint` if the project has a UI (UI patterns are its job, not this one's), and `/architect` for the next feature — it can now ground its recommendations in a real map.
