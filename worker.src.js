// KS HOME Material Selection: the online version, as one Cloudflare Worker.
// Does what start.bat / server.ps1 do on one computer, for the whole team:
//   - asks for the team password before showing anything
//   - serves the page (index.html) and the user guide
//   - /proxy: reads the shop websites that block cross-site requests
//   - /api/projects: keeps every customer project in Workers KV, shared by the team
//
// worker.js is built from this file by build-worker.bat (it puts index.html and the guide inside).
// Set up once in the Cloudflare dashboard (see คู่มือติดตั้งระบบออนไลน์.md):
//   - Secret      APP_PASSWORD : the team password
//   - KV binding  PROJECTS     : where the projects are kept

const PAGE_HTML = __INDEX_HTML__;
const GUIDE_HTML = __GUIDE_HTML__;

const SESSION_COOKIE = 'ks_session';
const SESSION_DAYS = 14;
const TRASH_DAYS = 30;
const PROJECT_PREFIX = 'project:';
const TRASH_PREFIX = 'deleted:';
const MAX_PROJECT_BYTES = 25 * 1024 * 1024 - 64 * 1024; // KV keeps values up to 25 MiB
const ID_RE = /^[a-z0-9-]{3,64}$/;
const ALLOWED_HOSTS = new Set([
  'www.boonthavorn.com',
  'www.homepro.co.th', 'homepro.co.th', 'statice.homepro.co.th',
  'traphet.com', 'www.traphet.com',
  'www.eco-door.net', 'eco-door.net',
  'www.dbp.co.th', 'dbp.co.th', 'cdn.dbp.co.th',
]);
const FETCH_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36',
  'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
};
const PAGE_HEADERS = {
  'Content-Type': 'text/html; charset=utf-8',
  'Cache-Control': 'no-store',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'same-origin',
  'X-Robots-Tag': 'noindex, nofollow',
};
// The small pages this file draws itself (login, trash) run no scripts at all.
const SMALL_PAGE_CSP = "default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src data:; form-action 'self'; frame-ancestors 'none'; base-uri 'none'";

const enc = new TextEncoder();

export default {
  async fetch(request, env) {
    try {
      return await route(request, env);
    } catch (err) {
      return notice(500, 'เกิดข้อผิดพลาดในระบบ: ' + ((err && err.message) || err));
    }
  },
};

async function route(request, env) {
  const url = new URL(request.url);
  const path = url.pathname;

  if (path === '/robots.txt') return plain(200, 'User-agent: *\nDisallow: /\n');
  if (path === '/favicon.ico') return new Response(null, { status: 204 });
  if (!env.APP_PASSWORD) return smallPage(500, 'ยังตั้งค่าไม่ครบ', setupMissingBody());

  if (path === '/login') {
    if (request.method === 'POST') return login(request, env);
    if (await hasSession(request, env)) return redirect('/');
    return smallPage(200, 'เข้าสู่ระบบ', loginBody(''));
  }
  if (path === '/logout') return logout();

  if (!(await hasSession(request, env))) {
    // The page's own requests get a plain answer; people get the login page.
    if (path === '/proxy' || path === '/proxy-status' || path.startsWith('/api/')) return notice(401, 'กรุณาเข้าสู่ระบบ');
    return redirect('/login');
  }

  if (path === '/proxy-status') return plain(200, 'ok', { 'X-KS-Host': 'cloud' });
  if (path === '/proxy') return request.method === 'GET' || request.method === 'HEAD' ? proxy(url) : plain(405, 'Method not allowed');
  if (path === '/api/projects' || path.startsWith('/api/projects/')) return projects(request, env, path);
  if (path === '/trash') return request.method === 'POST' ? restoreFromTrash(request, env, url) : trashPage(env, url);
  if (path === '/' || path === '/index.html') return new Response(PAGE_HTML, { headers: PAGE_HEADERS });
  if (GUIDE_HTML && path.endsWith('.html')) return new Response(GUIDE_HTML, { headers: PAGE_HEADERS });
  return plain(404, 'Not found');
}

// ---------- Responses ----------
function plain(status, body, extra = {}) {
  return new Response(body, {
    status,
    headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', ...extra },
  });
}
// A message the page shows to the user as it is.
const notice = (status, message) => plain(status, message, { 'X-KS-Message': '1' });
const redirect = (location, extra = {}) =>
  new Response(null, { status: 303, headers: { Location: location, 'Cache-Control': 'no-store', ...extra } });
const json = (value) =>
  new Response(JSON.stringify(value), { headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' } });

// ---------- Team password and session ----------
// The session cookie is "<expiry>.<signature>", signed with a key made from the password,
// so changing APP_PASSWORD signs everyone out.
const failures = new Map(); // ip -> { count, until }: slows down password guessing

function hmacKey(secret) {
  return crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign', 'verify']);
}
const sessionKey = (env) => hmacKey('ks-session|' + env.APP_PASSWORD);

function b64url(buf) {
  let s = '';
  for (const b of new Uint8Array(buf)) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function fromB64url(s) {
  const bin = atob(s.replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

function readCookie(request, name) {
  for (const part of (request.headers.get('Cookie') || '').split(';')) {
    const i = part.indexOf('=');
    if (i > 0 && part.slice(0, i).trim() === name) return part.slice(i + 1).trim();
  }
  return '';
}

async function hasSession(request, env) {
  const m = /^(\d{13})\.([A-Za-z0-9_-]{43})$/.exec(readCookie(request, SESSION_COOKIE));
  if (!m || Number(m[1]) < Date.now()) return false;
  return crypto.subtle.verify('HMAC', await sessionKey(env), fromB64url(m[2]), enc.encode('session:' + m[1]));
}

async function newSessionCookie(env) {
  const exp = Date.now() + SESSION_DAYS * 86400000;
  const sig = await crypto.subtle.sign('HMAC', await sessionKey(env), enc.encode('session:' + exp));
  return `${SESSION_COOKIE}=${exp}.${b64url(sig)}; Path=/; Max-Age=${SESSION_DAYS * 86400}; HttpOnly; Secure; SameSite=Lax`;
}

// Compares signatures of the two passwords, so the time taken says nothing about the password.
async function samePassword(given, real) {
  const key = await hmacKey('ks-compare');
  const [a, b] = await Promise.all([given, real].map((s) => crypto.subtle.sign('HMAC', key, enc.encode(s))));
  const x = new Uint8Array(a);
  const y = new Uint8Array(b);
  let diff = 0;
  for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0;
}

async function login(request, env) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const now = Date.now();
  const f = failures.get(ip);
  if (f && f.count >= 5 && f.until > now) {
    return smallPage(429, 'เข้าสู่ระบบ', loginBody('ใส่รหัสผ่านผิดหลายครั้ง กรุณารอ 10 นาทีแล้วลองใหม่'));
  }
  let password = '';
  try { password = String((await request.formData()).get('password') || ''); } catch (_) { password = ''; }
  if (!password || !(await samePassword(password, String(env.APP_PASSWORD)))) {
    if (!f || f.until < now) failures.set(ip, { count: 1, until: now + 10 * 60000 });
    else f.count++;
    if (failures.size > 5000) failures.clear();
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return smallPage(401, 'เข้าสู่ระบบ', loginBody('รหัสผ่านไม่ถูกต้อง'));
  }
  failures.delete(ip);
  return redirect('/', { 'Set-Cookie': await newSessionCookie(env) });
}

function logout() {
  return redirect('/login', { 'Set-Cookie': `${SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax` });
}

// ---------- Shop websites (same allowlist as server.ps1) ----------
function allowedTarget(raw, base) {
  try {
    const u = base ? new URL(raw, base) : new URL(raw);
    return u.protocol === 'https:' && !u.port && !u.username && !u.password && ALLOWED_HOSTS.has(u.hostname) ? u : null;
  } catch (_) {
    return null;
  }
}

async function proxy(url) {
  let target = allowedTarget(url.searchParams.get('url') || '');
  if (!target) return plain(403, 'This address is not allowed.');
  try {
    // Redirects are followed here, and only to the same list of websites.
    for (let hop = 0; hop < 5; hop++) {
      const res = await fetch(target.href, { headers: FETCH_HEADERS, redirect: 'manual' });
      const location = res.headers.get('Location');
      if (res.status >= 300 && res.status < 400 && location) {
        target = allowedTarget(location, target);
        if (!target) return plain(403, 'This address is not allowed.');
        continue;
      }
      const headers = {
        'Content-Type': res.headers.get('Content-Type') || 'application/octet-stream',
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
        // Opened straight in the browser, a fetched page must not run as part of this site.
        'Content-Security-Policy': "sandbox; default-src 'none'",
      };
      const noBody = [101, 204, 205, 304].includes(res.status);
      return new Response(noBody ? null : res.body, { status: res.status, headers });
    }
    return plain(508, 'Too many redirects');
  } catch (err) {
    return plain(502, 'Fetch failed: ' + ((err && err.message) || err));
  }
}

// ---------- Projects ----------
// "project:<id>" holds the whole project as the page sent it; its summary (customer,
// project name, item count, times) rides along as KV metadata, so the list is one read.
// Deleted projects move to "deleted:<id>" and disappear by themselves after TRASH_DAYS.
async function projects(request, env, path) {
  // Only the page sends this header; other websites can't add it to a request.
  if (request.headers.get('X-KS-App') !== '1') return plain(403, 'Forbidden');
  if (!env.PROJECTS) return notice(500, 'ยังไม่ได้เชื่อมที่เก็บโปรเจกต์ (KV namespace ชื่อ PROJECTS) ใน Cloudflare');
  const kv = env.PROJECTS;
  const method = request.method;
  const parts = path.slice('/api/projects'.length).split('/').filter(Boolean);

  if (!parts.length) {
    if (method !== 'GET') return plain(405, 'Method not allowed');
    return json(await listSummaries(kv, PROJECT_PREFIX));
  }
  const id = parts[0];
  if (parts.length > 1 || !ID_RE.test(id)) return plain(400, 'Bad project id');
  const key = PROJECT_PREFIX + id;

  if (method === 'GET') {
    const value = await kv.get(key, { type: 'stream' });
    if (!value) return notice(404, 'ไม่พบโปรเจกต์นี้ (อาจถูกลบไปแล้ว)');
    return new Response(value, { headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' } });
  }
  if (method === 'PUT') {
    const meta = cleanSummary(request.headers.get('X-KS-Meta'), id);
    if (!meta) return plain(400, 'Missing project summary');
    // Stored exactly as received: no parsing, so a big project costs almost no CPU time.
    const body = await request.arrayBuffer();
    if (!body.byteLength) return plain(400, 'Empty project');
    if (body.byteLength > MAX_PROJECT_BYTES) {
      return notice(413, 'โปรเจกต์นี้ใหญ่เกิน 25 MB จึงบันทึกออนไลน์ไม่ได้ ลองลดจำนวนรูปภาพประกอบ หรือแยกเป็นหลายโปรเจกต์');
    }
    try {
      await kv.put(key, body, { metadata: meta });
    } catch (err) {
      return kvFailed(err);
    }
    return plain(200, 'saved');
  }
  if (method === 'DELETE') {
    try {
      const found = await kv.getWithMetadata(key, { type: 'arrayBuffer' });
      if (found.value) {
        const meta = { ...(found.metadata || { id }), deletedAt: new Date().toISOString() };
        await kv.put(TRASH_PREFIX + id, found.value, { metadata: meta, expirationTtl: TRASH_DAYS * 86400 });
        await kv.delete(key);
      }
    } catch (err) {
      return kvFailed(err);
    }
    return plain(200, 'deleted');
  }
  return plain(405, 'Method not allowed');
}

function kvFailed(err) {
  const msg = String((err && err.message) || err);
  if (/limit|quota|429|too many/i.test(msg)) {
    return notice(429, 'วันนี้บันทึกครบโควต้าฟรีของ Cloudflare แล้ว (1,000 ครั้งต่อวัน) จะบันทึกได้อีกครั้งหลัง 07:00 น.');
  }
  return notice(500, 'บันทึกในระบบออนไลน์ไม่สำเร็จ: ' + msg);
}

// The summary the page sends with each save (X-KS-Meta), cut to fit KV's 1 KB of metadata.
function cleanSummary(header, id) {
  let m = null;
  try { m = JSON.parse(decodeURIComponent(header || '')); } catch (_) { return null; }
  if (!m || m.id !== id) return null;
  const str = (v, n) => String(v == null ? '' : v).slice(0, n);
  const num = (v) => (Number.isFinite(Number(v)) ? Number(v) : 0);
  const meta = {
    id,
    project: str(m.project, 120),
    owner: str(m.owner, 120),
    items: num(m.items),
    pages: num(m.pages),
    createdAt: str(m.createdAt, 40),
    updatedAt: str(m.updatedAt, 40),
  };
  // Leave room for "deletedAt" when the project goes to the trash.
  while (enc.encode(JSON.stringify(meta)).length > 900) {
    meta.project = meta.project.slice(0, -10);
    meta.owner = meta.owner.slice(0, -10);
  }
  return meta;
}

async function listSummaries(kv, prefix) {
  const out = [];
  let cursor;
  do {
    const page = await kv.list({ prefix, cursor });
    for (const k of page.keys) if (k.metadata && k.metadata.id) out.push(k.metadata);
    cursor = page.list_complete ? null : page.cursor;
  } while (cursor);
  return out;
}

// ---------- Trash: deleted projects, restorable for TRASH_DAYS ----------
async function trashPage(env, url) {
  if (!env.PROJECTS) return smallPage(500, 'โปรเจกต์ที่ลบ', '<p class="msg bad">ยังไม่ได้เชื่อมที่เก็บโปรเจกต์ (KV namespace ชื่อ PROJECTS)</p>');
  const items = (await listSummaries(env.PROJECTS, TRASH_PREFIX))
    .sort((a, b) => String(b.deletedAt || '').localeCompare(String(a.deletedAt || '')));
  const when = (iso) => {
    const d = new Date(iso);
    return isNaN(d) ? '-' : d.toLocaleString('th-TH', { timeZone: 'Asia/Bangkok', dateStyle: 'medium', timeStyle: 'short' });
  };
  const label = (m) => `${m.owner || 'ยังไม่ระบุลูกค้า'} — ${m.project || 'ยังไม่ตั้งชื่อโครงการ'}`;
  const done = url.searchParams.get('done');
  const error = url.searchParams.get('error');
  const msg = done
    ? '<p class="msg ok">กู้คืนแล้ว กลับไปหน้าหลักแล้วเลือกจากรายการ “โปรเจกต์ลูกค้า” (อาจใช้เวลาไม่เกิน 1 นาทีจึงจะเห็นในรายการ)</p>'
    : error === 'exists'
      ? '<p class="msg bad">กู้คืนไม่ได้ เพราะยังมีโปรเจกต์นี้อยู่ในรายการ</p>'
      : error ? '<p class="msg bad">กู้คืนไม่สำเร็จ ลองใหม่อีกครั้ง</p>' : '';
  const rows = items.map((m) => `<li>
      <div><strong>${esc(label(m))}</strong><span>${m.items || 0} รายการ · ลบเมื่อ ${esc(when(m.deletedAt))}</span></div>
      <form method="post" action="/trash"><input type="hidden" name="id" value="${esc(m.id)}"><button type="submit">กู้คืน</button></form>
    </li>`).join('');
  return smallPage(200, 'โปรเจกต์ที่ลบ', `
    <h1>โปรเจกต์ที่ลบ</h1>
    <p class="sub">เก็บไว้ ${TRASH_DAYS} วันนับจากวันที่ลบ แล้วระบบจะลบทิ้งเอง</p>
    ${msg}
    ${rows ? `<ul class="trash">${rows}</ul>` : '<p class="sub">ไม่มีโปรเจกต์ที่ลบ</p>'}
    <p><a href="/">← กลับหน้าหลัก</a></p>`, true);
}

async function restoreFromTrash(request, env, url) {
  // A form on another website can't use this (the cookie is SameSite=Lax too).
  const origin = request.headers.get('Origin');
  const fromHere = origin ? origin === url.origin
    : request.headers.get('Sec-Fetch-Site') === 'same-origin' || (request.headers.get('Referer') || '').startsWith(url.origin + '/');
  if (!fromHere) return plain(403, 'Forbidden');
  if (!env.PROJECTS) return redirect('/trash?error=1');
  let id = '';
  try { id = String((await request.formData()).get('id') || ''); } catch (_) { id = ''; }
  if (!ID_RE.test(id)) return redirect('/trash?error=1');
  const kv = env.PROJECTS;
  try {
    const existing = await kv.get(PROJECT_PREFIX + id, { type: 'stream' });
    if (existing) {
      await existing.cancel();
      return redirect('/trash?error=exists');
    }
    const found = await kv.getWithMetadata(TRASH_PREFIX + id, { type: 'arrayBuffer' });
    if (!found.value) return redirect('/trash?error=1');
    const meta = { ...(found.metadata || { id }) };
    delete meta.deletedAt;
    await kv.put(PROJECT_PREFIX + id, found.value, { metadata: meta });
    await kv.delete(TRASH_PREFIX + id);
  } catch (_) {
    return redirect('/trash?error=1');
  }
  return redirect('/trash?done=1');
}

// ---------- Small pages: login, trash, setup ----------
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

let logoSrc = null;
// The KS HOME logo already inside index.html.
function logo() {
  if (logoSrc === null) {
    const m = /DEFAULT_LOGO = \{ data: '(data:image\/png;base64,[A-Za-z0-9+/=]+)'/.exec(PAGE_HTML);
    logoSrc = m ? m[1] : '';
  }
  return logoSrc ? `<img class="logo" src="${logoSrc}" alt="KS HOME">` : '';
}

function loginBody(error) {
  return `
    ${logo()}
    <h1>ระบบเลือกวัสดุ KS HOME</h1>
    <p class="sub">ใส่รหัสผ่านของทีมเพื่อเข้าใช้งาน</p>
    <form method="post" action="/login">
      <label for="pw">รหัสผ่าน</label>
      <input id="pw" name="password" type="password" autocomplete="current-password" required autofocus>
      ${error ? `<p class="msg bad" role="alert">${esc(error)}</p>` : ''}
      <button type="submit">เข้าสู่ระบบ</button>
    </form>
    <p class="note">ไม่ทราบรหัสผ่าน สอบถามผู้ดูแลระบบของบริษัท</p>`;
}

function setupMissingBody() {
  return `
    <h1>ยังตั้งค่าไม่ครบ</h1>
    <p class="msg bad">ยังไม่ได้ตั้งรหัสผ่านของทีม</p>
    <p>ผู้ดูแลระบบ: เข้า Cloudflare → Workers &amp; Pages → เลือก Worker นี้ → <strong>Settings</strong> → <strong>Variables and Secrets</strong> → <strong>Add</strong>
      เลือกชนิด <strong>Secret</strong> ชื่อ <code>APP_PASSWORD</code> ใส่รหัสผ่านของทีม แล้วกด <strong>Deploy</strong></p>`;
}

function smallPage(status, title, body, wide = false) {
  const html = `<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>${esc(title)} · KS HOME</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #f6f5f2; --surface: #ffffff; --surface-2: #f1efea; --text: #1d1d1b; --muted: #6b6a65; --border: #e3e0d9;
    --accent: #0f6e5c; --accent-hover: #0b5a4b; --accent-ink: #ffffff; --accent-soft: #e2f1ec;
    --ok: #1f7a3a; --ok-soft: #e3f3e7; --bad: #b4321f; --bad-soft: #fbe8e4;
    color-scheme: light;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #141413; --surface: #1e1e1c; --surface-2: #282826; --text: #ecebe6; --muted: #a3a19a; --border: #363531;
      --accent: #4fbfa5; --accent-hover: #6fd0b9; --accent-ink: #0b1f1a; --accent-soft: #17322c;
      --ok: #74d18f; --ok-soft: #173022; --bad: #f29482; --bad-soft: #3a1d18;
      color-scheme: dark;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px 16px;
    background: var(--bg); color: var(--text); line-height: 1.6;
    font-family: "IBM Plex Sans Thai", "Leelawadee UI", "Noto Sans Thai", Tahoma, system-ui, sans-serif;
  }
  main {
    width: 100%; max-width: ${wide ? 640 : 400}px; padding: 28px 24px;
    background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, .04), 0 6px 20px rgba(0, 0, 0, .05);
  }
  .logo { display: block; width: 72px; height: auto; margin: 0 auto 12px; padding: 6px; background: #fff; border-radius: 10px; }
  h1 { margin: 0; font-size: 1.35rem; line-height: 1.3; text-align: ${wide ? 'left' : 'center'}; }
  .sub { margin: 4px 0 18px; color: var(--muted); font-size: .9rem; text-align: ${wide ? 'left' : 'center'}; }
  label { display: block; font-weight: 600; font-size: .9rem; margin-bottom: 6px; }
  input[type="password"] {
    width: 100%; padding: 11px 14px; font: inherit; color: var(--text); background: var(--surface);
    border: 1.5px solid var(--border); border-radius: 10px; outline: none;
  }
  input[type="password"]:focus { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-soft); }
  button {
    font: inherit; font-weight: 600; color: var(--accent-ink); background: var(--accent);
    border: 0; border-radius: 10px; cursor: pointer; padding: 10px 18px;
  }
  button:hover { background: var(--accent-hover); }
  button:focus-visible, a:focus-visible, input:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
  form button { width: 100%; margin-top: 14px; min-height: 46px; }
  .msg { margin: 12px 0 0; padding: 10px 12px; border-radius: 10px; font-size: .9rem; }
  .msg.bad { background: var(--bad-soft); color: var(--bad); }
  .msg.ok { background: var(--ok-soft); color: var(--ok); }
  .note { margin: 16px 0 0; font-size: .8rem; color: var(--muted); text-align: center; }
  a { color: var(--accent); }
  code { padding: 1px 6px; border-radius: 5px; background: var(--surface-2); font-size: .9em; }
  .trash { list-style: none; margin: 16px 0; padding: 0; }
  .trash li { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 0; border-top: 1px solid var(--border); }
  .trash li div { min-width: 0; }
  .trash strong { display: block; overflow-wrap: anywhere; }
  .trash span { font-size: .85rem; color: var(--muted); }
  .trash form button { width: auto; margin: 0; min-height: 0; padding: 7px 14px; font-size: .9rem; }
</style>
</head>
<body>
<main>${body}</main>
</body>
</html>`;
  return new Response(html, { status, headers: { ...PAGE_HEADERS, 'Content-Security-Policy': SMALL_PAGE_CSP } });
}
