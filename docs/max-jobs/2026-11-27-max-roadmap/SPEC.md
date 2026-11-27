# SPEC — max-roadmap (MAX v8.4, ขนาด XL)

ย่อ path: `S/` = `plugins/max-v8/skills/max/` · `LITE` = `S/scripts/max_lite.py` · `TEST` = `S/scripts/test_max_lite.py`

## แผน (ภาษาคน)
- **จะเปลี่ยนอะไรให้คุณ:** MAX จะมี "แผนที่งาน" ไฟล์เดียว (`docs/roadmap.md`) บอกว่าตอนนี้ทำอะไรอยู่ ถึงด่านไหน ติดใคร งานถัดไปคืออะไร และทุกงานจะมี "แฟ้มงาน" ถาวรใน `docs/max-jobs/` (แผน + หลักฐาน) ที่ commit ไปกับงาน เปิด session ใหม่ก็ไม่หาย
- **ขั้นตอน:** 1) เพิ่มคำสั่งในสคริปต์ของ MAX (แผนที่ · แฟ้มงาน · ทำต่อ · ตรวจซ้ำ · สถิติ) 2) แก้คู่มือของ MAX ให้ใช้คำสั่งพวกนี้ + โชว์แผนภาษาคนก่อนลงมือ (M ทำต่อเลย, L/XL รอ "ลุย") 3) ใส่แผนที่งานของ repo นี้ + แฟ้มงานของ v8.3 ย้อนหลัง 4) ลองจริง 3 รอบ
- **พิสูจน์ยังไง:** เทสอัตโนมัติของสคริปต์ (เดิม 29 ต้องผ่านครบ + ใหม่) · ลองจริง: ให้ MAX ทำงานขนาด M → ลบโฟลเดอร์ชั่วคราว `.max/` ทิ้ง → สั่ง "ตรวจซ้ำ" และ "ทำต่อ" ต้องทำได้จากไฟล์ที่ commit เท่านั้น → แกล้งทำพัง 1 จุด แล้ว "ตรวจซ้ำ" ต้องบอกว่าข้อไหนพัง ตั้งแต่ commit ไหน
- **ความเสี่ยง:** แฟ้มงานถูก commit จึงต้องไม่มีรหัสผ่าน/ข้อมูลลูกค้า (สคริปต์ตัดค่าที่ดูเป็นความลับออกให้ แต่ชื่อลูกค้าสคริปต์ดูไม่ออก ต้องคุมด้วยกฎ) · ทดสอบบน Windows จริงไม่ได้ในเครื่องนี้
- **ไม่ทำ:** ไม่แก้ตัวเว็บ/ระบบออนไลน์ · ไม่แก้ host `dbp.co.th` (แค่ใส่ในแผนที่เป็นงานถัดไป) · ไม่แก้ `CLAUDE.md` (ต้องให้คุณอนุมัติเอง)

## 1. เป้าหมาย
MAX จำงานข้าม session ได้จากไฟล์ที่ commit: รู้ว่าอยู่ด่านไหน ทำต่อได้ ตรวจงานเก่าซ้ำได้ และวัดได้ว่าดีขึ้นจริง

เกณฑ์รับ (ทุกข้อ = C-id ในข้อ 3):
- หลัง `rm -rf .max` คำสั่ง `status` + `resume` ทำงานที่ค้างต่อได้ และ `recheck` ตรวจงานที่ปิดแล้วได้ (เห็นทันทีหลังติดตั้ง v8.4)
- ผู้ใช้เปิด `docs/roadmap.md` เห็น 4 หัวข้อ ไม่เกิน ~60 บรรทัด, เปิด `docs/max-jobs/<id>/` เห็นแผน + หลักฐานของงาน
- งาน M+ ผู้ใช้เห็นแผนภาษาคน 5–10 บรรทัดก่อนลงมือ; L/XL หยุดรอ "ลุย"; ทุกด่านมีความคืบหน้า 1 บรรทัด

คำขอ: "ผมต้องการให้ Max ผมเก่งที่สุดในโลก รอบคอบ เก่ง วางแผนชัดเจน ผมสามารถกลับมาตรวจซ้ำ ละเอียดมากขึ้น มีแผนที่นำทางไว้สำหรับทำงานต่อได้ไวง่าย"
- "เก่งที่สุดในโลก / เก่ง" (วัดได้ ไม่ใช่คำอ้าง) → C16, C15, C23, C24, C25
- "รอบคอบ" → C9, C10, C11, C12, C14, C20, C26
- "วางแผนชัดเจน" → C17, C18
- "กลับมาตรวจซ้ำ" → C8, C13, C14, C23, C25 · "ละเอียดมากขึ้น" → C27
- "แผนที่นำทาง" → C1, C2, C3, C4, C5, C22 · "ทำงานต่อได้ไวง่าย" → C6, C7, C24
- ข้อบังคับของงาน → C19, C20, C21

## 2. แนวทาง + สิ่งที่ไม่ทำ
ตามแนวทางที่เลือก 5 ข้อ โดยปรับให้คมขึ้น 6 จุด (เหตุผลต่อท้าย):
1. **แฟ้มงานถูกเขียนทุกด่าน ไม่ใช่เฉพาะตอน close** (`gate` คัดลอก SPEC/ledger/proof/preflight เข้า `docs/max-jobs/<id>/`) — เพราะ cloud ล้าง `.max/` กลางงาน ถ้ารอ close งานที่ค้างจะไม่มี SPEC ให้ "ทำต่อ"; เพิ่มคำสั่ง `resume` กู้ `.max/<job>/` กลับจากแฟ้ม
2. **id แฟ้ม = `<วันเริ่ม>-<job>`** (ไม่ใช่วันปิด) — id ต้องคงที่ตั้งแต่ด่านแรก
3. **แผนภาษาคนเป็นหัวข้อแรกของ SPEC.md** (`แผน (ภาษาคน)`) ไม่แยกไฟล์ — advisor/main เขียนอยู่แล้ว, เข้าแฟ้มงานอัตโนมัติ, `gate <job> plan` พิมพ์ให้ main ส่งต่อโดยไม่ต้องอ่าน SPEC
4. **`docs/roadmap.md` ใช้ `merge=union`** (driver ที่ git มีในตัว ผ่าน `.gitattributes`) + สคริปต์ล้างบรรทัดซ้ำ/เครื่องหมาย conflict เองทุกครั้งที่เขียน — สอง session แก้พร้อมกันจึงไม่ชน
5. **สถิติอ่านจาก `docs/max-jobs/*/record.md` เท่านั้น** — `.max/history.md` หายใน cloud; "แจ้งซ้ำ" ของงานที่ปิดแล้วเขียนลงแฟ้มด้วยคำสั่ง `repeat`
6. **กฎของ verifier สำหรับตรวจซ้ำอยู่ใน `references/recheck.md`** (brief ชี้ไป) — ไม่แก้ไฟล์ agent (ท้ายบรรทัด LF/CRLF ผสม) และไม่แก้ `max-deep` (สำเนา 2 ที่ต้องเหมือนกัน)

ไม่ทำ: งาน S ไม่ขึ้นแผนที่และไม่มีแฟ้ม (worklog พอ) · ไม่คัดลอก review.diff / รูป / report ของ coder เข้าแฟ้ม · ไม่แก้ hook, agents, `max-deep`, `CLAUDE.md` · ไม่ push/merge PR #1 · ไม่แก้ `dbp.co.th`

## สมมติฐาน (coder รันก่อน T1; ไม่ตรง → `NEEDS_CONTEXT` พร้อมค่าจริง)
- A1 `.max/` ถูก ignore: `git check-ignore -v .max/x` → `.gitignore:6:.max/`
- A2 hook ไม่สนไฟล์ใต้ `docs/` (จึงไม่ต้องแก้ hook): `grep -n "IGNORE = " plugins/max-v8/hooks/require-worklog.mjs` → มี `/^docs\//`
- A3 เทสเดิมผ่าน 29: `python3 plugins/max-v8/skills/max/scripts/test_max_lite.py 2>&1 | tail -3` → `Ran 29 tests` + `OK`; และไฟล์เทสรันคลาสเดียวได้: `tail -3 plugins/max-v8/skills/max/scripts/test_max_lite.py` → มี `unittest.main()`
- A4 ขนาดตอนนี้: `cat plugins/max-v8/skills/max/SKILL.md plugins/max-v8/skills/max/references/ml.md | wc -c` → `22236`
- A5 สำเนาเหมือนกัน: `cmp plugins/max-v8/hooks/require-worklog.mjs .claude/hooks/require-worklog.mjs && cmp plugins/max-v8/skills/max-deep/SKILL.md .claude/skills/max-deep/SKILL.md && echo SAME` → `SAME`
- A6 งานเก่ายังอยู่ในเครื่องนี้: `ls .max/closed/max-upgrade-202611270541/{SPEC,proof,ledger,preflight}.md` → ครบ 4 ไฟล์ (ไม่ครบ → T9 ข้าม backfill แล้วรายงาน)
- A7 ยังไม่มีไฟล์ปลายทาง: `ls docs/roadmap.md docs/max-jobs .gitattributes 2>&1` → ไม่พบทั้ง 3 (มี `.gitattributes` อยู่แล้ว → ต่อท้าย ห้ามเขียนทับ)
- A8 เทสเดิมที่ผูกกับ output ของ `dir`/ร่าง worklog: `grep -n "budget=\|ไม่มีไฟล์เปลี่ยน\|ไม่มีงาน MAX ค้าง" plugins/max-v8/skills/max/scripts/test_max_lite.py` → อ่านทุกจุดก่อนเพิ่มบรรทัด output
- A9 version ตอนนี้: `grep -n '"version"' plugins/max-v8/.claude-plugin/plugin.json .claude-plugin/marketplace.json` → `8.3.0` ทั้งสอง
- A10 ledger ของงานนี้เป็นหัวแบบ v8.3 (ไม่มี `record=`): `head -1 .max/max-roadmap/ledger.md` → มี `start=2026-11-27` ไม่มี `record=`
- A11 (สำหรับด่านลองจริง) `claude --version` รันได้ และ `claude plugin validate .` ผ่าน

## 3. รายการครอบคลุม
- C1 `dir <job> --size M|L|XL` สร้าง/อัปเดต `docs/roadmap.md` (4 หัวข้อ, 1 บรรทัดใน "กำลังทำ"); `--size S` ไม่สร้างอะไรใน `docs/`
- C2 `gate` อัปเดตบรรทัดของงานนั้นบรรทัดเดียว + พิมพ์ความคืบหน้า 1 บรรทัด
- C3 `close` ย้ายงานไป "เสร็จล่าสุด" พร้อมลิงก์แฟ้ม; เหลือ ≤ 10 บรรทัด (แฟ้มเก่าไม่ถูกลบ)
- C4 `abandon` ลงแผนที่เป็น `ทิ้ง: <เหตุผล>` (มี SPEC → มีแฟ้ม)
- C5 `todo next|wait|done` จัดการ "ถัดไป"/"รอผู้ใช้"; เต็มเพดานแล้วปฏิเสธ ไม่ตัดของเก่าทิ้งเงียบๆ
- C6 `status` พิมพ์ กำลังทำ / รอผู้ใช้ / ถัดไป 3 อันดับแรก + งานเปิดใน `.max/` + `กู้ได้` / `หาย` / `ซ่อมแผนที่`
- C7 `resume <job>` กู้ `.max/<job>/` จากแฟ้มหลัง `.max/` ถูกลบ และไม่เขียนทับไฟล์ที่มีอยู่
- C8 แฟ้มงาน `docs/max-jobs/<id>/` มี SPEC.md, ledger.md, proof.md, preflight.md (ที่มี) + `record.md` ทั้งตอน `gate` และ `close`
- C9 แฟ้มงานไม่มีค่าความลับ (ตัดเป็น `[ตัดออก]`), ไม่มี path เต็มของเครื่อง, มีเฉพาะไฟล์ใน whitelist
- C10 `close` ล้มกลางทางแล้วรันซ้ำ → ได้ผลเท่ากับปิดรอบเดียว; `close` ที่ถูกปฏิเสธไม่เขียนอะไรเลย
- C11 แผนที่ที่ถูก merge จากสอง session: ไม่ conflict (`merge=union`), ไม่มีบรรทัดซ้ำ/เครื่องหมาย conflict หลังเขียนครั้งถัดไป
- C12 งานเก่าใน `.max/closed/` ที่ไม่มีแฟ้ม: `recheck` ใช้ได้ถ้าโฟลเดอร์ยังอยู่, ไม่อยู่ → ข้อความชัดเจน exit 1; `backfill` สร้างแฟ้มย้อนหลัง
- C13 `recheck <job>` พิมพ์ทุก C-id พร้อมหลักฐานเดิม + ไฟล์ของงาน + ช่วง commit
- C14 `recheck <job> --sum` สรุป ยังผ่าน / พังแล้ว / ตรวจไม่ได้, ปฏิเสธถ้าไม่ครบทุก C-id, ข้อที่พังขึ้น "ถัดไป" เป็น P1
- C15 `repeat <job> "<ข้อความ>"` บันทึก `แจ้งซ้ำ:` ได้ทั้งงานเปิดและงานที่ปิดแล้ว
- C16 `stats` พิมพ์ จำนวนงาน · ขนาด · แจ้งซ้ำ · C-id ที่ยังไม่ได้ตรวจ · เกินเพดาน · turn เฉลี่ย · ตรวจซ้ำ
- C17 แผนภาษาคน: SPEC ขึ้นต้นด้วยหัวข้อ `แผน (ภาษาคน)`; `gate <job> plan` พิมพ์หัวข้อนั้น, ไม่มี → exit 1
- C18 คู่มือ (SKILL.md + ml.md): M โชว์แผนแล้วทำต่อ · L/XL โชว์แล้วรอ "ลุย" (มาจาก max-deep ที่อนุมัติ preflight แล้ว ไม่ถามซ้ำ) · `gate` ทุกด่าน · "ทำต่อ" = `status` → `resume` · description มีคำเรียก `ทำต่อ` `ตรวจซ้ำ`
- C19 ไฟล์ใหม่ `S/references/roadmap.md` และ `S/references/recheck.md` (โหลดเฉพาะโหมดนั้น); ทุกคำสั่งที่เขียนไว้รันได้จริง
- C20 เทสเดิม 29 ผ่านครบ + เทสใหม่ทุกคลาสผ่าน; ขนาด `SKILL.md + ml.md` ≤ 23,736 bytes
- C21 `cmp` สำเนา 2 คู่ยังเหมือนเดิม · version `8.4.0` ทั้ง 2 ไฟล์ · `claude plugin validate .` ผ่าน
- C22 repo นี้มี `docs/roadmap.md` (PR #1 รอผู้ใช้ · dbp.co.th ถัดไป P1 · v8.3 เสร็จ), `.gitattributes`, แฟ้มย้อนหลัง `max-upgrade`, แฟ้มของงานนี้เอง
- C23 ลองจริง ก: `claude -p` งาน M → ลบ `.max/` → `claude -p "ตรวจซ้ำ <job>"` สำเร็จ ทุก C-id `ยังผ่าน`
- C24 ลองจริง ข: งานค้างที่ด่าน สร้าง + ลบ `.max/` → `claude -p "ทำต่อ"` ทำจนปิดงานได้
- C25 ลองจริง ค: แกล้งพัง 1 จุด + commit → "ตรวจซ้ำ" รายงาน `พังแล้ว` พร้อม commit ที่ทำพัง และขึ้น "ถัดไป"
- C26 ไม่มี path เครื่อง / ข้อมูลลูกค้า / ความลับ ใน `plugins/max-v8/` และ `docs/max-jobs/` (grep)
- C27 "ตรวจซ้ำละเอียด" = ตรวจซ้ำ + `max-hunter` บนไฟล์ของงาน + skill `code-review` ระดับ high (เขียนใน recheck.md; ลองจริงเฉพาะส่วน hunter ใน repo ทดลองของ C25 ถ้างบพอ ไม่ได้ลอง → `ยังไม่ได้ตรวจ`)

## 4. interface (ค่าที่ต้องตรงกันทุก task — เขียนที่นี่ที่เดียว)
**Path:** แผนที่ `docs/roadmap.md` · แฟ้ม `docs/max-jobs/<id>/` · `<id>` = `<YYYY-MM-DD ของ start= ในหัว ledger>-<job>`; ชนกับแฟ้มที่ `สถานะ` ปิด/ทิ้งแล้ว → ต่อ `-2`, `-3`. `dir` เขียน ` — record=<id>` ต่อท้ายหัว ledger; หัวเก่าที่ไม่มี → คำนวณจาก `start=`
**ชื่อ job:** ปฏิเสธ (exit 1, ไม่สร้างอะไร) ถ้ามี `/` `\` `..` หรือขึ้นต้นด้วย `.`
**Whitelist แฟ้ม:** `SPEC.md` `ledger.md` `proof.md` `preflight.md` (+ `record.md`, `recheck-<YYYY-MM-DD>.md` ที่เขียนในแฟ้มโดยตรง) — ไฟล์อื่นไม่คัดลอกเด็ดขาด
**การเขียนไฟล์:** utf-8, `newline="\n"`, เขียน `<ไฟล์>.tmp` แล้ว `os.replace` ทีละไฟล์ (ห้ามสลับทั้งโฟลเดอร์ — Windows ทำไม่ได้)

**roadmap.md** (หัวข้อตรงตัว เรียงตามนี้):
```
# แผนที่งาน
<!-- MAX เขียนไฟล์นี้ผ่าน max_lite.py · แก้มือได้ที่ "ถัดไป" และ "รอผู้ใช้" -->
## กำลังทำ
- [<job>] <size> · ด่าน: <ด่าน> · ถัดไป: <ข้อความ|-> · ติด: <ข้อความ|-> · <YYYY-MM-DD HH:MM>
## ถัดไป
- (P<1|2|3>) <ข้อความ>
## รอผู้ใช้
- <ข้อความ> (<YYYY-MM-DD>)
## เสร็จล่าสุด
- <YYYY-MM-DD> [<job>] <ปิด · C <n> · ยังไม่ได้ตรวจ <m> | ทิ้ง: <เหตุผล>> → docs/max-jobs/<id>/
```
กติกาเขียน (ทุกคำสั่งที่เขียนแผนที่ใช้ฟังก์ชันเดียวกัน): ทิ้งบรรทัด `<<<<<<<` `=======` `>>>>>>>` · รวมหัวข้อที่ซ้ำ · "กำลังทำ" คีย์ `[job]` เก็บบรรทัดเวลาล่าสุด · "เสร็จล่าสุด" คีย์ `[job]`+id ใหม่สุดอยู่บน เหลือ 10 · job ที่อยู่ทั้ง "กำลังทำ" และ "เสร็จล่าสุด" → ลบจาก "กำลังทำ" · "ถัดไป"/"รอผู้ใช้" ลบบรรทัดซ้ำตรงตัว, "ถัดไป" เรียง P1→P3 คงลำดับเดิม · บรรทัด/หัวข้อที่ไม่รู้จักเก็บไว้ตามเดิม · ข้อความที่สคริปต์รับมา: ขึ้นบรรทัดใหม่ → เว้นวรรค, ยาวเกิน 200 ตัว → ตัด + `…` · เพดาน: ถัดไป 20, รอผู้ใช้ 10
สร้างแผนที่ครั้งแรก → เพิ่มบรรทัด `docs/roadmap.md merge=union` ใน `.gitattributes` (ครั้งเดียว, ต่อท้าย)

**ด่าน** (arg → ข้อความ → "ถัดไป" ตั้งต้น): `spec`→`SPEC`→`เขียน SPEC` · `plan`→`รออนุมัติแผน`→`รอผู้ใช้พิมพ์ ลุย` (ตั้ง `ติด: ผู้ใช้ (อนุมัติแผน)`) · `build`→`สร้าง`→`รอ coder` · `review`→`รีวิว+ตรวจ`→`รอ reviewer + verifier` · `fix`→`แก้ตามรีวิว`→`รอ coder แก้` · `proof`→`รอปิด`→`close`

**คำสั่ง** (ของเดิม `dir` `diff` `status` `close` `abandon` output เดิมต้องยังอยู่ครบ):
| คำสั่ง | ทำ | พิมพ์ |
|---|---|---|
| `dir <job> --size S\|M\|L\|XL` | เดิม + (ไม่ใช่ S) บรรทัด "กำลังทำ" ด่าน `SPEC` | เดิม + `record=docs/max-jobs/<id>` |
| `gate <job> <ด่าน> [--next "<t>"] [--wait "<t>"]` | ต่อท้าย ledger `ด่าน: <ข้อความ> — <YYYY-MM-DD HH:MM>` · อัปเดตแผนที่ · sync แฟ้ม (`record.md` สถานะ `กำลังทำ`) · `plan`: พิมพ์เนื้อหัวข้อ `แผน` ของ SPEC ก่อน | `ด่าน: [<job>] <ข้อความ> → ถัดไป: <t>` (+ `ตัดออก: <n>` เมื่อ n>0) |
| `todo next "<t>" [--p 1\|2\|3]` (ตั้งต้น 2) · `todo wait "<t>"` · `todo done "<ส่วนของข้อความ>"` | เพิ่ม/ลบใน ถัดไป/รอผู้ใช้; `done` ต้องตรง 1 บรรทัดพอดี | `เพิ่ม: <บรรทัด>` / `ลบ 1: <บรรทัด>`; exit 1: `เต็ม <n>` / `ไม่พบ` / `ตรงหลายบรรทัด:` + รายการ |
| `status` | อ่านอย่างเดียว ยกเว้นซ่อมแผนที่; ไม่มีแผนที่ → ไม่สร้าง | `กำลังทำ: …` · `รอผู้ใช้: …` · `ถัดไป: …` (3 แรก + `(+n)`) · `ค้าง [job]: <บรรทัดท้าย ledger>` (เดิม) · `กู้ได้ [job]: docs/max-jobs/<id>/ → resume <job>` · `หาย [job]: ไม่มีทั้ง .max และแฟ้ม — ดู docs/worklog.md` · `ซ่อมแผนที่: [job]` · `ไม่มีงาน MAX ค้าง` (เดิม: เมื่อไม่มีงานเปิดใน `.max/`) |
| `resume <job>` | สร้าง `.max/<job>/` จากแฟ้มเฉพาะไฟล์ที่ยังไม่มี · ต่อท้าย ledger `กู้คืนจากแฟ้ม: <เวลา>` | `dir=` `base=` `ด่าน: …` + ≤ 5 บรรทัดท้าย ledger; ไฟล์ที่ข้าม `มีอยู่แล้ว: <ชื่อ>`; exit 1: `ไม่มีแฟ้มงาน <job>` / `งานปิดแล้ว — ใช้ recheck` |
| `close <job> [--turns <n>]` | ลำดับตายตัว: 1 ตรวจ (เดิม) → 2 sync แฟ้ม → 3 `record.md` สถานะ `ปิด` → 4 แผนที่ → 5 history + ย้ายไป `.max/closed/` (เดิม) | เดิม + `record=docs/max-jobs/<id>` + `ตัดออก: <n>` |
| `abandon <job> "<why>"` | เดิม + แผนที่ + (มี SPEC) แฟ้มสถานะ `ทิ้ง: <why>` | เดิม |
| `backfill <ชื่อโฟลเดอร์ใน .max/closed>` | สร้างแฟ้มจากงานเก่า สถานะ `ปิด (ย้อนหลัง)` + บรรทัด "เสร็จล่าสุด" | `record=…` |
| `recheck <job\|id>` | อ่านอย่างเดียว; หา: แฟ้ม (ใหม่สุดของ job) → `.max/closed/<job>-*` | `แฟ้ม: <path> (ที่มา: แฟ้มถาวร\|.max/closed)` · `ช่วง: <BASE>..<sha ล่าสุดที่แตะ record.md \| ยังไม่ commit>  HEAD=<sha>` · `ไฟล์: …` · ต่อ C-id `C<n> \| <บรรทัดใน SPEC ≤160> \| <บรรทัด proof สุดท้าย ≤200>` · `recheck=<แฟ้ม>/recheck-<YYYY-MM-DD>.md`; exit 1: `ไม่มีแฟ้มงาน <job> — ดู docs/worklog.md` |
| `recheck <job\|id> --sum` | อ่านไฟล์ `recheck=` (บรรทัดสุดท้ายของแต่ละ C ชนะ) · ครบ → ต่อท้าย `record.md` + ข้อ `พังแล้ว` เข้า "ถัดไป" `(P1) แก้ <job> C<n> ที่พังแล้ว — <หลักฐาน ≤80>` (ไม่ติดเพดาน, คีย์ `แก้ <job> C<n>`) | `ตรวจซ้ำ [<job>]: ยังผ่าน <a> · พังแล้ว <b> (C..) · ตรวจไม่ได้ <c> (C..)`; exit 1 ไม่เขียนอะไร: `ตรวจซ้ำไม่ครบ: ขาด C..` |
| `repeat <job> "<t>"` | ต่อท้าย `แจ้งซ้ำ: <t> (<YYYY-MM-DD>)` ใน ledger ของงานเปิด หรือ `ledger.md` ในแฟ้ม | `บันทึก: <path>` |
| `stats` | อ่าน `docs/max-jobs/*/record.md` + ledger ในแฟ้ม (ไม่นับสถานะ `กำลังทำ`) | ดูด้านล่าง |

**แถวในไฟล์ recheck:** `C<n> ยังผ่าน|พังแล้ว|ตรวจไม่ได้ — <หลักฐาน ≥ 8 ตัวอักษร>` (เขียนด้วยการต่อท้าย; แต่ละรอบขึ้นหัว `## <YYYY-MM-DD HH:MM> HEAD=<sha>`)
**record.md** (บรรทัดละ `คีย์: ค่า` ตามลำดับ): `# แฟ้มงาน <job>` · `งาน:` · `ขนาด:` · `สถานะ: กำลังทำ|ปิด|ปิด (ย้อนหลัง)|ทิ้ง: <why>` · `เริ่ม:` · `ปิด:` · `BASE:` · `C-id: <n>` · `ยังไม่ได้ตรวจ: <m> (C..)` · `เกินเพดาน: <จำนวนบรรทัด เกินเพดาน: ใน ledger>` · `turn: <n>` (เฉพาะเมื่อมี `--turns`) · `ตัดออก: <n>` · `ไฟล์: a, b` (วิธีเดียวกับร่าง worklog) · ต่อท้ายได้หลายบรรทัด `ตรวจซ้ำ: <YYYY-MM-DD> ยังผ่าน <a> · พังแล้ว <b> · ตรวจไม่ได้ <c>`
**stats output:**
```
งาน: <n> (ปิด <a> · ทิ้ง <b>) · ขนาด: M <x> · L <y> · XL <z>
แจ้งซ้ำ: <n> ครั้ง ใน <k> งาน
C-id: <n> · ยังไม่ได้ตรวจ <m> (<p>%)
เกินเพดาน: <n> งาน
turn เฉลี่ย: M <x> · L <y> (จาก <k> งาน) | turn เฉลี่ย: ไม่มีข้อมูล
ตรวจซ้ำ: <n> ครั้ง · พังแล้ว <m>
```
ไม่มีแฟ้ม → `ยังไม่มีแฟ้มงาน`
**ทำความสะอาดก่อนเข้าแฟ้ม** (ไฟล์ใน `.max/` ไม่ถูกแก้):
- path ราก repo (ทั้งแบบ `/` และ `\`) → `.`
- คีย์=ค่า: `(?i)\b(APP_PASSWORD|password|passwd|secret|token|api[_-]?key|authorization|ks_session)\b(\s*[=:]\s*["']?)([^\s"']{6,})` และ `(รหัสผ่าน\s*[=:]\s*)(\S{6,})` → เก็บคีย์ แทนค่าด้วย `[ตัดออก]`
- token: [ตัดออก] · `gh[pousr]_[A-Za-z0-9]{20,}` · `github_pat_[A-Za-z0-9_]{20,}` · `AKIA[0-9A-Z]{16}` · `eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}` · `Bearer\s+[A-Za-z0-9._~+/-]{20,}` · บรรทัดที่มี `-----BEGIN [A-Z ]*PRIVATE KEY-----` → `[ตัดออก]`
- ไฟล์ > 300,000 bytes → ตัดท้าย + บรรทัด `[ตัดท้าย: ไฟล์ยาวเกิน]`
**ตัวแปรเทสเท่านั้น:** `MAX_LITE_FAIL_AFTER=<2|3|4>` → `close` ออกด้วย exit 9 หลังจบขั้นนั้น
**`diff` และร่าง worklog:** ไม่นับ `docs/roadmap.md` และ `docs/max-jobs/`

## 5. กฎที่ผูก
- R1 (CLAUDE.md ห้ามเด็ดขาด) ห้ามมีรหัสผ่าน/secret/ข้อมูลลูกค้า (`projects/`, `*.ksproject.json`) ในไฟล์ใดที่ commit รวม `docs/max-jobs/` → T2, T8, T9
- R2 (playbook 4.2) แก้ MAX ที่ `plugins/max-v8/` · version `8.4.0` ทั้ง `plugins/max-v8/.claude-plugin/plugin.json` และ `.claude-plugin/marketplace.json` · `claude plugin validate .` → T8
- R3 (playbook 4.5) `require-worklog.mjs` และ `max-deep/SKILL.md` สองสำเนาต้อง `cmp` เท่ากัน — งานนี้ไม่แตะทั้งคู่ → T8 ตรวจ
- R4 (playbook 4.4) ทุกคำสั่งที่เขียนในคู่มือต้องรันจริงก่อน commit → T7, T8
- R5 (playbook 4.6b) ไม่มี path เต็มของเครื่องใน skill/agent/แฟ้ม → T7, T8, T2
- R6 (playbook 4.6) สำรอง `plugins/max-v8/` ไป `.max/max-roadmap/before-v8.3/` ก่อนแก้ · ชื่อไฟล์ไทยกับ git ใช้ `-c core.quotePath=false` (ใช้ฟังก์ชัน `git()` เดิม) → T1
- R7 stdlib Python เท่านั้น · Windows/macOS/Linux · ของใหม่ห้ามพึ่ง hook · output ไทยผ่าน `out()` → T1–T6
- R8 `cat S/SKILL.md S/references/ml.md | wc -c` ≤ 23,736 → T7
- R9 `docs/roadmap.md` ≤ ~60 บรรทัด (เพดานในข้อ 4) → T1, T3

## 6. จุดที่ต้องระวัง (Review focus)
1. **แฟ้มงานรั่วความลับ/ข้อมูลลูกค้า** — สคริปต์ตัดได้เฉพาะรูปแบบในข้อ 4; ชื่อ/ที่อยู่ลูกค้าตรวจอัตโนมัติไม่ได้ → เทส T2 + กฎใน recheck.md/roadmap.md ("หลักฐานใช้ fixture/ตัวเลข ไม่ใช้ข้อมูลลูกค้าจริง") + C26 grep + main ดู `git diff --stat docs/max-jobs` ก่อน commit
2. **close ล้มกลางทาง** (แฟ้มคัดลอกแล้วแต่ยังไม่ย้าย / แผนที่ยังค้าง "กำลังทำ") → เทส `MAX_LITE_FAIL_AFTER` ใน T3 + `status` ซ่อมแผนที่ใน T4
3. **`.max/` หาย หรือเป็นงานเก่าไม่มีแฟ้ม** (งานจาก v8.3, หัว ledger ไม่มี `record=`, `.max/closed` ไม่อยู่แล้ว) → เทส T2 (หัวเก่า), T4 (`กู้ได้`/`หาย`/backfill), T5 (fallback + ข้อความ)
4. **สอง session แก้แผนที่พร้อมกัน** → เทส merge จริงสอง branch ใน T1; GitHub merge ผ่านเว็บจะเคารพ `merge=union` หรือไม่ **ยังไม่ได้ยืนยัน** → ตาข่ายคือการล้างเครื่องหมาย conflict ใน T1
5. **แผนที่/แฟ้มโตไม่หยุด และข้อมูลผู้ใช้หาย** — เพดาน + ปฏิเสธเมื่อเต็ม (ไม่ตัดเงียบ) + บรรทัดที่ผู้ใช้เขียนมือต้องรอด → เทส T1, T3 (ปิด 11 งาน)
6. **ของเดิมพัง** — `dir` สร้างไฟล์ใหม่ใน `docs/` ทำให้ร่าง worklog / `diff` / เทสเดิมเปลี่ยนผล → T3 ตัดออก + เทสเดิม 29 ต้องผ่านทุกชุด

## 7. tasks
ลำดับ: กลุ่ม A ทีละชุด (ไฟล์เดียวกัน) · กลุ่ม B ทำขนานกับ A ได้ (ใช้ข้อ 4 เท่านั้น) · กลุ่ม C หลัง A + B เสร็จ · แล้วด่านลองจริง
คำสั่งเทสทุก task ของ A: `python3 plugins/max-v8/skills/max/scripts/test_max_lite.py` (ทั้งไฟล์ ต้อง `OK`) · เฉพาะคลาส: ต่อท้ายชื่อคลาส เช่น `… test_max_lite.py TestRoadmap`
เทสใหม่ทุกตัวสืบจากคลาส `Repo` เดิม (`TEST:26`) ใช้ `lite()` (`TEST:21`)

### T1 — แผนที่: อ่าน/เขียน + `dir` + `todo` · กลุ่ม: A (ชุด 1)
ไฟล์: `LITE` (เพิ่มฟังก์ชันหลัง `read()` `LITE:57`; แก้ `cmd_dir` `LITE:64-79`; ตาราง `cmds` `LITE:231`; docstring `LITE:2-12`) · `TEST` (คลาสใหม่ `TestRoadmap`)
ก่อนเริ่ม: รัน A1–A11 · สำรองตาม R6
ให้: `roadmap_load(r) -> dict`, `roadmap_save(r, data)` (ใช้กติกาเขียนในข้อ 4), `record_id(jd, job) -> str`, `check_job_name(job)`, คำสั่ง `todo` · ใช้: `git()`, `root()`, `out()`, `read()` เดิม
เทส (`input → expected`):
- `dir j1 --size M` → มี `docs/roadmap.md`; หัวข้อ 4 อันเรียงตามข้อ 4; ใต้ "กำลังทำ" มี 1 บรรทัดขึ้นต้น `- [j1] M · ด่าน: SPEC`; stdout มี `budget=25` และ `record=docs/max-jobs/<วันนี้>-j1`; หัว ledger มี `record=<วันนี้>-j1`
- `dir j1 --size M` สองครั้ง → ยัง 1 บรรทัด · `dir s1 --size S` → ไม่มีโฟลเดอร์ `docs/`
- `dir ../x`, `dir a/b`, `dir .x` → exit 1, ไม่มีโฟลเดอร์ใหม่ทั้งใน `.max/` และ `docs/`
- `todo next "แก้ dbp" --p 1` แล้ว `todo next "อื่น"` → `- (P1) แก้ dbp` อยู่เหนือ `- (P2) อื่น` · `todo wait "merge PR"` → `- merge PR (<วันนี้>)`
- `todo done "dbp"` → บรรทัดหาย พิมพ์ `ลบ 1:` · ไม่ตรงเลย → exit 1 `ไม่พบ` · ตรง 2 บรรทัด → exit 1 และไฟล์เท่าเดิมทุก byte
- `todo next` ครั้งที่ 21 → exit 1 `เต็ม 20`, ไฟล์เท่าเดิมทุก byte
- เขียนมือเพิ่ม `## โน้ต\n- x` และบรรทัดแปลกใต้ "ถัดไป" → หลัง `todo next` ยังอยู่ครบ
- ไฟล์มีเครื่องหมาย conflict + `[j1]` สองบรรทัดเวลาต่างกัน → หลังเขียนครั้งถัดไป: ไม่มีบรรทัดเครื่องหมาย, เหลือ `[j1]` บรรทัดเดียวที่เวลาใหม่กว่า
- merge จริง: สอง branch ต่าง `todo next` คนละข้อความ → `git merge` exit 0; หลัง `todo wait "x"` มีครบ 2 ข้อความ หัวข้อละ 1 ครั้ง
- `.gitattributes` เดิมมี 1 บรรทัดอื่น → หลัง `dir` สองครั้ง: บรรทัดเดิมอยู่, `docs/roadmap.md merge=union` มี 1 ครั้ง
- ข้อความไทย 250 ตัว + ขึ้นบรรทัดใหม่ → บรรทัดเดียว ยาว 200 + `…`; ไฟล์ไม่มี `\r`

### T2 — แฟ้มงาน + ทำความสะอาด + `gate` · **Core** · กลุ่ม: A (ชุด 1 — จบชุด)
ไฟล์: `LITE` (ฟังก์ชันใหม่ + คำสั่ง `gate`) · `TEST` (คลาส `TestRecord`)
ใช้: T1 `roadmap_load/save`, `record_id` · ให้: `clean(text, r) -> (text, n_cut)`, `sync_record(r, jd, job, status, extra=None) -> (id, n_cut)`, คำสั่ง `gate`
เทส (assertion ทุกตัว):
- `gate j1 build --next "รอ coder G1"` (มี SPEC.md) → บรรทัดท้าย ledger ขึ้นต้น `ด่าน: สร้าง — `; แผนที่: `- [j1] M · ด่าน: สร้าง · ถัดไป: รอ coder G1 · ติด: - ·`; stdout บรรทัดแรก `ด่าน: [j1] สร้าง → ถัดไป: รอ coder G1`; แฟ้มมี `SPEC.md` `ledger.md` `record.md` (`สถานะ: กำลังทำ`); ไม่มี `proof.md` ถ้าต้นทางไม่มี
- `gate j1 nope` → exit 1 พิมพ์ชื่อด่านที่ใช้ได้ 6 ตัว · `gate nojob build` → exit 1 · `gate j1 build` ตอนไม่มี SPEC.md → exit 1 `ยังไม่มี SPEC` (ยกเว้นด่าน `spec`)
- `gate j1 plan`: SPEC มีหัวข้อ `## แผน (ภาษาคน)` 3 บรรทัด → stdout มี 3 บรรทัดนั้น ไม่มีบรรทัดของหัวข้อถัดไป; แผนที่มี `ติด: ผู้ใช้ (อนุมัติแผน)` · SPEC มีแต่ `## แผนที่` → exit 1 `ไม่มีหัวข้อ แผน ใน SPEC`, แผนที่เท่าเดิมทุก byte
- ทำความสะอาด: SPEC มี `APP_PASSWORD=[ตัดออก] `รหัสผ่าน: [ตัดออก] `ghp_` + 30 ตัว, `Bearer ` + 26 ตัว, และ path ราก repo → ในแฟ้ม: ไม่มีค่าทั้ง 4, มี `[ตัดออก]` 4 ครั้ง, ยังมี `APP_PASSWORD=`, ไม่มี path ราก (เป็น `.`); stdout มี `ตัดออก: 4`; `record.md` มี `ตัดออก: 4`; `.max/j1/SPEC.md` เท่าเดิมทุก byte
- ไม่ตัดเกิน: `C1 ผ่าน — test_login::test_password_required 3 passed` และ `คำว่า รหัสผ่าน ในหน้า login` → ในแฟ้มเท่าเดิม
- whitelist: วาง `review.diff`, `shot.png`, `x.ksproject.json`, `j1-G1.md` ใน `.max/j1/` → ไม่มีในแฟ้ม
- SPEC 400,000 bytes → ไฟล์ในแฟ้ม ≤ 300,100 bytes บรรทัดท้าย `[ตัดท้าย: ไฟล์ยาวเกิน]`
- กฎ twice = once: `gate j1 build` สองครั้ง → ไฟล์ในแฟ้ม (ยกเว้น ledger.md) เท่ากันทุก byte; ไม่มีไฟล์ `.tmp` เหลือ
- หัว ledger แบบ v8.3 (ไม่มี `record=`, `start=2026-11-27 05:48`) → แฟ้มอยู่ที่ `docs/max-jobs/2026-11-27-j1/`

### T3 — `close` / `abandon` เขียนแฟ้ม + แผนที่ · **Core** · กลุ่ม: A (ชุด 2 — จบชุด)
ไฟล์: `LITE` (`cmd_close` `LITE:151-189`, `archive` `LITE:142-148`, `print_draft` `LITE:192-218`, `cmd_abandon` `LITE:221-227`, `cmd_diff` `LITE:96,105-107`) · `TEST` (คลาส `TestCloseRecord`)
ใช้: T1, T2 `sync_record` · ให้: ลำดับ 5 ขั้นในข้อ 4, `job_files(r, base) -> list` (ใช้ร่วมกับ `print_draft`)
เทส (assertion ทุกตัว):
- ปิดสำเร็จ (SPEC มี C1 C2, proof: C1 ผ่าน, C2 ยังไม่ได้ตรวจ, แก้ `a.txt`) → `record.md`: `สถานะ: ปิด`, `ขนาด: M`, `BASE: <sha>`, `C-id: 2`, `ยังไม่ได้ตรวจ: 1 (C2)`, `ไฟล์:` มี `a.txt` ไม่มี `docs/`; แผนที่: ไม่มี `[j1]` ใต้ "กำลังทำ", บรรทัดแรกใต้ "เสร็จล่าสุด" = `- <วันนี้> [j1] ปิด · C 2 · ยังไม่ได้ตรวจ 1 → docs/max-jobs/<id>/`; มี `.max/closed/j1-*`; stdout ยังมี `ยังไม่ได้ตรวจจริง:`, `MAX: j1`, `--- ร่างบันทึก`, `archived=` + `record=docs/max-jobs/<id>`
- ปิดถูกปฏิเสธ (ไม่มี proof ของ C2) → exit 1; `docs/roadmap.md` และทุกไฟล์ในแฟ้มเท่าเดิมทุก byte
- `--turns 23` → `turn: 23` · `--turns x` → exit 1 ก่อนเขียนอะไร (ไฟล์เท่าเดิม)
- ปิด 11 งาน → "เสร็จล่าสุด" 10 บรรทัด งานแรกไม่อยู่ในแผนที่ แต่โฟลเดอร์แฟ้มของมันยังอยู่
- ล้มกลางทาง: `MAX_LITE_FAIL_AFTER` = 2, 3, 4 (แยกเทส) → exit 9; แล้ว `close j1` ธรรมดา → exit 0; ผลสุดท้าย: "เสร็จล่าสุด" มี `[j1]` 1 บรรทัด, `record.md` `สถานะ: ปิด` 1 บรรทัด, ไม่มี `.max/j1/`, ไม่มี `.tmp`
- `abandon j1 "เปลี่ยนใจ"` มี SPEC → `record.md` `สถานะ: ทิ้ง: เปลี่ยนใจ`; "เสร็จล่าสุด": `[j1] ทิ้ง: เปลี่ยนใจ → docs/max-jobs/<id>/` · ไม่มี SPEC → ไม่มีโฟลเดอร์แฟ้ม, บรรทัด "เสร็จล่าสุด" ไม่มี `→`
- งาน S (`dir s1 --size S` → close) → พฤติกรรม v8.3 เดิม ไม่มีโฟลเดอร์ `docs/`
- ร่าง worklog `ไฟล์:` และไฟล์ `review.diff` ไม่มี `docs/roadmap.md` / `docs/max-jobs/` (งานที่ไม่แก้ไฟล์อื่น → `(ไม่มีไฟล์เปลี่ยน)`)
- เทสเดิม 29 ผ่านครบโดยไม่แก้ assertion เดิม (จำเป็นต้องแก้ → `NEEDS_CONTEXT` บอกบรรทัด)

### T4 — `status` + `resume` + `backfill` · **Core** · กลุ่ม: A (ชุด 3 — จบชุด)
ไฟล์: `LITE` (`cmd_status` `LITE:132-139`, คำสั่งใหม่ 2 ตัว) · `TEST` (คลาส `TestResume`)
ใช้: T1–T3 · ให้: `find_record(r, job_or_id) -> path|None` (ใหม่สุดของ job; T5, T6 ใช้)
เทส (assertion ทุกตัว):
- `dir` → เขียน SPEC → `gate j1 build` → `git add -A && commit` → ลบ `.max/` → `status`: มี `กำลังทำ: - [j1] M · ด่าน: สร้าง` และ `กู้ได้ [j1]: docs/max-jobs/<id>/ → resume j1`
- `resume j1` → `.max/j1/SPEC.md` เท่ากับในแฟ้มทุก byte; stdout มี `dir=`, `base=`, `ด่าน: สร้าง`; ledger ลงท้าย `กู้คืนจากแฟ้ม:`; `status` รอบถัดไปไม่มี `กู้ได้` แต่มี `ค้าง [j1]:`
- กฎไม่เขียนทับ: `.max/j1/SPEC.md` มีอยู่ เนื้อต่างจากแฟ้ม → หลัง `resume j1` เท่าเดิมทุก byte, stdout `มีอยู่แล้ว: SPEC.md`
- `resume nojob` → exit 1 `ไม่มีแฟ้มงาน nojob` · job ที่แฟ้ม `สถานะ: ปิด` → exit 1 `งานปิดแล้ว — ใช้ recheck`
- ไม่มีแผนที่ ไม่มีงาน → stdout = `ไม่มีงาน MAX ค้าง` บรรทัดเดียว และไม่มีโฟลเดอร์ `docs/`
- ซ่อม: ปิดด้วย `MAX_LITE_FAIL_AFTER=3` แล้วลบ `.max/j1/` → `status` พิมพ์ `ซ่อมแผนที่: [j1]`; แผนที่: `[j1]` อยู่ "เสร็จล่าสุด" ไม่อยู่ "กำลังทำ"
- บรรทัด "กำลังทำ" ของ job ที่ไม่มีทั้ง `.max/` และแฟ้ม → `หาย [jx]: ไม่มีทั้ง .max และแฟ้ม — ดู docs/worklog.md` (ไม่ลบบรรทัด)
- "ถัดไป" 5 ข้อ → พิมพ์ 3 บรรทัด + `(+2)`
- backfill: `.max/closed/old-202611270541/` มี SPEC/proof/ledger (หัว `start=2026-11-27 05:00`, มี `APP_PASSWORD=[ตัดออก] → `backfill old-202611270541` → `docs/max-jobs/2026-11-27-old/record.md` `สถานะ: ปิด (ย้อนหลัง)`, ไม่มี `hunter2secret`, มีบรรทัด "เสร็จล่าสุด"; รันซ้ำ → เท่าเดิม (1 บรรทัด); โฟลเดอร์ต้นทางเท่าเดิม; ไม่มีโฟลเดอร์ → exit 1

### T5 — `recheck` + `repeat` · กลุ่ม: A (ชุด 4)
ไฟล์: `LITE` · `TEST` (คลาส `TestRecheck`)
ใช้: T4 `find_record`, regex C-id เดิม `LITE:160` · ให้: คำสั่ง `recheck`, `repeat`
เทส:
- งานปิดแล้ว (C1, C2, C10) → `recheck j1`: บรรทัด `แฟ้ม: docs/max-jobs/<id>/ (ที่มา: แฟ้มถาวร)`, `ช่วง: <BASE>..`, `ไฟล์: a.txt`, มี 3 บรรทัด `C1 |` `C2 |` `C10 |` (แต่ละบรรทัดมีหลักฐานของตัวเอง), `recheck=docs/max-jobs/<id>/recheck-<วันนี้>.md`; ใช้ `<id>` แทน job ได้ผลเดียวกัน; ไม่สร้าง/แก้ไฟล์ใด (`git status --short` เท่าเดิม)
- ลบแฟ้ม เหลือ `.max/closed/j1-*` → `(ที่มา: .max/closed)` · ไม่เหลือทั้งคู่ → exit 1 `ไม่มีแฟ้มงาน j1 — ดู docs/worklog.md`
- `--sum`: ไฟล์ recheck มี `C1 ยังผ่าน — 3 passed test_a`, `C2 พังแล้ว — ตั้งแต่ abc1234 test_b fail`, `C10 ตรวจไม่ได้ — ต้องรันบน Windows` → stdout `ตรวจซ้ำ [j1]: ยังผ่าน 1 · พังแล้ว 1 (C2) · ตรวจไม่ได้ 1 (C10)`; "ถัดไป" มี `(P1) แก้ j1 C2 ที่พังแล้ว`; `record.md` ลงท้าย `ตรวจซ้ำ: <วันนี้> ยังผ่าน 1 · พังแล้ว 1 · ตรวจไม่ได้ 1`; รัน `--sum` ซ้ำ → "ถัดไป" ยังมีบรรทัดนั้น 1 บรรทัด
- ไม่มีบรรทัด C2 / หลักฐาน C2 สั้นกว่า 8 ตัว → exit 1 `ตรวจซ้ำไม่ครบ: ขาด C2`; แผนที่และ `record.md` เท่าเดิมทุก byte
- บรรทัดสุดท้ายชนะ: `C2 พังแล้ว …` แล้วตามด้วย `C2 ยังผ่าน — แก้แล้ว 3 passed` → พังแล้ว 0
- `repeat j1 "ปุ่มยังไม่ขึ้น — ไม่ได้เปิดจอจริง"`: งานเปิด → ledger ใน `.max/j1/` ลงท้าย `แจ้งซ้ำ: ปุ่มยังไม่ขึ้น`; งานปิดแล้ว → `docs/max-jobs/<id>/ledger.md`; ไม่มี job → exit 1

### T6 — `stats` + docstring · กลุ่ม: A (ชุด 4)
ไฟล์: `LITE` (คำสั่ง `stats`; docstring `LITE:2-12` ครบทุกคำสั่งในข้อ 4) · `TEST` (คลาส `TestStats`)
ใช้: รูปแบบ `record.md` ข้อ 4
เทส:
- 3 แฟ้ม: (M ปิด, C-id 4, ยังไม่ได้ตรวจ 0, turn 20) (L ปิด, C-id 10, ยังไม่ได้ตรวจ 2, ledger มี `แจ้งซ้ำ:` 1 บรรทัด, `เกินเพดาน: 1`, มี `ตรวจซ้ำ: … พังแล้ว 1 …`) (M ทิ้ง: x) + 1 แฟ้ม `กำลังทำ` → output ตรงตัว:
  `งาน: 3 (ปิด 2 · ทิ้ง 1) · ขนาด: M 2 · L 1 · XL 0` / `แจ้งซ้ำ: 1 ครั้ง ใน 1 งาน` / `C-id: 14 · ยังไม่ได้ตรวจ 2 (14%)` / `เกินเพดาน: 1 งาน` / `turn เฉลี่ย: M 20 (จาก 1 งาน)` / `ตรวจซ้ำ: 1 ครั้ง · พังแล้ว 1`
- ไม่มี `docs/max-jobs/` → `ยังไม่มีแฟ้มงาน` exit 0 · ไม่มีแฟ้มไหนมี `turn:` → `turn เฉลี่ย: ไม่มีข้อมูล`
- `record.md` ขาดบรรทัด `C-id:` หรือเป็นไฟล์ว่าง → ไม่ crash, นับเป็นงานที่ค่านั้นเป็น 0
- รัน `python3 LITE` ไม่มี arg → docstring มีชื่อคำสั่งครบ: gate todo resume backfill recheck repeat stats

### T7 — คู่มือหลัก: `SKILL.md` + `ml.md` · กลุ่ม: B
ไฟล์: `S/SKILL.md` (frontmatter `:3`; ย่อหน้า job state `:8-11`; "ทำต่อ" `:92-94`) · `S/references/ml.md` (§1 `:11-47`; §2 `:49-60`; §4 `:64-75`; §5 `:77-94`)
ใช้: ชื่อคำสั่ง/ด่าน/หัวข้อ ตามข้อ 4 ตรงตัว · วิธีแก้: playbook 4.5 (python ที่ `assert` ว่าข้อความเดิมเจอครั้งเดียว)
เนื้อที่ต้องมี (กระชับ; เกินงบ R8 → ย่อข้อความเดิมที่ซ้ำกัน ห้ามตัดกฎเดิม):
- SKILL `description`: เพิ่มคำเรียก `ทำต่อ`, `ตรวจซ้ำ <งาน>`, `แผนที่งาน`
- SKILL `:8-11`: `.max/<job>/` = ที่ทำงานชั่วคราว (ไม่ commit); สคริปต์เขียน `docs/roadmap.md` + `docs/max-jobs/<id>/` ให้ → commit ไปพร้อมงาน; ห้ามมีความลับ/ข้อมูลลูกค้าในหลักฐาน
- SKILL `:92-94`: "ทำต่อ"/session ใหม่ → `status`; เจอ `กู้ได้` → `resume <job>` แล้วอ่าน ledger (กฎ `เริ่ม` ไม่มี `เสร็จ` คงเดิม) · "ตรวจซ้ำ <งาน>" / "ตรวจซ้ำละเอียด" → อ่าน `references/recheck.md` อย่างเดียว · แผนที่/งานถัดไป/สถิติ → `references/roadmap.md`
- ml §1: SPEC ขึ้นต้นด้วยหัวข้อ `แผน (ภาษาคน)` 5–10 บรรทัดไทย (เปลี่ยนอะไรให้ผู้ใช้ · ขั้นตอน · พิสูจน์ยังไง · ความเสี่ยง · ไม่ทำ) · M: ใส่แผนในข้อความเดียวกับที่ส่ง coder + `gate <job> build` แล้วทำต่อ · L/XL: `gate <job> plan` → ส่ง output ให้ผู้ใช้ตามตัว → จบ turn รอ "ลุย" → `gate <job> build` · มาจาก max-deep ที่ผู้ใช้อนุมัติ preflight แล้ว: ไม่ถามซ้ำ เว้นแต่ SPEC มีขอบเขตเกิน preflight
- ml §2/§4: `gate <job> build|review|fix|proof` ต่อท้ายในคำสั่งที่เรียกอยู่แล้ว (ไม่เพิ่ม turn) และส่งบรรทัด `ด่าน: …` ให้ผู้ใช้ 1 บรรทัด
- ml §5: `close <job> --turns <n>` เขียนแฟ้ม + แผนที่; `git add docs/max-jobs docs/roadmap.md` ใน commit เดียวกับงาน; ดู `ตัดออก:` และ `git diff --stat docs/max-jobs` ก่อน commit · แจ้งซ้ำ → `max_lite.py repeat <job> "<อะไร> — <ทำไมหลุด>"` (แทนการแก้ `history.md` ด้วยมือ) · `stats` คือตัววัด
เทส: `cat plugins/max-v8/skills/max/SKILL.md plugins/max-v8/skills/max/references/ml.md | wc -c` → ≤ 23736 · `grep -c "gate <job>" ml.md` ≥ 3 · `grep -n "resume <job>\|recheck.md\|roadmap.md" SKILL.md` → เจอทั้ง 3 · `grep -n "แผน (ภาษาคน)" ml.md` → เจอ · `grep -rnE "/home/|C:\\\\Users|~/" plugins/max-v8/skills` → 0 · หัวข้อไทย 8 ข้อเดิมของ §1 ยังอยู่ครบ (`grep -c` ทีละคำ)

### T8 — ไฟล์อ้างอิงใหม่ + README + version · กลุ่ม: B
ไฟล์ใหม่: `S/references/roadmap.md` (≤ 45 บรรทัด) · `S/references/recheck.md` (≤ 50 บรรทัด) · แก้: `plugins/max-v8/README.md` (หัว `:1` → v8.4 + หัวข้อไทยสั้น "มีอะไรใหม่": แผนที่งาน, แฟ้มงาน, ทำต่อ, ตรวจซ้ำ/ตรวจซ้ำละเอียด, แผนภาษาคน, สถิติ) · `plugins/max-v8/.claude-plugin/plugin.json:3-4` และ `.claude-plugin/marketplace.json:8-9` → `8.4.0` + คำอธิบาย v8.4
`roadmap.md` ต้องมี: รูปแบบไฟล์ (ข้อ 4) · คำสั่ง `todo` / `status` / `resume` / `backfill` / `stats` พร้อมตัวอย่างรันได้ · เมื่อไรเพิ่ม "ถัดไป" (เจอปัญหานอกขอบเขตงาน → `todo next`, ไม่แก้เอง) และ "รอผู้ใช้" (รอ merge/deploy/คำตอบ → `todo wait`) · `หาย`/`กู้ได้`/`ซ่อมแผนที่` แปลว่าอะไร ทำอะไรต่อ · กฎ R1
`recheck.md` ต้องมี:
- main: `recheck <job>` (1 call) → ส่ง `max-verifier` 1 ตัว brief: `ตรวจซ้ำ: <path แฟ้ม>` · `อ่าน: <path recheck.md> หัวข้อ "สำหรับ verifier"` · `recheck: <path จากบรรทัด recheck=>` · `lite:` · `คำขอ:` → กลับมา: `recheck <job> --sum` → รายงานผู้ใช้ต่อ C-id (ยังผ่าน / พังแล้ว ตั้งแต่ commit ไหน / ตรวจไม่ได้ เพราะอะไร) → commit ไฟล์ recheck + แผนที่ · ห้ามแก้โค้ดในโหมดนี้ (ข้อที่พัง → "ถัดไป" แล้วถามผู้ใช้)
- หัวข้อ "สำหรับ verifier": พิสูจน์ทุก C-id ใหม่กับ HEAD วันนี้ — รันเทส/คำสั่งที่หลักฐานเดิมระบุ, เปิดจอจริงสำหรับ C-id ที่เป็นจอ; ห้ามคัดลอกหลักฐานเดิม; เขียนแถวตามข้อ 4 ด้วยการต่อท้าย ขึ้นหัว `## <เวลา> HEAD=<sha>`; `พังแล้ว` → หา commit: `git log --oneline <sha ปิด>..HEAD -- <ไฟล์ของงาน>` + `git log -S"<ชื่อ/ข้อความที่หาย>"`; ระบุ sha เดียวเมื่อพิสูจน์ได้ (เทสผ่านที่ commit ก่อนหน้า) ไม่อย่างนั้นเขียน `น่าจะ: <sha..>`; หลักฐานเดิมรันไม่ได้ที่นี่ (Windows, เว็บจริง) → `ตรวจไม่ได้ — <เหตุผล>`; หลักฐานห้ามมีข้อมูลลูกค้า/ความลับ; ไม่แก้ไฟล์โค้ด
- "ตรวจซ้ำละเอียด": ทั้งหมดข้างบน + ในข้อความเดียวกัน `max-hunter` บนไฟล์จากบรรทัด `ไฟล์:` (brief ตาม `hunt.md`, `findings: <แฟ้ม>/hunt-<วันที่>.md`) + skill `code-review` ระดับ high บนไฟล์ชุดเดียวกันถ้ามี skill นั้น (ไม่มี → บอกผู้ใช้ 1 บรรทัด) → สิ่งที่เจอ: `todo next` ทีละข้อ (P ตามความรุนแรง)
- งานเก่าไม่มีแฟ้ม: ลอง `backfill`; ไม่ได้ → บอกผู้ใช้ว่าตรวจได้เฉพาะจาก `docs/worklog.md`
เทส: `claude plugin validate .` → ผ่าน · `grep -n '"version"' plugins/max-v8/.claude-plugin/plugin.json .claude-plugin/marketplace.json` → `8.4.0` สองบรรทัด · A5 ยัง `SAME` · `wc -l` สองไฟล์ใหม่ไม่เกินเพดาน · `grep -rnE "/home/|C:\\\\Users|~/" plugins/max-v8 --include=*.md --include=*.json` → 0 · (หลังกลุ่ม A เสร็จ, R4) verifier รันทุกคำสั่งตัวอย่างใน 2 ไฟล์ใหม่ + T7 ใน repo ทิ้งได้ → exit ตามที่เอกสารบอก

### T9 — ใส่ข้อมูลของ repo นี้ · กลุ่ม: C (หลัง A + B)
ไฟล์ (สร้างด้วยคำสั่งเท่านั้น ห้ามพิมพ์มือ): `docs/roadmap.md` · `.gitattributes` · `docs/max-jobs/2026-11-27-max-upgrade/` · แก้มือ: `docs/playbook.md` (§0 ข้อ 1–2 `:9-10` เพิ่ม "รัน `max_lite.py status` / อ่าน `docs/roadmap.md`"; §4 เพิ่มข้อ 8: สูตรของ v8.4 ที่ใช้ได้ผลในงานนี้)
ขั้น (รันจากราก repo, `LITE` = path เต็มของสคริปต์ใน repo):
1. `python3 LITE backfill max-upgrade-202611270541` → แฟ้ม v8.3 + บรรทัด "เสร็จล่าสุด"
2. `python3 LITE todo wait "merge PR #1 (MAX v8.3) แล้วรัน /plugin marketplace update ks-home"`
3. `python3 LITE todo next "เพิ่ม host dbp.co.th ใน server.ps1 และ proxy-worker.js ให้ตรงกับ worker.src.js (Core: รายการ proxy)" --p 1`
4. `python3 LITE gate max-roadmap review` → แฟ้มของงานนี้เอง `docs/max-jobs/2026-11-27-max-roadmap/` + บรรทัด "กำลังทำ"
เทส: `python3 LITE status` → มี `กำลังทำ: - [max-roadmap] XL`, `รอผู้ใช้:` มี `PR #1`, `ถัดไป: - (P1)` มี `dbp.co.th` · `wc -l docs/roadmap.md` ≤ 60 · `cat .gitattributes` → มี `docs/roadmap.md merge=union` · `ls docs/max-jobs/2026-11-27-max-upgrade/` → `SPEC.md ledger.md preflight.md proof.md record.md` เท่านั้น · `grep -rnE "/home/user|hunter2|APP_PASSWORD\s*[=:]\s*[^\s\[]{6,}|ksproject\.json\"" docs/max-jobs` → 0 · `git check-ignore docs/roadmap.md docs/max-jobs/x` → ไม่ ignore · `python3 LITE recheck max-upgrade` → 16 บรรทัด `C<n> |` · `node .claude/tools/check-worker-sync.mjs` → ผลเท่ากับก่อนเริ่มงาน (งานนี้ไม่แตะ 3 ไฟล์นั้น)

### ด่านสุดท้าย — ลองจริง (`max-verifier`; หลัง T1–T9 + รีวิวผ่าน)
ทำใน git repo ทิ้งได้ 2 อันใต้ scratchpad (ไม่ใช่ใน repo นี้) · `PLUGIN` = path เต็มของ `plugins/max-v8` · รูปคำสั่งตาม playbook 4.6:
`claude -p "<ข้อความ>" --plugin-dir PLUGIN --allowedTools Read Write Edit Glob Grep Agent Skill "Bash(python3:*)" "Bash(git:*)" --output-format json` (ห้าม bypassPermissions) · เก็บ `is_error`, `num_turns`, `total_cost_usd` ทุกรอบ
- **ก (C23):** repo 1 มี `textutil.py` ว่าง + commit แรก → รอบ 1: `"MAX ขนาด M: เพิ่มฟังก์ชัน slugify(text) ใน textutil.py พร้อมเทส unittest แล้ว commit"` → ต้องได้: `docs/max-jobs/*/record.md` มี `สถานะ: ปิด`, `docs/roadmap.md` มี job ใต้ "เสร็จล่าสุด", ผลลัพธ์มีแผนภาษาคน; ไฟล์ `docs/` ยังไม่ commit → ผู้ลอง commit แล้ว**จดไว้ว่า MAX ไม่ได้ commit เอง** → `rm -rf .max` → รอบ 2: `"ตรวจซ้ำ <job>"` → `is_error=false`; มี `docs/max-jobs/<id>/recheck-<วันนี้>.md` ครบทุก C-id เป็น `ยังผ่าน`; `record.md` มีบรรทัด `ตรวจซ้ำ:`
- **ค (C25, C27):** repo 1 ต่อ: แก้ `slugify` ให้ผิด 1 พฤติกรรมที่มี C-id → commit `"break"` (จด sha) → รอบ 3: `"ตรวจซ้ำ <job>"` → ไฟล์ recheck มี ≥ 1 บรรทัด `พังแล้ว` ที่มี sha นั้น; "ถัดไป" มี `(P1) แก้ <job> C`; โค้ดไม่ถูกแก้ (`git diff --stat HEAD -- textutil.py` ว่าง) · งบเหลือ → รอบ 4 `"ตรวจซ้ำละเอียด <job>"` ต้องมี `hunt-<วันที่>.md`; ไม่ได้ลอง → C27 `ยังไม่ได้ตรวจ`
- **ข (C24):** repo 2: commit แรก → `dir t-resume --size M` → เขียน SPEC ~15 บรรทัด (หัวข้อ `แผน (ภาษาคน)`, C1 `add(2,3) → 5`, C2 `add("a",1) → TypeError`, task เดียว ไฟล์ `calc.py` + `test_calc.py`) → `gate t-resume build` → `git add -A && git commit` → `rm -rf .max` → `claude -p "ทำต่อ"` → ต้องได้: `record.md` `สถานะ: ปิด`, `python3 -m unittest` ใน repo 2 ผ่าน, ไม่มี `[t-resume]` ใต้ "กำลังทำ", transcript มี `status` แล้ว `resume t-resume`
- จบ: `stats` ใน repo 1 พิมพ์ 6 บรรทัดตามข้อ 4 (C16 ของจริง) · ใน repo นี้: `python3 TEST` → `OK`, `claude plugin validate .` ผ่าน
- XL: `max-advisor` (fable) รีวิว diff ทั้งงานหลังด่านนี้ + `/code-review high` (playbook 4.6)

## 8. สิ่งที่ห้ามแตะ
`index.html` · `worker.src.js` · `worker.js` · `server.ps1` · `proxy-worker.js` · `คู่มือการใช้งาน.html` · `CLAUDE.md` · `.claude/settings.json` · `plugins/max-v8/hooks/*` และ `.claude/hooks/*` · `plugins/max-v8/skills/max-deep/SKILL.md` และ `.claude/skills/max-deep/SKILL.md` · `plugins/max-v8/agents/*.md` · `S/references/hunt.md` · `S/references/project-kedit.md` · เนื้อใน `.max/closed/` (อ่านอย่างเดียว) · `projects/` · บรรทัด `.max/` ใน `.gitignore` · ไม่ push / ไม่ merge PR #1

## เปลี่ยนแปลง (หลังรีวิว Core ชุด 1 — advisor FIX 6)
- ข้อ 4 กติกา "job อยู่ทั้ง กำลังทำ และ เสร็จล่าสุด → ลบจาก กำลังทำ" เปลี่ยนเป็น: ลบเฉพาะเมื่อ id ตรงกัน (id จากลิงก์ `→ docs/max-jobs/<id>/`) — งานใหม่ที่ชื่อซ้ำงานที่ปิดแล้ว (id `-2`) ต้องอยู่ใน "กำลังทำ" (เหตุ: ทำตามตัวอักษรแล้วพัง C1 C6 C7)
- C9 ตัดความลับเพิ่ม: ชื่อคีย์ที่มี prefix (`CLOUDFLARE_API_TOKEN=`, `DB_PASSWORD=`), คีย์แบบ JSON (`"password": "…"`), path เครื่องแบบ escape (`C:\\Users\\…`) และ home (`~`); รูปแบบที่ยังตัดไม่ได้เขียนเป็นข้อจำกัดใน references/recheck.md
- id แฟ้มต้องตรง `^\d{4}-\d\d-\d\d-[^/\\\s]+$` ไม่มี `..` (ไม่งั้นคำนวณใหม่) · ชื่อ job ห้ามมีช่องว่าง `[` `]` `:*?"<>|`
- ข้อความ `todo` ผ่าน clean() · ล้างเครื่องหมาย conflict แบบ diff3 (`|||||||`)
- CLAUDE.md: ผู้ใช้อนุมัติให้เพิ่ม 2 บรรทัดในหัวข้อ "ความจำงาน" (ตอบ "ลุย + เพิ่ม CLAUDE.md" ตอนอนุมัติแผน) — main เพิ่มใน T9 (ยกเลิกข้อ "ไม่แก้ CLAUDE.md")
