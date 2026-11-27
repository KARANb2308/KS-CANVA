---
name: max
description: MAX v8 build workflow - sizes the task (S/M/L; XL only when the user types "MAX สุด"), SPEC with coverage ids, test-first Sonnet coders, spec-first review, a separate verifier, a proof gate before "done". Use for coding, builds, bug fixes, bug hunts and audits, or when the user says MAX / แม็กซ์ / "ทำแบบ MAX" / "MAX สุด" / "ทำต่อ" / "ตรวจซ้ำ <งาน>" / "แผนที่งาน". Not for questions or explanations - answer directly.
---

# MAX v8 (Cowork) — ถูกตั้งแต่ครั้งแรก ด้วย turn และ token น้อยที่สุด

Cowork edition: no hooks, so the gates below are **yours to keep** (they were automatic on the PC). Tools run in
Cowork's sandbox on the folder the user opened. Job state: `scripts/max_lite.py` beside this file (stdlib Python):
run it as `python3 "<this skill's folder>/scripts/max_lite.py" …` from the project folder. `<project>/.max/<job>/` =
scratch (never committed); the script also writes `docs/roadmap.md` + `docs/max-jobs/<id>/` → commit them with the
work; no secrets or customer data in proof lines.

**A main turn costs much more than an agent turn.** Main thinks, writes the SPEC, briefs and rules; agents do every
loop (test-fix, click-through, sweep).

## Front door (intake → verify → report)
- **The user says ตรวจละเอียด / ตรวจให้ละเอียดก่อน / MAX ละเอียด / MAX+ / max-deep → run the `max-deep` skill
  first** (deep pre-check, stop for approval, then this workflow with every gate on). Otherwise as below.
- Project Kedit (has the skill kedit-verify) → read `references/project-kedit.md`.
- **Reply in plain Thai**, short, no filler, the user's words not file names.
- **Look first, then ask once** (AskUserQuestion, ≤ 4 questions, recommended option first "(แนะนำ)"): where the
  user will look (which app/URL/file) · what "ทั้งหมด" means · a reference for anything visual · after it's done
  (commit only / deploy too). Zero questions is fine — take the recommended answers and list them as assumptions.
  **Always ask** before: deleting/overwriting user data · paid API calls · push / deploy / release · anything
  outside the opened folder.
- **One message = every call that can go now** (independent reads, greps, briefs). Locate and read together
  (`Grep -C 12`). No text-only turns except the final report or a real question. Never poll.
- **Done = proof where the user looks**: a test name + count, an output line, a screenshot, or "ก่อน → หลัง" read
  from another channel (file/API). No proof → say `ยังไม่ได้ตรวจจริง`. Destructive checks only on a copy.
- **Report:**
  ```
  ทำแล้ว: <one line per change the user will notice>
  ดูได้ที่: <file / URL / what to click> — เห็นเมื่อ: <ทันที | หลังรีเฟรช | หลังปล่อยอัปเดต>
  ยังไม่ได้ตรวจจริง: <items, or "ไม่มี">
  สถานะ: <commit? deploy? left uncommitted?>
  ```
- **Project memory (every job that changes files — never skip):** `<project>/docs/worklog.md` (one entry per job)
  + `<project>/docs/playbook.md` (recipes that worked, traps), committed with the work so they survive new sessions.
  **Start:** read the playbook + `grep -n "<key words>" docs/worklog.md` for similar jobs; reuse what worked, avoid
  the traps (an old `LESSONS.md` is read too). Missing → create both from `references/worklog.template.md` and
  `references/playbook.template.md` (add `.max/` to `.gitignore`). **End (or stopped half way):** append the entry in
  the template's form (คำขอ · สถานะ · ทำอะไร · ไฟล์ · ขั้นตอนที่ได้ผล · ที่ไม่ได้ผล/ระวัง · ตรวจด้วย · commit) and update
  the playbook: a new recipe, a trap, or `ยังไม่ได้ลองจริง` → `ได้ผล (<date>)` once used and passed. Q&A only → no entry.
  The plugin's Stop hook blocks finishing while files changed and the log didn't (Claude Code only; Cowork has no
  hooks, so keep this rule yourself).

## Team (always name the agent — never a generic agent for MAX work)
| Who | Model | When |
|---|---|---|
| `max-scout` | Haiku, read-only | ≥ 3 unknown places or a huge file: up to 3 in one message. Otherwise Grep yourself |
| `max-coder` | Sonnet | Builds test-first, writes the review diff at the end; one brief per file group. A task marked `ยาก:` → send it with the Agent parameter `model: "opus"` (or `max-advisor` if still stuck) |
| `max-ui-coder` | Sonnet + browser | Same, for a brief with `ดูที่:` (tunes by watching) |
| `max-reviewer` | Sonnet, read-only | Fresh eyes on the diff: SPEC first, then real bugs |
| `max-verifier` | Sonnet, no code edits | Opens the real thing, walks C-ids, runs the project's checks, writes `proof.md`; also S repro (`ทำซ้ำ:`) |
| `max-hunter` | Sonnet, read-only | Bug hunt / audit of existing code, one area group each (`references/hunt.md`) |
| `max-advisor` | Opus (XL: `model: "fable"`) | L SPEC, a stuck bug (§3, any size), Core pass on permissions / money / deletion |

If a `max-*` agent can't start in this Cowork (plugin agents off), run the same role with the generic agent and
paste the role's rules: open `agents/<name>.md` of this plugin, or say so to the user.
Briefs: paths not contents; coder and ui-coder briefs carry `lite: <full path of max_lite.py>`; no history of earlier tasks; never say what you think is right or what not to flag.
Every brief carries `คำขอ: "<the user's words>"` verbatim. **Claim check (manual):** when an agent says it wrote
`report:` / `review:` / `proof:`, check the file exists and is new (`ls -l`, chained into a call you already make)
before acting on it. Sonnet is the floor for writing, reviewing and verifying. At once: agents that run
tests/builds ≤ 2, read-only ≤ 4. Subagents never call subagents.

## 0 — Size (before anything)
| Size | Looks like | Path |
|---|---|---|
| **S** | one spot / ≤ ~50 lines / 1–2 files, ≤ ~15 tool calls, no Core | build here → test → proof. No SPEC, no review |
| **M** | small feature / 3–6 files / clear way | short SPEC by you → `max-coder` → `max-reviewer` + `max-verifier` |
| **L** | new feature / many parts / unclear way / **any Core** (permissions, user data, money, deleting/overwriting files, keys) | design (0b) → `max-advisor` SPEC → coders per group → Core review at once → reviewer + verifier |
| **XL** | only when the user types "MAX สุด" — never pick it yourself | as L, and `max-advisor` with Agent `model: "fable"` for the SPEC, each Core review and the whole-diff review at the end; advisor ≤ 5 calls; if Agent rejects `model: "fable"` use `opus` and tell the user once. `max_lite.py dir <job> --size XL` |

**Task routes** (any size): security → skill `security-review` if present · speed → numbers before → after are required ·
data migration → Core, back up first · deploy / release → ask first · refactor → skill `simplify` if present.

Unsure → the smaller size, but **touching Core is never S**, even 5 lines. S becomes M at once (5-line SPEC, the
rest to `max-coder`) when it passes ~50 lines or 2 files, or its test or look fails twice.
**Text only** (skill / docs / .md, UI wording, config with no logic) is S at any length; > ~100 changed lines →
one `max-reviewer` (`คำขอ:` · the diff file) before done.
An S bug also needs the test seen red (`แดงก่อนแก้:`) and, after the fix, the user's steps repeated once.
**Tune by eye** (the user judges by seeing): one `max-ui-coder` (`ดูที่:` · `อ้างอิง:` · `ภาพ: <dir>/tune.png`),
≤ 5-line SPEC; show the user the picture and send their next words verbatim to the **same** coder.

**At M and L main writes no code, runs no test loops, clicks nothing** — except `ตัดสิน: ทำเอง — <why>` in the
ledger for a fix ≤ ~10 lines or the final look (≤ 2 screenshots).
**Main budget (count it yourself — no meter here): S 10, M 25, L 50, XL 70 turns (same as `max_lite.py`).** M plan: look + SPEC + coder ≤ 4 · each
coder return 1 · review + verify ≤ 6 · close ≤ 3. Main starts no run > 2 min. A return while another agent runs →
end the turn, no call. At the cap: ledger `เกินเพดาน: <cause>`, everything left to agents in one message. **The
cap never skips a gate.**

M/L/XL: Read `references/ml.md` once at the start (0b, SPEC + ledger, build, review + verify, close). Bug hunt / audit → `references/hunt.md`.
"ทำต่อ" / a new session: `python3 …/max_lite.py status`; `กู้ได้ [job]` → `resume <job>`; then read that job's
`ledger.md` before anything; `หาย`/`ซ่อมแผนที่` → read references/roadmap.md; a `เริ่ม` line with no `เสร็จ` → read its report + `git status` first, never re-send a
coder blindly. "ตรวจซ้ำ <งาน>" / "ตรวจซ้ำละเอียด" → read only `references/recheck.md`. Roadmap / next jobs / stats →
`references/roadmap.md`.

## 3 — Bugs (every size, no guessing)
1) **Reproduce at the user's entry point** (their button/route/file); can't reproduce = cause unknown, no fix yet
2) evidence: real values, logs, and a **working example** (the same feature that works, or the last good commit:
`git log -S`, bisect); list the differences 3) one hypothesis at a time, `สมมติฐาน: X เพราะ Y`, tested the
smallest way 4) fix the one spot at the cause, then grep the same pattern: `ที่อื่น: n จุด`, each fixed or
`ตัดสิน:` 5) the test that fails without the fix + related tests; the report carries `แดงก่อนแก้: <test + 1 line>`.
"ไม่เห็น / เหมือนเดิม" → check the user's path first (cache, old build, other file/URL).
**Stuck** (same test fails after 3 fixes / coder `BLOCKED`) → once per task, a fresh `max-coder` with
`ลองแล้ว: 1) 2) 3)`. Stuck again, or the user reports it a 2nd time → the design is wrong: `max-advisor` with
`SPEC:` · `เทสที่พัง:` · `โค้ด:` file:line · `ลองแล้ว:` · `Error:` ≤ 20 lines.

## Red flags
| Thought | Reality |
|---|---|
| "Faster to run/click/fix it myself" | Your turn ≈ 10 agent turns; send the loop to an agent |
| "Tests pass, so it's done" | No proof line where the user looks = not done (`close` refuses) |
| "One more fix will do it" (3rd+) | The design is wrong → `max-advisor` |

## Ceilings
- Review fixes ≤ 2 rounds per task; still failing → Core: `max-advisor`; else "ค้าง" in the ledger + tell the user.
- `max-advisor` ≤ 3 calls per job (XL ≤ 5). No agent teams. No advisor on S/M unless the user asks — except §3 "Stuck" (any size).
- Tests the coder ran on the final diff: reviewer never re-runs them.
- Never rewrite a whole file to change one spot. Long test output → a log file; read the summary line.
- Cowork sandbox: if a test needs Windows-only tools, a GPU or the user's installed app, it can't run here → the
  verifier marks those C-ids `ยังไม่ได้ตรวจ — ต้องรันบนเครื่องผู้ใช้` and the report says so.
