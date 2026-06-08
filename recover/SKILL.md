---
name: recover
description: Diagnose why a long session has gone off the rails and apply the right correction. Use when you're hours into a session, attempts keep failing, and you can't tell whether it's a real bug, polluted context, or a wrong assumption made earlier. Triggers — "we're spiraling", "this isn't working and I don't know why", "recover", "reset", "we're stuck", or whenever fix attempts have stopped moving the problem.
---

# Recover

The failure this prevents: four hours in, something is wrong and nobody knows *which kind* of wrong. The three causes — a real bug, a context that's filled with stale junk, a false premise adopted early — feel identical from the inside: "we keep trying and it's not working." So the agent applies the wrong remedy (more reasoning when the cure was fresh ground truth; another fix when the cure was auditing a premise), fails again, and both of you spiral.

This skill stops the spiral and runs a differential diagnosis. The point is **not to fix the problem yet** — it's to find out which of three problems you actually have, because each needs an opposite response.

## First move: stop and freeze

Before anything else, **stop writing code.** No new fix, no new theory. The spiral is made of attempts; adding another deepens it.

State plainly, in one or two lines: what we're trying to achieve, and what's actually happening instead. Just the observable gap — no theory about *why* yet. If you can't state the gap cleanly, that's already a signal (lean toward pollution below).

## Establish ground truth

The diagnosis runs on facts, not on what the conversation believes. Get fresh reality, ignoring everything said earlier in the session:

- **Re-read the relevant files from disk right now.** Not from memory of them — actually read them.
- **Re-run the failing thing and read the real output**, not the remembered output.
- Note any place where fresh reality **disagrees** with what the conversation has been asserting. Those disagreements are the strongest diagnostic signal you have.

This step is also the cure for one of the three modes, so it is never wasted.

## Triage: which failure mode?

Walk these in order. The first that matches is your diagnosis. If two seem to match, polluted context is almost always underneath the others — clear it first, then re-triage.

### Mode A — Polluted context

The conversation now contains stale or contradictory information stated as fact: file contents that no longer match disk, bugs "already fixed" that reappear, the agent contradicting itself or re-suggesting something already ruled out.

**Tell-tale signal:** fresh ground truth (the re-read, the re-run) **disagrees** with what the conversation has been confidently asserting.

**Correction — discard, don't reason.** More thinking on top of bad inputs produces more bad outputs. Instead:
- Trust only what you just read from disk/output. Treat every earlier claim in the session as unverified.
- Write a clean, cold restatement of the problem and current state from ground truth alone — short enough that a fresh agent with no history could act on it.
- If contradictions are pervasive, recommend the user `/clear` (or start a new session) and paste that cold restatement in. A fresh context with a clean problem statement beats a polluted one every time.

### Mode B — Wrong assumption from earlier

Every fix has been locally sensible — each one *should* have worked — yet the problem never moves. You're solving a real problem competently; it's just not *the* problem, because something you took as given is false.

**Tell-tale signal:** the repeated gap between "this should work" and "it didn't." Sound reasoning, reality keeps disagreeing. One or two attempts failing is normal; the fifth reasonable fix failing means a premise upstream is wrong.

**Correction — audit premises, don't try harder.** Trying harder on a false premise just fails more precisely.
- List the load-bearing assumptions the work has rested on: where this code is called from, how that API behaves, the shape of the data, which file/branch/env is actually live, that the thing you're editing is the thing that runs.
- Find the **earliest** one that was never directly verified against reality.
- Verify *that one* against ground truth before touching anything else. Wrong premises are usually early and cheap to check once named.

### Mode C — Real targeting bug

Ground truth matches what the conversation believes, and the fixes have been aimed at the right place — the defect is just hiding (off-by-one, race, wrong variable, edge case). Reach this mode only after A and B are ruled out; "it's just a hard bug" is the spiral's favorite excuse for not checking the other two.

**Tell-tale signal:** no contradictions with ground truth, no false premise found — the system is understood correctly and the bug is genuinely elusive.

**Correction — narrow, don't guess.** Stop proposing fixes; make the bug observable.
- Get the **smallest reproduction** that still fails. Shrinking the surface usually exposes the cause.
- Add observability — log/print actual values at each step — and compare expected vs actual to localize where reality first diverges.
- Bisect: which change, input, or commit introduced it? Binary-search the space instead of pattern-matching.

## Report the diagnosis

Tell the user, briefly:
1. **Which mode** (A/B/C) and the one concrete signal that points there — the specific contradiction, the specific failed-but-sound fix, or the confirmed-clean state.
2. **The matching correction** and the immediate next step.
3. If it's Mode A and severe, the recommendation to `/clear` and the cold restatement to carry over.

Then, with the user's go-ahead, take that next step. Do not slide back into fixing before the diagnosis is named and agreed — naming it is what breaks the spiral.

## The bar

A good recovery ends with the user able to say "we were stuck because *X*" in one sentence, and knowing the single next action. If you've only produced another fix attempt, you skipped the diagnosis.
