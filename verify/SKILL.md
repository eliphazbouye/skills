---
name: verify
description: Check a built feature in the real running app, the way a user would, before shipping it — not just in the tests. Launches the app locally, walks every scenario of the feature (brief scenarios, use cases, acceptance criteria) through its real interface — browser, API, CLI — records what was observed as evidence, hands the checks that need human eyes to the user as a short checklist, and turns every failure into a finding in the build plan for `build` to fix. Never fixes, never touches production. Use after `review` says the code is ready and before `ship`, when tests are green but you want to see it work, or whenever the user says "verify", "recette", "teste dans l'app", "vérifie que ça marche vraiment", "check it in the browser", or "does it actually work".
---

# Verify

The failure this prevents: every test is green, the review is clean, the PR goes out — and the first person who opens the page sees a blank screen, because the component was never wired into the route, or the API returns the right JSON with the wrong status code, or the env variable only exists on the author's machine. Tests prove what they test. This skill looks at the whole thing running, scenario by scenario, like the user will.

The goal is not to re-test the code. The goal is **each scenario the feature promised, seen working in the running app — or a precise finding saying where it breaks.**

## The rules

1. **Observe, don't fix.** This skill runs the app and reports. A failure becomes a finding in the build plan; fixing is `build`'s job. Don't "quickly patch" what you find — the fix needs a regression test, and the author's shortcut is how the bug got in.
2. **Never production.** Run locally, or against a dev/staging environment the project documents for this. Never against production data or services, never with real payments, emails or messages — use the project's test mode, sandbox or stubs. If a scenario can't be run safely, it goes to the manual checklist.
3. **Evidence, not impressions.** Each scenario's result names what was done and what was observed: the URL and what the page showed (a screenshot when a browser is driven), the request and the response, the command and its output. "Works" is not a result.
4. **The scenarios come from the record.** Walk what the brief, the use cases and the acceptance criteria promised — not what the implementation happens to do.
5. **Say what you couldn't check.** Visual quality, feel, copy, anything needing a real device or account: hand it to the user as a checklist. Never mark it passed yourself.

## Process

### 1. Gather the scenarios

From `context/features/<slug>/` — or, for a bug fix, its record `context/fixes/<slug>.md` (the *Report*: the trigger and the expected behavior, plus the neighbouring flows the fix could break): the brief's scenarios (`S-n`, with their examples), `use-cases.md` (`UC-n`, main and alternative flows), and the spec's acceptance criteria (`AC-n`) and *Edge cases & errors*. Build a list: each entry is one path through the app, with its expected result, citing where it comes from. Include the main error paths the user can trigger (wrong input, no permission, empty state).

No feature folder → ask the user what the change was supposed to do, and walk that.

### 2. Launch the app

- Find how the project runs: CLAUDE.md, `package.json` scripts, `Makefile`, `docker-compose.yml`, the README. If the built-in `run` skill is available, follow it to launch and drive the app.
- **In a worktree, isolate first** (`../feature/worktrees.md` → *Isolation when the app runs*): a free port, a database of its own, per the `## Worktrees` recipe in the **main worktree's** CLAUDE.md, with the ports from the plan header — other features may be running their app at the same time. A resource the recipe lists as *can't be isolated* means this run must not overlap with another; say so if one is running.
- Start what's needed (the app, its database, its workers) in the background, with the project's dev or test configuration. Seed test data if the project has a seed script; otherwise create only what the scenarios need, through the app itself.
- The app won't start → that's the first finding (🔴), with the error. Don't fix the environment beyond what the project's docs say; if a step is missing from the docs, that's a finding too.

### 3. Walk each scenario

Pick the interface the user would use:

- **Web UI** — drive a browser (Playwright or the tool the project already has, or the one `run` provides): navigate, fill, click, and check what's shown. Take a screenshot at the key moment of each scenario.
- **API** — `curl` (or the project's HTTP client): the request, the status, the body, the relevant headers.
- **CLI / worker / job** — run the command or trigger the job; check the output, the exit code, and the side effect (the row written, the file produced, the message queued).

For each: **pass** (observed = expected, with the evidence), **fail** (what was expected, what was observed, where), or **manual** (can't be checked here, and why). Also note anything off that no scenario covered — an error in the console, a slow page, a broken layout next to the feature — as an observation, without severity.

### 4. Record

In the feature's `build-plan.md` (or the fix record):

- Write an *Acceptance run* section (create it after *Review findings* if missing), replacing the previous one: `> Run: run N · YYYY-MM-DD · HEAD <sha> (+ uncommitted: yes/no) · <n> pass · <n> fail · <n> manual (<n> confirmed, <n> pending)`, with N the previous run's number + 1, then one line per scenario with its result and evidence (screenshots saved under the feature folder only if the user wants them kept; otherwise described).
- Confirm the `[~]` V items whose scenario now passes (`[x]` + `(fixed, run N)`); reopen (`[ ]`) those still failing.
- Add each new **fail** as an open item under *Review findings*: `` - [ ] **V<run>-<n>** 🔴|🟡 <short title> — <scenario id> ``. 🔴 when a promised scenario doesn't work; 🟡 when it works with a visible defect. If any V item is open, set `Status:` back to `in-progress`.
- Commit the context/ change on its own (`chore(context): acceptance run N of <slug>`).

### 5. Report and hand off

Present: the scenario table (pass / fail / manual, with evidence), the failures with where they break, the observations, and the **manual checklist** — short, concrete items the user can tick in a few minutes ("open /orders on a phone: the export button is reachable").

Stop the app processes you started — except, as a `endurance` worker, when there are manual items: leave the app running and report its URL (endurance asks and stops it). If there are manual items, ask with AskUserQuestion first — this is a decision point even when a pipeline is driving: "Manual checks done — all OK" / "One or more failed" / "I'll check later". Record each item as `manual — confirmed YYYY-MM-DD`, a new V finding, or `manual — pending`. A run with pending manual items has not passed.

Then ask with AskUserQuestion:

- failures → "Fix them with `/build` (Recommended)" / "Ship anyway (recorded in the PR)" — which strikes the V items as `~~V1-1~~ accepted — <reason>` — / "Stop here";
- all pass and nothing pending → "Ship it with `/ship` (Recommended)" / "Stop here".

After fixes, a new run replaces the *Acceptance run* section and ticks the `V` findings it confirms fixed.
