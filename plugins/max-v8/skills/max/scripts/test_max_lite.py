#!/usr/bin/env python3
"""Tests for max_lite.py and hooks/require-worklog.mjs (stdlib only)."""
import glob, json, os, shutil, subprocess, sys, tempfile, unittest

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
        self.assertEqual(os.listdir(self.d).count("z.txt.tmp"), 0)
        self.assertFalse(os.path.exists(p))

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
        for bad in ("../../x", "a/b", "2026-11-27-a..b", "x"):
            self.w(".max/jj/ledger.md", f"# h — start=2026-01-02 05:00 — record={bad}\n")
            self.assertEqual(max_lite.record_id(os.path.join(self.d, ".max", "jj"), "jj"), "2026-01-02-jj", bad)

    def test_utf16_and_symlink_sources(self):
        self.w(".max/j1/SPEC.md", "C1 ภาษาไทย\n".encode("utf-16"), "wb")
        self.assertEqual(lite(self.d, "gate", "j1", "build")[0], 0)
        os.remove(os.path.join(self.d, ".max", "j1", "SPEC.md"))
        self.w("secret-outside.txt", "TOPSECRET\n")
        try:
            os.symlink(os.path.join(self.d, "secret-outside.txt"), os.path.join(self.d, ".max", "j1", "SPEC.md"))
        except (OSError, NotImplementedError):
            self.skipTest("no symlinks")
        shutil.rmtree(self.rec)
        lite(self.d, "gate", "j1", "spec")
        self.assertFalse(os.path.exists(self.rp("SPEC.md")))

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

    def test_same_name_job_after_close_stays_active(self):
        self.start()
        self.assertEqual(lite(self.d, "close", "j1")[0], 0)
        lite(self.d, "dir", "j1", "--size", "M")
        lite(self.d, "todo", "next", "x")
        act = section(self.rmt(), "กำลังทำ")
        self.assertEqual(len([l for l in act if l.startswith("- [j1] ")]), 1)
        self.assertIn(f"record={self.rid()}-2", rd(os.path.join(self.d, ".max", "j1", "ledger.md")).splitlines()[0])
        self.assertEqual(len([l for l in section(self.rmt(), "เสร็จล่าสุด") if "[j1]" in l]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
