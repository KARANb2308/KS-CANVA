# SPEC — max-upgrade (MAX v8.2 → v8.3)
BASE=fbe9f32 · ต้นฉบับ v8.2 สำรองไว้ที่ `.max/max-upgrade/before-v8.2/` · preflight: `.max/max-upgrade/preflight.md`

## เป้าหมาย
MAX v8.3: แก้ของพัง, ลดสิ่งที่โหลดต่องาน, เพิ่มระดับ XL "MAX สุด" (Fable) และเส้นทางตามประเภทงาน โดยกฎเดิมไม่หาย
คำขอ: "อัพเกรดให้ Max ฉลาดที่สุด เก่งที่สุด" → C7 C8 C10 · "รอบคอบ ละเอียดที่สุด" → C2 C3 C5 C13 C14 · "ทำงานได้รอบด้านที่สุด" → C8 C10 ·
"แต่กิน Token เวลา น้อยที่สุด" → C1 C4 C5 C6 C9 C10 C12 · "ลดความเสี่ยง ลดข้อเสียให้เหลือน้อยที่สุด" → C13 C16
ผู้ใช้เลือกแล้ว: advisor งาน L = opus (เดิม) · XL "MAX สุด" เรียกได้เฉพาะเมื่อผู้ใช้พิมพ์คำนี้ ใช้ Fable · Kedit → ไฟล์แยก

## แนวทาง + สิ่งที่ไม่ทำ
- แก้ทีละจุดด้วย Edit เท่านั้น **ห้ามเขียนไฟล์เดิมใหม่ทั้งไฟล์** (ไฟล์ใหม่ใช้ Write ได้) · ต้นฉบับจริง = `plugins/max-v8/` ·
  สำเนาใน `.claude/` คัดลอกจากต้นฉบับเท่านั้น (`cp plugins/... .claude/...` แล้ว `cmp`)
- ไม่ทำ: คำสั่ง `recall` · กฎข้าม scout · รวม coder กับ ui-coder · ไม่แตะไฟล์เว็บ (index.html, worker*.js, server.ps1, proxy-worker.js, *.bat, *.ps1)
- ไม่เปลี่ยนพฤติกรรมนอกที่ระบุใน C-id (สิ่งที่ "ย้าย" ต้องย้ายครบ ไม่ใช่ลบ)

## สมมติฐาน (ตรวจแล้วโดย main ทุกข้อจริง — coder รันซ้ำก่อน T1 ได้)
- A1 `grep -c 'max_lite.py" --dir' plugins/max-v8/skills/max/references/ml.md` → 1
- A2 `wc -l < .max/max-upgrade/kedit-lines.txt` → 12 (รายการบรรทัด Kedit ที่ต้องย้าย)
- A3 `cmp .claude/hooks/require-worklog.mjs plugins/max-v8/hooks/require-worklog.mjs` → เหมือน
- A4 `cmp .claude/skills/max-deep/SKILL.md plugins/max-v8/skills/max-deep/SKILL.md` → เหมือน
- A5 `grep -h '"version"' plugins/max-v8/.claude-plugin/plugin.json .claude-plugin/marketplace.json` → 8.2.0 ทั้งคู่

## รายการครอบคลุม
- C1 ml.md สั่ง `max_lite.py" dir <job> --size ...` (ไม่มี `--dir`) และคำสั่งตามเอกสาร exit 0
- C2 close(): regex C-id `(?<![A-Za-z0-9_])C(\d+)(?![0-9])` ทั้ง SPEC และ proof · **บรรทัด proof สุดท้าย** ของแต่ละ C-id ตัดสิน · ผ่านต้องมีหลักฐานหลัง `—`/`-` ยาว ≥ 8 ตัวอักษร · พฤติกรรมเดิมคงอยู่ (ขาด/ไม่ผ่าน → exit 1, ยังไม่ได้ตรวจ → แสดงแต่ปิดได้)
- C3 diff: ไฟล์ review เริ่มด้วย `# stat` (git diff --stat) → `# ข้อความไทยใหม่:` (บรรทัด `+` ที่มีอักษรไทย U+0E00–U+0E7F รูปแบบ `<file>: <ข้อความ>` หรือ `ไม่มี`) → diff `-U10` → `=== NEW FILE <p> ===` · ไฟล์ใหม่ที่ไม่ใช่ utf-8 → `=== NEW FILE <p> (binary, <n> bytes) ===` ไม่ล้ม · base ใช้ไม่ได้ (`git rev-parse --verify <base>^{commit}` ล้ม) → stderr + exit 1
- C4 close สำเร็จ → พิมพ์ร่างบันทึก (ก่อน archive) รูปแบบ interface ข้างล่าง
- C5 hook: มีโฟลเดอร์งานเปิดใน `.max/` (ไม่ใช่ `closed`, มี `ledger.md`) → exit 0 เงียบ · กรณีเดิมทั้งหมดยังเหมือนเดิม · 2 สำเนาเหมือนกัน (cmp)
- C6 brief ของ coder, ui-coder, verifier มี `lite: <path เต็มของ max_lite.py>` และ agent ใช้ค่านั้น (ไม่มี → Glob `**/skills/max/scripts/max_lite.py` ในปลั๊กอิน max-v8) · brief โหมด `กวาด:` มี `findings:`
- C7 กฎตรงกันทางเดียว: `ยาก:` = ส่ง Agent tool parameter `model: "opus"` ให้ max-coder (ไม่ใช่ข้อความใน brief) · §3 ติดซ้ำ → advisor ได้ทุกขนาด (ข้อ "No advisor on S/M" ยกเว้น §3) · advisor มี Bash (อ่านอย่างเดียว: git log/show/diff, grep) · budget: SKILL.md = max_lite (S10 M25 L50 XL70) และ max-deep บอก "+10 สำหรับขั้นตรวจก่อนเริ่ม"
- C8 ระดับ XL "MAX สุด" ใน SKILL.md (แถวในตารางขนาด + เงื่อนไข): เฉพาะเมื่อผู้ใช้พิมพ์ "MAX สุด" ห้ามเลือกเอง · ทำเหมือน L ทุกด่าน + เรียก max-advisor ด้วย Agent `model: "fable"` สำหรับ SPEC, รีวิว Core และรีวิว diff ทั้งงานตอนท้าย · advisor ≤ 5 ครั้ง · `max_lite.py dir --size XL` budget 70 · description ของ skill max และ README บอกคำนี้
- C9 12 บรรทัด Kedit (kedit-lines.txt) + `build: cd frontend && npm run build` ย้ายไป `skills/max/references/project-kedit.md` (เนื้อหาครบ) · ไฟล์ที่โหลดทุกงาน (SKILL.md, ml.md, agents/*.md) `grep -ci kedit` = 0 ยกเว้นบรรทัดชี้ 1 บรรทัดใน SKILL.md: "โปรเจกต์ Kedit (มี skill kedit-verify) → อ่าน references/project-kedit.md" · agent ที่เคยอ้าง Kedit ให้ใช้ "ขั้นตรวจของโปรเจกต์จาก CLAUDE.md / docs/playbook.md / skill ตรวจของโปรเจกต์"
- C10 §3b ของ ml.md ย้ายไป `skills/max/references/hunt.md` (ครบ) + ml.md เหลือบรรทัดชี้ 1 บรรทัด · description ของ skill max บอก "ไม่ใช่สำหรับคำถาม/อธิบาย — ตอบตรง" · ตารางเส้นทางประเภทงาน ≤ 3 บรรทัดใน SKILL.md (ความปลอดภัย → skill security-review ถ้ามี · ทำให้เร็ว → ตัวเลขก่อน→หลังบังคับ · ย้ายข้อมูล/migration → Core สำรองก่อน · deploy/release → ถามก่อน · refactor → skill simplify ถ้ามี) · description agent ทั้ง 7 ย่อ (ยังบอกว่าใช้เมื่อไหร่)
- C11 เอกสารตรงสคริปต์: ml.md หัว ledger เขียนโดยสคริปต์ (ไม่ใช่ main) · close ย้ายโฟลเดอร์ไป `.max/closed/` (ไม่ใช่ "clears" / `closed-ledger.md`) · worklog.template `commit:` → `commit: ดู git log (commit เดียวกับบันทึกนี้)` · LESSONS.template บรรทัด hook → ไม่อ้าง hook · ui-coder:11 ไม่สั่ง Read ไฟล์อื่นซ้ำ และไม่ขัดกับ :21 · verifier เขียน proof ด้วยการต่อท้าย `>>` เท่านั้น (บรรทัดล่าสุดชนะ) ที่ verifier และ ml.md
- C12 ขนาดที่โหลดต่องาน M ลดลง: `wc -c SKILL.md ml.md` < 22,260 และ descriptions (`grep -h '^description:' agents/*.md skills/*/SKILL.md | wc -c`) < 3,202
- C13 `python3 plugins/max-v8/skills/max/scripts/test_max_lite.py` ผ่านทุกเทส (ครอบ C1–C5 ทุกกรณีข้างบน + hook ผ่าน node) · `claude plugin validate .` ผ่าน · version 8.3.0 ทั้ง 2 ที่ · cmp สำเนา `.claude/` = ต้นฉบับ · `node --check` hook
- C14 ลองจริง: `claude -p --plugin-dir plugins/max-v8` ทำงาน M เล็ก 1 งานใน git repo ทดสอบ (scratchpad) จนปิดงานด้วย close ได้ · บันทึก num_turns + total_cost_usd
- C15 บันทึกงานใน docs/worklog.md + playbook · commit/push branch เดิม (PR #1) — main ทำ
- C16 กฎไม่หาย: รายการกฎ (บรรทัดที่เป็นข้อบังคับ) ใน BASE เทียบ v8.3 ทุกข้อ "อยู่เหมือนเดิม / ย้ายไป <ไฟล์> / ตั้งใจเปลี่ยน (C-id)" — reviewer ตรวจ

## interface
- `max_lite.py dir <job> --size S|M|L|XL` → `dir=`, `base=`, `budget=<n> main turns (<size>)`; BUDGET = S10 M25 L50 XL70
- `max_lite.py diff <base> --job <job> [files...]` → `review=<path>` `lines=<n>`; รูปแบบไฟล์ตาม C3
- `max_lite.py close <job>` สำเร็จ พิมพ์ (ต่อจาก `MAX:` เดิม ก่อน `archived=`):
```
--- ร่างบันทึก docs/worklog.md (เติม ขั้นตอนที่ได้ผล) ---
## <YYYY-MM-DD> — <job>
- คำขอ: <ข้อความหลัง "คำขอ:" บรรทัดแรกใน SPEC | (ไม่พบใน SPEC)>
- สถานะ: เสร็จ
- ไฟล์: <ชื่อไฟล์จาก git diff --stat <BASE จากบรรทัดแรก ledger> คั่นด้วย ", " | (ไม่มี base)>
- ขั้นตอนที่ได้ผล: (เติม)
- ที่ไม่ได้ผล / ต้องระวัง: <บรรทัด ledger ที่ขึ้นต้น ตัดสิน: / แจ้งซ้ำ: / เกินเพดาน: | (เติม)>
- ตรวจด้วย: <บรรทัด proof สุดท้ายของแต่ละ C-id คั่นด้วย " · ">
```
- hook: ก่อนนับไฟล์ ถ้า `.max/*/ledger.md` มีอยู่ (ยกเว้น `.max/closed/`) → exit 0
- brief: `lite: <path>` (main ส่งทุก brief ของ coder/ui-coder/verifier)

## กฎที่ผูก
stdlib Python เท่านั้น ใช้ได้ทั้ง Windows/macOS/Linux · ไม่มี path ของเครื่องใดเครื่องหนึ่ง · ไม่มีอะไรใหม่ที่พึ่ง hook (Cowork ไม่มี hook) · ข้อความไทยสั้น ไม่มีศัพท์เทคนิคเกินจำเป็น · `set -e` / `&&` ในสคริปต์หลายขั้น

## จุดที่ต้องระวัง
1. ย่อ/ย้ายแล้วกฎหาย (C16)
2. สำเนาไม่ตรงต้นฉบับ (เคยเกิด) — cp ทิศเดียว + cmp
3. version 2 ที่ไม่ตรง
4. close เปลี่ยน exit code / พิมพ์ร่างแล้ว archive ไม่ทำ
5. hook เงียบตลอดไปเพราะงานค้างไม่ปิด — `status` ยังแสดงงานค้าง, รายงานต้องบอก

## tasks
กลุ่ม A (max-coder 1) — ไฟล์: `skills/max/scripts/max_lite.py`, ใหม่ `skills/max/scripts/test_max_lite.py`, `hooks/require-worklog.mjs` (+สำเนา `.claude/hooks/`)
- T1 close (C2 C4) · T2 diff (C3) · T3 dir XL (C7 budget, C8) · T4 hook (C5) + เทสใน test_max_lite.py ที่รัน node กับ hook ใน git repo ชั่วคราว
- เทส: `python3 plugins/max-v8/skills/max/scripts/test_max_lite.py`
กลุ่ม B (max-coder 2) — ไฟล์: `skills/max/SKILL.md`, `skills/max/references/{ml.md,hunt.md(ใหม่),project-kedit.md(ใหม่),worklog.template.md,LESSONS.template.md}`, `agents/*.md`, `skills/max-deep/SKILL.md` (+สำเนา), `README.md`, `.claude-plugin/plugin.json`, `./.claude-plugin/marketplace.json`
- T5 ml.md: C1, C6 (brief), C7 (`ยาก:`), C9, C10 (§3b→hunt.md), C11 · T6 SKILL.md: C7, C8, C9 บรรทัดชี้, C10 · T7 agents/*.md: C6, C7 (advisor Bash + description), C9, C10 descriptions, C11 (ui-coder, verifier `>>`), reviewer ให้ตรงรูปแบบ diff C3 · T8 templates C11, max-deep budget "+10" (C7) + cp/cmp, README (C8), version 8.3.0 ทั้ง 2 ที่
- เทส: `grep`/`wc`/`cmp` ตาม C1 C9 C10 C12 C13 + `cd . && claude plugin validate .`

## สิ่งที่ห้ามแตะ
ไฟล์เว็บทั้งหมด · `docs/` · `CLAUDE.md` · `.max/max-upgrade/before-v8.2/` · `.claude/settings.json`
