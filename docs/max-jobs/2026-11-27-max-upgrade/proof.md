C1 ผ่าน — grep -c 'max_lite.py" --dir' ml.md → 0; ml.md:12 ใช้ `max_lite.py" dir <job> --size M|L`; รันจริง `dir jobx --size M` exit 0 (dir=/base=/budget=25)
C2 ผ่าน — test_max_lite 20/20 OK (test_last_line_wins_*, test_c1_not_matched_by_c10_or_prefix, test_short_evidence_rejected); รันเองในสำเนา: C2 ผ่านแล้ว ไม่ผ่านทีหลัง → exit 1, ไม่ผ่านแล้วผ่านทีหลัง → ปิดได้, หลักฐาน "ok" สั้นเกิน → exit 1
C3 ผ่าน — รัน diff เอง: ไฟล์ review ขึ้น `# stat` → `# ข้อความไทยใหม่:` (t.txt: สวัสดี) → diff; base ผิด → stderr "base ใช้ไม่ได้: nosuch" exit 1; test_format/test_binary_new_file/test_bad_base ผ่าน
C4 ผ่าน — close สำเร็จพิมพ์ "--- ร่างบันทึก docs/worklog.md (เติม ขั้นตอนที่ได้ผล) ---" ก่อน archived= (เห็นใน transcript trial 13ff6429 และ test_draft_and_archive/test_draft_without_request_or_base)
C5 ผ่าน — test_open_job_silent / test_closed_job_still_blocks / test_blocks_baseline / test_stop_hook_active / test_no_worklog_silent ผ่าน (รัน node จริง); cmp .claude/hooks/require-worklog.mjs ต้นฉบับ = เหมือน; node --check ผ่าน
C6 ผ่าน — ml.md:52,67 มี `lite: <full path of max_lite.py>` + Glob fallback; max-coder:33, max-ui-coder:44 ใช้ "<path จาก lite:>"; max-verifier:13 ได้ `lite:`; max-hunter:11 + hunt.md มี `findings:`; verifier กวาด: มี findings:
C7 ผ่าน — ml.md:53 `ยาก:` → Agent parameter model: "opus"; SKILL.md:116 "No advisor on S/M unless the user asks — except §3 Stuck (any size)"; max-advisor tools: Read, Grep, Glob, Write, Bash; SKILL.md:87 budget S10 M25 L50 XL70; max-deep:95 "+10 for the pre-check"; รัน dir --size M → 25, XL → 70
C8 ผ่าน — SKILL.md:72 แถว XL "only when the user types MAX สุด — never pick it yourself" + advisor model: "fable" (SPEC, Core, whole-diff), advisor ≤5 (:116); description บรรทัด 3 มี "MAX สุด"; README:7 มีหัวข้อ MAX สุด; dir --size XL → budget=70 (ยังไม่ได้ลองเรียก fable จริง)
C9 ผ่าน — project-kedit.md 18 บรรทัด มีครบ (เทส:/build: cd frontend && npm run build/sweep list/verifier steps); grep -c 'kedit|Kedit|KEDIT' ml.md=0, agents/*=0 ทั้ง 7, SKILL.md=1 (บรรทัดชี้ :19); NotebookEdit ที่ตรงตามตัดสิน ledger ไม่นับ
C10 ผ่าน — hunt.md 13 บรรทัดมี steps 1-4 ครบ (เทียบ before-v8.2 ml.md §3b; คำเฉพาะ Kedit ถูกทำให้ทั่วไป + ชี้ project-kedit.md); ml.md:62 เหลือบรรทัดชี้ 1 บรรทัด; description skill max มี "Not for questions or explanations - answer directly"; SKILL.md:74-75 task routes 2 บรรทัด (ครบ 5 เส้นทาง); description agent ทั้ง 7 ≤ ~200 ตัวอักษร ยังบอกว่าใช้เมื่อไหร่
C11 ผ่าน — ml.md:44 "header line is written by max_lite.py dir, not by main"; ml.md:83 ย้ายไป .max/closed/ (ไม่มี clears/closed-ledger); worklog.template:17 "commit: ดู git log (commit เดียวกับบันทึกนี้)"; LESSONS.template ไม่มีคำว่า hook; ui-coder:11 "ไม่ต้อง Read ไฟล์อื่นซ้ำ" ไม่ขัด :21; verifier:26,33 และ ml.md:68 ใช้ `>>` เท่านั้น
C12 ผ่าน — wc -c SKILL.md+ml.md = 11119+11083 = 22202 < 22260 (ผ่านเฉียด ห่าง 58 ตัวอักษร); descriptions = 2406 < 3202
C13 ผ่าน — test_max_lite 20/20 OK; claude plugin validate . = "Validation passed with warnings" (คำเตือนเดียว: README ไม่มีบรรทัดติดตั้ง ไม่ใช่ข้อผิดพลาด); node --check ผ่าน; cmp .claude/hooks + .claude/skills/max-deep เหมือนต้นฉบับ; version 8.3.0 ทั้ง plugin.json และ marketplace.json
C14 ผ่าน — claude -p --plugin-dir จริงใน trial-v83: is_error=false num_turns=28 total_cost_usd=1.2575 duration_ms=167075 (wall 237s); .max/closed/slugify-202611270531 มี SPEC (C1-C6) ledger proof review.diff; history.md "ปิด · C 6 · ยังไม่ได้ตรวจ 0"; transcript มี "ร่างบันทึก…" ก่อน archived=; unittest ของ repo 20/20 OK; subagent ใช้ max-coder x2 max-reviewer x2 (ไม่มี verifier)
C15 ยังไม่ได้ตรวจ — main ทำเอง
C16 ยังไม่ได้ตรวจ — reviewer ตรวจ
C2 ผ่าน — รอบแก้ 1: test_max_lite.py Ran 23 tests in 3.589s  OK 
C4 ผ่าน — รอบแก้ 1: เทสร่างบันทึก (ไฟล์ untracked, ไม่มีไฟล์เปลี่ยน) อยู่ใน Ran 23 tests in 3.589s  OK 
C9 ผ่าน — รอบแก้ 1: grep kedit|Kedit|KEDIT ใน ml.md+agents = plugins/max-v8/skills/max/references/ml.md:0 plugins/max-v8/agents/max-advisor.md:0 plugins/max-v8/agents/max-coder.md:0 plugins/max-v8/agents/max-hunter.md:0 plugins/max-v8/agents/max-reviewer.md:0 plugins/max-v8/agents/max-scout.md:0 plugins/max-v8/agents/max-ui-coder.md:0 plugins/max-v8/agents/max-verifier.md:1 ; verifier.md อ่าน kedit: จาก brief
C12 ผ่าน — รอบแก้ 1: SKILL.md+ml.md 22167 B < 22260 · descriptions 2470 B < 3202
C13 ผ่าน — รอบแก้ 1: tests Ran 23 tests in 3.589s  OK  · Validation passed with warnings · cmp same
C16 ผ่าน — reviewer ตรวจกฎ v8.2→v8.3 เทียบไฟล์จริง: ทุกข้ออยู่/ย้ายครบ (hunt.md, project-kedit.md)/เปลี่ยนตาม C7 C11; re-review รอบแก้ 1 VERDICT: PASS
C8 ผ่าน — XL: dir --size XL budget 70 (verifier) · Agent(model: "fable") เรียกได้จริง ตอบ ok · fallback opus อยู่ใน SKILL.md
C15 ผ่าน — worklog + playbook อัปเดต commit f360fc4 push ไป ccr-dc26de92-82bie5 (PR #1)
