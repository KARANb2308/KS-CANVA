# MAX — M/L steps (0b, SPEC + ledger, build, review + verify, close; hunt → hunt.md)
Read once at the start of an M/L job. Sizes, Team, bugs (§3), red flags and ceilings stay in `../SKILL.md`.

## 0b — Design first (L, or an M whose way is unclear) — one round
1. Look first (NOTES, Grep, the screen). Note for yourself: purpose and user · "done" where they look · non-goals ·
   does the data it needs exist in real (old) projects?
2. 2–3 real approaches, one-line trade-off each, recommended first — asked **once** inside the intake
   `AskUserQuestion` (sent in the same message as the scouts when the questions don't depend on them).
3. Way clear, or "ไม่ต้องถาม" → recommended one, `ตัดสิน:` line, go on.

## 1 — SPEC + ledger (M, L)
`python3 "<skill folder>/scripts/max_lite.py" dir <job> --size M|L` → `dir` (`<project>/.max/<job>/`), `base` and
`budget` (same message as the SPEC Write + coder brief). Keep
SPEC, ledger, proof and reports in `dir`. Write the SPEC and send the coder in **one** message
(Write, then Agent). **SPEC starts with `แผน (ภาษาคน)`**: 5–10 Thai lines (เปลี่ยนอะไรให้ผู้ใช้ · ขั้นตอน ·
พิสูจน์ยังไง · ความเสี่ยง · ไม่ทำ). M: put the plan in the message that sends the coder, `gate <job> build`, go on. L/XL:
`gate <job> plan` → give its output to the user as is → end the turn, wait for "ลุย" → `gate <job> build`. Every turn ending with the job still open (ลุย, question, over budget): the `gate` call also runs `git add docs/max-jobs docs/roadmap.md && git commit -m "max: <job> ด่าน <x>"`; say in one line if pushed (project push rules); not pushed = a new session cannot resume. From
max-deep with preflight approved → don't ask again, unless the SPEC goes beyond the preflight. L advisor brief: `SPEC: <path>` · `dir:` · `คำขอ:` the user's words · intake answers / `ตัดสิน:` lines · NOTES paths · bound rules (e.g. docs/rules/<area>.md) · `skill:` the project skill path · `ml: <this skill's folder>/references/ml.md` (absolute). It self-checks and returns STATUS + a table `G · tasks · files · test command`; main reads the SPEC only when STATUS has concerns. `SPEC.md` (M: by you, ≤ ~50 lines, skip empty headings; L: `max-advisor`), Thai
headings exactly:
1. `เป้าหมาย`: 1–2 lines + checkable acceptance criteria (what the user clicks, sees, where, and when — now or
   after a release) + `คำขอ: "<the user's words, piece by piece>" → C1, C3` (every piece has an id)
2. `แนวทาง + สิ่งที่ไม่ทำ`, then `สมมติฐาน`: what the SPEC believes about the real code and data (a field exists
   in old projects, n callers, what a function returns), `A1 …` each with a one-line read-only check command. The
   coder runs them before T1; a false one → `NEEDS_CONTEXT` with the real value, nothing is built on it. This is
   the cheap guard against a SPEC built on a wrong picture
3. `รายการครอบคลุม`: `C1 …` one per line, every variant, screen and case (SKILL.md 'Front door'). Code used in several
   places (e.g. desktop + web) → one C-id per place. "ทุก/ทั้งหมด X" is counted **two ways** (grep of
   the code + what the screen/API lists, e.g. `grep -c "kind=" → 7` and the menu shows 7) — mismatch = fix the
   list before T1. A visual C-id carries `อ้างอิง: <path/URL>`; without one it can only be `ยังไม่ได้ตรวจ`.
   Bug jobs: `C1 ทำซ้ำตามผู้ใช้: <steps>` — the verifier repeats it after the fix
4. `interface`: names, routes, params, return shapes once; each task says `ใช้:` / `ให้:`. A `ให้:` that changes
   data returns `changed: n` (or why not)
5. `กฎที่ผูก`: project rules this job must follow, exact values, named in the tasks they bind
6. `จุดที่ต้องระวัง`: 3–5 failures most likely to hurt a real user, most likely first. Always consider: fails
   half way (raise after step k → old data intact, no half-written file) · old saved data (a fixture copied from
   a real project, load → save → load equal) · preview ≠ export · Thai text · empty / huge · 8 GB · double click
7. `tasks`, in order: files + `file:line`, test (`input → expected`; Core: assertions written out + one rule test:
   do → undo = same · load → save → load = same · twice = once), command, **Core** label, `กลุ่ม: A`.
   Several small edits of one kind → one task
8. `สิ่งที่ห้ามแตะ`
**Self-check before T1**: every criterion and `คำขอ` piece has a task/C-id · no line that decides nothing ("handle
errors", "ตามความเหมาะสม", "TBD") · names match across tasks · every `จุดที่ต้องระวัง` is tested or a C-id ·
≤ ~2× what the job needs · read `คำขอ:` once more against `เป้าหมาย`: where would the user say "นี่ไม่ใช่ที่ขอ"?
fix that first (unsure what they meant → it was an intake question; ask now, before T1). Then `SPEC ตรวจแล้ว` in
the ledger. A real change mid-job → "เปลี่ยนแปลง" heading + why.

`ledger.md` = the job's memory (its header line is written by `max_lite.py dir`, not by main). **Agents append their
own lines** (coder: `G1 เสร็จ T1-T3 เทส 12/12 review: <path>`; verifier: `ตรวจแล้ว: C1 C2`); main writes only
`SPEC ตรวจแล้ว` and `ตัดสิน: <choice> — <why> [— ถ้าผิด: <cost>]`,
inside a call it already makes. Stop and ask only for what SKILL.md 'Front door' lists.

## 2 — Build (`max-coder`; brief has `ดูที่:` → `max-ui-coder`; one brief per file group)
- Brief: `SPEC: <path>` · `tasks: 2,3,4` (in order; ≤ 4, or ≤ 8 small fixes in one big file; a Core task ends the
  batch) · `เทส: <command>` · `report: <dir>/<job>-G<n>.md` · `ledger: <dir>/ledger.md` · `base: <sha>` ·
  `job: <job>` · `lite: <full path of max_lite.py>` (coder and ui-coder use it; none → they Glob `**/skills/max/scripts/max_lite.py` in the max-v8 plugin) · `คำขอ:` verbatim · `proof: <dir>/proof.md` (M with no screen; M with a screen too — the coder
  writes the C-ids its tests prove, the verifier keeps only what the screen shows) · `ยาก:` task → pass the Agent tool parameter `model: "opus"` to `max-coder` (not text in the brief) · `ดูที่:` when a screen is tuned (→ `max-ui-coder`) · decisions the SPEC can't know. An M is usually one coder.
- `gate <job> build|review|fix|proof` is chained onto a call you already make (no extra turn); show the user its `ด่าน:` line.
- Every task: the test is written and seen **red first** (`แดงก่อนแก้:` in the report). The coder ends by running
  `max_lite.py diff` itself and returns `review:` in STATUS.
- More work on files a coder has open → SendMessage it while its context is under ~100k; past that, a fresh coder
  with `report: <its last report>`. Different `กลุ่ม` → up to 2 coders in one message.
- `STATUS:` `DONE` needs test numbers, `ตรวจตัวเอง: ครบ` and `review:`; `DONE_WITH_CONCERNS` → rule on each
  (`ตัดสิน:`); `NEEDS_CONTEXT` → decide, continue the same coder; `BLOCKED` → SKILL.md §3.
- A **Core** task done → `max-reviewer` at once (same message as the next independent brief).

## 3b — Bug hunt / audit ("หาบัคทั้งหมด", "ตรวจทั้งแอป") → read `hunt.md` (this folder).

## 4 — Review + verify (M and L; S has no reviewer, and a verifier only for `ทำซ้ำ:`)
- Coder's `review:` path → `max-reviewer` (`SPEC:` · `คำขอ:` · `review:` · `report:`) and `max-verifier` (`SPEC:` · `คำขอ:` ·
  `ดูที่:` what the user opens — built app / live URL, not a dev server · `เทส: <project check order>` from CLAUDE.md / docs/playbook.md / the project's check skill; `เทสเต็ม:` only when a full suite is needed ·
  `proof: <dir>/proof.md` · `report:` · `ledger:` · `build:` when the project's build step applies) in **one message**. The verifier counts in the "tests/builds ≤ 2 at once" group. M with no screen and no user-visible C-id:
  no verifier — the coder runs the checks and writes `C<n> ผ่าน — <test>` into proof.md. The verifier (and the coder) write proof lines only by appending (`>>`) — the last line of a C-id wins.
- Results back: one arrived, the other still running and nothing is Core → end the turn with no call; send the
  coder **one** fix message with both. A Core `FIX` goes at once.
- Fix round: reviewer (the fix's review file) + verifier (`เฉพาะ: C3 C5`) in one message. Skip the re-review when
  every fix is non-`ร้ายแรง`, non-Core, ≤ ~30 lines with `แดงก่อนแก้:`. A reviewer `ชั้น 2: ยังไม่ได้ตรวจ` → the
  re-review is a full one.
- A rejected point: `ตัดสิน:` line with why, never dropped. `จุดที่ต้องระวังที่ยังไม่มีเทส` → a test to the same
  coder, or a C-id for the verifier. L touching permissions, money or deletion: review file → `max-advisor`.

## 5 — Proof, then close
- proof.md lines: `C<n> ผ่าน — <test name | ก่อน: x → หลัง: y (read via API/file) | shot path>`; an action C-id
  (กด ลาก บันทึก ส่งออก ลบ) needs "ก่อน … → หลัง …", a visual C-id with `อ้างอิง:` needs an image path; any other
  evidence names a test (`file::name`, `N passed`, `N/M`), a file path or a URL. The verifier's proof counts as looking; you look once (≤ 2 shots it names).
- `python3 "<skill folder>/scripts/max_lite.py" close <job> --turns <n>; git status --short | head` in **one** call,
  the report in the next message: refuses while a C-id has no proof line;
  prints `ยังไม่ได้ตรวจจริง:`, `MAX:`, `record=`, `ตัดออก:` and a worklog draft; writes `docs/max-jobs/<id>/` + `docs/roadmap.md`; appends to `history.md`; moves the job folder to `.max/closed/`.
  Check `ตัดออก:` + `git diff --stat docs/max-jobs`; `git add docs/max-jobs docs/roadmap.md` in the work's commit.
- `close` refuses any `ไม่ผ่าน`; a knowingly accepted failure: a `ตัดสิน: ยอมรับ C<n> ไม่ผ่าน — <why>` line in the ledger and append the proof line `C<n> ยังไม่ได้ตรวจ — ยอมรับ: <why>`, then `close`.
- A job dropped, or finished without `close`: `abandon <job> "<why>"` (logged in history.md, the job folder moved to
  `.max/closed/`; also writes the record + roadmap) so it stops showing as open.
- Main over budget → one line `เกินเพดาน: <cause>` in the ledger (close copies it to history).
- Project memory (SKILL.md 'Front door'; paste the worklog draft `close` printed and fill in ขั้นตอนที่ได้ผล): the job's entry in `docs/worklog.md` — the SPEC's `สมมติฐาน` that proved
  false, the `จุดที่ต้องระวัง` that bit, the `แจ้งซ้ำ` lines go under ที่ไม่ได้ผล/ระวัง — and the playbook updated, in the
  same commit as the work.
- Report = SKILL.md 'Front door' report. Commit / merge / deploy: SKILL.md 'Front door' decides.

**Repeat reports:** the user reports again something called done → `max_lite.py repeat <job> "<what> — <why it slipped>"` (not by hand), then SKILL.md §3. `stats` is the measure.

