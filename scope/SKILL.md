---
name: scope
description: Interview the user until no grey zone is left on WHAT to build and WHY — the problem behind the request, who it's for, what success looks like, what's in and out, the constraints, concrete scenarios, and vague words hiding different meanings. Keeps a ledger of unknowns ranked by impact, asks ONE question at a time with a recommended answer, digs into vague, contradictory or second-hand answers, checkpoints regularly so the interview never drags, and writes the brief to context/ as it goes so an interrupted interview resumes where it stopped. Stops when every high-impact unknown is settled, then plays the brief back, finalizes it (features/<slug>/brief.md, or project/brief.md — split into features — for a whole new project) and hands off to `architect`. Use when a feature or project request is fuzzy, solution-shaped or under-specified, BEFORE design decisions. It is the default first step when a request just names a feature or product ("ajoute des notifications", "fais-moi une app de X", "build me a CRM") and context/ holds no brief for it — even when phrased as an order to build. Also whenever the user says "scope", "clarify this", "what should X do", "interview me", "cadrons le besoin", "cadrer", "clarifie", "pose-moi des questions sur le besoin", "lève les zones d'ombre", or "je sais pas trop ce que je veux".
---

# Scope

The failure this prevents: the request is "add notifications" or "build me a CRM", and everyone — you, the user, the agent — fills the gaps with a different picture. Notifications by email or in-app? For which events? Who turns them off? The design gets made, the code gets written, and only at the demo does it turn out the real need was something else. `architect` settles *how* to build; it assumes the *what* is already clear. Most of the time it isn't. This skill makes it clear first.

The goal is not a requirements document. The goal is **a shared picture with no blind spot: every unknown that would change what gets built is answered, deliberately deferred, or deliberately excluded — and written down.**

## The rules

1. **One question per AskUserQuestion call.** Never a list of questions in prose, never several in one call. Ask, wait, let the answer reshape what comes next. The only exception is the batch of low-impact defaults at a checkpoint (step 3).
2. **Always recommend.** Each question offers 2–4 concrete answers, the most likely one first with "(Recommended)", each description saying what that answer implies for the product. Ground the recommendation in what you know — the codebase, the domain, earlier answers — not in generic best practice. The user can always pick "Other".
3. **Rank every unknown by impact.** **High** — the answer changes what gets built (a scenario, a boundary, who the users are, a constraint). **Low** — a detail with a sensible default (a label, a limit, a sort order). High ones are asked one by one, most constraining first. Low ones are never asked one by one: they're settled in batches of proposed defaults.
4. **The interview must not drag.** Every 5 AskUserQuestion calls (follow-ups included), checkpoint: show the ledger and ask how to continue (step 3). An interview that exhausts the user produces careless answers — worse than a deferred question.
5. **Dig until it's concrete.** A high-impact answer is only resolved when two people would build the same thing from it. Vague words ("simple", "fast", "users", "secure", "like Notion", "handle errors") get a follow-up: a real example, a number, the exact case. A contradiction with an earlier answer gets named and settled, never quietly picked.
6. **Know who said it.** Every answer carries its source: **user** (they know it first-hand), **on behalf of <role>** (the user speaking for someone else — "sales want an export"), **code** / **context** (with the path). A second-hand answer is `[unverified]` until that person confirms it.
7. **Don't ask what you can find.** If the code, `context/`, the docs or an earlier answer settles it, record it with its source and move on. Ask only what only the user can know.
8. **What, not how.** Stay on the problem, the users, the behavior they'll see, the boundaries and the constraints. Technical choices belong to `architect`: record them as *hints for architect* and move on — unless it's an imposed constraint ("must run on our existing Postgres"). A technical assumption the whole thing rests on ("their API lets us do this") is flagged for `/spike`.
9. **"I don't know" is an answer, not an end.** Offer to take the recommended answer (**defaulted**), to defer it with an owner and a deadline (**deferred**), or to cut it (**out of scope**). An unknown never just stays open.
10. **Write at milestones, not after every answer.** The brief exists as a `draft` file from the first question on, with the ledger inside it. It's rewritten at each checkpoint and whenever the interview pauses or stops — so an interruption loses at most a few answers, without a file write after each one.

## The ledger

Kept in the brief's *Ledger* section while it's a draft, and shown in the conversation at each checkpoint. Each entry: status, impact, the question or answer, and the source.

```
[open]       high  Who can see a notification after it's dismissed?
[decided]    high  Channels: in-app only for v1 — user
[unverified] high  Sales need a weekly digest — on behalf of sales
[defaulted]  low   Retention: 30 days
[deferred]   high  Legal wording of the opt-out — owner: legal team, before release
[out]        high  Mobile push
```

`[unverified]` — a second-hand or technically conditional answer — counts as settled for moving on, but is listed at the handoff so someone confirms it.

## Process

### 0. Locate, or resume

- Check `context/`. If it exists, read `context/README.md`, `context/project/` (`architecture.md`, `brief.md` if any, `memory.md`, ADR titles) and list `context/features/`. If the request extends an existing feature, work in its folder and read what's there — the grey zones are then about the *change*.
- **A draft brief already exists** for this feature or project (`Status: draft`) → this is a resumed interview. Show its ledger in a few lines ("7 settled, 3 open — next: who can see dismissed notifications"), then continue at step 2 from the open high-impact entries. Don't re-ask what the ledger settles.
- **A feature** → the brief goes to `context/features/<slug>/brief.md` — the slug is short kebab-case in English, no date (`orders-csv-export`, `auth-login`), and `architect` keeps it. Tell the user the slug: it's what `/feature <slug>` takes. If `feature` or `endurance` already chose it (you're in its worktree), keep it. **A whole new project** → `context/project/brief.md`. If `context/` doesn't exist yet, create only `context/README.md` (from `architect/templates/context-readme.md` if available) and the folder the brief goes in; `architect` sets up the rest (it initializes whatever is missing, including `architecture.md`).
- **No `context/` but the repo already has substantial code** → the brief will be sharper on mapped code. Offer with AskUserQuestion: "Map the codebase first with `/map` (Recommended)" / "Scope now, map later".
- **A feature of a project that has a `context/project/brief.md`** → the feature brief builds on it: cite its scenarios (`S-n`), answers and constraints by reference, and record only what's new for this feature. Never copy them.
- On an existing codebase, read the code the request will touch, so questions are grounded and you don't ask what the code already answers.

### 1. Restate, seed the ledger — or exit fast

**Restate** the request in two or three sentences — your current understanding, gaps included.

**Solution-shaped request?** When the request is already a solution ("add a CSV export button", "we need a cache"), the real need may be elsewhere. Add *"what problem does this solve?"* as the first high-impact entry — but only if the answer could change what gets built. Ask it once, framed with candidate problems as options. If the user says the solution is the point, record it as a given and move on; don't insist.

**Seed the ledger** by walking these areas and adding every unknown — **high** if it changes what gets built, **low** if it has a sensible default:

- **Problem** — what pain or opportunity, for whom, and what happens today without it? Why now?
- **Users & actors** — who exactly (roles, not "users")? How many? Who else is affected (admins, support, third parties)?
- **Outcome & success** — what does "it works" look like for the user? How will we know it succeeded (a metric, a behavior, a date)?
- **Scenarios** — the main ones, walked through concretely: who does what, sees what, then what? At least one real example per scenario.
- **Boundaries** — what's in, what's explicitly out, what's the smallest version that's still worth shipping?
- **Edge behavior the user will see** — empty, too much, wrong input, no permission, the thing is deleted meanwhile, two people at once.
- **Data & content** — what information comes in and goes out, from where, who owns it, what must never be lost or leaked?
- **Constraints** — deadline, budget, imposed tech or platform, compliance/legal, languages, accessibility, existing systems to fit into.
- **Assumptions** — what are we taking for granted that, if wrong, breaks the whole thing?
- **Vocabulary** — domain words that could mean two things ("account", "project", "active").

**Reality check.** A request that presupposes something the code doesn't have ("add a logout link to the menu" in an app with no menu or no auth) is not clear, however simple it sounds: the missing premise is a high-impact entry.

**Fast exit.** If the seeded ledger has no high-impact entry — the request is already clear — say so in one line and ask with AskUserQuestion: "Skip to `/architect` — the need is clear (Recommended)" / "Scope it anyway". On a skip, write no file: pass the low-impact defaults to `architect` in the conversation as hints, and follow that skill. Don't interview for form's sake.

Otherwise, **write the draft brief** from `templates/brief.md`, in the language the user speaks with you (or the project docs' language) (`Status: draft`, the restatement as *Problem*, the ledger in *Ledger*), show the restatement and the ledger, and start asking.

### 2. Interview

Pick the open high-impact entry that constrains the most others (usually problem, users or boundaries first — a wrong answer there invalidates the rest). For each:

- One AskUserQuestion call: the question plainly, why it matters for what gets built, 2–4 options with the recommended one first. Use `preview` when comparing concrete things (two versions of a screen flow, two example outputs).
- Read the answer critically:
  - **Specific enough?** If not, a follow-up on the same point — ask for a real example, a number, or the exact case.
  - **Second-hand?** Record it `[unverified]` with the source *on behalf of <role>*; it goes to *Assumptions* and to *To ask others*.
  - **New unknowns?** Add them to the ledger, with their impact.
  - **Contradicts something?** Name both statements and ask which holds.
  - **Settles other entries?** Resolve them too, and say so.
  - **Rests on a technical unknown** ("only if their API allows it")? Record it `[unverified]`, marked *needs spike* — the answer is conditional until `/spike` or `architect` settles it.
- Update the ledger in the conversation. The brief file catches up at the next checkpoint: the ledger, and each answer in the section it belongs to (a scenario, a scope line, a constraint, a glossary term…).

Useful probes when an answer stays vague:
- "Give me a real example — the last time this happened, what exactly did you need?"
- "What should happen when <edge case>?"
- "If we shipped only X, would that be useful, or useless?"
- "What would make you say this failed?"
- "When you say <word>, do you mean A or B?"

### 3. Checkpoint

Every 5 AskUserQuestion calls, follow-ups included — and at once if the user's answers get short or impatient — rewrite the draft brief, show the ledger compactly (counts per status, the open high-impact entries by name), then ask with AskUserQuestion:

- "Continue — <n> high-impact left (Recommended)"
- "Take your defaults for the <m> low-impact details" — then show the proposed defaults as one list and let the user correct any of them in a single reply; record them as **defaulted**
- "Pause here — resume later" — the draft brief now holds everything; suggest `/remember` and stop

If the session ends between checkpoints (the user stops, the context is about to be compacted), rewrite the draft brief first.

Adapt the recommendation: when no high-impact entry is left, recommend settling the low-impact defaults and moving to the sweep.

### 4. Sweep

When no high-impact entry is open and the low-impact ones are settled, ask one last open-ended question with AskUserQuestion: "Is anything missing?" — "Nothing — the brief is complete (Recommended)" / "A scenario we didn't cover" / "A constraint we didn't mention" / "Someone else who should be consulted" — the last one adds that person and their questions to *To ask others*, without blocking the brief. Also check yourself: re-walk the areas of step 1 against the answers — anything still assumed rather than said goes back to the ledger.

### 5. Project mode: split into features

Only for a whole-project brief. Propose how the project breaks down into features, in the order they should be built: one line each (what it delivers, which scenarios it covers), its dependencies, and which one comes first — usually the smallest one that delivers a real scenario end to end. Confirm with AskUserQuestion ("This split and order (Recommended)" / "Change the split" / "Change the order"). It goes into the brief's *Features* section; each feature gets its own `scope` or `architect` pass later.

### 6. Play back and confirm

Present the brief, condensed, in the conversation — what the file will say. Omit empty sections; for a feature with three scenarios or fewer, keep it under ~15 lines:

- **Problem & why now** — one paragraph.
- **Users** — who, one line each.
- **Success** — how we'll know it worked.
- **Scenarios** — each walked through in a few lines, with its example.
- **In scope / Out of scope / Smallest useful version.**
- **Constraints.**
- **Assumptions** — each with its source and marked *confirmed*, *unverified* or *needs spike*.
- **To ask others** — per person or role, the questions only they can confirm.
- **Glossary** — the words pinned down.
- **Answers** — every question settled, marked *decided* / *defaulted* / *unverified*.
- **Deferred** — each with owner and when it must be answered.
- **Features** (project mode) — the split and order.
- **Hints for architect** — technical points raised on the way.

Confirm with AskUserQuestion: "Correct — finalize the brief (Recommended)" / "Something is wrong or missing" / "Change the scope". On a correction, fix it (re-open ledger entries if needed), and play it back again.

### 7. Finalize

Rewrite the brief in its final form: `Status: final`, the *Ledger* section removed (everything in it now lives in its proper section), a line in *Revisions*. If a final brief already existed, update it in place. Under `feature` or `endurance` (you're in the feature's worktree), commit the brief on its own (`chore(context): brief for <slug>`) — at each checkpoint for the draft, and when finalized — so the other features and endurance can see it. Deferred items that block building also go to the *Open questions* of the feature's `build-plan.md` if one already exists. Don't write `spec.md`, use cases or ADRs — that's `architect`'s job, and it builds them from this brief.

### 8. Hand off

Report in one line what was written where. List the `[unverified]` answers and, if *To ask others* isn't empty, who to ask — those confirmations are the user's to get. Then ask with AskUserQuestion:

- **Feature brief:** "Design it now with `/architect` (Recommended)" / "Settle a *needs spike* assumption first with `/spike`" (only if there is one) / "Stop here".
- **Project brief:** "Scope the first feature, <name>, with `/scope` (Recommended)" — or "Design the first feature with `/architect`" if it's already clear — / "Stop here".

On `/architect`, follow that skill: it reads the brief as settled ground, doesn't re-ask what it answers, turns its scenarios into use cases and its answers into the spec. On "Stop here", suggest `/remember` so the next session knows the brief is ready.
