# Playbook — ขั้นตอนที่ได้ผล (อ่านก่อนเริ่มงาน)

สูตรทำงานแยกตามประเภทงาน กลั่นจาก `docs/worklog.md`
- **ได้ผล (วันที่)** = ใช้จริงแล้วผ่าน · **ยังไม่ได้ลองจริง** = มาจากการอ่านโค้ด ใช้ด้วยความระวัง แล้วอัปเดตหลังลอง
- จบงานแล้ว ถ้าได้วิธีใหม่ เจอกับดัก หรือพบว่าสูตรเดิมผิด → แก้ข้อนั้นในไฟล์นี้ (สั้น ใช้ซ้ำได้ ไม่ใช่เล่าเรื่อง)

## 0. ทุกงาน — เริ่มและจบ
**ได้ผล (2026-11-27)**
1. `python3 plugins/max-v8/skills/max/scripts/max_lite.py status` (หรืออ่าน `docs/roadmap.md`) → รู้งานค้าง/รอผู้ใช้/ถัดไปใน 1 คำสั่ง
   → อ่าน `CLAUDE.md` → ไฟล์นี้ → `grep -n "<คำสำคัญของงาน>" docs/worklog.md` ดูงานที่คล้ายกัน
2. `git status --short` และ `git log --oneline -10` ดูว่ามีงานค้างไหม หรือผู้ใช้แก้อะไรบน GitHub มาก่อน
3. ทำงาน (ผู้ใช้พูด "ตรวจละเอียด" → skill `max-deep`, พูด "MAX" → skill `max`)
4. ตรวจด้วยหลักฐานจริง (ข้อ 5)
5. ต่อท้าย `docs/worklog.md` + อัปเดตไฟล์นี้ → commit พร้อมงาน → push ไป branch ที่กำหนด

## 1. แก้หน้าเว็บ (`index.html`)
**ยังไม่ได้ลองจริง**
1. `index.html` ใหญ่ (~270 KB) ให้ Grep หาจุดก่อน แล้ว Read เป็นช่วง ห้ามเขียนทับทั้งไฟล์
2. ค่าคงที่ของแหล่งสินค้าอยู่ราว `index.html:925` (`SOURCES`, `SOURCE_UI`, `WOO_BASE`)
3. หลังแก้ ให้เปิดด้วย Playwright (`file:///…/index.html`) จับ `pageerror` และถ่ายภาพก่อน/หลัง
4. ส่วนที่ต้องใช้ proxy (HomePro, รูปตราเพชร/Eco door) ตรวจผ่าน file:// ไม่ได้ → ให้บอกผู้ใช้
5. `node .claude/tools/check-worker-sync.mjs` → จะ OUT OF SYNC เสมอหลังแก้ → บอกผู้ใช้ให้รัน `build-worker.bat` แล้ววาง `worker.js` ใน Cloudflare

## 2. เพิ่มหรือแก้แหล่งสินค้า (ร้านใหม่ / host ใหม่)
**ยังไม่ได้ลองจริง**
1. host ต้องเพิ่มให้ครบ **3 ที่**: `worker.src.js` (`ALLOWED_HOSTS`), `server.ps1` (`$allowedHosts`), `proxy-worker.js` (`ALLOWED_HOSTS`)
   ตรวจด้วย `grep -n "<host>" worker.src.js server.ps1 proxy-worker.js` ต้องเจอครบทั้ง 3 ไฟล์
2. ใน `index.html`: `SOURCES` + `SOURCE_UI` + ปุ่ม radio `name="source"` (ราว `index.html:704`) + ฟังก์ชันค้นหาของแหล่งนั้น
3. อัปเดตตารางใน README (เปิดผ่าน start.bat / เปิดไฟล์โดยตรง)
4. กับดักที่รู้แล้ว: `dbp.co.th` มีใน `worker.src.js` แต่ไม่มีใน `server.ps1` / `proxy-worker.js` (พบ 2026-11-27 ยังไม่แก้)

## 3. แก้ระบบออนไลน์ (`worker.src.js`)
**ยังไม่ได้ลองจริง**
1. เป็นส่วน Core (รหัสผ่าน, session, KV, ถังขยะ) → ใช้ MAX ขนาด L หรือ "ตรวจละเอียด"
2. `node --check worker.src.js` ต้องผ่าน (placeholder `__INDEX_HTML__` ยังเป็น syntax ที่ถูก)
3. ห้ามเปลี่ยนรูปแบบข้อมูลใน KV จนโปรเจกต์เก่าเปิดไม่ได้ → ทดสอบ: โหลดข้อมูลเก่า → บันทึก → โหลด ต้องได้เท่าเดิม
4. แก้เสร็จแล้วต้อง rebuild `worker.js` (ข้อ 1.5)

## 4. ตั้งค่า Claude / skill / hook ของโปรเจกต์
**ได้ผล (2026-11-27)**
1. skill ของโปรเจกต์อยู่ที่ `.claude/skills/<ชื่อ>/SKILL.md` (frontmatter `name` + `description` ที่บอกว่าใช้เมื่อไหร่) → ใช้ได้ session ถัดไป
2. ต้นฉบับ MAX อยู่ที่ `plugins/max-v8/` ใน repo นี้ (marketplace `ks-home`) → แก้ที่นี่ เพิ่ม version ทั้งใน `plugins/max-v8/.claude-plugin/plugin.json` และ `.claude-plugin/marketplace.json`
   → `claude plugin validate .` → commit/push → เครื่องผู้ใช้รัน `/plugin marketplace update ks-home` · zip สำหรับ claude.ai/Cowork: `cd plugins && zip -r max-v8.zip max-v8`
   ปลั๊กอินที่ sync จากบัญชี (`/root/.claude/plugins/synced/…`) แก้แล้วไม่ถาวร อย่าแก้ตรงนั้น
3. hook อยู่ใน `.claude/settings.json` ทดสอบด้วยการส่ง JSON เข้า stdin ก่อนเสมอ และต้องไม่บล็อกเมื่อตัวเอง error
4. ทุกคำสั่งที่เขียนในเอกสารให้ Claude ใช้ ต้องลองรันจริงก่อน commit
5. แก้ปลั๊กอิน MAX: แก้ในสำเนาที่ scratchpad เท่านั้น ใช้ python ที่ `assert` ว่าข้อความเดิมเจอครั้งเดียว → `claude plugin validate <โฟลเดอร์>` → zip
   ไฟล์ที่มีทั้งใน repo และในปลั๊กอิน (`require-worklog.mjs`, `max-deep/SKILL.md`) ให้แก้ที่ repo แล้วคัดลอก repo → ปลั๊กอิน ห้ามคัดลอกย้อนกลับ ตรวจด้วย `cmp`
6. อัปเกรด MAX (ได้ผล 2026-11-27): สำรองทั้งโฟลเดอร์ใน `.max/<job>/before-…/` → แก้ → `python3 plugins/max-v8/skills/max/scripts/test_max_lite.py`
   → `claude plugin validate .` → ลองงานจริง: git repo ทิ้งได้ + `claude -p "MAX ขนาด M: …" --plugin-dir plugins/max-v8 --allowedTools Read Write Edit Glob Grep Agent Skill "Bash(python3:*)" "Bash(git:*)" --output-format json`
   (ห้าม bypassPermissions — ถูกปฏิเสธ) → reviewer เทียบกฎเดิม↔ใหม่ → `/code-review high` (เจอบั๊กที่ reviewer พลาด คุ้ม) · ไฟล์ agent มีท้ายบรรทัด LF/CRLF ผสม ห้ามแปลงทั้งไฟล์
   · แถว proof ต้องเป็น `C<n> ผ่าน — <หลักฐาน ≥ 8 ตัว>` · ชื่อไฟล์ไทยกับ git ต้อง `-c core.quotePath=false`
6b. agent/skill ห้ามเขียน path เต็มของเครื่องใดเครื่องหนึ่ง (เช่น `C:\Users\...`) → ให้ main ส่ง path ใน brief + ทางสำรองเป็น Glob ตรวจทั้งปลั๊กอินด้วย grep ก่อน zip (เจอ 2026-11-27)
7. สคริปต์หลายขั้นต้องหยุดทันทีเมื่อขั้นใดล้มเหลว (`set -e` หรือต่อด้วย `&&`) ไม่อย่างนั้นขั้นถัดไปอาจเขียนทับไฟล์ผิด (เจอ 2026-11-27)

## 5. วิธีตรวจที่ใช้ได้ในเครื่อง cloud
**ได้ผล (2026-11-27)**
- `node .claude/tools/check-worker-sync.mjs` → IN SYNC / OUT OF SYNC
- `node --check worker.src.js` / `node --check proxy-worker.js`
- Playwright: `chromium.launch()` → `page.goto('file:///home/user/KS-CANVA/index.html')` → ฟัง `pageerror`, `screenshot`
- ตรวจไม่ได้: `start.bat` / `server.ps1` / `build-worker.ps1` (ต้องใช้ Windows), Cloudflare จริง, เว็บร้านค้าที่เครือข่ายอาจบล็อก
