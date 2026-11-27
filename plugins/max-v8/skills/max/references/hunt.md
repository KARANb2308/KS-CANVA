# MAX — 3b Bug hunt / audit ("หาบัคทั้งหมด", "ตรวจทั้งแอป", "ติแบบมืออาชีพ")
Moved from ml.md (v8.3). Read when the job is a hunt or audit. Sizes, Team, bugs (§3) stay in `../SKILL.md`.

1. List the areas (NOTES / `docs/rules`), **group into ≤ 6**. More → a second round after the first is fixed.
2. `max-hunter` per group: 4 in one message, groups 5–6 when one returns. Brief: `area:` · `files:` (ranges) ·
   `ผู้ใช้ดูที่:` · `rules:` · `findings: <dir>/<area>-found.md` (the hunter writes the full list there and replies only `FOUND: n` + the path). Nothing else.
3. Code reading misses drags, timing, zoom, big data, small screens, old projects and cross-area bugs (e.g. several
   features combined with undo): one `max-verifier` sweep of the real screen covers those, in the same message
   as the first hunters (verifier brief `กวาด: <drag, big data, small screen, old project, combined features>`, `findings: <path>`,
   no SPEC; it answers in the hunter `FOUND:` format); hunters' "ตรวจจากโค้ดไม่ได้" become C-ids for the verifier after the fixes.
   Kedit project → its sweep list is in `project-kedit.md`.
4. `FOUND` lists → SPEC tasks (no duplicates, `ร้ายแรง` first; > ~15 fixes → an M SPEC by main from the findings files; Core / unclear way → L, advisor only then). The report lists each
   area `ตรวจแล้ว / ยังไม่ได้ตรวจ` — never "ไม่มีบัคแล้ว".
