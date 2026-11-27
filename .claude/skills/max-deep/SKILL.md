---
name: max-deep
description: MAX ละเอียด (deep pre-check) — before touching any code, maps everything the task touches, takes a "before" baseline where the user looks, runs every assumption check, gets an independent second opinion on the plan, asks every open question, and STOPS for the user's go-ahead; then runs MAX with every gate on. Use ONLY when the user says ตรวจละเอียด / ตรวจให้ละเอียดก่อน / ตรวจให้ละเอียดที่สุด / MAX ละเอียด / MAX+ / max-deep / "เช็คก่อนเริ่ม". Normal MAX jobs use the `max` skill without this.
---

# MAX ละเอียด — ตรวจให้ครบก่อนแตะโค้ด แล้วค่อยทำแบบ MAX เต็มทุกด่าน

The user chose thoroughness over speed and tokens for this job. This skill **adds a pre-check before MAX** and
**turns off MAX's shortcuts** afterwards. Everything in the `max` skill (Front door, Team, §3 Bugs, ceilings) still
applies; where this file is stricter, this file wins.

## กฎเหล็ก
- **Until the user approves the preflight: no edits to project files, no commit / push / deploy.** Writes go only
  to `<project>/.max/<job>/` (never committed). Reading, grepping, running read-only checks and opening the page are fine.
- **No guessing.** Every claim in the preflight carries evidence: `file:line`, a command and its output, or a screenshot path.
  Something not checked is written `ยังไม่ได้ตรวจ — <why>`, never presented as fact.
- **Ask, don't assume.** In normal MAX, zero questions is fine; here every real ambiguity becomes a question (with a
  recommended answer). Only skip a question when the code or the user's words settle it, and say which.
- Read the project's `CLAUDE.md` and `LESSONS.md` first; their project rules (generated files, run modes, Core areas,
  what can't be tested here) are part of the check.

## D1 — Intake (one message, every independent call together)
- `คำขอ:` the user's words verbatim, split into pieces `P1 … Pn` (each piece will map to C-ids later).
- `git status --short` · `git log --oneline -15` · `python3 "<max skill folder>/scripts/max_lite.py" status`
  (an open job → read its ledger first, as `max` says) · `git log -S"<key word>" --oneline | head` for the area's history.
- Up to 3 `max-scout` in the same message, one question each:
  (a) where the feature lives + the user's entry point (button / route / menu)
  (b) every reader, writer and caller of the function or data that will change
  (c) the same pattern or copied list elsewhere that must change together

## D2 — Map (read ranges from the scout pointers, `Grep -C 12`, never whole big files)
Write down, with `file:line`:
- **จะแก้:** each spot that will change
- **กระทบ:** each spot that reads / depends on it, and how it could break
- **ต้องสร้างใหม่ / ซิงก์:** generated or duplicated files (see CLAUDE.md)
- **ข้อมูลที่บันทึกไว้:** saved data shapes the change reads or writes — old saved data must still load
- **ทุกที่ที่ผู้ใช้จะเห็น:** every place / mode / screen the change shows up (one C-id each later)
- **ที่อื่น: n จุด** — grep of the same pattern, each listed

## D3 — Baseline "ก่อน" where the user looks
- Run the project's existing checks now and record the result lines (so later failures aren't blamed on the change).
- Open the real thing at the user's entry point (Playwright for a page) and save `before/*.png` or the current values.
- Bug job: reproduce it now with the user's steps. Can't reproduce → `สาเหตุ: ยังไม่รู้`, and that is a question for the user, not a guess.

## D4 — Risk + assumptions (checked now, not left to the coder)
- `สมมติฐาน: A1 …` — every belief the plan rests on (a field exists in old data, n callers, a function returns X,
  a host is allowed). **Run each one's read-only check now** and write `A1 จริง — <output>` or `A1 ไม่จริง — <real value>`.
  A false one changes the plan before anything else.
- **Core?** (permissions / password / session, user data, deleting or overwriting, keys / secrets, money) → size L,
  and say which Core it touches.
- `จุดที่ต้องระวัง:` the 3–7 failures most likely to hurt a real user, most likely first. Always consider: half-way
  failure leaves old data intact · old saved data · preview ≠ export · Thai text · empty / huge input · double click ·
  slow or failed network · every run mode the project has.
- `ตรวจที่นี่ไม่ได้:` what this environment cannot prove (Windows-only tools, sites the network blocks, the user's
  live deployment) — said up front, so the user knows before they approve.

## D5 — Second opinion (fresh eyes, not anchored on yours)
Write `.max/<job>/preflight.md` (format below), then send **one** reviewer agent:
- L or Core → `max-advisor` · existing code area with bug risk → `max-hunter` · otherwise → the `Plan` agent.
- Brief: `คำขอ:` verbatim · `preflight: <path>` · the files list · "หาสิ่งที่ preflight นี้พลาด: จุดที่กระทบแต่ไม่ได้ระบุ,
  กรณีที่ไม่ได้คิด, สมมติฐานที่ผิด, ทางที่ง่ายกว่า — ทุกข้อต้องมี file:line" · `findings: .max/<job>/second-opinion.md`.
  **Never** tell it what you think is safe or what not to flag.
- Each finding → added to the preflight, or a `ตัดสิน: ไม่รับ — <why>` line. Never silently dropped.

## D6 — Questions
Every open point → one `AskUserQuestion` (≤ 4 questions, recommended option first with "(แนะนำ)", each question
standalone). Typical: where the user will look · what "ทั้งหมด" covers · approach when there are 2–3 real ways ·
anything visual without a reference · after done: commit only / push / deploy. Answers go into the preflight.

## D7 — Preflight report, then STOP
Update `.max/<job>/preflight.md` and show the user this summary in plain Thai (short, the user's words, not file dumps):
```
เข้าใจว่า: <1–3 lines — what will be different for the user>
จะแก้: <file:line — what>            กระทบ: <file:line — why>
ตรวจแล้วก่อนเริ่ม: <A1 จริง … · baseline: <checks> ผ่าน n/n · ภาพก่อนแก้: <path>>
ความเสี่ยง: <most likely first>
ความเห็นที่สอง: <n ข้อ — รับ n / ไม่รับ n (why)>
ตรวจที่นี่ไม่ได้: <items, or "ไม่มี">
ขนาดงาน: <S|M|L> — <why>
แผน: C1 … Cn — <how each will be proven>
รอคำยืนยัน: พิมพ์ "ลุย" เพื่อเริ่ม หรือบอกสิ่งที่อยากเปลี่ยน
```
**End the turn here.** No edits until the user says go ("ลุย" / "ตกลง" / "เริ่มได้" / approves). Changes asked → update
the preflight and show it again.

## D8 — Build with every gate on (after approval)
Run the `max` skill for the job, with these overrides:
- The SPEC is built from the preflight: its `P`-pieces → C-ids, its `A`-ids (already checked) go in `สมมติฐาน`,
  its `จุดที่ต้องระวัง` each get a test or a C-id.
- **Size never goes down from the preflight.** S only when the preflight shows ≤ 1 file, ≤ ~20 lines, no Core —
  and even then `max-reviewer` + `max-verifier` still run (no S shortcut, no review skip rule).
- Core → `max-advisor` reviews the Core part (as MAX L).
- Budget for main, pre-check included: M ≤ 35 turns, L ≤ 70. The cap never skips a gate.

## D9 — Close
- Final diff: `max-reviewer` (MAX) **and** the `code-review` skill at `high`; touched Core → also `security-review`.
- `max_lite.py close <job>`; the MAX report adds one line:
  `เทียบกับแผน: ทำครบ C1–Cn | เปลี่ยนจากแผน: <what + why>`.
- Something learned that will repeat in this project → one line in `LESSONS.md`.
