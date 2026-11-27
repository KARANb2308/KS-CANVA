#!/usr/bin/env python3
"""MAX v8 (Cowork) job state - stdlib only, works on Linux (Cowork VM), macOS and Windows.

Job files live in <project>/.max/<job>/ so they survive a new Cowork session
(the VM home folder does not). `.max/` is added to .git/info/exclude (never committed).

  python3 max_lite.py dir <job> --size S|M|L|XL  -> make the job folder, print dir/base/budget
  python3 max_lite.py diff <base> --job <job> [files...]  -> write review.diff, print its path
  python3 max_lite.py status                     -> open jobs + their last ledger line
  python3 max_lite.py close <job>                -> refuse if a C-id has no proof / any ไม่ผ่าน; else archive
  python3 max_lite.py abandon <job> "<why>"      -> archive an unfinished job with a reason
  python3 max_lite.py gate <job> <spec|plan|build|review|fix|proof> [--next "<t>"] [--wait "<t>"]
                                                 -> log the stage, update docs/roadmap.md + docs/max-jobs/<id>/
  python3 max_lite.py resume <job>               -> rebuild .max/<job>/ from docs/max-jobs/<id>/ (never overwrites)
  python3 max_lite.py backfill <folder in .max/closed>  -> make a record for an old closed job
  python3 max_lite.py todo next "<t>" [--p 1|2|3] | wait "<t>" | done "<part>"  -> edit the roadmap lists
"""
import datetime, os, re, shutil, subprocess, sys

BUDGET = {"S": 10, "M": 25, "L": 50, "XL": 70}


def out(s):
    try:
        sys.stdout.write(s + "\n")
    except UnicodeEncodeError:
        sys.stdout.buffer.write((s + "\n").encode("utf-8"))


def git(args, cwd):
    try:
        r = subprocess.run(["git", "-c", "core.quotePath=false"] + args, cwd=cwd, capture_output=True, text=True,
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
        raw = open(p, "rb").read()
    except OSError:
        return ""
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", "replace").replace("\r\n", "\n")
    return raw.decode("utf-8-sig", "replace").replace("\r\n", "\n")


# ---------- roadmap (docs/roadmap.md) + job record (docs/max-jobs/<id>/) ----------
RM_SECS = ["กำลังทำ", "ถัดไป", "รอผู้ใช้", "เสร็จล่าสุด"]
RM_HEAD = ["# แผนที่งาน", '<!-- MAX เขียนไฟล์นี้ผ่าน max_lite.py · แก้มือได้ที่ "ถัดไป" และ "รอผู้ใช้" -->']
RM_CAP = {"ถัดไป": 20, "รอผู้ใช้": 10}
RM_DONE_KEEP = 10
STAGES = {"spec": ("SPEC", "เขียน SPEC"), "plan": ("รออนุมัติแผน", "รอผู้ใช้พิมพ์ ลุย"),
          "build": ("สร้าง", "รอ coder"), "review": ("รีวิว+ตรวจ", "รอ reviewer + verifier"),
          "fix": ("แก้ตามรีวิว", "รอ coder แก้"), "proof": ("รอปิด", "close")}
WHITELIST = ["SPEC.md", "ledger.md", "proof.md", "preflight.md"]
MAX_FILE = 300000
CUT = "[ตัดออก]"
GATTR = "docs/roadmap.md merge=union"
EXCL = [":(exclude).max", ":(exclude)docs/roadmap.md", ":(exclude)docs/max-jobs"]


def check_job_name(job):
    if (not job or "/" in job or "\\" in job or ".." in job or job.startswith(".")
            or re.search(r"[\s\[\]:*?\"<>|]", job)):
        out(f"ชื่องานใช้ไม่ได้: {job!r} (ห้ามมี / \\ .. ช่องว่าง [ ] : * ? \" < > | หรือขึ้นต้นด้วย .)"
            " ถ้าเป็นโฟลเดอร์งานเก่าใน .max/ ให้เปลี่ยนชื่อโฟลเดอร์ก่อน")
        sys.exit(1)


def atomic_write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def append_line(path, text):
    cur = read(path)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(("" if cur.endswith("\n") or not cur else "\n") + text + "\n")


def one_line(t, limit=200):
    t = re.sub(r"\s+", " ", str(t)).strip()
    return t[:limit] + "…" if len(t) > limit else t


def rm_path(r):
    return os.path.join(r, "docs", "roadmap.md")


def roadmap_load(r):
    head, sec, extra, cur = [], {k: [] for k in RM_SECS}, {}, None
    for l in read(rm_path(r)).splitlines():
        if re.match(r"^(<{7}|={7}|>{7}|\|{7})", l):
            continue
        l = l.rstrip()
        m = re.match(r"^##\s+(?!#)(.*)$", l)
        if m:
            name = m.group(1).strip()
            cur = sec[name] if name in sec else extra.setdefault(name, [])
            continue
        if l.strip():
            (head if cur is None else cur).append(l)
    return {"head": head, "sec": sec, "extra": extra}


def _uniq(lines):
    seen, res = set(), []
    for l in lines:
        if l not in seen:
            seen.add(l)
            res.append(l)
    return res


def _rm_norm(r, data):
    sec = {k: list(data["sec"].get(k, [])) for k in RM_SECS}
    head, seen_h = [], set()
    for l in data["head"]:  # only our own heading lines are de-duplicated (add/add merge)
        if l in RM_HEAD and l in seen_h:
            continue
        seen_h.add(l)
        head.append(l)
    if "# แผนที่งาน" not in head:
        head = RM_HEAD + [l for l in head if l not in RM_HEAD]
    done_re = re.compile(r"^- (\d{4}-\d\d-\d\d) \[([^\]]+)\] ")
    seen, rec, rest = set(), [], []
    for l in sec["เสร็จล่าสุด"]:
        m = done_re.match(l)
        if not m:
            if l not in rest:
                rest.append(l)
            continue
        i = re.search(r"docs/max-jobs/([^/\s]+)/?\s*$", l)
        key = (m.group(2), i.group(1) if i else l)
        if key not in seen:
            seen.add(key)
            rec.append((m.group(1), l))
    done_ids = {(done_re.match(l).group(2), (re.search(r"docs/max-jobs/([^/\s]+)/?\s*$", l) or [0, None])[1])
                for _, l in rec}
    rec = sorted(rec, key=lambda x: x[0], reverse=True)[:RM_DONE_KEEP]
    sec["เสร็จล่าสุด"] = [l for _, l in rec] + rest
    act, order, rest = {}, [], []
    for l in sec["กำลังทำ"]:
        m = re.match(r"^- \[([^\]]+)\]", l)
        if not m:
            if l not in rest:
                rest.append(l)
            continue
        t = re.search(r"(\d{4}-\d\d-\d\d \d\d:\d\d)\s*$", l)
        t = t.group(1) if t else ""
        k = m.group(1)
        if k not in act:
            order.append(k)
            act[k] = (t, l)
        elif t >= act[k][0]:
            act[k] = (t, l)
    sec["กำลังทำ"] = [act[k][1] for k in order if (k, _active_id(r, k)) not in done_ids] + rest
    nxt = _uniq(sec["ถัดไป"])
    pri = [l for l in nxt if re.match(r"^- \(P[123]\)", l)]
    sec["ถัดไป"] = sorted(pri, key=lambda l: l[4]) + [l for l in nxt if l not in pri]
    sec["รอผู้ใช้"] = _uniq(sec["รอผู้ใช้"])
    return head, sec, {k: list(v) for k, v in data["extra"].items()}


def _active_id(r, job):
    jd = os.path.join(r, ".max", job)
    return record_id(jd, job) if os.path.isfile(os.path.join(jd, "ledger.md")) else None


def ensure_gitattr(r):
    p = os.path.join(r, ".gitattributes")
    try:
        raw = open(p, "rb").read() if os.path.exists(p) else b""
        if GATTR in raw.decode("utf-8", "replace").split():
            return
        eol = b"\r\n" if b"\r\n" in raw else b"\n"
        with open(p, "ab") as f:
            f.write((b"" if raw.endswith(b"\n") or not raw else eol) + GATTR.encode() + eol)
    except OSError:
        pass


def roadmap_save(r, data):
    head, sec, extra = _rm_norm(r, data)
    lines = list(head)
    for k in RM_SECS:
        lines += ["", "## " + k] + sec[k]
    for k, v in extra.items():
        lines += ["", "## " + k] + v
    new = not os.path.exists(rm_path(r))
    atomic_write(rm_path(r), "\n".join(lines) + "\n")
    if new:
        ensure_gitattr(r)


def ledger_head(jd):
    led = read(os.path.join(jd, "ledger.md")).splitlines()
    return led[0] if led else ""


def record_id(jd, job):
    h = ledger_head(jd)
    m = re.search(r"record=(\S+)", h)
    if m and re.match(r"^\d{4}-\d\d-\d\d-[^/\\\s]+$", m.group(1)) and ".." not in m.group(1):
        return m.group(1)
    m = re.search(r"start=(\d{4}-\d\d-\d\d)", h)
    return f"{m.group(1) if m else datetime.date.today().isoformat()}-{job}"


def unique_id(r, job, date):
    rid, n = f"{date}-{job}", 1
    while True:
        st = read(os.path.join(r, "docs", "max-jobs", rid, "record.md"))
        if not re.search(r"^สถานะ: (ปิด|ทิ้ง)", st, re.M):
            return rid
        n += 1
        rid = f"{date}-{job}-{n}"


def active_line(job, size, stage, nxt, wait, ts):
    f = lambda t: one_line(str(t or "-").replace("·", "-")) or "-"
    return f"- [{job}] {size} · ด่าน: {f(stage)} · ถัดไป: {f(nxt)} · ติด: {f(wait)} · {ts}"


def set_active(data, job, line):
    keep = [l for l in data["sec"]["กำลังทำ"] if not l.startswith(f"- [{job}] ")]
    data["sec"]["กำลังทำ"] = keep + [line]


def find_active(data, job):
    for l in data["sec"]["กำลังทำ"]:
        if l.startswith(f"- [{job}] "):
            return l
    return None


def cmd_todo(argv):
    sub = argv[0] if argv else ""
    if sub not in ("next", "wait", "done") or len(argv) < 2:
        sys.exit('usage: todo next "<t>" [--p 1|2|3] | wait "<t>" | done "<part>"')
    r = root()
    p = 2
    rest = argv[1:]
    if "--p" in rest:
        i = rest.index("--p")
        if i + 1 >= len(rest) or rest[i + 1] not in ("1", "2", "3"):
            out("--p ต้องเป็น 1, 2 หรือ 3")
            sys.exit(1)
        p = int(rest[i + 1])
        rest = rest[:i] + rest[i + 2:]
    text = one_line(clean(" ".join(rest), r)[0])
    if not text:
        sys.exit("ข้อความว่าง")
    if sub == "done":
        if not os.path.exists(rm_path(r)):
            out("ไม่พบ: ยังไม่มีแผนที่งาน")
            sys.exit(1)
        data = roadmap_load(r)
        hits = [(k, l) for k in ("ถัดไป", "รอผู้ใช้") for l in data["sec"][k] if text in l]
        if not hits:
            out(f"ไม่พบ: {text}")
            sys.exit(1)
        if len(hits) > 1:
            out("ตรงหลายบรรทัด:\n" + "\n".join(l for _, l in hits))
            sys.exit(1)
        k, l = hits[0]
        data["sec"][k].remove(l)
        roadmap_save(r, data)
        out(f"ลบ 1: {l}")
        return
    data = roadmap_load(r)
    key = "ถัดไป" if sub == "next" else "รอผู้ใช้"
    line = f"- (P{p}) {text}" if sub == "next" else f"- {text} ({datetime.date.today().isoformat()})"
    if line not in data["sec"][key]:
        n = len([l for l in data["sec"][key] if l.startswith("- ")])
        if n >= RM_CAP[key]:
            out(f"เต็ม {RM_CAP[key]}: ลบข้อเก่าด้วย todo done ก่อน")
            sys.exit(1)
        data["sec"][key].append(line)
    roadmap_save(r, data)
    out(f"เพิ่ม: {line}")


def scan_proof(spec, proof):
    cid_re = r"(?<![A-Za-z0-9_#])C(\d+)(?![0-9A-Za-z_])"
    row_re = re.compile(r"^\s*(?:-\s+)?C(\d+)\s*:?\s*(ไม่ผ่าน|ยังไม่ได้ตรวจ|ผ่าน)\s*(?:[—-]\s*(.*))?$")
    prow = [m for m in (row_re.match(l) for l in proof.splitlines()) if m]
    cids = sorted(set(re.findall(cid_re, spec)), key=int)
    missing, failed, unchecked, last = [], [], [], {}
    for c in cids:
        rows = [m for m in prow if m.group(1) == c]
        if not rows:
            missing.append(f"C{c}")
            continue
        m = rows[-1]  # last proof row decides; only the verdict right after the leading C-id counts
        last[c] = m.group(0).strip()
        if m.group(2) == "ไม่ผ่าน":
            failed.append(f"C{c}")
        elif m.group(2) == "ยังไม่ได้ตรวจ":
            unchecked.append(f"C{c}")
        elif len((m.group(3) or "").strip()) < 8:
            missing.append(f"C{c}")
    return cids, missing, failed, unchecked, last


_SECRET_AUTH = re.compile(r"(?i)(?<![A-Za-z0-9])([A-Za-z0-9_-]*authorization[\"']?\s*[=:]\s*[\"']?)([^\r\n]{6,})")
_SECRET_KV = re.compile(r"(?i)(?<![A-Za-z0-9])([A-Za-z0-9_-]*(?:password|passwd|secret|token|api[_-]?key|"
                        r"ks_session))([\"']?\s*[=:]\s*[\"']?)([^\s\"']{6,})")
_SECRET_URL = re.compile(r"(://[^/\s:@]+:)([^/\s@]{3,})(@)")
_SECRET_TH = re.compile(r"(รหัสผ่าน\s*[=:]\s*)(\S{6,})")
_SECRET_TOK = [re.compile(x) for x in (
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)",
    r"sk-[A-Za-z0-9_-]{20,}", r"gh[pousr]_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
    r"AKIA[0-9A-Z]{16}", r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}", r"Bearer\s+[A-Za-z0-9._~+/-]{20,}")]
_SECRET_TOK[0] = re.compile(_SECRET_TOK[0].pattern, re.S)


def clean(text, r):
    n = [0]

    def cut(m, vg):  # replace only the value group vg; skip if it was already cut
        if m.group(vg) == CUT:
            return m.group(0)
        n[0] += 1
        return m.group(0)[:m.start(vg) - m.start(0)] + CUT + m.group(0)[m.end(vg) - m.start(0):]

    for pat in _SECRET_TOK:
        text = pat.sub(lambda m: (n.__setitem__(0, n[0] + 1) or CUT), text)
    text = _SECRET_AUTH.sub(lambda m: cut(m, 2), text)
    text = _SECRET_URL.sub(lambda m: cut(m, 2), text)
    text = _SECRET_KV.sub(lambda m: cut(m, 3), text)
    text = _SECRET_TH.sub(lambda m: cut(m, 2), text)
    for base, repl in ((r, "."), (os.path.expanduser("~"), "~")):
        fwd = base.replace("\\", "/")
        if len(fwd) > 1 and fwd != "~":
            for form in (fwd.replace("/", "\\\\"), fwd.replace("/", "\\"), fwd):
                flags = re.I if re.match(r"^[A-Za-z]:", form) else 0
                text = re.sub(r"(?<![A-Za-z0-9_.~-])" + re.escape(form) + r"(?![A-Za-z0-9_-]|\.[A-Za-z0-9])",
                              repl, text, flags=flags)
    return text, n[0]


def ensure_record(r, jd, job):
    """Pin a valid record= in the ledger head; a head without one (v8.3) must not reuse a closed record's id."""
    rid = record_id(jd, job)
    if re.search(r"record=" + re.escape(rid) + r"(\s|$)", ledger_head(jd)):
        return rid
    rid = unique_id(r, job, rid[:10])
    led = os.path.join(jd, "ledger.md")
    lines = read(led).split("\n")
    h = lines[0] if lines else ""
    lines[0] = re.sub(r"record=\S+", f"record={rid}", h) if "record=" in h else f"{h} — record={rid}"
    atomic_write(led, "\n".join(lines))
    return rid


def sync_record(r, jd, job, status, extra=None, rid=None):
    extra = extra or {}
    rid = rid or ensure_record(r, jd, job)
    dest = os.path.join(r, "docs", "max-jobs", rid)
    n_cut = 0
    for name in WHITELIST:
        src = os.path.join(jd, name)
        if not os.path.isfile(src) or os.path.islink(src):
            continue
        txt = read(src)
        if "\x00" in txt:
            out(f"ข้าม {name}: ไม่ใช่ UTF-8")
            continue
        txt, n = clean(txt, r)
        n_cut += n
        raw = txt.encode("utf-8")
        if len(raw) > MAX_FILE:
            txt = raw[:MAX_FILE].decode("utf-8", "ignore") + "\n[ตัดท้าย: ไฟล์ยาวเกิน]\n"
        atomic_write(os.path.join(dest, name), txt)
    head = ledger_head(jd)
    g = lambda k: (re.search(k + r"=(\S+(?: \d\d:\d\d)?)", head) or [None, ""])[1]
    cids, _, _, unchecked, _ = scan_proof(read(os.path.join(jd, "SPEC.md")), read(os.path.join(jd, "proof.md")))
    over = len([l for l in read(os.path.join(jd, "ledger.md")).splitlines() if l.strip().startswith("เกินเพดาน:")])
    old = read(os.path.join(dest, "record.md")).splitlines()
    lines = [f"# แฟ้มงาน {job}", f"งาน: {job}", f"ขนาด: {g('size')}", f"สถานะ: {status}", f"เริ่ม: {g('start')}"]
    if extra.get("ปิด"):
        lines.append(f"ปิด: {extra['ปิด']}")
    lines += [f"BASE: {g('BASE')}", f"C-id: {len(cids)}",
              f"ยังไม่ได้ตรวจ: {len(unchecked)}" + (f" ({' '.join(unchecked)})" if unchecked else ""),
              f"เกินเพดาน: {over}"]
    if extra.get("turn") is not None:
        lines.append(f"turn: {extra['turn']}")
    lines.append(f"ตัดออก: {n_cut}")
    if extra.get("ไฟล์") is not None:
        lines.append(f"ไฟล์: {extra['ไฟล์']}")
    lines += [l for l in old if l.startswith("ตรวจซ้ำ:")]
    atomic_write(os.path.join(dest, "record.md"), "\n".join(lines) + "\n")
    return rid, n_cut


def plan_section(spec):
    lines, level, res = spec.splitlines(), None, []
    for l in lines:
        m = re.match(r"^(#{1,6})\s+(.*)$", l)
        if level is None:
            if m and re.match(r"^แผน\s*(\(|$)", m.group(2)):
                level = len(m.group(1))
        elif m and len(m.group(1)) <= level:
            break
        elif level is not None:
            res.append(l)
    if level is None:
        return None
    return "\n".join(res).strip("\n")


def cmd_gate(argv):
    if len(argv) < 2:
        sys.exit('usage: gate <job> <spec|plan|build|review|fix|proof> [--next "<t>"] [--wait "<t>"]')
    job, st = argv[0], argv[1]
    check_job_name(job)
    opt = {}
    rest = argv[2:]
    for i, a in enumerate(rest):
        if a in ("--next", "--wait"):
            if i + 1 >= len(rest):
                sys.exit(f"{a} ต้องมีข้อความ")
            opt[a] = rest[i + 1]
    if st not in STAGES:
        out("ด่านที่ใช้ได้: " + " ".join(STAGES))
        sys.exit(1)
    r = root()
    jd = os.path.join(r, ".max", job)
    if not os.path.isfile(os.path.join(jd, "ledger.md")):
        out(f"ไม่มีงาน {job} (รัน dir ก่อน)")
        sys.exit(1)
    spec = read(os.path.join(jd, "SPEC.md"))
    if st != "spec" and not os.path.isfile(os.path.join(jd, "SPEC.md")):
        out("ยังไม่มี SPEC")
        sys.exit(1)
    plan = None
    if st == "plan":
        plan = plan_section(spec)
        if plan is None:
            out("ไม่มีหัวข้อ แผน ใน SPEC")
            sys.exit(1)
    label, nxt = STAGES[st]
    nxt = clean(opt.get("--next", nxt), r)[0]
    wait = clean(opt["--wait"], r)[0] if "--wait" in opt else ("ผู้ใช้ (อนุมัติแผน)" if st == "plan" else "-")
    now = datetime.datetime.now()
    append_line(os.path.join(jd, "ledger.md"), f"ด่าน: {label} — {now:%Y-%m-%d %H:%M}")
    size = (re.search(r"size=(\w+)", ledger_head(jd)) or [None, "M"])[1]
    n_cut = 0
    if plan is not None:
        out(plan)
    out(f"ด่าน: [{job}] {label} → ถัดไป: {one_line(nxt) or '-'}")
    if size != "S":
        data = roadmap_load(r)
        tail = f" → docs/max-jobs/{record_id(jd, job)}/"  # job continues after a half-way close: undo its done line
        data["sec"]["เสร็จล่าสุด"] = [l for l in data["sec"]["เสร็จล่าสุด"]
                                   if not (f" [{job}] " in l and l.rstrip().endswith(tail))]
        set_active(data, job, active_line(job, size, label, nxt, wait, f"{now:%Y-%m-%d %H:%M}"))
        roadmap_save(r, data)
        _, n_cut = sync_record(r, jd, job, "กำลังทำ")
    if n_cut:
        out(f"ตัดออก: {n_cut}")


def cmd_dir(argv):
    if not argv:
        sys.exit("usage: dir <job> --size S|M|L|XL")
    job, size = argv[0], "M"
    if "--size" in argv:
        size = argv[argv.index("--size") + 1].upper()
    check_job_name(job)
    r = root()
    jd = os.path.join(max_dir(r), job)
    os.makedirs(jd, exist_ok=True)
    base = git(["rev-parse", "--short", "HEAD"], r) or "no-git"
    led = os.path.join(jd, "ledger.md")
    now = datetime.datetime.now()
    if not os.path.exists(led):
        rec = f" — record={unique_id(r, job, now.strftime('%Y-%m-%d'))}" if size != "S" else ""
        with open(led, "w", encoding="utf-8") as f:
            f.write(f"# MAX {job} — SPEC: {jd}/SPEC.md — BASE={base} — size={size} — "
                    f"start={now:%Y-%m-%d %H:%M}{rec}\n")
    out(f"dir={jd}\nbase={base}\nbudget={BUDGET.get(size, 25)} main turns ({size})")
    if size != "S":
        data = roadmap_load(r)
        if find_active(data, job) is None:
            set_active(data, job, active_line(job, size, "SPEC", "เขียน SPEC", "-", f"{now:%Y-%m-%d %H:%M}"))
            roadmap_save(r, data)
        out(f"record=docs/max-jobs/{record_id(jd, job)}")


def cmd_diff(argv):
    if not argv or "--job" not in argv:
        sys.exit("usage: diff <base> --job <job> [files...]")
    base = argv[0]
    i = argv.index("--job")
    job = argv[i + 1]
    check_job_name(job)
    files = [a for k, a in enumerate(argv[1:], 1) if k not in (i, i + 1)]
    r = root()
    jd = os.path.join(max_dir(r), job)
    os.makedirs(jd, exist_ok=True)
    if subprocess.run(["git", "rev-parse", "--verify", "--quiet", base + "^{commit}"], cwd=r,
                      capture_output=True).returncode != 0:
        sys.stderr.write(f"base ใช้ไม่ได้: {base}\n")
        sys.exit(1)
    sel = (files or ["."]) + EXCL + ([":(exclude).gitattributes"] if _attr_only_ours(r, base) else [])
    stat = git(["diff", "--stat", base, "--"] + sel, r)
    body = git(["diff", "-U10", base, "--"] + sel, r)
    thai, cur = [], ""
    for l in body.splitlines():
        if l.startswith("+++ "):
            cur = l[6:] if l.startswith("+++ b/") else l[4:]
        elif l.startswith("+") and re.search("[\u0e00-\u0e7f]", l):
            thai.append(f"{cur}: {l[1:].strip()}")
    untracked = git(["ls-files", "--others", "--exclude-standard", "--"] + (files or ["."]), r)
    new_files = ""
    for p in [u for u in untracked.splitlines()
              if u and not u.startswith((".max/", "docs/max-jobs/")) and u != "docs/roadmap.md"
              and not (u == ".gitattributes" and _attr_only_ours(r, base))]:
        try:
            raw = open(os.path.join(r, p), "rb").read()
        except OSError:
            continue
        try:
            txt = raw.decode("utf-8")
        except UnicodeDecodeError:
            new_files += f"\n=== NEW FILE {p} (binary, {len(raw)} bytes) ===\n"
            continue
        new_files += f"\n=== NEW FILE {p} ===\n{txt}"
        thai += [f"{p}: {l.strip()}" for l in txt.splitlines() if re.search("[\u0e00-\u0e7f]", l)]
    text = ("# stat\n" + stat + "\n\n# ข้อความไทยใหม่:\n" + ("\n".join(thai) if thai else "ไม่มี")
            + "\n\n" + body + "\n" + new_files)
    p = os.path.join(jd, "review.diff")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    out(f"review={p}\nlines={text.count(chr(10)) + 1}")


def open_jobs(md):
    return sorted(d for d in os.listdir(md)
                  if os.path.isdir(os.path.join(md, d)) and d != "closed")


def find_record(r, key):
    """docs/max-jobs/<id> for an exact id, else the newest record of job `key` (None if there is none)."""
    base = os.path.join(r, "docs", "max-jobs")
    if not key or re.search(r"[/\\]|\.\.", key) or not os.path.isdir(base):
        return None
    if re.match(r"^\d{4}-\d\d-\d\d-", key) and os.path.isfile(os.path.join(base, key, "record.md")):
        return os.path.join(base, key)
    pat = re.compile(r"^(\d{4}-\d\d-\d\d)-" + re.escape(key) + r"(?:-(\d+))?$")
    c = []
    for d in os.listdir(base):
        m = pat.match(d)
        if m and os.path.isfile(os.path.join(base, d, "record.md")):
            c.append((m.group(1), int(m.group(2) or 1), d))
    return os.path.join(base, max(c)[2]) if c else None


def rec_field(path, key):
    m = re.search(r"^" + re.escape(key) + r": ?(.*)$", read(os.path.join(path, "record.md")), re.M)
    return m.group(1).strip() if m else ""


def done_line(rec, job, label, date):
    cid = (re.search(r"\d+", rec_field(rec, "C-id")) or [""])[0] or "0"
    unc = (re.search(r"\d+", rec_field(rec, "ยังไม่ได้ตรวจ")) or [""])[0] or "0"
    return f"- {date} [{job}] {label} · C {cid} · ยังไม่ได้ตรวจ {unc} → docs/max-jobs/{os.path.basename(rec)}/"


def cmd_status(argv):
    r = root()
    md = max_dir(r)
    jobs = open_jobs(md)
    if os.path.exists(rm_path(r)):
        data = roadmap_load(r)
        fixed, notes = [], []
        for l in list(data["sec"]["กำลังทำ"]):
            m = re.match(r"^- \[([^\]]+)\]", l)
            if not m or m.group(1) in jobs:
                continue
            job = m.group(1)
            rec = find_record(r, job)
            st = rec_field(rec, "สถานะ") if rec else ""
            if rec and re.match(r"(ปิด|ทิ้ง)", st):
                date = (re.search(r"\d{4}-\d\d-\d\d", rec_field(rec, "ปิด")) or [datetime.date.today().isoformat()])[0]
                label = st if st.startswith("ทิ้ง") else "ปิด"
                data["sec"]["กำลังทำ"].remove(l)
                data["sec"]["เสร็จล่าสุด"].insert(0, done_line(rec, job, label, date))
                fixed.append(job)
            elif rec:
                notes.append(f"กู้ได้ [{job}]: docs/max-jobs/{os.path.basename(rec)}/ → resume {job}")
            else:
                notes.append(f"หาย [{job}]: ไม่มีทั้ง .max และแฟ้ม — ดู docs/worklog.md")
        if fixed:
            roadmap_save(r, data)
            data = roadmap_load(r)
        for l in data["sec"]["กำลังทำ"]:
            out(f"กำลังทำ: {l}")
        for l in data["sec"]["รอผู้ใช้"]:
            out(f"รอผู้ใช้: {l}")
        nxt = data["sec"]["ถัดไป"]
        for k, l in enumerate(nxt[:3]):
            out(f"ถัดไป: {l}" + (f" (+{len(nxt) - 3})" if k == 2 and len(nxt) > 3 else ""))
    else:
        fixed, notes = [], []
    if not jobs:
        out("ไม่มีงาน MAX ค้าง")
    for j in jobs:
        lines = [l for l in read(os.path.join(md, j, "ledger.md")).splitlines() if l.strip()]
        out(f"ค้าง [{j}]: {lines[-1] if lines else '(ledger ว่าง)'}")
    for n in notes:
        out(n)
    for j in fixed:
        out(f"ซ่อมแผนที่: [{j}]")


def cmd_resume(argv):
    if not argv:
        sys.exit("usage: resume <job>")
    job = argv[0]
    check_job_name(job)
    r = root()
    rec = find_record(r, job)
    if not rec:
        out(f"ไม่มีแฟ้มงาน {job}")
        sys.exit(1)
    if re.match(r"(ปิด|ทิ้ง)", rec_field(rec, "สถานะ")):
        out("งานปิดแล้ว — ใช้ recheck")
        sys.exit(1)
    jd = os.path.join(max_dir(r), job)
    os.makedirs(jd, exist_ok=True)
    for name in WHITELIST:
        src, dst = os.path.join(rec, name), os.path.join(jd, name)
        if not os.path.isfile(src):
            continue
        if os.path.exists(dst):
            out(f"มีอยู่แล้ว: {name}")
        else:
            atomic_write(dst, read(src))
    led = os.path.join(jd, "ledger.md")
    append_line(led, f"กู้คืนจากแฟ้ม: {datetime.datetime.now():%Y-%m-%d %H:%M}")
    lines = [l for l in read(led).splitlines() if l.strip()]
    base = (re.search(r"BASE=(\S+)", lines[0]) or [None, ""])[1]
    stage = [l for l in lines if l.startswith("ด่าน:")]
    out(f"dir={jd}\nbase={base}")
    if stage:
        out(stage[-1])
    for l in lines[-5:]:
        out(l)


def cmd_backfill(argv):
    if not argv:
        sys.exit("usage: backfill <folder in .max/closed>")
    name = argv[0]
    check_job_name(name)
    r = root()
    src = os.path.join(r, ".max", "closed", name)
    if not os.path.isdir(src):
        out(f"ไม่มีโฟลเดอร์ .max/closed/{name}")
        sys.exit(1)
    job = re.sub(r"-\d{12}$", "", name)
    head = ledger_head(src)
    date = (re.search(r"start=(\d{4}-\d\d-\d\d)", head) or [None, datetime.date.today().isoformat()])[1]
    stamp = re.search(r"-(\d{4})(\d\d)(\d\d)\d{4}$", name)
    done = f"{stamp.group(1)}-{stamp.group(2)}-{stamp.group(3)}" if stamp else date
    rid, n = f"{date}-{job}", 1
    while True:
        st = read(os.path.join(r, "docs", "max-jobs", rid, "record.md"))
        busy = re.search(r"record=" + re.escape(rid) + r"(\s|$)", ledger_head(os.path.join(r, ".max", job)))
        if "สถานะ: ปิด (ย้อนหลัง)" in st.splitlines() or (not st and not busy):
            break
        n += 1
        rid = f"{date}-{job}-{n}"
    _, n_cut = sync_record(r, src, job, "ปิด (ย้อนหลัง)", rid=rid)
    rec = os.path.join(r, "docs", "max-jobs", rid)
    finish_map(r, job, rid, done_line(rec, job, "ปิด (ย้อนหลัง)", done), drop_active=False)
    out(f"record=docs/max-jobs/{rid}")
    if n_cut:
        out(f"ตัดออก: {n_cut}")


def archive(md, job, line):
    with open(os.path.join(md, "history.md"), "a", encoding="utf-8") as f:
        f.write(f"- {datetime.datetime.now():%Y-%m-%d %H:%M} {job}: {line}\n")
    dest = os.path.join(md, "closed", f"{job}-{datetime.datetime.now():%Y%m%d%H%M}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.move(os.path.join(md, job), dest)
    out(f"archived={dest}")


def fail_after(n):  # test hook only: simulate a crash after close step n
    if os.environ.get("MAX_LITE_FAIL_AFTER") == str(n):
        sys.exit(9)


def _attr_only_ours(r, base):
    cur = [l.strip() for l in read(os.path.join(r, ".gitattributes")).splitlines() if l.strip()]
    old = [l.strip() for l in git(["show", f"{base}:.gitattributes"], r).splitlines() if l.strip()]
    return [l for l in cur if l != GATTR] == old


def job_files(r, base):
    names = git(["diff", "--name-only", base, "--", "."] + EXCL, r)
    new = git(["ls-files", "--others", "--exclude-standard", "--", "."] + EXCL, r)
    seen = []
    for n in names.splitlines() + new.splitlines():
        if n and n not in seen:
            seen.append(n)
    if ".gitattributes" in seen and _attr_only_ours(r, base):
        seen.remove(".gitattributes")
    return seen


def finish_map(r, job, rid, line, drop_active=True):
    """Step 4: drop the job from กำลังทำ, put its new line on top of เสร็จล่าสุด (replacing the same job+id)."""
    data = roadmap_load(r)
    if drop_active:
        data["sec"]["กำลังทำ"] = [l for l in data["sec"]["กำลังทำ"] if not l.startswith(f"- [{job}] ")]
    tail = f" → docs/max-jobs/{rid}/"
    same = lambda l: f" [{job}] " in l and (l.rstrip().endswith(tail) if rid else l == line)
    data["sec"]["เสร็จล่าสุด"] = [line] + [l for l in data["sec"]["เสร็จล่าสุด"] if not same(l)]
    roadmap_save(r, data)


def cmd_close(argv):
    if not argv:
        sys.exit("usage: close <job> [--turns <n>]")
    job = argv[0]
    check_job_name(job)
    turns = None
    if "--turns" in argv:
        i = argv.index("--turns")
        if i + 1 >= len(argv) or not argv[i + 1].isdigit():
            out("--turns ต้องเป็นตัวเลข")
            sys.exit(1)
        turns = int(argv[i + 1])
    r = root()
    md = max_dir(r)
    jd = os.path.join(md, job)
    if not os.path.isdir(jd):
        sys.exit(f"no job folder {jd}")
    spec, proof = read(os.path.join(jd, "SPEC.md")), read(os.path.join(jd, "proof.md"))
    cids, missing, failed, unchecked, last = scan_proof(spec, proof)
    if spec and not cids:
        out("เตือน: SPEC ไม่มี C-id เลย")
    if missing or failed:
        out(f"ปิดไม่ได้: ไม่มีหลักฐาน {' '.join(missing) or 'ไม่มี'} · ไม่ผ่าน {' '.join(failed) or 'ไม่มี'}")
        sys.exit(1)
    out(f"ยังไม่ได้ตรวจจริง: {' '.join(unchecked) or 'ไม่มี'}")
    out(f"MAX: {job} · C-id {len(cids)} · ผ่าน {len(cids) - len(unchecked)}")
    print_draft(jd, job, spec, last)
    over = [l.strip() for l in read(os.path.join(jd, "ledger.md")).splitlines()
            if l.strip().startswith("เกินเพดาน:")]
    head = ledger_head(jd)
    size = (re.search(r"size=(\w+)", head) or [None, "M"])[1]
    msg = (f"ปิด · C {len(cids)} · ยังไม่ได้ตรวจ {len(unchecked)}")
    if size != "S":
        now = datetime.datetime.now()
        sync_record(r, jd, job, "กำลังทำ")                                      # 2
        fail_after(2)
        base = (re.search(r"BASE=(\S+)", head) or [None, ""])[1]
        files = ", ".join(job_files(r, base)) if base and base != "no-git" else ""
        rid, n_cut = sync_record(r, jd, job, "ปิด", {"ปิด": f"{now:%Y-%m-%d %H:%M}", "turn": turns, "ไฟล์": files})  # 3
        fail_after(3)
        finish_map(r, job, rid, f"- {now:%Y-%m-%d} [{job}] {msg} → docs/max-jobs/{rid}/")  # 4
        fail_after(4)
        out(f"record=docs/max-jobs/{rid}")
        if n_cut:
            out(f"ตัดออก: {n_cut}")
    archive(md, job, msg + "".join(" · " + o[:120] for o in over))             # 5


def print_draft(jd, job, spec, last):
    req = "(ไม่พบใน SPEC)"
    for l in spec.splitlines():
        if "คำขอ:" in l:
            req = l.split("คำขอ:", 1)[1].strip() or req
            break
    led = read(os.path.join(jd, "ledger.md")).splitlines()
    m = re.search(r"BASE=(\S+)", led[0]) if led else None
    base = m.group(1) if m else ""
    files = "(ไม่มี base)"
    if base and base != "no-git":
        files = ", ".join(job_files(root(), base)) or "(ไม่มีไฟล์เปลี่ยน)"
    notes = [l.strip() for l in led if l.strip().startswith(("ตัดสิน:", "แจ้งซ้ำ:", "เกินเพดาน:"))]
    out("--- ร่างบันทึก docs/worklog.md (เติม ขั้นตอนที่ได้ผล) ---")
    out(f"## {datetime.datetime.now():%Y-%m-%d} — {job}")
    out(f"- คำขอ: {req}")
    out("- สถานะ: เสร็จ")
    out(f"- ไฟล์: {files}")
    out("- ขั้นตอนที่ได้ผล: (เติม)")
    out(f"- ที่ไม่ได้ผล / ต้องระวัง: {' · '.join(notes) or '(เติม)'}")
    out(f"- ตรวจด้วย: {' · '.join(last[c] for c in sorted(last, key=int))}")


def cmd_abandon(argv):
    if len(argv) < 2:
        sys.exit('usage: abandon <job> "<why>"')
    job = argv[0]
    check_job_name(job)
    r = root()
    md = max_dir(r)
    jd = os.path.join(md, job)
    if not os.path.isdir(jd):
        sys.exit("no such job")
    why = one_line(clean(" ".join(argv[1:]), r)[0])
    size = (re.search(r"size=(\w+)", ledger_head(jd)) or [None, "M"])[1]
    if size != "S":
        now = datetime.datetime.now()
        if (os.path.isfile(os.path.join(jd, "SPEC.md"))
                or os.path.isfile(os.path.join(r, "docs", "max-jobs", record_id(jd, job), "record.md"))):
            rid, _ = sync_record(r, jd, job, f"ทิ้ง: {why}", {"ปิด": f"{now:%Y-%m-%d %H:%M}"})
            finish_map(r, job, rid, f"- {now:%Y-%m-%d} [{job}] ทิ้ง: {why} → docs/max-jobs/{rid}/")
            out(f"record=docs/max-jobs/{rid}")
        else:
            finish_map(r, job, None, f"- {now:%Y-%m-%d} [{job}] ทิ้ง: {why}")
    archive(md, job, "ทิ้ง: " + " ".join(argv[1:]))


if __name__ == "__main__":
    cmds = {"dir": cmd_dir, "diff": cmd_diff, "status": cmd_status, "close": cmd_close, "abandon": cmd_abandon,
            "gate": cmd_gate, "todo": cmd_todo, "resume": cmd_resume, "backfill": cmd_backfill}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        out(__doc__)
        sys.exit(2)
    cmds[sys.argv[1]](sys.argv[2:])
