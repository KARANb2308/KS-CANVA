#!/usr/bin/env python3
"""MAX v8 (Cowork) job state - stdlib only, works on Linux (Cowork VM), macOS and Windows.

Job files live in <project>/.max/<job>/ so they survive a new Cowork session
(the VM home folder does not). `.max/` is added to .git/info/exclude (never committed).

  python3 max_lite.py dir <job> --size S|M|L     -> make the job folder, print dir/base/budget
  python3 max_lite.py diff <base> --job <job> [files...]  -> write review.diff, print its path
  python3 max_lite.py status                     -> open jobs + their last ledger line
  python3 max_lite.py close <job>                -> refuse if a C-id has no proof / any ไม่ผ่าน; else archive
  python3 max_lite.py abandon <job> "<why>"      -> archive an unfinished job with a reason
"""
import datetime, os, re, shutil, subprocess, sys

BUDGET = {"S": 10, "M": 25, "L": 50}


def out(s):
    try:
        sys.stdout.write(s + "\n")
    except UnicodeEncodeError:
        sys.stdout.buffer.write((s + "\n").encode("utf-8"))


def git(args, cwd):
    try:
        r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        return r.stdout.strip() if r.returncode == 0 else ""
    except OSError:
        return ""


def root():
    cwd = os.getcwd()
    top = git(["rev-parse", "--show-toplevel"], cwd)
    return os.path.normpath(top) if top else cwd


def max_dir(r):
    d = os.path.join(r, ".max")
    os.makedirs(d, exist_ok=True)
    gitdir = git(["rev-parse", "--git-dir"], r)
    if gitdir:
        ex = os.path.join(r, gitdir, "info", "exclude") if not os.path.isabs(gitdir) else os.path.join(gitdir, "info", "exclude")
        try:
            os.makedirs(os.path.dirname(ex), exist_ok=True)
            cur = open(ex, encoding="utf-8").read() if os.path.exists(ex) else ""
            if ".max/" not in cur.split():
                with open(ex, "a", encoding="utf-8") as f:
                    f.write(("" if cur.endswith("\n") or not cur else "\n") + ".max/\n")
        except OSError:
            pass
    return d


def read(p):
    try:
        return open(p, encoding="utf-8").read()
    except OSError:
        return ""


def cmd_dir(argv):
    if not argv:
        sys.exit("usage: dir <job> --size S|M|L")
    job, size = argv[0], "M"
    if "--size" in argv:
        size = argv[argv.index("--size") + 1].upper()
    r = root()
    jd = os.path.join(max_dir(r), job)
    os.makedirs(jd, exist_ok=True)
    base = git(["rev-parse", "--short", "HEAD"], r) or "no-git"
    led = os.path.join(jd, "ledger.md")
    if not os.path.exists(led):
        with open(led, "w", encoding="utf-8") as f:
            f.write(f"# MAX {job} — SPEC: {jd}/SPEC.md — BASE={base} — size={size} — "
                    f"start={datetime.datetime.now():%Y-%m-%d %H:%M}\n")
    out(f"dir={jd}\nbase={base}\nbudget={BUDGET.get(size, 25)} main turns ({size})")


def cmd_diff(argv):
    if not argv or "--job" not in argv:
        sys.exit("usage: diff <base> --job <job> [files...]")
    base = argv[0]
    i = argv.index("--job")
    job = argv[i + 1]
    files = [a for k, a in enumerate(argv[1:], 1) if k not in (i, i + 1)]
    r = root()
    jd = os.path.join(max_dir(r), job)
    os.makedirs(jd, exist_ok=True)
    args = ["diff", base, "--"] + (files or ["."]) + [":(exclude).max"]
    body = git(args, r)
    untracked = git(["ls-files", "--others", "--exclude-standard", "--"] + (files or ["."]), r)
    for p in [u for u in untracked.splitlines() if u and not u.startswith(".max/")]:
        body += f"\n\n=== NEW FILE {p} ===\n" + read(os.path.join(r, p))
    p = os.path.join(jd, "review.diff")
    with open(p, "w", encoding="utf-8") as f:
        f.write(body + "\n")
    out(f"review={p}\nlines={body.count(chr(10)) + 1}")


def open_jobs(md):
    return sorted(d for d in os.listdir(md)
                  if os.path.isdir(os.path.join(md, d)) and d != "closed")


def cmd_status(argv):
    md = max_dir(root())
    jobs = open_jobs(md)
    if not jobs:
        out("ไม่มีงาน MAX ค้าง")
    for j in jobs:
        lines = [l for l in read(os.path.join(md, j, "ledger.md")).splitlines() if l.strip()]
        out(f"ค้าง [{j}]: {lines[-1] if lines else '(ledger ว่าง)'}")


def archive(md, job, line):
    with open(os.path.join(md, "history.md"), "a", encoding="utf-8") as f:
        f.write(f"- {datetime.datetime.now():%Y-%m-%d %H:%M} {job}: {line}\n")
    dest = os.path.join(md, "closed", f"{job}-{datetime.datetime.now():%Y%m%d%H%M}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.move(os.path.join(md, job), dest)
    out(f"archived={dest}")


def cmd_close(argv):
    if not argv:
        sys.exit("usage: close <job>")
    job = argv[0]
    md = max_dir(root())
    jd = os.path.join(md, job)
    if not os.path.isdir(jd):
        sys.exit(f"no job folder {jd}")
    spec, proof = read(os.path.join(jd, "SPEC.md")), read(os.path.join(jd, "proof.md"))
    cids = sorted(set(re.findall(r"\bC(\d+)\b", spec)), key=int)
    missing, failed, unchecked = [], [], []
    for c in cids:
        rows = [l for l in proof.splitlines() if re.search(rf"\bC{c}\b", l)]
        if not rows:
            missing.append(f"C{c}")
        elif any("ไม่ผ่าน" in l for l in rows):
            failed.append(f"C{c}")
        elif any("ยังไม่ได้ตรวจ" in l for l in rows):
            unchecked.append(f"C{c}")
        elif not any("ผ่าน" in l and ("—" in l or "-" in l) for l in rows):
            missing.append(f"C{c}")
    if spec and not cids:
        out("เตือน: SPEC ไม่มี C-id เลย")
    if missing or failed:
        out(f"ปิดไม่ได้: ไม่มีหลักฐาน {' '.join(missing) or '-'} · ไม่ผ่าน {' '.join(failed) or '-'}")
        sys.exit(1)
    out(f"ยังไม่ได้ตรวจจริง: {' '.join(unchecked) or 'ไม่มี'}")
    out(f"MAX: {job} · C-id {len(cids)} · ผ่าน {len(cids) - len(unchecked)}")
    archive(md, job, f"ปิด · C {len(cids)} · ยังไม่ได้ตรวจ {len(unchecked)}")


def cmd_abandon(argv):
    if len(argv) < 2:
        sys.exit('usage: abandon <job> "<why>"')
    md = max_dir(root())
    if not os.path.isdir(os.path.join(md, argv[0])):
        sys.exit("no such job")
    archive(md, argv[0], "ทิ้ง: " + " ".join(argv[1:]))


if __name__ == "__main__":
    cmds = {"dir": cmd_dir, "diff": cmd_diff, "status": cmd_status, "close": cmd_close, "abandon": cmd_abandon}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        out(__doc__)
        sys.exit(2)
    cmds[sys.argv[1]](sys.argv[2:])
