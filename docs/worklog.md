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

## 2026-11-27 — ปลั๊กอิน MAX v8.2 ที่มีระบบความจำงาน
- คำขอ: "ทำ zip ใหม่ที่มีระบบจำด้วย"
- สถานะ: เสร็จ (รอผู้ใช้อัปโหลด zip เอง)
- ทำอะไร: `max-v8.2.zip` คือ MAX ที่อ่านและเขียน `docs/worklog.md` + `docs/playbook.md` ในทุกโปรเจกต์ สร้างไฟล์ให้เองตอนงานแรก และมี Stop hook ติดมากับปลั๊กอิน
- ไฟล์:
  - ปลั๊กอิน: `skills/max/SKILL.md` (หัวข้อ Project memory แทนบรรทัด LESSONS), `references/ml.md` (§5 close), `agents/max-advisor.md` (อ่าน playbook),
    `references/worklog.template.md`, `references/playbook.template.md`, `hooks/hooks.json`, `hooks/require-worklog.mjs`, `README.md`, version 8.2.0
  - repo: `.claude/hooks/require-worklog.mjs` (เพิ่ม opt-in + หลีกให้สำเนาของโปรเจกต์), `.claude/skills/max-deep/SKILL.md` (D9 สร้างไฟล์จาก template) — ทั้ง 2 ไฟล์เหมือนในปลั๊กอินทุกตัวอักษร
- ขั้นตอนที่ได้ผล:
  1. hook ตัวเดียวใช้ได้ทั้งในโปรเจกต์และในปลั๊กอิน: ไม่ทำงานถ้าโปรเจกต์ไม่มี `docs/worklog.md` (opt-in) และตัวในปลั๊กอินหลีกทางเมื่อโปรเจกต์มี `.claude/hooks/require-worklog.mjs` ของตัวเอง (เทียบ realpath) → ไม่บล็อกซ้ำ 2 ครั้ง
  2. แก้ไฟล์ปลั๊กอินด้วย python ที่ `assert` ว่าข้อความเดิมเจอครั้งเดียว แก้เสร็จแล้ว `claude plugin validate <โฟลเดอร์>` → Validation passed
  3. ทดสอบ hook 5 กรณี: repo สะอาด / แก้แต่ไม่บันทึก → บล็อก / ปลั๊กอินในโปรเจกต์ที่มีสำเนาเอง → หลีก / โปรเจกต์ไม่มี worklog → ผ่าน / มี worklog แต่ไม่บันทึก → บล็อก
- ที่ไม่ได้ผล / ต้องระวัง:
  - คำสั่ง `cp` ที่อยู่บรรทัดถัดจากสคริปต์ที่ล้มเหลวยังทำงานต่อ และคัดลอกไฟล์เก่าทับไฟล์ใหม่ใน repo → กู้คืนด้วย `git checkout --` แล้ว ต่อไปให้ต่อคำสั่งด้วย `&&` หรือ `set -e` และคัดลอกจาก repo ไปปลั๊กอินเท่านั้น
  - `agents/max-advisor.md` ในปลั๊กอินเดิมอ้าง path แบบ Windows (`C:\Users\Acer\.claude\skills\max\references\ml.md`) ซึ่งบนเครื่อง cloud ไม่มี → ยังไม่ได้แก้ (เป็นของเดิม)
  - `claude plugin validate` เตือนว่าไม่มี LICENSE/icon → เรื่องนี้มีผลเฉพาะตอนส่งเข้า directory สาธารณะ ปลั๊กอินส่วนตัวไม่ต้องมี
- ตรวจด้วย: `claude plugin validate` → Validation passed; `cmp` ไฟล์ hook และ max-deep ระหว่าง repo กับปลั๊กอิน → เหมือนกัน; `node --check` hook ผ่าน
- commit: (ดู git log — commit เดียวกับบันทึกนี้)

## 2026-11-27 — แก้ path ของ max-advisor ใน MAX v8.2
- คำขอ: "แก้ path ของ max-advisor ใน v8.2 ด้วย"
- สถานะ: เสร็จ (รอผู้ใช้อัปโหลด `max-v8.2.zip` ตัวใหม่)
- ทำอะไร: advisor ไม่อ้าง `C:\Users\Acer\.claude\skills\max\references\ml.md` แล้ว จึงหา ml.md เจอทั้งบน Windows, Cowork และเครื่อง cloud
- ไฟล์ (ในปลั๊กอิน):
  - `agents/max-advisor.md:13` — อ่าน ml.md จาก `ml:` ใน brief ถ้าไม่มี ให้ Glob `**/skills/max/references/ml.md` ใต้ `~/.claude`
  - `skills/max/references/ml.md:15` — brief ของ advisor ต้องส่ง `ml: <skill folder>/references/ml.md` (path เต็ม)
- ขั้นตอนที่ได้ผล:
  1. ค้น path ที่ผูกกับเครื่องทั้งปลั๊กอินด้วย `grep -rn 'C:\\|Acer|\.claude\\'` เจอจุดเดียว
  2. ให้ main เป็นคนส่ง path จริง (main รู้ตำแหน่ง skill ของตัวเอง) และให้ agent มีทางสำรองเป็น Glob แทนการเดา
  3. ลอง Glob สำรองบนเครื่อง cloud → เจอ `/root/.claude/plugins/synced/…/max-v8/skills/max/references/ml.md`
- ที่ไม่ได้ผล / ต้องระวัง: agent ของปลั๊กอินห้ามเขียน path แบบเต็มของเครื่องใดเครื่องหนึ่ง ให้รับ path จาก brief เสมอ
- ตรวจด้วย: grep ไม่เจอ path ของเครื่องเหลือ; `claude plugin validate` → Validation passed; Glob สำรองเจอไฟล์จริง
- commit: (ดู git log — commit เดียวกับบันทึกนี้)
