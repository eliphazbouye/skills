---
name: spike
description: Answer a technical question with a throwaway experiment instead of an argument — "does this library support streaming?", "is this query fast enough on 1M rows?", "can we call this API from the edge runtime?". Frames one question with a success criterion and a time budget, experiments in an isolated worktree or branch that never merges, reports observed facts, records the answer where the decision it feeds lives (usually an ADR), and cleans up. Use when a decision in `architect` can't be settled without trying, before committing to a library or approach, or whenever the user says "spike", "prototype this quickly", "check if X can do Y", "est-ce que X supporte Y", or "teste vite si…".
---

# Spike

The failure this prevents: a decision gets made on belief. "This library handles streaming" — it does, except not in the runtime you deploy to, which you discover halfway through the feature. Or the opposite: the conversation goes around in circles for twenty minutes over something ten minutes of code would have settled. This skill settles it with code, keeps that code away from the real codebase, and writes down the answer.

The goal is not a prototype of the feature. The goal is **one question answered with evidence, feeding one decision.**

## The rules

1. **A question, not a feature.** A spike answers one explicit question, with a success criterion stated before starting ("streams the first token in under 1 s through the edge runtime"). "Try out library X" is not a question.
2. **Timeboxed.** Agree on a budget before starting — attempts or time. When it runs out, stop and report what's known; "inconclusive" is a valid answer, and more budget is the user's call.
3. **Throwaway and isolated.** Spike code lives in its own git worktree or branch (`spike/<slug>`), never touches the real code, and is never merged. Quality doesn't matter; honesty of the result does.
4. **Facts, not impressions.** Report what was run and what was observed — commands, outputs, measurements, versions. "Seems to work" isn't a result; "ran X with version Y, got Z" is.
5. **The answer lands where the decision lives.** The spike's result goes into the ADR, spec or memory entry it informs — not into a spike report nobody reopens.

## Process

### 1. Frame

Write down, in the conversation:

- **The question** — one sentence, answerable by yes / no / a number.
- **Why it matters** — the decision it feeds (an open question in `architect`, an ADR option, a build-plan step that depends on it).
- **Success criterion** — what observed result means "yes".
- **Budget** — e.g. "3 attempts" or "30 minutes of work".
- **Setup** — the versions, runtime and data that make the answer representative of the real project (the project's actual runtime and dependency versions, a realistic data size).

Confirm with AskUserQuestion: "Run the spike as framed (Recommended)" / "Change the question or criterion" / "Change the budget". A spike that answers the wrong question wastes its whole budget.

### 2. Isolate

Create a git worktree on a new branch `spike/<slug>` (or, if worktrees aren't possible, a scratch directory outside the source tree). Install only what the experiment needs, in that isolated place. Never edit the real project's code, lockfile or config for a spike.

### 3. Experiment

Write the smallest code that can answer the question under the realistic setup. For each attempt, note what you tried, what you ran, and what you observed. Stop as soon as the success criterion is clearly met or clearly failed — or when the budget runs out.

If you discover the question itself was wrong (the real constraint is elsewhere), stop and say so instead of answering a different question quietly.

### 4. Report

Present:

- **Answer** — yes / no / partially / inconclusive, in one line.
- **Evidence** — the commands and the observed output or measurements, with versions.
- **Limits** — what the spike didn't cover (scale, edge cases, other runtimes) and how much that matters.
- **Surprises** — anything learned on the way that affects the decision (a licence, a missing feature, a cost).
- **Recommendation** for the decision it feeds.

### 5. Record

Put the result where the decision lives:

- **Feeding an `architect` decision** → return to the `architect` conversation with the answer; the ADR's *Context* or *Options considered* cites it ("Spike YYYY-MM-DD: streaming works on the edge runtime with v4.2, first token in 0.4 s").
- **Feeding an existing ADR or spec** → add the finding there, in its *Context* or *Decisions*.
- **A "no" with no decision pending** → a *Dead ends* entry in `context/project/memory.md`, so nobody retries it.

### 6. Clean up

Ask with AskUserQuestion: "Delete the spike worktree and branch (Recommended)" / "Keep the branch for reference". The recorded evidence is what survives; the code is disposable. Never merge a spike branch — if its code turns out to be worth keeping, it gets rebuilt properly through `/architect` and `/build`.
