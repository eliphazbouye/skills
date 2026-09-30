# Worktrees — the shared mechanics

<!-- Read by `feature`, `endurance`, `fix`, `verify`, `review`, `ship` and `land`. One source for how parallel features live side by side. -->

## The model

**One feature = one branch = one worktree.** The feature's `context/` files (brief, plan, findings, acceptance run) are committed on its branch, so its state travels with it and never collides with another feature's. Two agents never work in the same worktree at the same time.

- **Branch:** `feat/<slug>` for a feature, `fix/<slug>` for a bug fix.
- **Location:** what the `## Worktrees` section of `CLAUDE.md` says; otherwise `../<repo>.worktrees/<slug>` for a feature and `../<repo>.worktrees/fix-<slug>` for a fix (a sibling of the main checkout, so tools that scan the repo don't see it).
- **Main worktree:** the checkout where the base branch lives. `endurance` runs there; features don't.
- **Base ref:** always `origin/<base>` after a `git fetch` — never the local `<base>`, which can't be fast-forwarded while it's checked out in the main worktree and goes stale. (No remote → the local base.)

## Tooling

`scripts/wt.py` (next to this file) implements what follows — prefer it to retyping the git commands, which are shown below so the mechanics stay understandable and usable without the script:

- `wt.py create <slug> [--fix] [--from <branch>]` — worktree, branch without upstream, assigned ports
- `wt.py board` · `wt.py overlap` · `wt.py integrate --test "<cmd>"` — the view across features (used by `endurance`)
- `wt.py stale <worktree> <recorded HEAD>` — exit 1 when stale
- `wt.py renumber <worktree> [--apply]` — ADR / lesson collisions after a sync
- `wt.py mail …` · `wt.py event …` · `wt.py metrics` — messages between features, the flow log, the timings

Its shared state (port registry, messages, flow log) lives in `<git common dir>/endurance/` — seen by every worktree, never committed.

## The working root

Every stage runs against **one working root**: the feature's worktree.

- In a session started inside the worktree (`/feature` there), the working root is the current directory — nothing to do.
- In a session whose directory is elsewhere — the `endurance` session, or a worker — state `Working root: <absolute path>` at the start of the stage and hold to it: **every** relative path in the stage's skill (`context/…`, `CLAUDE.md`, source files) resolves under it, and **every** command runs as `cd <root> && …` or `git -C <root> …`. Never use the EnterWorktree tool for this (it creates a new worktree rather than entering an existing one, and its exit may offer to delete it).
- After a stage run from the `endurance` session, check the main worktree was not touched: `git -C <main> status --porcelain` is unchanged and `git -C <main> log -1` is the same commit. Anything else is an error — report it before going on.

## The recipe (first time only)

Before creating the first worktree, the project needs a `## Worktrees` section in `CLAUDE.md`. If it's missing, build it **first**:

1. List the ignored files at the root of the main worktree (`git ls-files --others --ignored --exclude-standard --directory`), keep the config-like ones (`.env*`, `CLAUDE.local.md`, local config), never `node_modules` or build output.
2. Find the install command, and how the app and its **tests** pick their port and database (env vars, compose file, test config).
3. Plan isolation (below). If it needs a project change — typically making a compose port configurable (`"${DB_PORT:-5432}:5432"`) — that's a decision: ask.
4. Propose the recipe; after the user confirms, commit it in the main worktree (`chore: worktree setup`, asking before committing on the base) and push it with approval — worktrees are created from `origin/<base>` and must see it. If the user doesn't want to push yet, create worktrees from the local `<base>` until it's pushed.

```markdown
## Worktrees
- Location: ../<repo>.worktrees/<slug>
- Copy from the main worktree: CLAUDE.local.md
- Generate per worktree (.env.local): PORT=<app port> DB_PORT=<db port> DATABASE_URL=postgres://…:<db port>/shop
- Install: npm ci
- Database: COMPOSE_PROJECT_NAME=shop-<slug> DB_PORT=<db port> docker compose up -d db && npm run db:migrate && npm run db:seed
- Can't be isolated: <e.g. the shared Stripe test webhook> → runs using it happen one at a time
```

Skills read the recipe from the **main worktree's** `CLAUDE.md` (it's the up-to-date one).

## Create and bootstrap

1. `wt.py create <slug>` does steps 1–2. By hand: `git fetch`, then `git worktree add --no-track -b feat/<slug> <path> origin/<base>` — `--no-track`, so the branch doesn't track the base (a plain `git push` would otherwise target it). `ship` pushes with `git push -u origin feat/<slug>`.
2. **Assign ports.** The script takes the next free pair in the shared registry (under a lock, so two agents never get the same); by hand, the next ones not used by another worktree's plan header. Record them in the plan (or fix record) header: `**Ports:** app 3002 · db 5434`. Don't rely on "whatever is free right now": two agents would pick the same.
3. **Bootstrap** with the recipe: copy the listed files, generate the per-worktree env file with the assigned ports, install, start and migrate the isolated database.
4. Fill the header fields `Branch`, `Worktree`, `Ports` as soon as the plan or record exists.

## Isolation

Two worktrees must never share what they write to — **in every stage that runs the app or the tests** (build, review's checks, verify, fix), not only in verify:

- **Ports** — the assigned ones, through the per-worktree env file.
- **Database** — its own, on its own host port (a compose project per slug with `DB_PORT`, or a database name suffixed with the slug). Migrations and seed run on it.
- **Anything else external** (a queue, a bucket, a webhook tunnel, a sandbox account) — isolated if the recipe says how; otherwise listed under *Can't be isolated*, and runs that use it happen one at a time (`endurance` serializes them).

## Entering a worktree

- **This session moves in** — only when the user is driving one feature with `/feature`: from now on, the working root is the worktree (see above).
- **A new session** — give the user the command for a new terminal: `cd <path> && claude "/feature <slug>"`. Recommend it when this session already drives another feature, or is the `endurance` session and the stage is a long conversation.

## Finding every feature in flight

- `git worktree list --porcelain` — each worktree, its path and branch.
- `git for-each-ref --format='%(refname:short)' refs/heads/feat refs/heads/fix` — branches that may have no worktree.
- A feature's state: read the files **in its worktree** (they include uncommitted work, see `git -C <wt> status --porcelain`); without a worktree, `git show <branch>:context/features/<slug>/build-plan.md` (or `brief.md`, or `context/fixes/<slug>.md`).
- Whether a PR merged: `gh pr view <n> --json state,mergedAt` — git alone can't tell after a squash merge.
- A worker marker `<wt>/.endurance-worker` (see `endurance`) means a worker is or was running there.

## Stale

A review or an acceptance run records the HEAD it checked. It is **stale** when the code the feature touches changed since then:

```
git -C "$wt" diff --name-only -z origin/<base>...HEAD -- . ':!context/' \
  | xargs -0 -r git -C "$wt" diff --quiet <recorded HEAD> HEAD --    # non-zero exit → stale
```

…or when `git -C "$wt" status --porcelain -- . ':!context/'` shows uncommitted changes. `wt.py stale <wt> <recorded HEAD>` runs both checks (exit 1 = stale) and lists the files. It compares trees, not commit dates: it survives a squash, ignores `context/` edits, and a sync with the base that touches none of the feature's files doesn't make it stale — one that does, does (the feature must be re-checked against the new code around it).

## Sync with the base

Run before opening the PR (`ship`), before merging (`land`), and after another feature merges (`endurance`) — only in a worktree where no worker is running.

1. `git fetch`, then bring `origin/<base>` in — rebase if nothing is pushed yet, merge if it is (unless CLAUDE.md says otherwise).
2. **A conflict you can't resolve with certainty** → `git rebase --abort` / `git merge --abort`, and hand it to the user (a worker returns `needs-decision`). Never leave a worktree mid-rebase.
3. **Conflicts in `context/`** — project-wide files (`lessons.md`, `memory.md`, `architecture.md`, the ADR folder) usually conflict because both sides *added* entries: keep both. Both sides changed the *same* rule or boundary in `architecture.md` → a decision: ask.
4. **Renumber** — `wt.py renumber <wt>` shows the plan (dry run), `--apply` does it and lists the references to check by hand. The rule: for each ADR number or `L-NNN` id this branch *added* that now also exists on the base: move it to the next free number (`git mv adr/0006-notif.md adr/0007-notif.md`, fix its title). Rewrite references **only in files this branch added or modified** (`git diff --name-only origin/<base>...HEAD`), matching both the id (`ADR-0006`) and the file name (`0006-notif`) — never in files that came from the base, which cite *their* ADR-0006. Check each hit by hand. Commit on its own (`chore(context): renumber ADR-0006 → ADR-0007`).
5. **Migrations** — schema migrations from both sides can clash or run out of order: re-sequence this branch's migrations per the ORM's rules (new timestamp or number after the base's latest), and re-run them on the worktree's isolated database from scratch.
6. **Conflicts in code** — resolve following `build`: understand both sides, keep both intents, run the tests. Ambiguous → abort and ask (step 2).
7. Run the full checks. Then apply **Stale**: if the sync touched the feature's files, the review and the acceptance run need redoing.

## Stacked features

A feature that needs another one still in flight starts from that one's branch instead of waiting: `wt.py create <b> --from feat/<a>`, with `**Depends on:** feat/<a>` in its plan header. Its PR targets `feat/<a>` (so its diff shows only its own work) and it never merges before `<a>`. When `<a>` merges: `git -C <B> rebase --onto origin/<base> <the commit of feat/<a> B was built on> feat/<b>` (`git merge-base feat/<b> feat/<a>` before `<a>`'s branch is deleted), retarget the PR to the base (`gh pr edit <n> --base <base>`, with approval), then the staleness rule applies.

## Messages between features

Features built at the same time tell each other what affects them: `wt.py mail post --from <slug> --to <slug|all> --kind heads-up|request|answer|info "<text>"`, `wt.py mail read <slug>` (marks read), `wt.py mail list`. Heads-ups go out *before* a shared function, file, schema or convention changes when possible. Messages inform; they never override a plan or a user's decision — a message that would change a plan is a decision for the user.

## Flow log

Every stage logs itself so delivery can be measured: `wt.py event <slug> <stage> start | wait | resume | end`, and `shipped` at the merge. `wait` when the stage stops for the user, `resume` when answered. `wt.py metrics [<slug>] [--gh] [--markdown]` turns it into lead time, time per stage (active and waiting), re-runs, CI and delivery durations, and quality counters. When one session drives the feature alone (`feature`), it logs; under `endurance`, endurance logs for its workers.

## Removing a worktree

After the merge is confirmed (`gh pr view --json state` says `MERGED`), from another worktree — a session can't remove the one it stands in:

1. Stop its processes; tear down its isolated resources (`COMPOSE_PROJECT_NAME=<repo>-<slug> docker compose down -v`, or drop its database).
2. `git worktree remove <path>`.
3. Delete the branch: `git branch -D feat/<slug>` (`-d` refuses after a squash merge; the PR state is the proof it merged), and the remote branch if the platform didn't.

Ask before each deletion. Then `wt.py ports release <slug>`.
