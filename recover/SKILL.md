---
name: recover
description: Diagnose why a long session has gone off the rails and apply the right correction. Stops the attempts, lists what was tried, re-establishes ground truth (including whether context/ itself is lying), gets a second opinion from a fresh subagent, and triages between four causes — polluted context, a wrong assumption, a real hidden bug, or a plan that can't work — each with its own cure. Saves the dead ends so the next session doesn't retry them, and fixes the source of a false premise. Use when attempts keep failing and you can't tell why, when `build` stops after repeated failures, or when the user says "we're spiraling", "this isn't working and I don't know why", "recover", "reset", "we're stuck", "on tourne en rond", "je comprends plus rien" — or on your own initiative when a third sound fix for the same problem has failed.
---

# Recover

The failure this prevents: four hours in, something is wrong and nobody knows *which kind* of wrong. The causes — a context filled with stale junk, a false premise adopted early, a real bug hiding well, a plan that can't be satisfied — feel identical from the inside: "we keep trying and it's not working." So the agent applies the wrong remedy (more reasoning when the cure was fresh ground truth; another fix when the cure was auditing a premise), fails again, and both of you spiral. And when the session ends, everything learned in the spiral — what was tried, what was ruled out — is lost, so the next session starts the same spiral.

This skill stops the spiral and runs a differential diagnosis. The point is **not to fix the problem yet** — it's to find out which problem you actually have, because each needs a different response — and to make sure the lesson survives the session.

## First move: stop and freeze

Before anything else, **stop writing code.** No new fix, no new theory. The spiral is made of attempts; adding another deepens it.

State plainly, in one or two lines: what we're trying to achieve, and what's actually happening instead. Just the observable gap — no theory about *why* yet. If you can't state the gap cleanly, that's already a signal (lean toward pollution below).

## List what was tried

From the session, write the **attempt log**: each approach tried, what it was supposed to fix, and what actually happened. Keep it factual — one line each.

This log is evidence (five sound fixes that all failed point to a wrong premise) and it is the most valuable thing to save: it becomes the *Dead ends* at the end.

## Establish ground truth

The diagnosis runs on facts, not on what the conversation believes. Get fresh reality, ignoring everything said earlier in the session:

- **Re-read the relevant files from disk right now.** Not from memory of them — actually read them.
- **Re-run the failing thing and read the real output**, not the remembered output.
- **Check the environment** — the cheap, classic culprits: a stale build or cache, a container image not rebuilt after a dependency change, a dev server still running old code, the wrong runtime or dependency version, a missing or different environment variable, the edited file not being the one that runs (wrong path, wrong package in a monorepo, a compiled copy).
- **Check what `context/` told the session.** The session was steered by `context/project/` (architecture, ADRs, lessons, memory's *Resume here*), the feature's `spec.md` and `build-plan.md`, and CLAUDE.md's commands. Check the claims the work relied on against the code and git as they are now.
- Note every place where fresh reality **disagrees** with what the conversation — or the context files — assert. Those disagreements are the strongest diagnostic signal you have.

## Get a second opinion

Write a **cold restatement**: the goal, the observable gap, the ground-truth facts you just verified, and the attempt log — no theories, no "probably", nothing from the session that you haven't just re-verified.

Give it to a fresh `general-purpose` subagent (it has never seen this conversation) and ask it, read-only, to investigate and propose its own diagnosis — which of the four modes below, and why, with evidence. Don't tell it your hypothesis.

- **It agrees with you** → the diagnosis is solid.
- **It disagrees** → take that seriously: a fresh context seeing something different is itself a strong sign the session's context is polluted (Mode A). Weigh its evidence, not its confidence.

Skip this for a very small problem where ground truth already made the cause obvious.

## Triage: which failure mode?

Walk these in order. The first that matches is your diagnosis. If two seem to match, polluted context is almost always underneath the others — clear it first, then re-triage.

### Mode A — Polluted context

The conversation now contains stale or contradictory information stated as fact: file contents that no longer match disk, bugs "already fixed" that reappear, the agent contradicting itself or re-suggesting something already ruled out.

**Tell-tale signal:** fresh ground truth **disagrees** with what the conversation has been confidently asserting — or the fresh subagent reads the situation differently.

**Correction — discard, don't reason.** More thinking on top of bad inputs produces more bad outputs.
- Trust only what you just read from disk/output. Treat every earlier claim in the session as unverified.
- If contradictions are pervasive, the cure is a fresh context: save the cold restatement into *Resume here* in `context/project/memory.md` (see *Save what the spiral taught*), then recommend the user `/clear` and say "where were we" — the `remember` skill's resume mode picks up from a clean state, nothing to paste.

### Mode B — Wrong assumption from earlier

Every fix has been locally sensible — each one *should* have worked — yet the problem never moves. You're solving a real problem competently; it's just not *the* problem, because something you took as given is false.

**Tell-tale signal:** the attempt log — a run of reasonable fixes, each failing. One or two attempts failing is normal; the fifth reasonable fix failing means a premise upstream is wrong.

**Correction — audit premises, don't try harder.** Trying harder on a false premise just fails more precisely.
- List the load-bearing assumptions the work has rested on: where this code is called from, how that API behaves, the shape of the data, which file/branch/env is actually live, that the thing you're editing is the thing that runs — **and what the context files said** (an ADR, `architecture.md`, a spec line, *Resume here*, a CLAUDE.md command).
- Find the **earliest** one that was never directly verified against reality.
- Verify *that one* against ground truth before touching anything else. Wrong premises are usually early and cheap to check once named.
- **If the false premise came from `context/`, fix the source** — or the next session walks into the same trap. A stale *Resume here* or a wrong fact in memory → correct it now. A wrong or outdated ADR, spec or architecture claim → route it: `/architect` for a decision, `/map` for architecture drift, `/tidy` for the broader cleanup.

### Mode C — Real hidden bug

Ground truth matches what the conversation believes, the environment is clean, and the fixes have been aimed at the right place — the defect is just hiding (off-by-one, race, wrong variable, edge case). Reach this mode only after A and B are ruled out; "it's just a hard bug" is the spiral's favorite excuse for not checking the others.

**Tell-tale signal:** no contradictions with ground truth, no false premise found — the system is understood correctly and the bug is genuinely elusive.

**Correction — narrow, don't guess.** Stop proposing fixes; make the bug observable.
- **Reproduce it with a failing test** — the smallest one that still fails. Shrinking the surface usually exposes the cause, and the test becomes the regression test once it's fixed (as in `build`).
- Add observability — log/print actual values at each step — and compare expected vs actual to localize where reality first diverges.
- **Bisect.** If it used to work, `git bisect run <the failing test>` finds the commit that broke it; otherwise binary-search the inputs or the code path instead of pattern-matching.

### Mode D — The plan can't work

The code does what the plan says, but the plan itself is contradictory or impossible: two acceptance criteria that can't both hold, a constraint the current architecture can't meet, a spec that assumed something the system doesn't do.

**Tell-tale signal:** fixes trade one failure for another — making `AC-2` pass breaks `AC-4`, and back again — or every correct implementation of the step violates an ADR or a boundary.

**Correction — fix the plan, not the code.** No amount of code resolves a contradiction in the requirements.
- Name the contradiction precisely: which criteria, constraints or ADRs conflict, with the evidence.
- Hand it back to the user: the decision belongs in `/architect` (revise the spec, supersede the ADR, or cut scope). Mark the affected build-plan step as blocked with a one-line note — don't tick it, and don't keep coding around it.

## Report and agree

Tell the user, briefly:

1. **Which mode** (A/B/C/D) and the one concrete signal that points there — the specific contradiction, the failed-but-sound fix, the confirmed-clean state, or the conflicting requirements — and whether the fresh subagent agreed.
2. **The matching correction** and the immediate next step.

Then ask with AskUserQuestion: "Apply the Mode X correction (Recommended)" / "I think it's a different cause" / "Stop here". Do not slide back into fixing before the diagnosis is named and agreed — naming it is what breaks the spiral.

**Offer a return to the last good state** when the working tree holds a pile of half-finished attempts: shelve them — `git stash push -m "recover: attempts on <problem>"` or a `wip/<problem>` branch, never a destructive reset — and restart from the last commit that worked. Offer it as an option in the same question when it applies; do it only on the user's choice.

## Save what the spiral taught

Before moving on (or before the user clears the session), with a quick confirmation of what will be written:

- **Dead ends** → add the attempt log's ruled-out approaches to *Dead ends* in `context/project/memory.md`, each with why it failed. This is what stops the next session from retrying them.
- **Resume here** → update it with the cold restatement and the agreed next step, so a `/clear` + resume starts clean.
- **The source of a false premise** → corrected or routed (Mode B).
- **A lesson, if the cause generalizes** — a mistake a future agent could make on a different feature ("rebuild the container after changing dependencies", "the ORM's `update` silently ignores unknown fields") → propose an entry in `context/project/lessons.md`, as the `review` skill does: stated as an instruction, with why and where it was seen. Only with the user's OK; a one-off bug is not a lesson.

## The bar

A good recovery ends with the user able to say "we were stuck because *X*" in one sentence, knowing the single next action — and with the next session unable to fall into the same spiral. If you've only produced another fix attempt, you skipped the diagnosis.
