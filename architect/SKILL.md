---
name: architect
description: Run the architecture conversation that should happen before building any serious feature. Reads the project's context/ folder, surfaces the decisions that haven't been made yet (auth, data model, error handling, boundaries…), asks focused questions ONE AT A TIME, presents a plan for approval, and passes to implementation only once the user confirms. Use before implementing a non-trivial feature, when a task has unstated design decisions, or whenever the user says "architect", "plan this feature", or "let's design X before building".
---

# Architect

The failure this prevents: you ask an agent to build a feature, it silently guesses at decisions you never made — what authentication to use, how to shape the data, what happens on error — and you discover the wrong guess only after it's built, then refactor. This skill forces that conversation *first*.

The goal is not to produce a big document. The goal is to **make the implicit decisions explicit and let the user decide them**, then capture the result as a plan.

## The rules

1. **One question at a time.** Never dump a list of questions. Ask one focused question, wait for the answer, let it inform the next. A wall of ten questions gets skimmed and half-answered — exactly the guessing this skill exists to stop.
2. **Surface decisions, don't make them.** When you spot a fork the user hasn't decided, name it and ask. Offer a recommended default so answering is easy, but the user chooses.
3. **Only ask what matters.** Skip decisions already settled by the context files, or ones with an obvious convention in this codebase. Don't manufacture questions to look thorough.
4. **Stop when the unknowns are resolved.** When nothing material is left to decide, present the plan. Don't pad the conversation.

## Process

### 1. Read the context

Read everything in `./context/`, `docs`(the context/docs folder in the current project's working directory). These files describe the project's goals, conventions, prior decisions, and constraints. Treat them as ground truth — they answer some questions for you.

If there is no `context/` folder, say so and offer to proceed from what's in the repo (CLAUDE.md, README, the code itself). Don't block on it.

Also skim the relevant existing code so your questions are grounded in what's actually there, not generic.

### 2. Surface the unmade decisions

From the feature request + context, build a private list of decisions this feature requires. Walk these categories and flag the ones that are genuinely open:

- **Boundaries & scope** — what's in this feature vs explicitly out? What's the smallest version that's still useful?
- **Authentication & authorization** — who can do this? How is identity established and checked?
- **Data model** — what entities/fields/relationships? Where does state live? Migrations?
- **Interfaces & contracts** — API shape, function signatures, events. What calls this, what does it call?
- **Error & edge behavior** — what happens on failure, empty, concurrent, or partial input? Retries, timeouts, idempotency?
- **Dependencies & integration** — new libraries or services? How does it fit existing modules?
- **Non-functional** — performance, scale, security, observability expectations.
- **Testing & rollout** — how is correctness verified? Feature-flagged? Migration/backfill path?

A decision is "open" only if the context files and codebase conventions don't already answer it. Don't re-ask what's already decided.

### 3. Ask, one at a time

Lead with the decision that most constrains the rest (usually scope or data model). For each:

- State the decision plainly and why it matters for this feature.
- Give 2–4 concrete options with a recommended default, or ask open-endedly if options would be artificial.
- Wait. Use the answer to prune or reshape the remaining questions.

Use the AskUserQuestion tool when the choice is a clean pick from a few options; ask in prose when it's genuinely open-ended.

### 4. Present the plan

When the material unknowns are resolved, present the plan directly in the conversation — do not write it to a file. Keep it tight and skimmable:

- **Feature** — one-paragraph summary of what's being built and why.
- **Decisions** — every decision made in this conversation, each with the chosen option and a one-line rationale. This is the most important section: it's the record that stops the re-guessing.
- **Out of scope** — what was explicitly excluded.
- **Implementation steps** — ordered, concrete steps to follow. Reference real files/modules.
- **Open questions** — anything deferred, with who/what unblocks it.

### 5. Confirm, then implement

Ask the user to confirm the plan. Invite corrections — if they want a decision changed, adjust the plan and show it again.

Only once the user explicitly confirms, proceed to implement the feature following the agreed plan. Do not start writing code before that confirmation — the whole point of this skill is that the conversation and approval happen *before* the building.
