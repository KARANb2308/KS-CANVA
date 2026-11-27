// Stop hook: Claude may not finish while its own work is not yet in docs/worklog.md.
// "Its own work" = files changed but not committed, plus files in commits made by Claude
// (commit message carries "Claude-Session") since docs/worklog.md was last committed.
// The user's own commits (e.g. edits on github.com) never trigger it.
// Never blocks twice in a row (stop_hook_active), and never blocks on its own errors.
// Opt-in: does nothing in a project without docs/worklog.md (MAX creates it on the first job).
// The same file ships in the MAX plugin and in a project's .claude/hooks/: when the project has
// its own copy, the plugin's copy steps aside so the check runs once.
import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync, realpathSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const LOG = 'docs/worklog.md';
const IGNORE = [/^docs\//, /^\.max\//];

function git(args, cwd) {
  return execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
}
const lines = s => (s ? s.split('\n').map(x => x.trim()).filter(Boolean) : []);

let input = {};
async function readStdin() {
  if (process.stdin.isTTY) return '';
  let data = '';
  for await (const chunk of process.stdin) data += chunk;
  return data;
}

try {
  try { input = JSON.parse(await readStdin()); } catch { input = {}; }
  if (input.stop_hook_active) process.exit(0);

  const cwd = process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd();
  git(['rev-parse', '--is-inside-work-tree'], cwd);

  const projectCopy = path.join(cwd, '.claude', 'hooks', 'require-worklog.mjs');
  const self = realpathSync(fileURLToPath(import.meta.url));
  if (existsSync(projectCopy) && realpathSync(projectCopy) !== self) process.exit(0);
  if (!existsSync(path.join(cwd, LOG))) process.exit(0);

  // an open MAX job (.max/<job>/ledger.md, not .max/closed) means MAX will draft the worklog at close
  try {
    const md = path.join(cwd, '.max');
    for (const e of readdirSync(md, { withFileTypes: true })) {
      if (e.isDirectory() && e.name !== 'closed' && existsSync(path.join(md, e.name, 'ledger.md'))) process.exit(0);
    }
  } catch {}

  const changed = new Set();
  // not committed yet (staged, unstaged, new files)
  for (const f of lines(git(['diff', '--name-only', 'HEAD'], cwd))) changed.add(f);
  for (const f of lines(git(['ls-files', '--others', '--exclude-standard'], cwd))) changed.add(f);

  // committed by Claude after the last worklog commit
  const last = git(['log', '-1', '--format=%H', '--', LOG], cwd);
  const range = last ? [`${last}..HEAD`] : ['HEAD'];
  const claudeCommits = lines(git(['log', '--format=%H', '--grep=Claude-Session', ...range], cwd));
  for (const c of claudeCommits) {
    for (const f of lines(git(['show', '--name-only', '--format=', c], cwd))) changed.add(f);
  }

  if (changed.has(LOG)) process.exit(0); // the log is being updated in this change
  const work = [...changed].filter(f => !IGNORE.some(re => re.test(f)));
  if (work.length === 0) process.exit(0);

  const list = work.slice(0, 15).join(', ') + (work.length > 15 ? ` … (+${work.length - 15})` : '');
  process.stdout.write(JSON.stringify({
    decision: 'block',
    reason:
      `ยังไม่ได้บันทึกงานนี้ใน ${LOG} (ไฟล์ที่เปลี่ยน: ${list}). ` +
      'ตามระบบความจำงาน (CLAUDE.md / skill max): เพิ่มบันทึกงานต่อท้าย docs/worklog.md ' +
      '(คำขอ · ทำอะไร · ไฟล์ · ขั้นตอนที่ได้ผล · ที่ไม่ได้ผล/ระวัง · ตรวจด้วย · ค้าง) ' +
      'และอัปเดต docs/playbook.md ถ้าได้วิธีใหม่ที่ใช้ซ้ำได้ แล้ว commit ไปพร้อมงาน ' +
      'ถ้างานยังไม่เสร็จหรือผู้ใช้ยังไม่อนุมัติ ให้บันทึกสถานะเป็น "ค้าง" ได้',
  }));
} catch {
  process.exit(0); // never block on the hook's own failure
}
