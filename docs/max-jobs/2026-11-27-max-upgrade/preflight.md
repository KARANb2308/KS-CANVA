# preflight — max-upgrade (MAX v8.2 → v8.3)

คำขอ: "อัพเกรดให้ Max ฉลาดที่สุด เก่งที่สุด รอบคอบ ละเอียดที่สุด ทำงานได้รอบด้านที่สุด แต่กิน Token เวลา น้อยที่สุด บอกผมก่อนว่ามีอะไรบ้าง"
- P1 ฉลาด/เก่งที่สุด · P2 รอบคอบ/ละเอียดที่สุด · P3 รอบด้านที่สุด (งานหลายประเภท) · P4 กิน token/เวลาน้อยที่สุด · P5 บอกก่อนว่ามีอะไรบ้าง (= preflight นี้ ยังไม่แก้)

## แผนที่ (source = repo `plugins/max-v8/`, ~98 KB)
- skills/max/SKILL.md (10 KB, โหลดทุกงาน) · references/ml.md (12 KB, M/L) · scripts/max_lite.py (6.7 KB)
- agents: coder 11 KB · ui-coder 12.7 KB · verifier 10 KB · reviewer 7.4 KB · advisor 6.9 KB · hunter 3.9 KB · scout 1.8 KB
- skills/max-deep/SKILL.md (9 KB) — สำเนาเหมือนกันที่ `.claude/skills/max-deep/` (ต้องซิงก์ repo → plugin, cmp)
- hooks/require-worklog.mjs — สำเนาเหมือนกันที่ `.claude/hooks/` (ซิงก์, cmp)
- version: plugins/max-v8/.claude-plugin/plugin.json + .claude-plugin/marketplace.json (ต้องตรงกัน)

## ตรวจแล้วก่อนเริ่ม (สมมติฐาน)
- A1 ไม่จริง: ml.md:12 สั่ง `max_lite.py --dir <job>` แต่สคริปต์รับ `dir <job>` → exit 2 (รันจริงใน repo ทดสอบ) = ทุกงาน M/L เสีย turn แรก
- A2 จริง: มีเนื้อหาเฉพาะโปรเจกต์ Kedit 12 บรรทัด (ml.md 12 จุด, verifier 7, reviewer 3, hunter 2, advisor 1) → `.max/max-upgrade/kedit-lines.txt`
- A3 จริง: `close()` ใช้ `\bC(\d+)\b` → `C1ผ่าน` (ไทยติด) ไม่ถูกนับ → ปิดงานไม่ได้ทั้งที่ผ่าน (python -c ยืนยัน)
- A4 จริง: max-advisor `model: opus` แต่ description เขียน "Fable, most expensive"
- A5: ไม่มีเทสของ max_lite.py เลย

## ข้อเสนอ (ยังไม่ทำ)
ก. แก้ของพัง: 1) ml.md `--dir`→`dir` 2) close() regex ไทยติด 3) advisor model ให้ตรง description (ถามผู้ใช้)
ข. ลด token/เวลา: 4) ย้ายเนื้อหา Kedit ออกจากไฟล์ที่โหลดทุกงาน ไปไว้ `references/project-kedit.md` (อ่านเฉพาะเมื่อโปรเจกต์คือ Kedit) และให้ verifier/reviewer ใช้ "ขั้นตรวจของโปรเจกต์" จาก CLAUDE.md/playbook แทน
   5) `max_lite.py recall "<คำ>"` ค้น worklog+playbook คืนเฉพาะบรรทัดที่ตรง ≤ 40 บรรทัด
   6) `max_lite.py log <job>` ร่างบันทึก worklog จาก ledger+SPEC(คำขอ)+proof ให้ main เติมเฉพาะขั้นตอนที่ได้ผล/กับดัก
   7) กฎใช้ความจำลดงาน: playbook มีสูตร "ได้ผล" ตรงงาน + worklog มี file:line → ไม่ส่ง scout ซ้ำ
ค. ฉลาด/รอบด้าน: 8) ตารางเส้นทางตามประเภทงานใน Front door: ถาม/อธิบาย (ตอบตรง ไม่ใช่ MAX) · ข้อความ/เอกสาร · หน้าจอ · บั๊ก · audit · refactor → skill `simplify` · ความปลอดภัย → `security-review` · ความเร็ว (ตัวเลขก่อน→หลังบังคับ) · ข้อมูล/migration (Core, สำรองก่อน) · deploy/release (ถามก่อน + checklist)
ง. พิสูจน์: เทส max_lite.py (unittest stdlib) · `claude plugin validate .` · grep ไม่เจอ Kedit ในไฟล์ที่โหลดทุกงาน · ขนาดไฟล์ก่อน→หลัง · cmp ซิงก์ · (ทางเลือก) ลองงานจริง 1 งานเล็กใน repo ทดสอบ

## จุดที่ต้องระวัง
1. ตัดเนื้อหา Kedit แล้วงานในโปรเจกต์ Kedit ของผู้ใช้เสียขั้นตรวจเดิม → ต้องย้าย ไม่ลบ และชี้ทางให้เจอ
2. แก้ข้อความ skill แล้ว Claude ทำงานต่างไปโดยไม่ตั้งใจ (กฎหายจากการย่อ) → diff ทีละไฟล์ ห้ามเขียนทั้งไฟล์ใหม่ reviewer เทียบกฎเดิม↔ใหม่
3. ซิงก์ repo ↔ plugin หลุด (เคยเกิด: cp ผิดทาง) → set -e, cmp
4. version ไม่ตรง 2 ที่ → `/plugin marketplace update` ไม่เห็นเวอร์ชันใหม่
5. Cowork ไม่มี hook / Windows path → อย่าเพิ่มอะไรที่พึ่ง bash-only หรือ path เครื่อง
6. "ฉลาดที่สุด + ถูกที่สุด" ขัดกัน → วัดได้เฉพาะ: ขนาดที่โหลดต่องาน (bytes) และ turn ที่ประหยัด (A1) ส่วน "ฉลาดขึ้น" พิสูจน์ได้แค่จากงานทดลองจริง

## ตรวจที่นี่ไม่ได้
Cowork จริง (ไม่มี) · โปรเจกต์ Kedit ของผู้ใช้ (ไม่มีใน session) · ผลระยะยาวว่า token ลดจริงกี่ % ต่องาน

## ขนาด: M (≈10 ไฟล์ ข้อความ + สคริปต์ 1 ไฟล์มี logic, ไม่แตะ Core)

---
## อัปเดตหลังความเห็นที่สอง + คำตอบผู้ใช้ (ฉบับรออนุมัติ)
ตรวจซ้ำเองแล้ว: 1.2 จริง (`→C1, C2ทำซ้ำ` → ['1']) · 1.3 จริง (ไม่ผ่านแล้วต่อท้ายผ่าน → ปิดไม่ได้) · 1.5 จริง (ไฟล์ภาพใหม่ → UnicodeDecodeError) · 1.6 จริง · 1.8 จริง (advisor ไม่มี Bash)
A6 จริง: `claude -p --plugin-dir plugins/max-v8` รันได้ในเครื่องนี้ (1 turn, $0.14) → ทดลองงานจริงด้วยปลั๊กอินใหม่ได้

คำตอบผู้ใช้: advisor L = Opus · เพิ่มระดับ XL "MAX สุด" (เฉพาะเมื่อสั่ง) ใช้ Fable · Kedit → ไฟล์แยก · ลองจริง 1 งาน · ส่งใน PR #1

รับจากความเห็นที่สอง: 1.1/U1 1.2 1.3/U2 1.4/U3 1.5 1.6/U4 1.7 1.8 1.9/U9 1.10 1.11 1.12 1.13 1.14 U5 U6 U7 U8 + ข้อ 2 (ตารางย่อ ≤3 บรรทัด, skill เสริม "ถ้ามี")
ตัดสิน: ไม่ทำ recall (ข้อ 5) — grep รวมใน call เดิมอยู่แล้ว · ไม่ทำกฎข้าม scout (ข้อ 7) — มีกฎ <3 จุด Grep เองอยู่แล้ว · ไม่รวม coder/ui-coder — แค่ diff ส่วนซ้ำให้ตรงกัน

## แผน C-id
C1 ml.md เรียก `max_lite.py dir` ถูก (รันคำสั่งตามเอกสารได้ exit 0)
C2 close(): C-id ติดไทยนับครบทั้ง SPEC/proof · บรรทัดล่าสุดของ C-id ชนะ · หลักฐาน ≥ 8 ตัวอักษร
C3 diff: --stat + -U10 + `# ข้อความไทยใหม่:` · base ผิด → exit 1 · ไฟล์ binary ข้ามได้
C4 close พิมพ์ร่างบันทึก worklog (คำขอ/ไฟล์/ตรวจด้วย) ใน call เดิม
C5 hook ไม่บล็อกเมื่อมีงาน MAX เปิดอยู่ (ซิงก์ 2 สำเนา, cmp)
C6 brief ส่ง `lite:` path ให้ coder/ui-coder/verifier · โหมดกวาดมี `findings:`
C7 กฎที่ขัดกันแก้ทางเดียว: `ยาก:` = Agent model param · advisor เมื่อติดซ้ำได้ทุกขนาด · advisor มี Bash อ่านอย่างเดียว · budget ตรงกัน
C8 ระดับ XL "MAX สุด": เรียกเฉพาะคำสั่งผู้ใช้ · advisor (Fable) ทำ SPEC + รีวิว Core + รีวิว diff ทั้งงาน · budget XL
C9 Kedit 12 บรรทัด → references/project-kedit.md · ไฟล์ที่โหลดทุกงาน grep ไม่เจอ Kedit · มีบรรทัดชี้ให้เปิดเมื่อเป็นโปรเจกต์ Kedit
C10 §3b → references/hunt.md · description ย่อ + "ไม่ใช่สำหรับคำถาม/อธิบาย" · ตารางเส้นทาง ≤ 3 บรรทัด
C11 เอกสารตรงสคริปต์ (ml.md:46, :93, :96) · template (commit:, LESSONS) · ui-coder:11
C12 ขนาดที่โหลดต่องาน ลดลง (bytes ก่อน→หลัง: SKILL.md + ml.md + descriptions)
C13 เทส max_lite.py (unittest) ผ่าน · `claude plugin validate .` ผ่าน · version 8.3.0 ตรง 2 ที่ · cmp repo↔plugin
C14 ลองจริง: `claude -p --plugin-dir` ทำงาน M เล็ก 1 งานใน repo ทดสอบจนปิดงานได้ บันทึก turn + ค่าใช้จ่าย
C15 worklog + playbook บันทึก · commit/push เข้า branch เดิม (PR #1)
