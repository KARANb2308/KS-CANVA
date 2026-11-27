# บันทึกงาน (Work log)

Claude เขียนบันทึกนี้หลังจบทุกงาน และอ่านก่อนเริ่มงานใหม่ (ค้นงานที่คล้ายกันด้วย Grep)
ให้เพิ่มงานใหม่**ต่อท้ายไฟล์** ห้ามลบหรือแก้บันทึกเก่า ยกเว้นเปลี่ยนสถานะ "ค้าง" เป็น "เสร็จ"
วิธีที่ใช้ซ้ำได้ให้สรุปลง `docs/playbook.md` ด้วย

แบบฟอร์ม:
```
## YYYY-MM-DD — <ชื่องานสั้นๆ>
- คำขอ: "<คำของผู้ใช้>"
- สถานะ: เสร็จ | ค้าง — <ค้างอะไร>
- ทำอะไร: <สิ่งที่ผู้ใช้จะเห็นว่าเปลี่ยน>
- ไฟล์: <ไฟล์ — แก้อะไร>
- ขั้นตอนที่ได้ผล: 1. … 2. … 3. …
- ที่ไม่ได้ผล / ต้องระวัง: <สิ่งที่ลองแล้วพัง หรือกับดักที่เจอ>
- ตรวจด้วย: <คำสั่ง/ภาพ/ผลเทส ที่เป็นหลักฐาน>
- commit: <hash สั้น> บน <branch>
```

---

## 2026-11-27 — ตั้งกฎให้ Claude + โหมดตรวจละเอียด (max-deep)
- คำขอ: "ทำทั้งหมดที่ว่ามา อัพเกรด Max ให้ประเมิน ตรวจสอบงานให้ละเอียดที่สุดเท่าที่ทำได้ก่อนเริ่มงาน ถ้าผมบอก"
- สถานะ: เสร็จ
- ทำอะไร: พิมพ์ "ตรวจละเอียด" / "MAX ละเอียด" แล้ว Claude จะตรวจและวางแผนครบก่อน รอคำว่า "ลุย" แล้วจึงทำแบบ MAX เต็มทุกด่าน
- ไฟล์:
  - `CLAUDE.md` — กฎก่อนเริ่มงาน แผนผังไฟล์ กฎที่ผูกกัน ส่วน Core สิ่งที่ตรวจในเครื่อง cloud ไม่ได้
  - `.claude/skills/max-deep/SKILL.md` — ขั้น D1–D9 (intake → map → baseline → risk → second opinion → ถาม → preflight แล้วหยุด → build → close)
  - `.claude/tools/check-worker-sync.mjs` — ตรวจว่า `worker.js` ตรงกับไฟล์ต้นฉบับ
  - `.gitignore` — `projects/`, `*.ksproject.json`, `.max/`
  - นอก repo: `max-v8.1.zip` (ปลั๊กอิน MAX ที่เพิ่ม max-deep) ส่งให้ผู้ใช้อัปโหลดเอง
- ขั้นตอนที่ได้ผล:
  1. อ่านปลั๊กอิน MAX ที่ `/root/.claude/plugins/synced/*/max-v8/` (SKILL.md, references/ml.md, agents/) ก่อนออกแบบ เพื่อใช้ศัพท์และ agent เดิม
  2. เขียนโหมดใหม่เป็น skill แยก (ไม่แก้ MAX เดิม) แล้วให้ MAX ชี้ไปหา ถ้าผู้ใช้พูดคำสั่ง
  3. เขียน builder ของ `build-worker.ps1` ใหม่ด้วย node แล้วเทียบผลกับ `worker.js` จริง → IN SYNC และทดสอบกรณีกลับด้าน (แก้สำเนา index.html → OUT OF SYNC)
  4. ตรวจทุกคำสั่งที่เขียนใน CLAUDE.md ว่ารันได้จริง (`node --check`, Playwright เปิด file:// ได้โดยไม่มี error)
- ที่ไม่ได้ผล / ต้องระวัง:
  - ไฟล์ปลั๊กอินใน `/root/.claude/plugins/synced/` แก้แล้วไม่ถาวร (เครื่อง cloud ถูกล้าง และ sync ทับ) → ต้องทำเป็น zip ให้ผู้ใช้อัปโหลด
  - skill ใหม่ใน `.claude/skills/` ใช้ได้ตั้งแต่ session **ถัดไป** เท่านั้น
  - PowerShell `AppendLine` เขียน CRLF ใน worker.js → ตอนเทียบต้อง normalize `\r\n`
- เจอระหว่างตรวจ (ยังไม่แก้): `server.ps1` และ `proxy-worker.js` ไม่มี host `dbp.co.th` แต่ `worker.src.js` มี → ตราเพชร SPC ผ่าน start.bat อาจใช้ไม่ได้ (ยังไม่ได้ยืนยันบน Windows)
- ตรวจด้วย: `node .claude/tools/check-worker-sync.mjs` → IN SYNC (exit 0); สำเนาที่แก้ → OUT OF SYNC (exit 1); `node --check worker.src.js proxy-worker.js` ผ่าน; Playwright เปิด index.html ได้ title "ค้นหาสินค้าวัสดุ" ไม่มี page error
- commit: 6280a31 บน ccr-dc26de92-82bie5

## 2026-11-27 — ระบบความจำงาน (worklog + playbook + Stop hook)
- คำขอ: "ให้จำงานทุกครั้ง เวลาผมสั่งงานใหม่ให้จำวิธีสร้าง แล้วเขียนสรุปมาเป็นขั้นตอนที่ได้ผลมาไว้สำหรับงานถัดไป"
- สถานะ: เสร็จ
- ทำอะไร: ทุกงานจะมีบันทึกในไฟล์นี้ และวิธีที่ได้ผลจะสรุปไว้ใน `docs/playbook.md` Claude อ่านก่อนเริ่มงานทุกครั้ง
- ไฟล์:
  - `docs/worklog.md` (ไฟล์นี้), `docs/playbook.md` — ความจำที่ commit ไว้ใน repo (เครื่อง cloud ถูกล้างทุก session)
  - `CLAUDE.md` — หัวข้อ "ความจำงาน": อ่านก่อนเริ่ม เขียนหลังจบ
  - `.claude/hooks/require-worklog.mjs` + `.claude/settings.json` — Stop hook ไม่ให้ Claude จบงานถ้าแก้ไฟล์แล้วยังไม่บันทึก
  - `.claude/skills/max-deep/SKILL.md` — D1 อ่าน playbook/worklog, D9 เขียนบันทึก
- ขั้นตอนที่ได้ผล:
  1. เก็บความจำเป็นไฟล์ใน repo แล้ว commit (ไม่ใช้ memory ของเครื่อง เพราะหายเมื่อปิด session)
  2. hook นับเฉพาะไฟล์ที่ยังไม่ commit + commit ของ Claude (มีคำว่า `Claude-Session`) หลังบันทึกล่าสุด → commit ที่ผู้ใช้แก้เองบน GitHub ไม่ทำให้ hook บล็อก
  3. hook ไม่บล็อกซ้ำ (`stop_hook_active`) และไม่บล็อกเมื่อตัวเอง error
  4. ทดสอบด้วยการส่ง JSON เข้า hook ตรงๆ: `echo '{}' | node .claude/hooks/require-worklog.mjs` → ได้ `decision: block`; `{"stop_hook_active":true}` → เงียบ
- ที่ไม่ได้ผล / ต้องระวัง:
  - `.claude/settings.json` สร้างกลาง session → hook อาจเริ่มทำงานตั้งแต่ session ถัดไป
  - Cowork ไม่มี hook → ใน Cowork ใช้กฎใน CLAUDE.md อย่างเดียว
- ตรวจด้วย: pipe-test ของ hook ทั้ง 3 กรณี (ก่อนบันทึก → block, stop_hook_active → ผ่าน, หลังบันทึกและ commit → ผ่าน) และ `jq -e` ตรวจ settings.json
- commit: (ดู git log — commit เดียวกับไฟล์นี้)
