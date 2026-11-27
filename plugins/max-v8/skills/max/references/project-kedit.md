# MAX — Kedit project rules (read only when the project is Kedit and has the skill `kedit-verify`)
Moved here from ml.md and `max-verifier` (v8.3). Same rules as before; other projects never load this file.

## Where each line applies
- SPEC coverage (ml.md §1, item 3): code used in several places (importers, desktop + `#/web`) → one C-id per place.
- Verifier brief (ml.md §4): `เทส:` = the project check order (Kedit: `kedit-verify` — changed-file tests; the full
  suite only before a release or when it says so).
- Verifier brief (ml.md §4): `build: cd frontend && npm run build` whenever frontend/ changed (worktree: with
  KEDIT_WORKSPACE as the project CLAUDE.md says).
- Bug-hunt sweep (hunt.md): verifier brief `กวาด: <drag, 200 clips, 1366×768, old project, ripple×transition×undo>`
  — code reading misses drags, timing, zoom, 200 clips, 1366×768, old projects and cross-area bugs
  (ripple × transition × undo × timelines).

## max-verifier (Kedit)
- The project's own check steps: `<repo>/.claude/skills/kedit-browser-check/SKILL.md`, `kedit-verify` → Read the file and follow it.
- `เทส:` = the project test command (Kedit: order from `kedit-verify`, tests of the changed files); the full suite only when the brief has `เทสเต็ม:`.
- The installed app (Launcher) can't be driven → `ยังไม่ได้ตรวจ — ต้องเปิดแอปที่ติดตั้งเอง`
- An animated C-id (ซับเคลื่อนไหว…): export for real, ≥ 3 frames at the word's time (`ffmpeg -ss`), compare size/position of the letters between preview and export. One still image = `ยังไม่ได้ตรวจ`
