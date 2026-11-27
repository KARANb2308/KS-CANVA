#!/usr/bin/env python3
"""Tests for max_lite.py and hooks/require-worklog.mjs (stdlib only)."""
import glob, json, os, re, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LITE = os.path.join(HERE, "max_lite.py")
HOOK = os.path.normpath(os.path.join(HERE, "..", "..", "..", "hooks", "require-worklog.mjs"))
sys.path.insert(0, HERE)
import max_lite  # noqa: E402

ENV = dict({k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")},
           PYTHONIOENCODING="utf-8", GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
           GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")


def rd(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def sh(args, cwd, **kw):
    return subprocess.run(args, cwd=cwd, capture_output=True, env=ENV, **kw)


def lite(cwd, *a):
    r = sh([sys.executable, LITE] + list(a), cwd, text=True, encoding="utf-8")
    return r.returncode, r.stdout, r.stderr


class Repo(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="maxlite-")
        self.assertEqual(sh(["git", "init", "-q"], self.d).returncode, 0)
        self.w("a.txt", "one\n")
        sh(["git", "add", "-A"], self.d)
        sh(["git", "commit", "-qm", "init"], self.d)
        self.base = sh(["git", "rev-parse", "--short", "HEAD"], self.d, text=True).stdout.strip()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def w(self, rel, text, mode="w"):
        p = os.path.join(self.d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if mode == "wb":
            with open(p, "wb") as f:
                f.write(text)
        else:
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)

    def job(self, spec, proof=None, ledger="# MAX j — BASE=%s — size=M\n"):
        self.w(".max/j/SPEC.md", spec)
        self.w(".max/j/ledger.md", ledger % self.base if "%s" in ledger else ledger)
        if proof is not None:
            self.w(".max/j/proof.md", proof)


class TestClose(Repo):
    def test_missing_exit1(self):
        self.job("C1 C2\n", "C1 ผ่าน — เทสครบถ้วน\n")
        rc, o, _ = lite(self.d, "close", "j")
        self.assertEqual(rc, 1)
        self.assertIn("C2", o)
        self.assertTrue(os.path.isdir(os.path.join(self.d, ".max", "j")))

    def test_last_line_wins_fail(self):
        self.job("C1\n", "C1 ผ่าน — เทสครบถ้วน\nC1 ไม่ผ่าน — พังแล้ว\n")
        self.assertEqual(lite(self.d, "close", "j")[0], 1)

    def test_last_line_wins_pass(self):
        self.job("C1\n", "C1 ไม่ผ่าน — พังแล้ว\nC1 ผ่าน — แก้แล้วเทสครบ\n")
        self.assertEqual(lite(self.d, "close", "j")[0], 0)

    def test_short_evidence_rejected(self):
        self.job("C1\n", "C1 ผ่าน — ok\n")
        self.assertEqual(lite(self.d, "close", "j")[0], 1)

    def test_no_evidence_rejected(self):
        self.job("C1\n", "C1 ผ่าน\n")
        self.assertEqual(lite(self.d, "close", "j")[0], 1)

    def test_c1_not_matched_by_c10_or_prefix(self):
        # proof for C10 must not satisfy C1; "AC1" is not C1
        self.job("C1 C10\n", "C10 ผ่าน — เทสยาวพอสมควร\nAC1 ผ่าน — เทสยาวพอสมควร\n")
        rc, o, _ = lite(self.d, "close", "j")
        self.assertEqual(rc, 1)
        self.assertIn("C1 ", o + " ")

    def test_unchecked_closes(self):
        self.job("C1\n", "C1 ยังไม่ได้ตรวจ — รอผู้ใช้\n")
        rc, o, _ = lite(self.d, "close", "j")
        self.assertEqual(rc, 0)
        self.assertIn("ยังไม่ได้ตรวจจริง: C1", o)

    def test_hex_color_and_thai_suffix(self):
        self.job("สี #C0392B ใช้\nC2ทำซ้ำ\n", "C2 ผ่าน — เทสครบถ้วนแล้ว\n")
        self.assertEqual(lite(self.d, "close", "j")[0], 0)

    def test_verdict_words_in_text(self):
        self.job("C1\n", "C1 ยังไม่ได้ตรวจ — ยอมรับ: เทสไม่ผ่านบน Windows\n")
        rc, o, _ = lite(self.d, "close", "j")
        self.assertEqual(rc, 0)
        self.assertIn("ยังไม่ได้ตรวจจริง: C1", o)

    def test_no_verdict_token_not_pass(self):
        self.job("C1\n", "C1 หน้า login ใส่รหัสผ่าน — รอผู้ใช้\n")
        self.assertEqual(lite(self.d, "close", "j")[0], 1)

    def test_cross_reference_ignored(self):
        self.job("C1 C3\n", "C1 ไม่ผ่าน — x\n- C3 ผ่าน — shot3.png เหมือน C1\n")
        rc, o, _ = lite(self.d, "close", "j")
        self.assertEqual(rc, 1)
        self.assertIn("ไม่ผ่าน C1", o)

    def test_thai_filename_and_overcap_history(self):
        self.job("คำขอ: x\nC1\n", "C1 ผ่าน — เทสครบถ้วน\n",
                 "# MAX j — BASE=%s — size=M\nเกินเพดาน: ติดบั๊ก\n")
        self.w("คู่มือ.html", "<p>x</p>\n")
        rc, o, _ = lite(self.d, "diff", self.base, "--job", "j")
        p = [l.split("=", 1)[1] for l in o.splitlines() if l.startswith("review=")][0]
        self.assertIn("=== NEW FILE คู่มือ.html ===", rd(p))
        rc, o, _ = lite(self.d, "close", "j")
        self.assertEqual(rc, 0, o)
        self.assertIn("คู่มือ.html", o)
        self.assertIn("เกินเพดาน: ติดบั๊ก", rd(os.path.join(self.d, ".max", "history.md")))

    def test_draft_and_archive(self):
        self.job("คำขอ: ทำของให้ดี\nC1 C2\n",
                 "C1 ผ่าน — ข้อแรกเก่า\nC1 ผ่าน — ข้อแรกล่าสุด\nC2 ผ่าน — ข้อสองครบถ้วน\n",
                 "# MAX j — BASE=%s — size=M\nตัดสิน: ใช้ทาง A\nแจ้งซ้ำ: เรื่อง X\nอื่นๆ\n")
        self.w("a.txt", "two\n")
        self.w("b.txt", "new\n")
        sh(["git", "add", "-A"], self.d)
        sh(["git", "commit", "-qm", "w"], self.d)
        rc, o, _ = lite(self.d, "close", "j")
        self.assertEqual(rc, 0, o)
        self.assertLess(o.index("MAX: j"), o.index("--- ร่างบันทึก"))
        self.assertLess(o.index("--- ร่างบันทึก"), o.index("archived="))
        self.assertIn("- คำขอ: ทำของให้ดี", o)
        self.assertIn("- สถานะ: เสร็จ", o)
        self.assertIn("- ไฟล์: a.txt, b.txt", o)
        self.assertIn("- ขั้นตอนที่ได้ผล: (เติม)", o)
        self.assertIn("ตัดสิน: ใช้ทาง A", o)
        self.assertIn("แจ้งซ้ำ: เรื่อง X", o)
        self.assertNotIn("อื่นๆ", o)
        self.assertIn("ข้อแรกล่าสุด", o)
        self.assertNotIn("ข้อแรกเก่า", o)
        self.assertIn(" · ", o.split("- ตรวจด้วย:")[1])
        self.assertTrue(os.path.isdir(os.path.join(self.d, ".max", "closed")))
        self.assertFalse(os.path.exists(os.path.join(self.d, ".max", "j")))

    def test_draft_without_request_or_base(self):
        self.job("C1\n", "C1 ผ่าน — เทสครบถ้วน\n", "# MAX j — no ledger base\n")
        rc, o, _ = lite(self.d, "close", "j")
        self.assertEqual(rc, 0)
        self.assertIn("(ไม่พบใน SPEC)", o)
        self.assertIn("- ไฟล์: (ไม่มี base)", o)
        self.assertIn("- ที่ไม่ได้ผล / ต้องระวัง: (เติม)", o)

    def test_draft_includes_untracked_new_file(self):
        self.job("C1\n", "C1 ผ่าน — เทสครบถ้วน\n")
        self.w("new.txt", "x\n")
        rc, o, _ = lite(self.d, "close", "j")
        self.assertEqual(rc, 0, o)
        self.assertIn("- ไฟล์: new.txt", o)
        self.assertNotIn(".max/", o.split("- ไฟล์:")[1].split("\n")[0])

    def test_draft_base_but_no_files(self):
        self.job("C1\n", "C1 ผ่าน — เทสครบถ้วน\n")
        rc, o, _ = lite(self.d, "close", "j")
        self.assertEqual(rc, 0, o)
        self.assertIn("- ไฟล์: (ไม่มีไฟล์เปลี่ยน)", o)

    def test_refusal_prints_none_not_dash(self):
        self.job("C1 C2\n", "C1 ผ่าน — เทสครบถ้วน\nC2 ไม่ผ่าน — ตรวจแล้วพัง\n")
        rc, o, _ = lite(self.d, "close", "j")
        self.assertEqual(rc, 1)
        self.assertIn("ไม่มีหลักฐาน ไม่มี", o)
        self.assertNotIn(" - ", o)


class TestDiff(Repo):
    def test_format(self):
        self.w("a.txt", "one\nสวัสดี\nplain\n")
        self.w("new.txt", "ไฟล์ใหม่\n")
        rc, o, _ = lite(self.d, "diff", self.base, "--job", "j")
        self.assertEqual(rc, 0, o)
        p = [l.split("=", 1)[1] for l in o.splitlines() if l.startswith("review=")][0]
        t = rd(p)
        self.assertTrue(t.startswith("# stat"))
        i1, i2, i3, i4 = (t.index(s) for s in ("# stat", "# ข้อความไทยใหม่:", "diff --git", "=== NEW FILE new.txt ==="))
        self.assertTrue(i1 < i2 < i3 < i4)
        self.assertIn("a.txt: สวัสดี", t)
        self.assertNotIn("a.txt: plain", t)

    def test_no_thai(self):
        self.w("a.txt", "one\nplain\n")
        _, o, _ = lite(self.d, "diff", self.base, "--job", "j")
        p = [l.split("=", 1)[1] for l in o.splitlines() if l.startswith("review=")][0]
        t = rd(p)
        self.assertIn("# ข้อความไทยใหม่:\nไม่มี", t)

    def test_context_10(self):
        self.w("a.txt", "".join(f"l{i}\n" for i in range(30)))
        sh(["git", "add", "-A"], self.d)
        sh(["git", "commit", "-qm", "m"], self.d)
        b = sh(["git", "rev-parse", "--short", "HEAD"], self.d, text=True).stdout.strip()
        self.w("a.txt", "".join(f"l{i}\n" for i in range(30)).replace("l15\n", "X\n"))
        _, o, _ = lite(self.d, "diff", b, "--job", "j")
        p = [l.split("=", 1)[1] for l in o.splitlines() if l.startswith("review=")][0]
        t = rd(p)
        self.assertIn("\n l5\n", t)
        self.assertNotIn("\n l4\n", t)

    def test_binary_new_file(self):
        self.w("bin.dat", b"\xff\xfe\x00\x80abc", "wb")
        rc, o, _ = lite(self.d, "diff", self.base, "--job", "j")
        self.assertEqual(rc, 0, o)
        p = [l.split("=", 1)[1] for l in o.splitlines() if l.startswith("review=")][0]
        self.assertIn("=== NEW FILE bin.dat (binary, 7 bytes) ===", rd(p))

    def test_bad_base(self):
        rc, o, e = lite(self.d, "diff", "deadbeefnope", "--job", "j")
        self.assertEqual(rc, 1)
        self.assertTrue(e.strip())


class TestDir(Repo):
    def test_budgets(self):
        for size, n in (("S", 10), ("M", 25), ("L", 50), ("XL", 70)):
            rc, o, _ = lite(self.d, "dir", "j" + size, "--size", size)
            self.assertEqual(rc, 0)
            self.assertIn(f"budget={n} main turns ({size})", o)
            self.assertIn("base=", o)


@unittest.skipUnless(shutil.which("node"), "node missing")
class TestHook(Repo):
    def run_hook(self):
        r = subprocess.run(["node", HOOK], cwd=self.d, input="{}", capture_output=True, text=True,
                           env=dict(ENV, CLAUDE_PROJECT_DIR=self.d))
        return r.returncode, r.stdout

    def setUp(self):
        super().setUp()
        self.w("docs/worklog.md", "log\n")
        sh(["git", "add", "-A"], self.d)
        sh(["git", "commit", "-qm", "log"], self.d)
        self.w("code.py", "x\n")  # uncommitted work

    def test_blocks_baseline(self):
        rc, o = self.run_hook()
        self.assertEqual(rc, 0)
        self.assertIn('"block"', o)

    def test_open_job_silent(self):
        self.w(".max/j/ledger.md", "# x\n")
        rc, o = self.run_hook()
        self.assertEqual((rc, o), (0, ""))

    def test_stale_open_job_blocks(self):
        self.w(".max/j/ledger.md", "# x\n")
        old = __import__("time").time() - 13 * 3600
        os.utime(os.path.join(self.d, ".max", "j", "ledger.md"), (old, old))
        rc, o = self.run_hook()
        self.assertIn('"block"', o)

    def test_closed_job_still_blocks(self):
        self.w(".max/closed/ledger.md", "# x\n")
        self.w(".max/j/other.md", "no ledger\n")
        rc, o = self.run_hook()
        self.assertIn('"block"', o)

    def test_stop_hook_active(self):
        r = subprocess.run(["node", HOOK], cwd=self.d, input='{"stop_hook_active":true}',
                           capture_output=True, text=True, env=dict(ENV, CLAUDE_PROJECT_DIR=self.d))
        self.assertEqual(r.stdout, "")

    def test_no_worklog_silent(self):
        os.remove(os.path.join(self.d, "docs", "worklog.md"))
        self.assertEqual(self.run_hook(), (0, ""))


import datetime as _dt, re as _re

TODAY = lambda: _dt.date.today().isoformat()


def section(text, name):
    out_, on = [], False
    for l in text.splitlines():
        if l.startswith("## "):
            on = l[3:].strip() == name
            continue
        if on and l.strip():
            out_.append(l)
    return out_


def rb(p):
    with open(p, "rb") as f:
        return f.read()


class TestRoadmap(Repo):
    def rmp(self):
        return os.path.join(self.d, "docs", "roadmap.md")

    def rm(self):
        return rd(self.rmp())

    def test_dir_m_creates_map(self):
        rc, o, _ = lite(self.d, "dir", "j1", "--size", "M")
        self.assertEqual(rc, 0)
        t = self.rm()
        heads = [l for l in t.splitlines() if l.startswith("## ")]
        self.assertEqual(heads, ["## กำลังทำ", "## ถัดไป", "## รอผู้ใช้", "## เสร็จล่าสุด"])
        act = section(t, "กำลังทำ")
        self.assertEqual(len(act), 1)
        self.assertTrue(act[0].startswith("- [j1] M · ด่าน: SPEC"), act[0])
        self.assertIn("budget=25", o)
        self.assertIn(f"record=docs/max-jobs/{TODAY()}-j1", o)
        self.assertIn(f"record={TODAY()}-j1", rd(os.path.join(self.d, ".max", "j1", "ledger.md")).splitlines()[0])

    def test_dir_twice_and_s(self):
        lite(self.d, "dir", "j1", "--size", "M")
        lite(self.d, "dir", "j1", "--size", "M")
        self.assertEqual(len(section(self.rm(), "กำลังทำ")), 1)
        d2 = tempfile.mkdtemp(prefix="maxlite-")
        try:
            sh(["git", "init", "-q"], d2)
            rc, o, _ = lite(d2, "dir", "s1", "--size", "S")
            self.assertEqual(rc, 0)
            self.assertNotIn("record=", o)
            self.assertFalse(os.path.exists(os.path.join(d2, "docs")))
        finally:
            shutil.rmtree(d2, ignore_errors=True)

    def test_bad_job_names(self):
        for bad in ("../x", "a/b", ".x", "a\\b"):
            rc, _, _ = lite(self.d, "dir", bad)
            self.assertEqual(rc, 1, bad)
        self.assertFalse(os.path.exists(os.path.join(self.d, "docs")))
        self.assertFalse(os.path.exists(os.path.join(self.d, ".max")))
        self.assertFalse(os.path.exists(os.path.join(self.d, "x")))

    def test_todo_next_wait_done(self):
        lite(self.d, "todo", "next", "แก้ dbp", "--p", "1")
        # add the P2 first in file order by writing P2 before P1 would still sort
        rc, o, _ = lite(self.d, "todo", "next", "อื่น")
        self.assertEqual(rc, 0)
        self.assertIn("เพิ่ม: - (P2) อื่น", o)
        self.assertEqual(section(self.rm(), "ถัดไป"), ["- (P1) แก้ dbp", "- (P2) อื่น"])
        lite(self.d, "todo", "wait", "merge PR")
        self.assertEqual(section(self.rm(), "รอผู้ใช้"), [f"- merge PR ({TODAY()})"])
        rc, o, _ = lite(self.d, "todo", "done", "dbp")
        self.assertEqual(rc, 0)
        self.assertIn("ลบ 1:", o)
        self.assertEqual(section(self.rm(), "ถัดไป"), ["- (P2) อื่น"])

    def test_p_sorts_even_if_added_later(self):
        lite(self.d, "todo", "next", "ช้า", "--p", "3")
        lite(self.d, "todo", "next", "ด่วน", "--p", "1")
        self.assertEqual(section(self.rm(), "ถัดไป"), ["- (P1) ด่วน", "- (P3) ช้า"])

    def test_done_not_found_and_ambiguous(self):
        lite(self.d, "todo", "next", "งาน หนึ่ง")
        lite(self.d, "todo", "next", "งาน สอง")
        before = rb(self.rmp())
        rc, o, _ = lite(self.d, "todo", "done", "ไม่มีแน่")
        self.assertEqual(rc, 1)
        self.assertIn("ไม่พบ", o)
        rc, o, _ = lite(self.d, "todo", "done", "งาน")
        self.assertEqual(rc, 1)
        self.assertIn("ตรงหลายบรรทัด:", o)
        self.assertEqual(rb(self.rmp()), before)

    def test_todo_cap(self):
        for i in range(20):
            self.assertEqual(lite(self.d, "todo", "next", f"ข้อ {i}")[0], 0)
        before = rb(self.rmp())
        rc, o, _ = lite(self.d, "todo", "next", "ข้อ 21")
        self.assertEqual(rc, 1)
        self.assertIn("เต็ม 20", o)
        self.assertEqual(rb(self.rmp()), before)

    def test_todo_failures_do_not_create_file(self):
        rc, o, _ = lite(self.d, "todo", "done", "x")
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(os.path.join(self.d, "docs")))

    def test_hand_written_survives(self):
        lite(self.d, "todo", "next", "a")
        t = self.rm().replace("## ถัดไป\n", "## ถัดไป\nบรรทัดแปลก ไม่ใช่ bullet\n") + "\n## โน้ต\n- x\n"
        with open(self.rmp(), "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
        lite(self.d, "todo", "next", "b")
        t = self.rm()
        self.assertIn("บรรทัดแปลก ไม่ใช่ bullet", section(t, "ถัดไป"))
        self.assertEqual(section(t, "โน้ต"), ["- x"])

    def test_conflict_markers_and_dupes(self):
        lite(self.d, "dir", "j1", "--size", "M")
        t = ("# แผนที่งาน\n## กำลังทำ\n<<<<<<< HEAD\n"
             "- [j1] M · ด่าน: สร้าง · ถัดไป: - · ติด: - · 2026-11-27 10:00\n||||||| base\n=======\n"
             "- [j1] M · ด่าน: รีวิว+ตรวจ · ถัดไป: - · ติด: - · 2026-11-27 11:30\n>>>>>>> other\n"
             "## ถัดไป\n- (P2) ซ้ำ\n- (P2) ซ้ำ\n")
        with open(self.rmp(), "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
        lite(self.d, "todo", "wait", "z")
        t = self.rm()
        for m in ("<<<<<<<", "=======", ">>>>>>>", "|||||||"):
            self.assertNotIn(m, t)
        act = section(t, "กำลังทำ")
        self.assertEqual(len(act), 1)
        self.assertIn("2026-11-27 11:30", act[0])
        self.assertEqual(section(t, "ถัดไป"), ["- (P2) ซ้ำ"])

    def test_todo_text_cleaned(self):
        lite(self.d, "todo", "next", "x APP_PASSWORD=hunter2secret")
        lite(self.d, "todo", "wait", "y DB_PASSWORD=hunter2secret")
        self.assertNotIn("hunter2secret", self.rm())
        self.assertIn("APP_PASSWORD=", self.rm())

    def test_head_and_unknown_not_deduped(self):
        lite(self.d, "todo", "next", "a")
        t = self.rm() + "\n## โน้ต\n- x\n- x\n"
        t = t.replace("# แผนที่งาน\n", "# แผนที่งาน\nบรรทัดหัวซ้ำ\nบรรทัดหัวซ้ำ\n", 1)
        with open(self.rmp(), "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
        lite(self.d, "todo", "next", "b")
        self.assertEqual(section(self.rm(), "โน้ต"), ["- x", "- x"])
        self.assertEqual(self.rm().count("บรรทัดหัวซ้ำ"), 2)

    def test_job_name_rejects_space_and_symbols(self):
        for bad in ("a b", "a[1]", "a]b", "a:b", "a*b", "a?b", 'a"b', "a<b", "a>b", "a|b"):
            self.assertEqual(lite(self.d, "dir", bad)[0], 1, bad)
        self.assertFalse(os.path.exists(os.path.join(self.d, "docs")))

    def test_atomic_write_removes_tmp_on_failure(self):
        p = os.path.join(self.d, "z.txt")
        with self.assertRaises(Exception):
            max_lite.atomic_write(p, b"bytes not str")
        self.assertEqual([f for f in os.listdir(self.d) if f.endswith(".tmp")], [])
        self.assertFalse(os.path.exists(p))
        with open(p + ".tmp", "w") as f:  # another process's tmp must survive
            f.write("other")
        max_lite.atomic_write(p, "mine")
        self.assertEqual(rd(p + ".tmp"), "other")
        self.assertEqual(rd(p), "mine")

    def test_only_roadmap_head_deduped(self):
        lite(self.d, "todo", "next", "a")
        t = self.rm().replace("# แผนที่งาน\n", "# แผนที่งาน\n# แผนที่งาน\nหัวผู้ใช้\nหัวผู้ใช้\n", 1)
        with open(self.rmp(), "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
        lite(self.d, "todo", "next", "b")
        self.assertEqual(self.rm().count("# แผนที่งาน"), 1)
        self.assertEqual(self.rm().count("หัวผู้ใช้"), 2)

    def test_diff_rejects_bad_job(self):
        self.assertEqual(lite(self.d, "diff", self.base, "--job", "a b")[0], 1)
        self.assertFalse(os.path.exists(os.path.join(self.d, ".max", "a b")))

    def test_real_git_merge_union(self):
        lite(self.d, "dir", "j1", "--size", "M")
        sh(["git", "add", "-A"], self.d)
        sh(["git", "commit", "-qm", "map"], self.d)
        main = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], self.d, text=True).stdout.strip()
        sh(["git", "checkout", "-qb", "b1"], self.d)
        lite(self.d, "todo", "next", "จาก b1")
        sh(["git", "commit", "-qam", "b1"], self.d)
        sh(["git", "checkout", "-q", main], self.d)
        sh(["git", "checkout", "-qb", "b2"], self.d)
        lite(self.d, "todo", "next", "จาก b2")
        sh(["git", "commit", "-qam", "b2"], self.d)
        r = sh(["git", "merge", "-q", "--no-edit", "b1"], self.d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lite(self.d, "todo", "wait", "x")
        t = self.rm()
        nxt = section(t, "ถัดไป")
        self.assertIn("- (P2) จาก b1", nxt)
        self.assertIn("- (P2) จาก b2", nxt)
        self.assertEqual(len([l for l in t.splitlines() if l == "## ถัดไป"]), 1)

    def test_gitattributes_append_once(self):
        self.w(".gitattributes", "*.png binary\n")
        lite(self.d, "dir", "j1", "--size", "M")
        lite(self.d, "dir", "j2", "--size", "M")
        ga = rd(os.path.join(self.d, ".gitattributes")).splitlines()
        self.assertIn("*.png binary", ga)
        self.assertEqual(ga.count("docs/roadmap.md merge=union"), 1)

    def test_long_text_one_line_no_cr(self):
        lite(self.d, "todo", "next", "ก" * 100 + "\n" + "ข" * 150)
        nxt = section(self.rm(), "ถัดไป")
        self.assertEqual(len(nxt), 1)
        self.assertEqual(nxt[0], "- (P2) " + "ก" * 100 + " " + "ข" * 99 + "…")
        self.assertNotIn(b"\r", rb(self.rmp()))


class TestRecord(Repo):
    def setUp(self):
        super().setUp()
        lite(self.d, "dir", "j1", "--size", "M")
        self.rec = os.path.join(self.d, "docs", "max-jobs", f"{TODAY()}-j1")

    def rp(self, name):
        return os.path.join(self.rec, name)

    def spec(self, text):
        self.w(".max/j1/SPEC.md", text)

    def test_gate_build(self):
        self.spec("# SPEC\nC1\n")
        rc, o, _ = lite(self.d, "gate", "j1", "build", "--next", "รอ coder G1")
        self.assertEqual(rc, 0)
        self.assertEqual(o.splitlines()[0], "ด่าน: [j1] สร้าง → ถัดไป: รอ coder G1")
        led = rd(os.path.join(self.d, ".max", "j1", "ledger.md")).splitlines()[-1]
        self.assertTrue(led.startswith("ด่าน: สร้าง — "), led)
        act = section(rd(os.path.join(self.d, "docs", "roadmap.md")), "กำลังทำ")
        self.assertEqual(len(act), 1)
        self.assertTrue(act[0].startswith("- [j1] M · ด่าน: สร้าง · ถัดไป: รอ coder G1 · ติด: - · "), act[0])
        for n in ("SPEC.md", "ledger.md", "record.md"):
            self.assertTrue(os.path.isfile(self.rp(n)), n)
        self.assertFalse(os.path.exists(self.rp("proof.md")))
        self.assertIn("สถานะ: กำลังทำ", rd(self.rp("record.md")).splitlines())

    def test_gate_bad_args(self):
        rc, o, _ = lite(self.d, "gate", "j1", "nope")
        self.assertEqual(rc, 1)
        for s in ("spec", "plan", "build", "review", "fix", "proof"):
            self.assertIn(s, o)
        self.assertEqual(lite(self.d, "gate", "nojob", "build")[0], 1)
        self.assertFalse(os.path.exists(os.path.join(self.d, ".max", "nojob")))
        rc, o, _ = lite(self.d, "gate", "j1", "build")
        self.assertEqual(rc, 1)
        self.assertIn("ยังไม่มี SPEC", o)
        self.assertFalse(os.path.exists(self.rec) and os.path.exists(self.rp("record.md")))
        self.assertEqual(lite(self.d, "gate", "j1", "spec")[0], 0)

    def test_gate_plan(self):
        self.spec("# SPEC\n\n## แผน (ภาษาคน)\n- p1\n- p2\n- p3\n\n## 1. เป้าหมาย\nXX\n")
        rc, o, _ = lite(self.d, "gate", "j1", "plan")
        self.assertEqual(rc, 0)
        for x in ("- p1", "- p2", "- p3"):
            self.assertIn(x, o)
        self.assertNotIn("เป้าหมาย", o)
        self.assertNotIn("XX", o)
        act = section(rd(os.path.join(self.d, "docs", "roadmap.md")), "กำลังทำ")[0]
        self.assertIn("ติด: ผู้ใช้ (อนุมัติแผน)", act)
        self.assertIn("ถัดไป: รอผู้ใช้พิมพ์ ลุย", act)

    def test_gate_plan_missing(self):
        self.spec("# SPEC\n\n## แผนที่\n- x\n")
        before = rb(os.path.join(self.d, "docs", "roadmap.md"))
        rc, o, _ = lite(self.d, "gate", "j1", "plan")
        self.assertEqual(rc, 1)
        self.assertIn("ไม่มีหัวข้อ แผน ใน SPEC", o)
        self.assertEqual(rb(os.path.join(self.d, "docs", "roadmap.md")), before)

    def test_clean_secrets(self):
        real = os.path.realpath(self.d)
        txt = ("APP_PASSWORD=hunter2secret\nรหัสผ่าน: abc12345\n" + "ghp_" + "a" * 30 + "\n"
               + "Bearer " + "x" * 26 + f"\npath {real}/.max/j1/SPEC.md\n")
        self.spec(txt)
        rc, o, _ = lite(self.d, "gate", "j1", "build")
        self.assertEqual(rc, 0)
        got = rd(self.rp("SPEC.md"))
        for bad in ("hunter2secret", "abc12345", "a" * 30, "x" * 26, real):
            self.assertNotIn(bad, got)
        self.assertEqual(got.count("[ตัดออก]"), 4)
        self.assertIn("APP_PASSWORD=", got)
        self.assertIn("./.max/j1/SPEC.md", got)
        self.assertIn("ตัดออก: 4", o)
        self.assertIn("ตัดออก: 4", rd(self.rp("record.md")).splitlines())
        self.assertEqual(rd(os.path.join(self.d, ".max", "j1", "SPEC.md")), txt)
        self.assertNotIn(real, rd(self.rp("ledger.md")))

    def test_private_key_block(self):
        self.spec("-----BEGIN RSA PRIVATE KEY-----\nMIIabc\ndef\n-----END RSA PRIVATE KEY-----\nต่อ\n")
        lite(self.d, "gate", "j1", "build")
        got = rd(self.rp("SPEC.md"))
        self.assertNotIn("MIIabc", got)
        self.assertIn("[ตัดออก]", got)
        self.assertIn("ต่อ", got)

    def test_no_over_cut(self):
        txt = "C1 ผ่าน — test_login::test_password_required 3 passed\nคำว่า รหัสผ่าน ในหน้า login\n"
        self.spec(txt)
        o = lite(self.d, "gate", "j1", "build")[1]
        self.assertEqual(rd(self.rp("SPEC.md")), txt)
        self.assertNotIn("ตัดออก:", o)

    def test_whitelist(self):
        self.spec("C1\n")
        for n in ("review.diff", "shot.png", "x.ksproject.json", "j1-G1.md"):
            self.w(f".max/j1/{n}", "data\n")
        lite(self.d, "gate", "j1", "build")
        self.assertEqual(sorted(os.listdir(self.rec)), ["SPEC.md", "ledger.md", "record.md"])

    def test_big_file_truncated(self):
        self.spec(("x" * 99 + "\n") * 4000)
        lite(self.d, "gate", "j1", "build")
        b = rb(self.rp("SPEC.md"))
        self.assertLessEqual(len(b), 300100)
        self.assertTrue(b.decode("utf-8").rstrip().endswith("[ตัดท้าย: ไฟล์ยาวเกิน]"))

    def test_clean_prefixed_and_json_keys(self):
        vals = ["cf12345678", "ss12345678", "pw12345678", "cs12345678", "at12345678", "hunter2secret", "tok123456"]
        self.spec("CLOUDFLARE_API_TOKEN=cf12345678\nSESSION_SECRET=ss12345678\nDB_PASSWORD=pw12345678\n"
                  "client_secret=cs12345678\naccess_token=at12345678\n"
                  '{"password": "hunter2secret"}\n' + "{'token': 'tok123456'}\n" + "max_tokens: 100000\n")
        lite(self.d, "gate", "j1", "build")
        got = rd(self.rp("SPEC.md"))
        for v in vals:
            self.assertNotIn(v, got)
        self.assertIn("max_tokens: 100000", got)
        self.assertIn("CLOUDFLARE_API_TOKEN=", got)

    def test_clean_basic_auth_and_url(self):
        self.spec("Authorization: Basic dXNlcjpwYXNzd29yZA==\nhttps://bob:pass1234@example.com/x\n")
        lite(self.d, "gate", "j1", "build")
        got = rd(self.rp("SPEC.md"))
        self.assertNotIn("dXNlcjpwYXNzd29yZA", got)
        self.assertNotIn("pass1234", got)
        self.assertIn("@example.com/x", got)

    def test_clean_paths_unit(self):
        root_ = "C:\\Users\\bob\\proj"
        txt = ("C:\\\\Users\\\\bob\\\\proj\\\\a.txt | C:\\Users\\bob\\proj\\b.txt | "
               "C:/Users/bob/proj/c.txt | at C:/Users/bob/proj. end | C:/Users/bob/proj.json")
        got = max_lite.clean(txt, root_)[0]
        self.assertEqual(got.count("Users"), 1)  # only the proj.json lookalike stays
        self.assertIn(".\\\\a.txt", got)
        self.assertIn("at .. end", got)
        self.assertIn("C:/Users/bob/proj.json", got)

    def test_clean_home_unit(self):
        old = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
        os.environ["HOME"] = os.environ["USERPROFILE"] = "/home/zed"
        try:
            got = max_lite.clean("see /home/zed/x and /home/zed.", "/srv/proj")[0]
        finally:
            for k, v in old.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.assertEqual(got, "see ~/x and ~.")

    def test_record_id_traversal_ignored(self):
        self.w(".max/j1/ledger.md", "# MAX j1 — BASE=abc — size=M — start=2026-11-27 05:48 — record=../../x\n")
        self.spec("C1\n")
        self.assertEqual(lite(self.d, "gate", "j1", "build")[0], 0)
        self.assertFalse(os.path.exists(os.path.join(self.d, "x")))
        self.assertTrue(os.path.isfile(os.path.join(self.d, "docs", "max-jobs", "2026-11-27-j1", "record.md")))

    def test_record_id_validation_unit(self):
        for bad in ("../../x", "a/b", "2026-11-27-a..b", "x", "2026-01-02-other", "2026-01-02-jj-x"):
            self.w(".max/jj/ledger.md", f"# h — start=2026-01-02 05:00 — record={bad}\n")
            self.assertEqual(max_lite.record_id(os.path.join(self.d, ".max", "jj"), "jj"), "2026-01-02-jj", bad)

    def test_utf16_and_symlink_sources(self):
        self.w(".max/j1/SPEC.md", "C1 ภาษาไทย\n".encode("utf-16"), "wb")
        self.assertEqual(lite(self.d, "gate", "j1", "build")[0], 0)
        self.assertIn("C1 ภาษาไทย", rd(self.rp("SPEC.md")))
        self.assertIn("C-id: 1", rd(self.rp("record.md")).splitlines())
        os.remove(os.path.join(self.d, ".max", "j1", "SPEC.md"))
        self.w("secret-outside.txt", "TOPSECRET\n")
        try:
            os.symlink(os.path.join(self.d, "secret-outside.txt"), os.path.join(self.d, ".max", "j1", "SPEC.md"))
        except (OSError, NotImplementedError):
            self.skipTest("no symlinks")
        shutil.rmtree(self.rec)
        lite(self.d, "gate", "j1", "spec")
        self.assertFalse(os.path.exists(self.rp("SPEC.md")))

    def test_utf16_secrets_cleaned(self):
        real = os.path.realpath(self.d)
        self.w(".max/j1/SPEC.md", f"C1\nAPP_PASSWORD=hunter2secret\n{real}/x\n".encode("utf-16"), "wb")
        rc, o, _ = lite(self.d, "gate", "j1", "build")
        self.assertEqual(rc, 0)
        b = rb(self.rp("SPEC.md"))
        for bad in ("hunter2secret", real):
            self.assertNotIn(bad.encode("utf-8"), b)
            self.assertNotIn(bad.encode("utf-16-le"), b)
        self.assertIn("C-id: 1", rd(self.rp("record.md")).splitlines())

    def test_utf16_without_bom_skipped(self):
        self.w(".max/j1/SPEC.md", "C1\nAPP_PASSWORD=hunter2secret\n".encode("utf-16-le"), "wb")
        rc, o, _ = lite(self.d, "gate", "j1", "build")
        self.assertEqual(rc, 0)
        self.assertIn("ข้าม SPEC.md: ไม่ใช่ UTF-8", o)
        self.assertFalse(os.path.exists(self.rp("SPEC.md")))

    def test_clean_lookbehind_and_authorization(self):
        old = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
        os.environ["HOME"] = os.environ["USERPROFILE"] = "/home/zed"
        try:
            got = max_lite.clean("a/home/zed/x /home/zed/y", "/srv/proj")[0]
            self.assertEqual(got, "a/home/zed/x ~/y")
        finally:
            for k, v in old.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        got = max_lite.clean("Authorization: Bearer abc\nAuthorization: Token abcdef ghi\nok", "/srv/proj")[0]
        self.assertNotIn("abc", got)
        self.assertNotIn("ghi", got)
        self.assertTrue(got.endswith("ok"))

    def test_v83_job_does_not_overwrite_closed_record(self):
        lite(self.d, "dir", "j1", "--size", "M")
        self.w(".max/j1/SPEC.md", "C1\n")
        self.w(".max/j1/proof.md", "C1 ผ่าน — เทสครบถ้วน\n")
        self.assertEqual(lite(self.d, "close", "j1")[0], 0)
        orig = rb(self.rp("record.md"))
        self.w(".max/j1/ledger.md", f"# MAX j1 — SPEC: x — BASE=abc — size=M — start={TODAY()} 05:48\n")
        self.spec("C1 C2\n")
        self.assertEqual(lite(self.d, "gate", "j1", "build")[0], 0)
        self.assertEqual(rb(self.rp("record.md")), orig)
        self.assertEqual(len([l for l in section(rd(os.path.join(self.d, "docs", "roadmap.md")), "เสร็จล่าสุด")
                              if "[j1] ปิด" in l]), 1)
        self.assertTrue(os.path.isfile(os.path.join(self.d, "docs", "max-jobs", f"{TODAY()}-j1-2", "record.md")))
        self.assertIn(f"record={TODAY()}-j1-2", rd(os.path.join(self.d, ".max", "j1", "ledger.md")).splitlines()[0])

    def test_authorization_does_not_cross_lines(self):
        got = max_lite.clean("Authorization:\nkeepme12345 here", "/srv/proj")[0]
        self.assertIn("keepme12345", got)

    def test_twice_equals_once(self):
        self.spec("C1 C2\nAPP_PASSWORD=hunter2secret\n")
        self.w(".max/j1/proof.md", "C1 ผ่าน — เทสครบถ้วน\n")
        lite(self.d, "gate", "j1", "build")
        first = {n: rb(self.rp(n)) for n in os.listdir(self.rec)}
        lite(self.d, "gate", "j1", "build")
        for n, b in first.items():
            if n != "ledger.md":
                self.assertEqual(rb(self.rp(n)), b, n)
        self.assertEqual(sorted(os.listdir(self.rec)), sorted(first))
        rec = rd(self.rp("record.md"))
        self.assertIn("C-id: 2", rec)
        self.assertFalse([n for n in os.listdir(self.rec) if n.endswith(".tmp")])

    def test_v83_head_without_record(self):
        shutil.rmtree(os.path.join(self.d, "docs"))
        self.w(".max/j1/ledger.md", "# MAX j1 — SPEC: x — BASE=abc — size=M — start=2026-11-27 05:48\n")
        self.spec("C1\n")
        rc, _, _ = lite(self.d, "gate", "j1", "build")
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.d, "docs", "max-jobs", "2026-11-27-j1", "record.md")))


class TestCloseRecord(Repo):
    def start(self, job="j1", spec="C1 C2\n", proof="C1 ผ่าน — เทสครบถ้วน\nC2 ยังไม่ได้ตรวจ\n", size="M"):
        lite(self.d, "dir", job, "--size", size)
        self.w(f".max/{job}/SPEC.md", spec)
        if proof is not None:
            self.w(f".max/{job}/proof.md", proof)

    def rmt(self):
        return rd(os.path.join(self.d, "docs", "roadmap.md"))

    def rid(self, job="j1"):
        return f"{TODAY()}-{job}"

    def rec(self, job="j1", name="record.md"):
        return os.path.join(self.d, "docs", "max-jobs", self.rid(job), name)

    def snap(self):
        res = {}
        for dp, _, fs in os.walk(os.path.join(self.d, "docs")):
            for f in fs:
                res[os.path.join(dp, f)] = rb(os.path.join(dp, f))
        return res

    def test_close_ok(self):
        self.start()
        self.w("a.txt", "two\n")
        rc, o, _ = lite(self.d, "close", "j1")
        self.assertEqual(rc, 0, o)
        rec = rd(self.rec()).splitlines()
        for l in ("สถานะ: ปิด", "ขนาด: M", f"BASE: {self.base}", "C-id: 2", "ยังไม่ได้ตรวจ: 1 (C2)"):
            self.assertIn(l, rec)
        files = [l for l in rec if l.startswith("ไฟล์:")][0]
        self.assertIn("a.txt", files)
        self.assertNotIn("docs/", files)
        t = self.rmt()
        self.assertEqual(section(t, "กำลังทำ"), [])
        self.assertEqual(section(t, "เสร็จล่าสุด")[0],
                         f"- {TODAY()} [j1] ปิด · C 2 · ยังไม่ได้ตรวจ 1 → docs/max-jobs/{self.rid()}/")
        self.assertTrue(glob.glob(os.path.join(self.d, ".max", "closed", "j1-*")))
        for s in ("ยังไม่ได้ตรวจจริง:", "MAX: j1", "--- ร่างบันทึก", "archived=", f"record=docs/max-jobs/{self.rid()}"):
            self.assertIn(s, o)

    def test_close_refused_writes_nothing(self):
        self.start(proof="C1 ผ่าน — เทสครบถ้วน\n")
        lite(self.d, "gate", "j1", "build")
        before = self.snap()
        self.assertEqual(lite(self.d, "close", "j1")[0], 1)
        self.assertEqual(self.snap(), before)
        self.assertTrue(os.path.isdir(os.path.join(self.d, ".max", "j1")))

    def test_turns(self):
        self.start()
        lite(self.d, "gate", "j1", "build")
        before = self.snap()
        self.assertEqual(lite(self.d, "close", "j1", "--turns", "x")[0], 1)
        self.assertEqual(self.snap(), before)
        self.assertTrue(os.path.isdir(os.path.join(self.d, ".max", "j1")))
        self.assertEqual(lite(self.d, "close", "j1", "--turns", "23")[0], 0)
        self.assertIn("turn: 23", rd(self.rec()).splitlines())

    def test_eleven_jobs_cap(self):
        for i in range(11):
            self.start(f"j{i}", "C1\n", "C1 ผ่าน — เทสครบถ้วน\n")
            self.assertEqual(lite(self.d, "close", f"j{i}")[0], 0)
        done = section(self.rmt(), "เสร็จล่าสุด")
        self.assertEqual(len(done), 10)
        self.assertIn("[j10]", done[0])
        self.assertFalse([l for l in done if "[j0]" in l])
        self.assertTrue(os.path.isdir(os.path.join(self.d, "docs", "max-jobs", self.rid("j0"))))

    def _fail_then_close(self, n):
        self.start()
        r = subprocess.run([sys.executable, LITE, "close", "j1"], cwd=self.d, capture_output=True, text=True,
                           encoding="utf-8", env=dict(ENV, MAX_LITE_FAIL_AFTER=str(n)))
        self.assertEqual(r.returncode, 9, r.stdout + r.stderr)
        self.assertEqual(lite(self.d, "close", "j1")[0], 0)
        self.assertEqual(len([l for l in section(self.rmt(), "เสร็จล่าสุด") if "[j1]" in l]), 1)
        self.assertEqual(rd(self.rec()).splitlines().count("สถานะ: ปิด"), 1)
        self.assertEqual(len([l for l in rd(self.rec()).splitlines() if l.startswith("สถานะ:")]), 1)
        self.assertFalse(os.path.exists(os.path.join(self.d, ".max", "j1")))
        self.assertEqual(section(self.rmt(), "กำลังทำ"), [])
        tmps = [f for _, _, fs in os.walk(os.path.join(self.d, "docs")) for f in fs if f.endswith(".tmp")]
        self.assertEqual(tmps, [])

    def test_fail_after_2(self):
        self._fail_then_close(2)

    def test_fail_after_3(self):
        self._fail_then_close(3)

    def test_fail_after_4(self):
        self._fail_then_close(4)

    def test_abandon_with_spec(self):
        self.start()
        rc, o, _ = lite(self.d, "abandon", "j1", "เปลี่ยนใจ")
        self.assertEqual(rc, 0)
        self.assertIn("สถานะ: ทิ้ง: เปลี่ยนใจ", rd(self.rec()).splitlines())
        self.assertEqual(section(self.rmt(), "เสร็จล่าสุด")[0],
                         f"- {TODAY()} [j1] ทิ้ง: เปลี่ยนใจ → docs/max-jobs/{self.rid()}/")
        self.assertEqual(section(self.rmt(), "กำลังทำ"), [])

    def test_abandon_without_spec(self):
        lite(self.d, "dir", "j1", "--size", "M")
        self.assertEqual(lite(self.d, "abandon", "j1", "ไม่เอาแล้ว")[0], 0)
        self.assertFalse(os.path.exists(os.path.join(self.d, "docs", "max-jobs", self.rid())))
        l = section(self.rmt(), "เสร็จล่าสุด")[0]
        self.assertIn("[j1] ทิ้ง: ไม่เอาแล้ว", l)
        self.assertNotIn("→", l)

    def test_size_s_unchanged(self):
        self.start("s1", "C1\n", "C1 ผ่าน — เทสครบถ้วน\n", size="S")
        rc, o, _ = lite(self.d, "close", "s1")
        self.assertEqual(rc, 0)
        self.assertNotIn("record=", o)
        self.assertFalse(os.path.exists(os.path.join(self.d, "docs")))

    def test_draft_and_diff_exclude_docs(self):
        self.start()
        lite(self.d, "gate", "j1", "build")
        rc, o, _ = lite(self.d, "close", "j1")
        self.assertIn("- ไฟล์: (ไม่มีไฟล์เปลี่ยน)", o)
        sh(["git", "add", "-A"], self.d)
        sh(["git", "commit", "-qm", "docs"], self.d)
        lite(self.d, "todo", "next", "ใหม่")
        self.w("docs/max-jobs/x/new.md", "ใหม่\n")
        rc, o, _ = lite(self.d, "diff", self.base, "--job", "j1")
        self.assertEqual(rc, 0, o)
        body = rd(os.path.join(self.d, ".max", "j1", "review.diff")) if os.path.exists(
            os.path.join(self.d, ".max", "j1", "review.diff")) else rd(o.split("review=")[1].split("\n")[0])
        self.assertNotIn("docs/roadmap.md", body)
        self.assertNotIn("docs/max-jobs", body)

    def test_abandon_after_gate_without_spec(self):
        lite(self.d, "dir", "j1", "--size", "M")
        lite(self.d, "gate", "j1", "spec")
        self.assertEqual(lite(self.d, "abandon", "j1", "x")[0], 0)
        st = [l for l in rd(self.rec()).splitlines() if l.startswith("สถานะ:")]
        self.assertEqual(st, ["สถานะ: ทิ้ง: x"])
        self.assertTrue(section(self.rmt(), "เสร็จล่าสุด")[0].endswith(f"→ docs/max-jobs/{self.rid()}/"))

    def test_abandon_twice_without_spec_keeps_both_lines(self):
        for why in ("a", "b"):
            lite(self.d, "dir", "j1", "--size", "M")
            lite(self.d, "abandon", "j1", why)
        self.assertEqual(len([l for l in section(self.rmt(), "เสร็จล่าสุด") if "[j1]" in l]), 2)

    def test_gate_after_half_close_repairs_line(self):
        self.start()
        subprocess.run([sys.executable, LITE, "close", "j1"], cwd=self.d, capture_output=True, text=True,
                       encoding="utf-8", env=dict(ENV, MAX_LITE_FAIL_AFTER="4"))
        self.assertEqual(lite(self.d, "gate", "j1", "build")[0], 0)
        t = self.rmt()
        self.assertEqual(len([l for l in section(t, "กำลังทำ") if l.startswith("- [j1] ")]), 1)
        self.assertEqual([l for l in section(t, "เสร็จล่าสุด") if "[j1]" in l], [])
        self.assertIn("สถานะ: กำลังทำ", rd(self.rec()).splitlines())

    def test_same_name_job_after_close_stays_active(self):
        self.start()
        self.assertEqual(lite(self.d, "close", "j1")[0], 0)
        lite(self.d, "dir", "j1", "--size", "M")
        lite(self.d, "todo", "next", "x")
        act = section(self.rmt(), "กำลังทำ")
        self.assertEqual(len([l for l in act if l.startswith("- [j1] ")]), 1)
        self.assertIn(f"record={self.rid()}-2", rd(os.path.join(self.d, ".max", "j1", "ledger.md")).splitlines()[0])
        self.assertEqual(len([l for l in section(self.rmt(), "เสร็จล่าสุด") if "[j1]" in l]), 1)


class TestResume(Repo):
    def rid(self):
        return f"{TODAY()}-j1"

    def rmt(self):
        return rd(os.path.join(self.d, "docs", "roadmap.md"))

    def built(self):
        lite(self.d, "dir", "j1", "--size", "M")
        self.w(".max/j1/SPEC.md", "# SPEC\nC1\n")
        lite(self.d, "gate", "j1", "build")
        sh(["git", "add", "-A"], self.d)
        sh(["git", "commit", "-qm", "wip"], self.d)
        shutil.rmtree(os.path.join(self.d, ".max"))

    def test_status_recoverable_then_resume(self):
        self.built()
        rc, o, _ = lite(self.d, "status")
        self.assertEqual(rc, 0)
        self.assertIn("กำลังทำ: - [j1] M · ด่าน: สร้าง", o)
        self.assertIn(f"กู้ได้ [j1]: docs/max-jobs/{self.rid()}/ → resume j1", o)
        rc, o, _ = lite(self.d, "resume", "j1")
        self.assertEqual(rc, 0, o)
        self.assertEqual(rb(os.path.join(self.d, ".max", "j1", "SPEC.md")),
                         rb(os.path.join(self.d, "docs", "max-jobs", self.rid(), "SPEC.md")))
        for s in ("dir=", "base=", "ด่าน: สร้าง"):
            self.assertIn(s, o)
        self.assertTrue(rd(os.path.join(self.d, ".max", "j1", "ledger.md")).splitlines()[-1].startswith("กู้คืนจากแฟ้ม:"))
        o = lite(self.d, "status")[1]
        self.assertNotIn("กู้ได้", o)
        self.assertIn("ค้าง [j1]:", o)

    def test_resume_never_overwrites(self):
        self.built()
        self.w(".max/j1/SPEC.md", "ของฉัน\n")
        rc, o, _ = lite(self.d, "resume", "j1")
        self.assertEqual(rd(os.path.join(self.d, ".max", "j1", "SPEC.md")), "ของฉัน\n")
        self.assertIn("มีอยู่แล้ว: SPEC.md", o)
        self.assertTrue(os.path.isfile(os.path.join(self.d, ".max", "j1", "ledger.md")))

    def test_resume_errors(self):
        rc, o, _ = lite(self.d, "resume", "nojob")
        self.assertEqual(rc, 1)
        self.assertIn("ไม่มีแฟ้มงาน nojob", o)
        lite(self.d, "dir", "j1", "--size", "M")
        self.w(".max/j1/SPEC.md", "C1\n")
        self.w(".max/j1/proof.md", "C1 ผ่าน — เทสครบถ้วน\n")
        lite(self.d, "close", "j1")
        rc, o, _ = lite(self.d, "resume", "j1")
        self.assertEqual(rc, 1)
        self.assertIn("งานปิดแล้ว — ใช้ recheck", o)
        self.assertEqual(lite(self.d, "resume", "../x")[0], 1)

    def test_status_nothing(self):
        rc, o, _ = lite(self.d, "status")
        self.assertEqual(o.strip(), "ไม่มีงาน MAX ค้าง")
        self.assertFalse(os.path.exists(os.path.join(self.d, "docs")))

    def test_status_repairs_half_closed(self):
        lite(self.d, "dir", "j1", "--size", "M")
        self.w(".max/j1/SPEC.md", "C1\n")
        self.w(".max/j1/proof.md", "C1 ผ่าน — เทสครบถ้วน\n")
        r = subprocess.run([sys.executable, LITE, "close", "j1"], cwd=self.d, capture_output=True, text=True,
                           encoding="utf-8", env=dict(ENV, MAX_LITE_FAIL_AFTER="3"))
        self.assertEqual(r.returncode, 9)
        shutil.rmtree(os.path.join(self.d, ".max", "j1"))
        o = lite(self.d, "status")[1]
        self.assertIn("ซ่อมแผนที่: [j1]", o)
        t = self.rmt()
        self.assertEqual(section(t, "กำลังทำ"), [])
        self.assertEqual(len([l for l in section(t, "เสร็จล่าสุด") if "[j1]" in l]), 1)
        self.assertNotIn("ซ่อมแผนที่", lite(self.d, "status")[1])

    def test_status_lost_job(self):
        lite(self.d, "dir", "jx", "--size", "M")
        shutil.rmtree(os.path.join(self.d, ".max"))
        shutil.rmtree(os.path.join(self.d, "docs", "max-jobs"), ignore_errors=True)
        o = lite(self.d, "status")[1]
        self.assertIn("หาย [jx]: ไม่มีทั้ง .max และแฟ้ม — ดู docs/worklog.md", o)
        self.assertIn("[jx]", self.rmt())

    def test_status_next_top3(self):
        for i in range(5):
            lite(self.d, "todo", "next", f"ข้อ {i}")
        o = lite(self.d, "status")[1]
        self.assertEqual(len([l for l in o.splitlines() if l.startswith("ถัดไป:")]), 3)
        self.assertIn("(+2)", o)

    def _old_closed(self):
        self.w(".max/closed/old-202611270541/SPEC.md", "C1\nAPP_PASSWORD=hunter2secret\n")
        self.w(".max/closed/old-202611270541/proof.md", "C1 ผ่าน — เทสครบถ้วน\n")
        self.w(".max/closed/old-202611270541/ledger.md",
               "# MAX old — SPEC: x — BASE=abc — size=M — start=2026-11-27 05:00\n")

    def test_backfill(self):
        self._old_closed()
        src = os.path.join(self.d, ".max", "closed", "old-202611270541")
        before = {n: rb(os.path.join(src, n)) for n in os.listdir(src)}
        rc, o, _ = lite(self.d, "backfill", "old-202611270541")
        self.assertEqual(rc, 0, o)
        rec = os.path.join(self.d, "docs", "max-jobs", "2026-11-27-old")
        self.assertIn("สถานะ: ปิด (ย้อนหลัง)", rd(os.path.join(rec, "record.md")).splitlines())
        self.assertNotIn("hunter2secret", rd(os.path.join(rec, "SPEC.md")))
        self.assertIn("record=docs/max-jobs/2026-11-27-old", o)
        self.assertEqual(len([l for l in section(self.rmt(), "เสร็จล่าสุด") if "[old]" in l]), 1)
        snap = {n: rb(os.path.join(rec, n)) for n in os.listdir(rec)}
        lite(self.d, "backfill", "old-202611270541")
        self.assertEqual({n: rb(os.path.join(rec, n)) for n in os.listdir(rec)}, snap)
        self.assertEqual(len([l for l in section(self.rmt(), "เสร็จล่าสุด") if "[old]" in l]), 1)
        self.assertEqual({n: rb(os.path.join(src, n)) for n in os.listdir(src)}, before)
        self.assertEqual(lite(self.d, "backfill", "nothere")[0], 1)

    def _mkrec(self):
        self.built()
        return os.path.join(self.d, "docs", "max-jobs", self.rid())

    def test_base_injection(self):
        pwn = os.path.join(tempfile.gettempdir(), f"pwned-{os.getpid()}")
        try:
            rec = self._mkrec()
            led = rd(os.path.join(rec, "ledger.md"))
            led = re.sub(r"BASE=\S+", "BASE=--output=" + pwn, led, count=1)
            with open(os.path.join(rec, "ledger.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write(led)
            self.assertEqual(lite(self.d, "resume", "j1")[0], 0)
            self.w(".max/j1/proof.md", "C1 ผ่าน — เทสครบถ้วน\n")
            lite(self.d, "close", "j1")
            self.assertFalse(os.path.exists(pwn))
        finally:
            if os.path.exists(pwn):
                os.remove(pwn)

    def test_resume_skips_symlink_source(self):
        rec = self._mkrec()
        out_ = tempfile.mkdtemp(prefix="maxout-")
        try:
            with open(os.path.join(out_, "s.txt"), "w") as f:
                f.write("TOPSECRET\n")
            os.remove(os.path.join(rec, "SPEC.md"))
            try:
                os.symlink(os.path.join(out_, "s.txt"), os.path.join(rec, "SPEC.md"))
            except (OSError, NotImplementedError):
                self.skipTest("no symlinks")
            rc, o, _ = lite(self.d, "resume", "j1")
            self.assertIn("ข้าม SPEC.md: symlink", o)
            for dp, _, fs in os.walk(os.path.join(self.d, ".max")):
                for f in fs:
                    self.assertNotIn("TOPSECRET", rd(os.path.join(dp, f)))
        finally:
            shutil.rmtree(out_, ignore_errors=True)

    def test_resume_refuses_symlink_folder(self):
        rec = self._mkrec()
        out_ = tempfile.mkdtemp(prefix="maxout-")
        try:
            moved = os.path.join(out_, "rec")
            shutil.move(rec, moved)
            try:
                os.symlink(moved, rec)
            except (OSError, NotImplementedError):
                self.skipTest("no symlinks")
            rc, o, _ = lite(self.d, "resume", "j1")
            self.assertEqual(rc, 1)
            self.assertFalse(os.path.exists(os.path.join(self.d, ".max", "j1")))
        finally:
            shutil.rmtree(out_, ignore_errors=True)

    def test_resume_refuses_symlink_job_dir(self):
        self._mkrec()
        out_ = tempfile.mkdtemp(prefix="maxout-")
        try:
            os.makedirs(os.path.join(self.d, ".max"), exist_ok=True)
            try:
                os.symlink(out_, os.path.join(self.d, ".max", "j1"))
            except (OSError, NotImplementedError):
                self.skipTest("no symlinks")
            rc, o, _ = lite(self.d, "resume", "j1")
            self.assertEqual(rc, 1)
            self.assertEqual(os.listdir(out_), [])
        finally:
            shutil.rmtree(out_, ignore_errors=True)

    def test_resume_twice_only_appends_ledger_line(self):
        self._mkrec()
        self.w(".max/j1/SPEC.md", "ของฉัน\n")
        self.w(".max/j1/ledger.md", "# ledger ของฉัน\nบรรทัดสอง\n")
        lite(self.d, "resume", "j1")
        lite(self.d, "resume", "j1")
        self.assertEqual(rd(os.path.join(self.d, ".max", "j1", "SPEC.md")), "ของฉัน\n")
        ls = rd(os.path.join(self.d, ".max", "j1", "ledger.md")).splitlines()
        self.assertEqual(ls[:2], ["# ledger ของฉัน", "บรรทัดสอง"])
        self.assertEqual(len(ls), 4)
        self.assertTrue(all(l.startswith("กู้คืนจากแฟ้ม:") for l in ls[2:]))

    def test_resume_bad_names(self):
        for bad in ("../x", "a/b", ".x"):
            self.assertEqual(lite(self.d, "resume", bad)[0], 1, bad)
        self.assertFalse(os.path.exists(os.path.join(self.d, ".max", "x")))
        self.assertFalse(os.path.exists(os.path.join(self.d, "x")))

    def test_resume_by_job_name_only(self):
        self._mkrec()
        self.assertEqual(lite(self.d, "resume", self.rid())[0], 1)

    def test_status_no_repair_leaves_roadmap_identical(self):
        self.built()
        before = rb(os.path.join(self.d, "docs", "roadmap.md"))
        lite(self.d, "status")
        self.assertEqual(rb(os.path.join(self.d, "docs", "roadmap.md")), before)

    def test_status_hostile_job_lines(self):
        lite(self.d, "todo", "next", "x")
        p = os.path.join(self.d, "docs", "roadmap.md")
        t = rd(p).replace("## กำลังทำ\n", "## กำลังทำ\n- [../../x] M · ด่าน: สร้าง · ถัดไป: - · ติด: - · 2026-01-01 10:00\n"
                          "- [a/b] M · ด่าน: สร้าง · ถัดไป: - · ติด: - · 2026-01-01 10:00\n")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
        before = set(os.listdir(os.path.dirname(self.d)))
        rc, o, _ = lite(self.d, "status")
        self.assertEqual(rc, 0)
        self.assertIn("หาย [../../x]", o)
        self.assertIn("หาย [a/b]", o)
        self.assertEqual(set(os.listdir(os.path.dirname(self.d))), before)

    def test_status_newer_line_than_close_not_repaired(self):
        lite(self.d, "dir", "j1", "--size", "M")
        self.w(".max/j1/SPEC.md", "C1\n")
        self.w(".max/j1/proof.md", "C1 ผ่าน — เทสครบถ้วน\n")
        lite(self.d, "close", "j1")
        p = os.path.join(self.d, "docs", "roadmap.md")
        t = rd(p).replace("## กำลังทำ\n", "## กำลังทำ\n- [j1] M · ด่าน: SPEC · ถัดไป: - · ติด: - · 2099-01-01 00:00\n")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
        o = lite(self.d, "status")[1]
        self.assertNotIn("ซ่อมแผนที่", o)
        self.assertIn("หาย [j1]", o)
        self.assertIn("- [j1] M · ด่าน: SPEC", rd(p))

    def _old_closed_n(self, name, start):
        self.w(f".max/closed/{name}/SPEC.md", "C1\n")
        self.w(f".max/closed/{name}/proof.md", "C1 ผ่าน — เทสครบถ้วน\n")
        self.w(f".max/closed/{name}/ledger.md", f"# MAX old — SPEC: x — BASE=abc — size=M — start={start}\n")

    def test_backfill_same_name_day_different_start(self):
        self._old_closed_n("old-202611270541", "2026-11-27 05:00")
        self._old_closed_n("old-202611270642", "2026-11-27 06:00")
        lite(self.d, "backfill", "old-202611270541")
        first = rb(os.path.join(self.d, "docs", "max-jobs", "2026-11-27-old", "record.md"))
        lite(self.d, "backfill", "old-202611270642")
        self.assertEqual(rb(os.path.join(self.d, "docs", "max-jobs", "2026-11-27-old", "record.md")), first)
        self.assertTrue(os.path.isfile(os.path.join(self.d, "docs", "max-jobs", "2026-11-27-old-2", "record.md")))
        lite(self.d, "backfill", "old-202611270642")
        self.assertFalse(os.path.exists(os.path.join(self.d, "docs", "max-jobs", "2026-11-27-old-3")))

    def test_backfill_source_with_existing_record(self):
        lite(self.d, "dir", "old", "--size", "M")
        self.w(".max/old/SPEC.md", "C1\n")
        self.w(".max/old/proof.md", "C1 ผ่าน — เทสครบถ้วน\n")
        lite(self.d, "gate", "old", "build")
        self.assertEqual(lite(self.d, "close", "old")[0], 0)
        name = os.path.basename(glob.glob(os.path.join(self.d, ".max", "closed", "old-*"))[0])
        snap = {p: rb(p) for p in glob.glob(os.path.join(self.d, "docs", "**", "*"), recursive=True) if os.path.isfile(p)}
        rc, o, _ = lite(self.d, "backfill", name)
        self.assertEqual(rc, 0)
        self.assertIn(f"มีแฟ้มแล้ว: docs/max-jobs/{TODAY()}-old", o)
        self.assertEqual({p: rb(p) for p in glob.glob(os.path.join(self.d, "docs", "**", "*"), recursive=True)
                          if os.path.isfile(p)}, snap)

    def test_backfill_does_not_take_open_job_id(self):
        self._old_closed_n("old-202611270541", f"{TODAY()} 05:00")
        lite(self.d, "dir", "old", "--size", "M")
        p = os.path.join(self.d, ".max", "old", "ledger.md")
        with open(p, "w", encoding="utf-8", newline="\n") as f:  # v8.3 style head, no record=
            f.write(f"# MAX old — SPEC: x — BASE=abc — size=M — start={TODAY()} 07:00\n")
        lite(self.d, "backfill", "old-202611270541")
        self.assertTrue(os.path.isfile(os.path.join(self.d, "docs", "max-jobs", f"{TODAY()}-old-2", "record.md")))
        self.assertEqual(len([l for l in section(self.rmt(), "กำลังทำ") if l.startswith("- [old] ")]), 1)

    def test_backfill_open_gated_job_untouched(self):
        lite(self.d, "dir", "old", "--size", "M")
        self.w(".max/old/SPEC.md", "C1\n")
        lite(self.d, "gate", "old", "build")
        orec = os.path.join(self.d, "docs", "max-jobs", f"{TODAY()}-old", "record.md")
        before = rb(orec)
        self._old_closed_n("old-202611270541", f"{TODAY()} 03:00")
        lite(self.d, "backfill", "old-202611270541")
        self.assertEqual(rb(orec), before)
        self.assertTrue(os.path.isfile(os.path.join(self.d, "docs", "max-jobs", f"{TODAY()}-old-2", "record.md")))

    def test_backfill_twice_identical_and_source_untouched(self):
        self._old_closed_n("old-202611270541", "2026-11-27 05:00")
        src = os.path.join(self.d, ".max", "closed", "old-202611270541")
        st = {n: os.stat(os.path.join(src, n)).st_mtime_ns for n in os.listdir(src)}
        st["."] = os.stat(src).st_mtime_ns
        lite(self.d, "backfill", "old-202611270541")
        rec = os.path.join(self.d, "docs", "max-jobs", "2026-11-27-old")
        snap = {n: rb(os.path.join(rec, n)) for n in os.listdir(rec)}
        lite(self.d, "backfill", "old-202611270541")
        self.assertEqual({n: rb(os.path.join(rec, n)) for n in os.listdir(rec)}, snap)
        self.assertEqual(len([l for l in section(self.rmt(), "เสร็จล่าสุด") if "[old]" in l]), 1)
        st2 = {n: os.stat(os.path.join(src, n)).st_mtime_ns for n in os.listdir(src)}
        st2["."] = os.stat(src).st_mtime_ns
        self.assertEqual(st2, st)

    def test_backfill_keeps_active_same_name(self):
        self._old_closed()
        lite(self.d, "dir", "old", "--size", "M")
        lite(self.d, "backfill", "old-202611270541")
        self.assertEqual(len([l for l in section(self.rmt(), "กำลังทำ") if l.startswith("- [old] ")]), 1)


class TestRecheck(Repo):
    SPEC = "# SPEC\n- C1 ทำก\n- C2 ทำข\n- C10 ทำค\n"
    PROOF = ("C1 ผ่าน — เทสครบถ้วน one\nC2 ผ่าน — เทสครบถ้วน two\nC10 ผ่าน — เทสครบถ้วน three\n")

    def setUp(self):
        super().setUp()
        lite(self.d, "dir", "j1", "--size", "M")
        self.w(".max/j1/SPEC.md", self.SPEC)
        self.w(".max/j1/proof.md", self.PROOF)
        self.w("a.txt", "two\n")
        self.assertEqual(lite(self.d, "close", "j1")[0], 0)
        self.id = f"{TODAY()}-j1"
        self.rec = os.path.join(self.d, "docs", "max-jobs", self.id)

    def gs(self):
        return sh(["git", "status", "--short"], self.d, text=True).stdout

    def rc_file(self):
        return os.path.join(self.rec, f"recheck-{TODAY()}.md")

    def test_recheck_prints(self):
        before = self.gs()
        rc, o, _ = lite(self.d, "recheck", "j1")
        self.assertEqual(rc, 0, o)
        ls = o.splitlines()
        self.assertIn(f"แฟ้ม: docs/max-jobs/{self.id}/ (ที่มา: แฟ้มถาวร)", ls)
        self.assertTrue([l for l in ls if l.startswith(f"ช่วง: {self.base}..")], ls)
        self.assertIn("ไฟล์: a.txt", ls)
        for c, ev in (("C1", "one"), ("C2", "two"), ("C10", "three")):
            row = [l for l in ls if l.startswith(c + " |")]
            self.assertEqual(len(row), 1, c)
            self.assertIn(ev, row[0])
        self.assertIn(f"recheck=docs/max-jobs/{self.id}/recheck-{TODAY()}.md", ls)
        self.assertEqual(lite(self.d, "recheck", self.id)[1].splitlines()[1:], ls[1:])
        self.assertEqual(self.gs(), before)
        self.assertFalse(os.path.exists(self.rc_file()))

    def test_recheck_fallbacks(self):
        shutil.rmtree(os.path.join(self.d, "docs", "max-jobs"))
        rc, o, _ = lite(self.d, "recheck", "j1")
        self.assertEqual(rc, 0)
        self.assertIn("(ที่มา: .max/closed)", o)
        shutil.rmtree(os.path.join(self.d, ".max", "closed"))
        rc, o, _ = lite(self.d, "recheck", "j1")
        self.assertEqual(rc, 1)
        self.assertIn("ไม่มีแฟ้มงาน j1 — ดู docs/worklog.md", o)

    def write_rc(self, text):
        with open(self.rc_file(), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def test_sum(self):
        self.write_rc("## x\nC1 ยังผ่าน — 3 passed test_a\nC2 พังแล้ว — ตั้งแต่ abc1234 test_b fail\n"
                      "C10 ตรวจไม่ได้ — ต้องรันบน Windows\n")
        rc, o, _ = lite(self.d, "recheck", "j1", "--sum")
        self.assertEqual(rc, 0, o)
        self.assertIn("ตรวจซ้ำ [j1]: ยังผ่าน 1 · พังแล้ว 1 (C2) · ตรวจไม่ได้ 1 (C10)", o)
        rm = rd(os.path.join(self.d, "docs", "roadmap.md"))
        self.assertEqual(len([l for l in section(rm, "ถัดไป") if "(P1) แก้ j1 C2 ที่พังแล้ว" in l]), 1)
        self.assertEqual(rd(os.path.join(self.rec, "record.md")).splitlines()[-1],
                         f"ตรวจซ้ำ: {TODAY()} ยังผ่าน 1 · พังแล้ว 1 · ตรวจไม่ได้ 1")
        lite(self.d, "recheck", "j1", "--sum")
        rm = rd(os.path.join(self.d, "docs", "roadmap.md"))
        self.assertEqual(len([l for l in section(rm, "ถัดไป") if "แก้ j1 C2" in l]), 1)
        self.assertEqual(len([l for l in rd(os.path.join(self.rec, "record.md")).splitlines()
                              if l.startswith("ตรวจซ้ำ:")]), 1)

    def test_sum_incomplete_writes_nothing(self):
        for body in ("C1 ยังผ่าน — 3 passed test_a\nC10 ยังผ่าน — 3 passed test_c\n",
                     "C1 ยังผ่าน — 3 passed test_a\nC2 พังแล้ว — สั้น\nC10 ยังผ่าน — 3 passed test_c\n"):
            self.write_rc(body)
            before = {p: rb(p) for p in (os.path.join(self.d, "docs", "roadmap.md"), os.path.join(self.rec, "record.md"))}
            rc, o, _ = lite(self.d, "recheck", "j1", "--sum")
            self.assertEqual(rc, 1)
            self.assertIn("ตรวจซ้ำไม่ครบ: ขาด C2", o)
            self.assertEqual({p: rb(p) for p in before}, before)

    def test_last_line_wins(self):
        self.write_rc("C1 ยังผ่าน — 3 passed test_a\nC2 พังแล้ว — ตั้งแต่ abc1234 fail\n"
                      "C2 ยังผ่าน — แก้แล้ว 3 passed\nC10 ยังผ่าน — 3 passed test_c\n")
        o = lite(self.d, "recheck", "j1", "--sum")[1]
        self.assertIn("ยังผ่าน 3 · พังแล้ว 0 · ตรวจไม่ได้ 0", o)

    def test_repeat(self):
        lite(self.d, "dir", "j2", "--size", "M")
        rc, o, _ = lite(self.d, "repeat", "j2", "ปุ่มยังไม่ขึ้น — ไม่ได้เปิดจอจริง")
        self.assertEqual(rc, 0)
        last = rd(os.path.join(self.d, ".max", "j2", "ledger.md")).splitlines()[-1]
        self.assertTrue(last.startswith("แจ้งซ้ำ: ปุ่มยังไม่ขึ้น"), last)
        rc, o, _ = lite(self.d, "repeat", "j1", "ซ้ำอีก APP_PASSWORD=hunter2secret")
        self.assertEqual(rc, 0)
        led = rd(os.path.join(self.rec, "ledger.md"))
        self.assertTrue(led.splitlines()[-1].startswith("แจ้งซ้ำ: ซ้ำอีก"))
        self.assertNotIn("hunter2secret", led)
        self.assertEqual(lite(self.d, "repeat", "nojob", "x")[0], 1)

    def test_recheck_bad_base_ignored(self):
        led = rd(os.path.join(self.rec, "ledger.md"))
        with open(os.path.join(self.rec, "ledger.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(re.sub(r"BASE=\S+", "BASE=--output=/nonexistent/x", led, count=1))
        rc, o, _ = lite(self.d, "recheck", "j1")
        self.assertEqual(rc, 0)
        self.assertNotIn("--output", o)


class TestStats(Repo):
    def rec(self, name, text, ledger=None):
        self.w(f"docs/max-jobs/{name}/record.md", text)
        if ledger is not None:
            self.w(f"docs/max-jobs/{name}/ledger.md", ledger)

    def test_stats_exact(self):
        self.rec("2026-01-01-a", "# a\nขนาด: M\nสถานะ: ปิด\nC-id: 4\nยังไม่ได้ตรวจ: 0\nเกินเพดาน: 0\nturn: 20\n")
        self.rec("2026-01-02-b", "# b\nขนาด: L\nสถานะ: ปิด\nC-id: 10\nยังไม่ได้ตรวจ: 2 (C1 C2)\nเกินเพดาน: 1\n"
                 "ตรวจซ้ำ: 2026-02-01 ยังผ่าน 9 · พังแล้ว 1 · ตรวจไม่ได้ 0\n", "# h\nแจ้งซ้ำ: x (2026-01-03)\n")
        self.rec("2026-01-03-c", "# c\nขนาด: M\nสถานะ: ทิ้ง: x\nC-id: 0\n")
        self.rec("2026-01-04-d", "# d\nขนาด: XL\nสถานะ: กำลังทำ\nC-id: 50\n", "# h\nแจ้งซ้ำ: y\n")
        rc, o, _ = lite(self.d, "stats")
        self.assertEqual(rc, 0)
        self.assertEqual(o.splitlines(), [
            "งาน: 3 (ปิด 2 · ทิ้ง 1) · ขนาด: M 2 · L 1 · XL 0",
            "แจ้งซ้ำ: 1 ครั้ง ใน 1 งาน",
            "C-id: 14 · ยังไม่ได้ตรวจ 2 (14%)",
            "เกินเพดาน: 1 งาน",
            "turn เฉลี่ย: M 20 (จาก 1 งาน)",
            "ตรวจซ้ำ: 1 ครั้ง · พังแล้ว 1"])

    def test_stats_empty(self):
        rc, o, _ = lite(self.d, "stats")
        self.assertEqual((rc, o.strip()), (0, "ยังไม่มีแฟ้มงาน"))
        self.rec("2026-01-01-a", "# a\nขนาด: M\nสถานะ: ปิด\nC-id: 4\n")
        self.assertIn("turn เฉลี่ย: ไม่มีข้อมูล", lite(self.d, "stats")[1])

    def test_stats_broken_records(self):
        self.rec("2026-01-01-a", "")
        self.rec("2026-01-02-b", "สถานะ: ปิด\nขนาด:\n")
        self.rec("2026-01-03-c", "สถานะ: ปิด\nC-id: x\nขนาด: M\nturn: abc\n")
        rc, o, _ = lite(self.d, "stats")
        self.assertEqual(rc, 0, o)
        self.assertIn("งาน: 3 (ปิด 2 · ทิ้ง 0)", o)
        self.assertIn("C-id: 0 · ยังไม่ได้ตรวจ 0 (0%)", o)

    def test_no_args_lists_commands(self):
        rc, o, _ = lite(self.d)
        self.assertEqual(rc, 2)
        for c in ("gate", "todo", "resume", "backfill", "recheck", "repeat", "stats"):
            self.assertIn(c, o)


if __name__ == "__main__":
    unittest.main(verbosity=1)
