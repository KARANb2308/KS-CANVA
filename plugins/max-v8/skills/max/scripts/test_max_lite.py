#!/usr/bin/env python3
"""Tests for max_lite.py and hooks/require-worklog.mjs (stdlib only)."""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LITE = os.path.join(HERE, "max_lite.py")
HOOK = os.path.normpath(os.path.join(HERE, "..", "..", "..", "hooks", "require-worklog.mjs"))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
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
        sh(["git", "init", "-q"], self.d)
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


if __name__ == "__main__":
    unittest.main(verbosity=1)
