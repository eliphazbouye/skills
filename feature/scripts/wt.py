#!/usr/bin/env python3
"""wt — mechanics for features built in parallel git worktrees.

Used by the feature, endurance, ship, land, verify and review skills (see ../worktrees.md).
Subcommands:
  create <slug> [--fix] [--from REF] [--path DIR]   worktree + branch + assigned ports
  ports [list|release <slug>]                         the shared port registry
  stale <worktree> <recorded-head>                    exit 0 fresh, 1 stale
  board [--json] [--gh]                               every feature in flight, with facts
  overlap                                             files / plans / ADR numbers shared between branches
  integrate [--test CMD] [BRANCH...]                  merge all active branches together in a scratch worktree
  renumber <worktree> [--apply]                       ADR / lesson numbers colliding with the base
  mail post|read|list ...                             the message channel between workers
  event <slug> <stage> start|end|wait|resume|shipped [--note T]   the flow log (timing)
  metrics [SLUG] [--gh] [--markdown]                  lead time, time per stage, waits, rework, quality
Everything is read-only except: create, ports release, renumber --apply, mail post/read (marks read),
and integrate (a temporary detached worktree, removed at the end).
"""
import argparse, fcntl, json, os, re, shutil, subprocess, sys, tempfile, time
from contextlib import contextmanager

# ---------------------------------------------------------------- git helpers

def git(*args, cwd=None, check=True, text=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=text)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.rstrip() if text else r.stdout

def git_ok(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True).returncode == 0

def common_dir(cwd=None):
    return os.path.abspath(os.path.join(cwd or os.getcwd(), git("rev-parse", "--git-common-dir", cwd=cwd)))

def main_worktree(cwd=None):
    out = git("worktree", "list", "--porcelain", cwd=cwd)
    return out.split("\n")[0].split(" ", 1)[1]

def has_remote(cwd=None):
    return "origin" in git("remote", cwd=cwd).split()

def base_name(cwd=None):
    if has_remote(cwd):
        ref = subprocess.run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
                             cwd=cwd, capture_output=True, text=True).stdout.strip()
        if ref:
            return ref.split("/", 1)[1]
    for b in ("main", "master", "trunk", "develop"):
        if git_ok("rev-parse", "--verify", "--quiet", f"refs/heads/{b}", cwd=cwd) or \
           git_ok("rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{b}", cwd=cwd):
            return b
    raise SystemExit("can't find the base branch (set origin/HEAD: git remote set-head origin -a)")

def base_ref(cwd=None):
    b = base_name(cwd)
    if has_remote(cwd) and git_ok("rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{b}", cwd=cwd):
        return f"origin/{b}"
    return b

def fetch(cwd=None):
    if has_remote(cwd):
        subprocess.run(["git", "fetch", "--quiet", "origin"], cwd=cwd, capture_output=True)

def worktrees(cwd=None):
    """[{path, branch}] for every worktree, main first."""
    res, cur = [], {}
    for line in git("worktree", "list", "--porcelain", cwd=cwd).split("\n") + [""]:
        if not line:
            if cur: res.append(cur); cur = {}
            continue
        k, _, v = line.partition(" ")
        if k == "worktree": cur["path"] = v
        elif k == "branch": cur["branch"] = v.replace("refs/heads/", "")
        elif k == "detached": cur["branch"] = None
        elif k == "prunable": cur["prunable"] = True
    return res

def feature_branches(cwd=None):
    out = git("for-each-ref", "--format=%(refname:short)", "refs/heads/feat", "refs/heads/fix", cwd=cwd)
    return [b for b in out.split("\n") if b]

@contextmanager
def locked(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".lock", "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try: yield
        finally: fcntl.flock(lf, fcntl.LOCK_UN)

def state_dir(cwd=None):
    d = os.path.join(common_dir(cwd), "endurance")
    os.makedirs(d, exist_ok=True)
    return d

# ---------------------------------------------------------------- features

def slug_of(branch):
    return branch.split("/", 1)[1] if branch and "/" in branch else branch

def kind_of(branch):
    return "fix" if branch and branch.startswith("fix/") else "feature"

def plan_path(kind, slug):
    return f"context/fixes/{slug}.md" if kind == "fix" else f"context/features/{slug}/build-plan.md"

def read_file(rel, wt=None, branch=None, cwd=None):
    if wt:
        p = os.path.join(wt, rel)
        return open(p, encoding="utf-8").read() if os.path.exists(p) else None
    r = subprocess.run(["git", "show", f"{branch}:{rel}"], cwd=cwd, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None

def section(md, title):
    m = re.search(rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", md or "", re.M | re.S)
    return m.group(1) if m else ""

def strip_comments(md):
    return re.sub(r"<!--.*?-->", "", md or "", flags=re.S)

def field(md, name):
    m = re.search(rf"\*\*{re.escape(name)}:\*\*\s*([^\n<·]*)", strip_comments(md))
    return m.group(1).strip().strip("`") if m else None

def parse_plan(md):
    if md is None:
        return None
    body = strip_comments(md)
    steps = re.findall(r"^- \[( |x)\] \*\*S\d+", section(body, "Steps"), re.M)
    findings = []
    for line in section(body, "Review findings").split("\n"):
        m = re.match(r"^- \[( |~|x)\] \*\*([RV])(\d+)-(\d+)\*\*\s*(🔴|🟡|⚪)?", line.strip())
        if m:
            findings.append({"state": m.group(1), "kind": m.group(2), "sev": m.group(5) or ""})
        elif re.match(r"^- (\[.\] )?~~", line.strip()):
            findings.append({"state": "struck", "kind": "", "sev": ""})
    def head(sec, pat):
        m = re.search(pat, section(md, sec))
        return m.group(1) if m else None
    review_head = head("Review findings", r"Last review:[^\n]*HEAD `([0-9a-f]{7,40})`")
    run = section(md, "Acceptance run")
    run_head = re.search(r"Run:[^\n]*HEAD `([0-9a-f]{7,40})`", run)
    ports = field(md, "Ports") or ""
    return {
        "status": (field(md, "Status") or "").split()[0] if field(md, "Status") else "",
        "pr": field(md, "PR"),
        "ports": ports,
        "steps_total": len(steps), "steps_done": steps.count("x"),
        "open_blocking": sum(1 for f in findings if f["state"] == " " and f["sev"] in ("🔴", "🟡")),
        "unconfirmed_R": sum(1 for f in findings if f["state"] == "~" and f["kind"] == "R"),
        "unconfirmed_V": sum(1 for f in findings if f["state"] == "~" and f["kind"] == "V"),
        "review_head": review_head,
        "run_head": run_head.group(1) if run_head else None,
        "run_failed": bool(re.search(r"\b\d*[1-9]\d* fail\b", run.split("\n")[1] if "\n" in run else run)) if run else False,
        "manual_pending": "manual — pending" in run,
        "pending_decisions": len(re.findall(r"unblocked by: user \(pending\)", body)),
        "planned_files": planned_files(body),
    }

def planned_files(md):
    txt = section(md, "Code context") + section(md, "Steps")
    return sorted({p for p in re.findall(r"`([\w./-]+\.[\w]+|[\w./-]+/)`", txt) if "/" in p or "." in p})

def is_stale(wt, recorded, base=None):
    """(stale: bool, files: list). Stale if the feature's own files differ from the recorded HEAD."""
    base = base or base_ref(wt)
    if not recorded or not git_ok("cat-file", "-e", f"{recorded}^{{commit}}", cwd=wt):
        return True, ["(recorded HEAD missing)"]
    files = [f for f in git("diff", "--name-only", "-z", f"{base}...HEAD", "--", ".", ":!context/",
                            cwd=wt).split("\0") if f]
    changed = []
    if files:
        changed = [f for f in git("diff", "--name-only", "-z", recorded, "HEAD", "--", *files,
                                  cwd=wt).split("\0") if f]
    dirty = [l[3:] for l in git("status", "--porcelain", "--", ".", ":!context/", cwd=wt).split("\n")
             if l and not l[3:].startswith(".endurance-worker")]
    return bool(changed or dirty), changed + [f"(uncommitted) {d}" for d in dirty]

def stage_of(kind, brief, plan, wt, pr_state=None):
    """The first matching row of feature's state table (best effort; the skill has the final word)."""
    if kind == "fix" and plan is None:
        return "fix"
    if kind == "feature":
        if plan is None and brief is None: return "scope"
        if brief is not None and "Status:** draft" in brief and plan is None: return "scope (resume)"
        if plan is None: return "architect"
    p = plan
    if p["status"] == "shipped": return "shipped"
    if p["pr"] and p["pr"] != "—":
        if pr_state == "MERGED": return "land (close-out)"
        return "land"
    if p["status"] == "draft" or p["steps_done"] < p["steps_total"]: return "build"
    if p["open_blocking"]: return "build (fix findings)"
    if p["status"] != "done" and kind == "feature": return "build (finish)"
    if wt:
        rstale = p["unconfirmed_R"] or not p["review_head"] or is_stale(wt, p["review_head"])[0]
        if rstale: return "review"
        vstale = (not p["run_head"] or p["unconfirmed_V"] or p["manual_pending"] or p["run_failed"]
                  or is_stale(wt, p["run_head"])[0])
        if vstale: return "verify"
    return "ship"

def owner(branch, base, cwd=None):
    out = git("log", "--format=%an", f"{base}..{branch}", cwd=cwd, check=False)
    names = [n for n in out.split("\n") if n]
    return max(set(names), key=names.count) if names else "—"

def pr_state(pr):
    m = re.search(r"(\d+)", pr or "")
    if not m or not shutil.which("gh"):
        return None
    r = subprocess.run(["gh", "pr", "view", m.group(1), "--json", "state"], capture_output=True, text=True)
    return json.loads(r.stdout)["state"] if r.returncode == 0 else None

def collect(use_gh=False, cwd=None):
    base = base_ref(cwd)
    wts = {w["branch"]: w for w in worktrees(cwd) if w.get("branch")}
    main = main_worktree(cwd)
    items = []
    for br in feature_branches(cwd):
        kind, slug = kind_of(br), slug_of(br)
        w = wts.get(br)
        wt = w["path"] if w else None
        brief = None if kind == "fix" else read_file(f"context/features/{slug}/brief.md", wt, br, cwd)
        plan_md = read_file(plan_path(kind, slug), wt, br, cwd)
        plan = parse_plan(plan_md)
        prs = pr_state(plan["pr"]) if (use_gh and plan and plan["pr"] and plan["pr"] != "—") else None
        dirty = len([l for l in git("status", "--porcelain", cwd=wt).split("\n") if l]) if wt else 0
        marker = os.path.exists(os.path.join(wt, ".endurance-worker")) if wt else False
        items.append({
            "slug": slug, "kind": kind, "branch": br, "worktree": wt,
            "stage": stage_of(kind, brief, plan, wt, prs),
            "status": plan["status"] if plan else ("brief draft" if brief and "Status:** draft" in brief else ""),
            "steps": f"{plan['steps_done']}/{plan['steps_total']}" if plan else "",
            "open_findings": plan["open_blocking"] if plan else 0,
            "pending_decisions": plan["pending_decisions"] if plan else 0,
            "pr": plan["pr"] if plan else None, "pr_state": prs,
            "ports": plan["ports"] if plan else "",
            "parent": parent_of(br, base, cwd) if parent_of(br, base, cwd) != base else None,
            "owner": owner(br, parent_of(br, base, cwd), cwd), "uncommitted": dirty, "worker_marker": marker,
            "unread_mail": len(mail_messages(slug, unread_only=True, cwd=cwd)),
        })
    orphans = [w["path"] for w in worktrees(cwd)[1:]
               if not w.get("branch") or not w["branch"].startswith(("feat/", "fix/"))]
    return {"base": base, "main_worktree": main, "features": items, "other_worktrees": orphans}

# ---------------------------------------------------------------- stacks

def stacks_path(cwd=None):
    return os.path.join(state_dir(cwd), "stacks.json")

def parent_of(branch, base, cwd=None):
    """The ref a feature's own work is measured against: its parent branch while stacked, else the base."""
    p = stacks_path(cwd)
    parent = (json.load(open(p)) if os.path.exists(p) else {}).get(branch)
    if parent and git_ok("rev-parse", "--verify", "--quiet", f"refs/heads/{parent}", cwd=cwd) \
            and not git_ok("merge-base", "--is-ancestor", parent, base, cwd=cwd) \
            and git_ok("merge-base", "--is-ancestor", parent, branch, cwd=cwd):
        return parent
    return base

# ---------------------------------------------------------------- ports

def registry(cwd=None):
    return os.path.join(state_dir(cwd), "ports.json")

def load_ports(cwd=None):
    p = registry(cwd)
    return json.load(open(p)) if os.path.exists(p) else {}

def assign_ports(slug, cwd=None, app_base=3001, db_base=5433):
    p = registry(cwd)
    with locked(p):
        reg = load_ports(cwd)
        if slug in reg:
            return reg[slug]
        used_app = {v["app"] for v in reg.values()}; used_db = {v["db"] for v in reg.values()}
        app = next(x for x in range(app_base, app_base + 1000) if x not in used_app)
        db = next(x for x in range(db_base, db_base + 1000) if x not in used_db)
        reg[slug] = {"app": app, "db": db}
        json.dump(reg, open(p, "w"), indent=2)
        return reg[slug]

# ---------------------------------------------------------------- mail

def mail_path(cwd=None):
    return os.path.join(state_dir(cwd), "mail.jsonl")

def mail_all(cwd=None):
    p = mail_path(cwd)
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

def mail_messages(slug, unread_only=False, cwd=None):
    msgs = [m for m in mail_all(cwd) if m["to"] in (slug, "all") and m["from"] != slug]
    return [m for m in msgs if slug not in m.get("read_by", [])] if unread_only else msgs

def mail_post(sender, to, kind, text, cwd=None):
    p = mail_path(cwd)
    with locked(p):
        msgs = mail_all(cwd)
        m = {"id": len(msgs) + 1, "at": time.strftime("%Y-%m-%d %H:%M"), "from": sender, "to": to,
             "kind": kind, "text": text, "read_by": []}
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
        return m

def mail_mark_read(slug, ids, cwd=None):
    p = mail_path(cwd)
    with locked(p):
        msgs = mail_all(cwd)
        for m in msgs:
            if m["id"] in ids and slug not in m["read_by"]:
                m["read_by"].append(slug)
        with open(p, "w", encoding="utf-8") as f:
            for m in msgs:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")

# ---------------------------------------------------------------- commands

def cmd_create(a):
    fetch()
    main = main_worktree()
    repo = os.path.basename(main.rstrip("/"))
    branch = f"{'fix' if a.fix else 'feat'}/{a.slug}"
    if git_ok("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"):
        raise SystemExit(f"branch {branch} already exists — recreate its worktree with: git worktree add <path> {branch}")
    path = a.path or os.path.join(os.path.dirname(main.rstrip("/")), f"{repo}.worktrees",
                                  f"fix-{a.slug}" if a.fix else a.slug)
    ref = a.from_ref or base_ref()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    git("worktree", "add", "--quiet", "--no-track", "-b", branch, path, ref)
    ports = assign_ports(a.slug)
    if a.from_ref and a.from_ref.replace("origin/", "").startswith(("feat/", "fix/")):
        sp = stacks_path()
        with locked(sp):
            st = json.load(open(sp)) if os.path.exists(sp) else {}
            st[branch] = a.from_ref.replace("origin/", "")
            json.dump(st, open(sp, "w"), indent=2)
    exclude = os.path.join(common_dir(), "info", "exclude")
    os.makedirs(os.path.dirname(exclude), exist_ok=True)
    if ".endurance-worker" not in (open(exclude).read() if os.path.exists(exclude) else ""):
        open(exclude, "a").write("\n.endurance-worker\n")
    for k, v in {"BRANCH": branch, "WORKTREE": path, "FROM": ref,
                 "APP_PORT": ports["app"], "DB_PORT": ports["db"]}.items():
        print(f"{k}={v}")

def cmd_ports(a):
    if a.action == "release":
        with locked(registry()):
            reg = load_ports(); reg.pop(a.slug, None)
            json.dump(reg, open(registry(), "w"), indent=2)
    for s, v in load_ports().items():
        print(f"{s}\tapp {v['app']}\tdb {v['db']}")

def cmd_stale(a):
    stale, files = is_stale(os.path.abspath(a.worktree), a.head)
    print("stale" if stale else "fresh")
    for f in files: print("  " + f)
    sys.exit(1 if stale else 0)

def cmd_board(a):
    data = collect(use_gh=a.gh)
    if a.json:
        print(json.dumps(data, indent=2, ensure_ascii=False)); return
    print(f"base: {data['base']}   main worktree: {data['main_worktree']}")
    rows = [("feature", "stage", "steps", "open", "asks", "mail", "owner", "worktree", "PR")]
    for f in data["features"]:
        name = f["slug"] + (" (fix)" if f["kind"] == "fix" else "") + (f" ⇡{slug_of(f['parent'])}" if f.get("parent") else "")
        flags = (" ⚙" if f["worker_marker"] else "") + (f" ✎{f['uncommitted']}" if f["uncommitted"] else "")
        rows.append((name, f["stage"] + flags, f["steps"], str(f["open_findings"] or ""),
                     str(f["pending_decisions"] or ""), str(f["unread_mail"] or ""), f["owner"],
                     os.path.relpath(f["worktree"], data["main_worktree"]) if f["worktree"] else "(no worktree)",
                     (f["pr"] or "") + (f" {f['pr_state']}" if f["pr_state"] else "")))
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip())
    if data["other_worktrees"]:
        print("worktrees without a feature branch: " + ", ".join(data["other_worktrees"]))
    print("⚙ worker marker present · ✎n uncommitted files · ⇡x stacked on x · asks = decisions pending for the user")

def branch_files(br, base, wt=None):
    files = set(f for f in git("diff", "--name-only", f"{base}...{br}").split("\n") if f)
    if wt:
        files |= {l[3:] for l in git("status", "--porcelain", cwd=wt).split("\n")
                  if l and not l[3:].startswith(".endurance-worker")}
    return files

def added_adrs(br, base, adr_dir="context/project/adr"):
    out = git("diff", "--name-only", "--diff-filter=A", f"{base}...{br}", "--", adr_dir, check=False)
    return {os.path.basename(f)[:4]: f for f in out.split("\n") if re.match(r".*/\d{4}-", f)}

def cmd_overlap(a):
    data = collect()
    base = data["base"]
    feats = [f for f in data["features"] if f["stage"] != "shipped"]
    info = {}
    for f in feats:
        plan = parse_plan(read_file(plan_path(f["kind"], f["slug"]), f["worktree"], f["branch"]))
        own_base = parent_of(f["branch"], base)
        info[f["slug"]] = {"actual": branch_files(f["branch"], own_base, f["worktree"]) - {""},
                           "planned": set(plan["planned_files"]) if plan else set(),
                           "adrs": added_adrs(f["branch"], own_base)}
    found = False
    names = list(info)
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            X, Y = info[x], info[y]
            both = sorted((X["actual"] & Y["actual"]) - {""})
            ctx = [p for p in both if p.startswith("context/")]
            code = [p for p in both if not p.startswith("context/")]
            planned = sorted(((X["planned"] | X["actual"]) & (Y["planned"] | Y["actual"]))
                             - set(both) - {""})
            planned = [p for p in planned if not p.startswith("context/") or p.endswith("architecture.md")]
            adr = sorted(set(X["adrs"]) & set(Y["adrs"]))
            if not (code or ctx or planned or adr):
                continue
            found = True
            print(f"{x} ↔ {y}")
            if code: print("  both changed:   " + ", ".join(code))
            if ctx: print("  both changed (context, usually additive): " + ", ".join(ctx))
            if planned: print("  planned overlap: " + ", ".join(planned))
            if adr: print("  same new ADR number: " + ", ".join(f"{n} ({X['adrs'][n]} / {Y['adrs'][n]})" for n in adr))
    if not found:
        print("no overlap between active branches")

def cmd_integrate(a):
    fetch()
    base = base_ref()
    data = collect()
    branches = a.branches or [f["branch"] for f in data["features"] if f["stage"] not in ("shipped",)]
    tmp = tempfile.mkdtemp(prefix="wt-integrate-")
    path = os.path.join(tmp, "integration")
    git("worktree", "add", "--quiet", "--detach", path, base)
    ident = ["-c", "user.name=wt-integrate", "-c", "user.email=wt-integrate@localhost"]
    merged, conflicts = [], []
    try:
        for br in branches:
            r = subprocess.run(["git", *ident, "merge", "--no-ff", "--no-edit", "--quiet", br],
                               cwd=path, capture_output=True, text=True)
            if r.returncode == 0:
                merged.append(br); continue
            files = git("diff", "--name-only", "--diff-filter=U", cwd=path, check=False).split("\n")
            conflicts.append((br, [f for f in files if f]))
            subprocess.run(["git", "merge", "--abort"], cwd=path, capture_output=True)
        print(f"base {base} + merged: {', '.join(merged) or '(none)'}", flush=True)
        for br, files in conflicts:
            print(f"CONFLICT merging {br} on top of the others: {', '.join(files)}")
        test_rc = None
        if a.test and merged:
            print(f"running tests in the integration worktree: {a.test}", flush=True)
            test_rc = subprocess.run(a.test, shell=True, cwd=path).returncode
            print("tests: " + ("PASS" if test_rc == 0 else f"FAIL (exit {test_rc})"))
        if a.keep:
            print(f"kept: {path}")
    finally:
        if not a.keep:
            subprocess.run(["git", "worktree", "remove", "--force", path], capture_output=True)
            shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if conflicts or (test_rc not in (None, 0)) else 0)

def lesson_ids(md):
    return {m.group(1): m.group(0) for m in re.finditer(r"^### (L-\d{3,})\b.*$", md or "", re.M)}

def cmd_renumber(a):
    wt = os.path.abspath(a.worktree)
    fetch(wt)
    base = base_ref(wt)
    adr_dir = "context/project/adr"
    readme = read_file("context/README.md", wt)
    m = re.search(r"ADR location:\s*`([^`]+)`", strip_comments(readme or ""))
    if m: adr_dir = m.group(1).rstrip("/")
    base_adrs = [f for f in git("ls-tree", "--name-only", f"{base}:{adr_dir}", cwd=wt, check=False).split("\n") if f]
    base_nums = {f[:4] for f in base_adrs if re.match(r"\d{4}-", f)}
    here = [f for f in os.listdir(os.path.join(wt, adr_dir))] if os.path.isdir(os.path.join(wt, adr_dir)) else []
    all_nums = base_nums | {f[:4] for f in here if re.match(r"\d{4}-", f)}
    mine = sorted(added_adrs("HEAD", base, adr_dir).values())
    added_files = set(f for f in git("diff", "--name-only", "--diff-filter=A", f"{base}...HEAD", cwd=wt).split("\n") if f)
    touched = set(f for f in git("diff", "--name-only", f"{base}...HEAD", cwd=wt).split("\n") if f)
    plan = []  # (kind, old_id, new_id, old_path, new_path)
    nxt = max([int(n) for n in all_nums] or [0]) + 1
    for path in mine:
        num = os.path.basename(path)[:4]
        if num in base_nums:
            new = f"{nxt:04d}"; nxt += 1
            plan.append(("adr", f"ADR-{num}", f"ADR-{new}", path,
                         os.path.join(os.path.dirname(path), new + os.path.basename(path)[4:])))
    lessons_rel = "context/project/lessons.md"
    here_l = lesson_ids(read_file(lessons_rel, wt))
    base_l = lesson_ids(read_file(lessons_rel, branch=base, cwd=wt))
    counts = {}
    for m2 in re.finditer(r"^### (L-\d{3,})\b", read_file(lessons_rel, wt) or "", re.M):
        counts[m2.group(1)] = counts.get(m2.group(1), 0) + 1
    base_headings = set(base_l.values())
    lnext = max([int(k[2:]) for k in list(here_l) + list(base_l)] or [0]) + 1
    lesson_moves = []
    for m2 in re.finditer(r"^### (L-\d{3,})\b.*$", read_file(lessons_rel, wt) or "", re.M):
        lid, heading = m2.group(1), m2.group(0)
        if lid in base_l and heading not in base_headings:
            new = f"L-{lnext:03d}"; lnext += 1
            lesson_moves.append((lid, new, heading))
            plan.append(("lesson", lid, new, lessons_rel, lessons_rel))
    if not plan:
        print("no collision with " + base); return
    for kind, old, new, op, np_ in plan:
        print(f"{kind}: {old} → {new}" + (f"   ({op} → {np_})" if op != np_ else ""))
    # references
    auto, manual = [], []
    for kind, old, new, op, np_ in plan:
        stem_old = os.path.basename(op)[:-3] if kind == "adr" else None
        for f in sorted(touched | {op}):
            p = os.path.join(wt, f)
            if not os.path.isfile(p) or f == lessons_rel and kind == "lesson":
                continue
            try: txt = open(p, encoding="utf-8").read()
            except UnicodeDecodeError: continue
            for i, line in enumerate(txt.split("\n"), 1):
                hit_id = re.search(rf"\b{re.escape(old)}\b", line)
                hit_file = stem_old and stem_old in line
                if not (hit_id or hit_file): continue
                if f in added_files or f == op or hit_file:
                    auto.append((f, i, kind, old, new, stem_old))
                else:
                    manual.append((f, i, line.strip()))
    if auto:
        print("references rewritten automatically (files this branch added, or links to the renamed file):")
        for f, i, *_ in auto: print(f"  {f}:{i}")
    if manual:
        print("CHECK BY HAND — files this branch modified but didn't create (the id may be the base's):")
        for f, i, line in manual: print(f"  {f}:{i}: {line[:120]}")
    if not a.apply:
        print("(dry run — add --apply to rename files and rewrite the automatic references)")
        return
    for kind, old, new, op, np_ in plan:
        if kind == "adr":
            git("mv", op, np_, cwd=wt)
    by_file = {}
    for f, i, kind, old, new, stem_old in auto:
        by_file.setdefault(f, []).append((i, kind, old, new, stem_old))
    ren = {op: np_ for k, o, n, op, np_ in plan if k == "adr"}
    for f, hits in by_file.items():
        p = os.path.join(wt, ren.get(f, f))
        lines = open(p, encoding="utf-8").read().split("\n")
        for i, kind, old, new, stem_old in hits:
            line = lines[i - 1]
            if stem_old and stem_old in line:
                line = line.replace(stem_old, new[4:] + stem_old[4:])
            line = re.sub(rf"\b{re.escape(old)}\b", new, line)
            lines[i - 1] = line
        open(p, "w", encoding="utf-8").write("\n".join(lines))
    if lesson_moves:
        p = os.path.join(wt, lessons_rel)
        txt = open(p, encoding="utf-8").read()
        for old, new, heading in lesson_moves:
            txt = txt.replace(heading, heading.replace(old, new, 1), 1)
        open(p, "w", encoding="utf-8").write(txt)
    print("applied — review the diff, then commit it on its own (chore(context): renumber …)")

def cmd_mail(a):
    if a.action == "post":
        m = mail_post(a.sender, a.to, a.kind, a.text)
        print(f"posted #{m['id']} to {m['to']}")
    elif a.action == "read":
        msgs = mail_messages(a.slug, unread_only=not a.all)
        for m in msgs:
            print(f"#{m['id']} {m['at']} {m['from']} → {m['to']} [{m['kind']}] {m['text']}")
        if not msgs: print("no new messages")
        if not a.all: mail_mark_read(a.slug, [m["id"] for m in msgs])
    else:
        for m in mail_all():
            print(f"#{m['id']} {m['at']} {m['from']} → {m['to']} [{m['kind']}] read by: {','.join(m['read_by']) or '—'}  {m['text']}")


# ---------------------------------------------------------------- flow (timing)

def events_path(cwd=None):
    return os.path.join(state_dir(cwd), "events.jsonl")

def events(cwd=None):
    p = events_path(cwd)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []

def cmd_event(a):
    p = events_path()
    e = {"t": int(a.at or time.time()), "slug": a.slug, "stage": a.stage, "what": a.what, "note": a.note or ""}
    with locked(p):
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(e['t']))} {a.slug} {a.stage} {a.what}")

def hours(sec):
    return f"{sec/3600:.1f}h" if sec >= 3600 else f"{sec/60:.0f}m"

def flow_of(slug, evs):
    """Per stage: active seconds, waiting-on-user seconds, runs (a stage entered again = rework)."""
    evs = sorted([e for e in evs if e["slug"] == slug], key=lambda e: e["t"])
    if not evs:
        return None
    stages, open_, wait_ = {}, {}, {}
    for e in evs:
        st = stages.setdefault(e["stage"], {"active": 0, "wait": 0, "runs": 0})
        if e["what"] == "start":
            st["runs"] += 1; open_[e["stage"]] = e["t"]
        elif e["what"] == "wait":
            wait_[e["stage"]] = e["t"]
            if e["stage"] in open_: st["active"] += e["t"] - open_.pop(e["stage"])
        elif e["what"] == "resume":
            if e["stage"] in wait_: st["wait"] += e["t"] - wait_.pop(e["stage"])
            open_[e["stage"]] = e["t"]
        elif e["what"] == "end":
            if e["stage"] in open_: st["active"] += e["t"] - open_.pop(e["stage"])
            if e["stage"] in wait_: st["wait"] += e["t"] - wait_.pop(e["stage"])
    first, last = evs[0]["t"], evs[-1]["t"]
    shipped = next((e["t"] for e in evs if e["what"] == "shipped"), None)
    busy = sum(s["active"] + s["wait"] for s in stages.values())
    return {"slug": slug, "start": first, "shipped": shipped,
            "lead": (shipped or last) - first, "in_progress": shipped is None,
            "stages": stages, "idle": max(0, (shipped or last) - first - busy)}

def ci_runs(branch):
    if not shutil.which("gh"):
        return []
    r = subprocess.run(["gh", "run", "list", "--branch", branch, "--limit", "50", "--json",
                        "name,createdAt,updatedAt,conclusion,workflowName"], capture_output=True, text=True)
    if r.returncode != 0:
        return []
    from datetime import datetime
    out = []
    for x in json.loads(r.stdout):
        try:
            d = (datetime.fromisoformat(x["updatedAt"].replace("Z", "+00:00")) -
                 datetime.fromisoformat(x["createdAt"].replace("Z", "+00:00"))).total_seconds()
        except Exception:
            continue
        out.append({"workflow": x.get("workflowName") or x["name"], "secs": d, "ok": x["conclusion"] == "success"})
    return out

def quality_of(slug, kind="feature", cwd=None):
    """Quality counters read from the plan on its branch or the base: review 🔴, verify fails, later fixes."""
    base = base_ref(cwd)
    br = f"{'fix' if kind == 'fix' else 'feat'}/{slug}"
    md = None
    for ref in (br, base):
        md = read_file(plan_path(kind, slug), branch=ref, cwd=cwd)
        if md: break
    txt = strip_comments(md or "")
    rounds = re.findall(r"Last review: round (\d+)", md or "")
    runs = re.findall(r"Run: run (\d+)", md or "")
    later_fixes = 0
    fixes = git("ls-tree", "--name-only", f"{base}:context/fixes", cwd=cwd, check=False).split("\n")
    for f in [f for f in fixes if f.endswith(".md")]:
        rec = read_file(f"context/fixes/{f}", branch=base, cwd=cwd) or ""
        if f"context/features/{slug}/" in rec:
            later_fixes += 1
    return {"review_rounds": int(rounds[-1]) if rounds else 0, "verify_runs": int(runs[-1]) if runs else 0,
            "red_findings": len(re.findall(r"\*\*R\d+-\d+\*\*\s*🔴", txt)),
            "verify_fails": len(re.findall(r"\*\*V\d+-\d+\*\*", txt)),
            "bugs_after_ship": later_fixes}

def cmd_metrics(a):
    evs = events()
    slugs = [a.slug] if a.slug else sorted({e["slug"] for e in evs})
    flows = [f for f in (flow_of(s, evs) for s in slugs) if f]
    if not flows:
        print("no flow events yet — stages log them with: wt.py event <slug> <stage> start|end|wait|resume|shipped")
        return
    order = ["scope", "architect", "build", "review", "verify", "ship", "land", "fix", "sync"]
    for f in flows:
        q = quality_of(f["slug"])
        state = "in progress" if f["in_progress"] else "shipped"
        if a.markdown:
            print(f"- **Lead time:** {hours(f['lead'])} ({state}) · idle between stages: {hours(f['idle'])}")
            print("| Stage | Active | Waiting on the user | Runs |\n|---|---|---|---|")
            for st in sorted(f["stages"], key=lambda s: order.index(s) if s in order else 99):
                v = f["stages"][st]
                print(f"| {st} | {hours(v['active'])} | {hours(v['wait'])} | {v['runs']} |")
            print(f"- **Quality:** review rounds {q['review_rounds']} · 🔴 found {q['red_findings']} · "
                  f"verify fails {q['verify_fails']} · bugs after ship {q['bugs_after_ship']}")
        else:
            print(f"{f['slug']}: lead time {hours(f['lead'])} ({state}), idle {hours(f['idle'])}")
            for st in sorted(f["stages"], key=lambda s: order.index(s) if s in order else 99):
                v = f["stages"][st]
                print(f"  {st:10} active {hours(v['active']):>6}  waiting on user {hours(v['wait']):>6}  runs {v['runs']}")
            print(f"  quality: review rounds {q['review_rounds']}, 🔴 {q['red_findings']}, "
                  f"verify fails {q['verify_fails']}, bugs after ship {q['bugs_after_ship']}")
        if a.gh:
            runs = ci_runs(f"feat/{f['slug']}") or ci_runs(f"fix/{f['slug']}")
            by = {}
            for r in runs: by.setdefault(r["workflow"], []).append(r["secs"])
            for w, ds in by.items():
                ds.sort()
                print(f"  CI {w}: {len(ds)} runs, median {hours(ds[len(ds)//2])}, max {hours(ds[-1])}")
    if a.gh and not a.markdown:
        base = base_name()
        runs = ci_runs(base)
        by = {}
        for r in runs:
            by.setdefault(r["workflow"], []).append(r["secs"])
        if by:
            print(f"\nworkflows on {base} (deploy/release ones are the path to production):")
            for w, ds in sorted(by.items(), key=lambda kv: -sorted(kv[1])[len(kv[1])//2]):
                ds.sort()
                tag = "  ← delivery" if re.search(r"deploy|release|prod|publish", w, re.I) else ""
                print(f"  {w}: {len(ds)} runs, median {hours(ds[len(ds)//2])}, max {hours(ds[-1])}{tag}")
    shipped = [f for f in flows if not f["in_progress"]]
    if len(flows) > 1 and not a.markdown:
        tot = {}
        for f in flows:
            for st, v in f["stages"].items():
                t = tot.setdefault(st, {"active": 0, "wait": 0, "rework": 0})
                t["active"] += v["active"]; t["wait"] += v["wait"]; t["rework"] += max(0, v["runs"] - 1)
        print("\nwhere the time goes (all features):")
        grand = sum(v["active"] + v["wait"] for v in tot.values()) or 1
        for st, v in sorted(tot.items(), key=lambda kv: -(kv[1]["active"] + kv[1]["wait"])):
            share = (v["active"] + v["wait"]) / grand * 100
            print(f"  {st:10} {share:5.1f}%  active {hours(v['active'])}  waiting {hours(v['wait'])}  re-runs {v['rework']}")
        if shipped:
            leads = sorted(f["lead"] for f in shipped)
            print(f"median lead time over {len(shipped)} shipped: {hours(leads[len(leads)//2])}")

def main():
    ap = argparse.ArgumentParser(prog="wt", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("create"); c.add_argument("slug"); c.add_argument("--fix", action="store_true")
    c.add_argument("--from", dest="from_ref"); c.add_argument("--path"); c.set_defaults(fn=cmd_create)
    c = sp.add_parser("ports"); c.add_argument("action", nargs="?", default="list", choices=["list", "release"])
    c.add_argument("slug", nargs="?"); c.set_defaults(fn=cmd_ports)
    c = sp.add_parser("stale"); c.add_argument("worktree"); c.add_argument("head"); c.set_defaults(fn=cmd_stale)
    c = sp.add_parser("board"); c.add_argument("--json", action="store_true"); c.add_argument("--gh", action="store_true")
    c.set_defaults(fn=cmd_board)
    c = sp.add_parser("overlap"); c.set_defaults(fn=cmd_overlap)
    c = sp.add_parser("integrate"); c.add_argument("branches", nargs="*"); c.add_argument("--test")
    c.add_argument("--keep", action="store_true"); c.set_defaults(fn=cmd_integrate)
    c = sp.add_parser("renumber"); c.add_argument("worktree"); c.add_argument("--apply", action="store_true")
    c.set_defaults(fn=cmd_renumber)
    c = sp.add_parser("mail"); msp = c.add_subparsers(dest="action", required=True)
    p = msp.add_parser("post"); p.add_argument("--from", dest="sender", required=True)
    p.add_argument("--to", required=True, help="a slug, or 'all'")
    p.add_argument("--kind", default="info", choices=["info", "heads-up", "request", "answer"])
    p.add_argument("text")
    r = msp.add_parser("read"); r.add_argument("slug"); r.add_argument("--all", action="store_true")
    msp.add_parser("list")
    c.set_defaults(fn=cmd_mail)
    c = sp.add_parser("event"); c.add_argument("slug"); c.add_argument("stage")
    c.add_argument("what", choices=["start", "end", "wait", "resume", "shipped"])
    c.add_argument("--note"); c.add_argument("--at", type=int, help="epoch seconds (tests)"); c.set_defaults(fn=cmd_event)
    c = sp.add_parser("metrics"); c.add_argument("slug", nargs="?"); c.add_argument("--gh", action="store_true")
    c.add_argument("--markdown", action="store_true"); c.set_defaults(fn=cmd_metrics)
    a = ap.parse_args()
    a.fn(a)

if __name__ == "__main__":
    main()
