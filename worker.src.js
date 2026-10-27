// =====================================================================
// KS Material Selection - ระบบออนไลน์บน Cloudflare Workers
//
// นี่คือไฟล์ต้นฉบับ (worker.src.js) ที่ยังไม่มีหน้าเว็บฝังอยู่
// ดับเบิลคลิก build-worker.bat เพื่อฝัง index.html และคู่มือการใช้งาน (.html)
// ลงไป จะได้ worker.js (ไฟล์เดียวจบ) สำหรับวางใน Cloudflare
//
// ทำอะไรได้
//   /login, /logout   หน้าเข้าสู่ระบบด้วยรหัสผ่านทีม (คุกกี้ลงลายเซ็น)
//   /                 หน้าเว็บ index.html ที่ฝังไว้ในไฟล์นี้ (ต้องล็อกอินก่อน)
//   /คู่มือการใช้งาน.html  คู่มือที่ฝังไว้ (เปิดที่ /guide ก็ได้) · /ks-home-logo.png โลโก้ (เปิดได้โดยไม่ต้องล็อกอิน)
//   /proxy?url=       ดึงหน้า / API / รูปจาก HomePro, ตราเพชร, Eco door (เฉพาะเว็บที่อนุญาต)
//   /api/projects     เก็บโปรเจกต์ลูกค้าออนไลน์ ทีมเห็นร่วมกัน (Cloudflare KV)
//
// ตั้งค่าครั้งเดียว (Workers & Pages -> Worker นี้ -> Settings)
//   1) Bindings -> Add -> KV namespace -> Variable name: PROJECTS
//      (สร้าง namespace ก่อนที่ Storage & Databases -> KV -> Create)
//   2) Variables and Secrets -> Add -> Type: Secret -> TEAM_PASSWORD = รหัสผ่านของทีม
//   (ไม่บังคับ) SESSION_SECRET = ข้อความสุ่มยาว ๆ เพิ่มความปลอดภัยของคุกกี้
// เปลี่ยน TEAM_PASSWORD ได้ทุกเมื่อ ทุกคนจะถูกออกจากระบบและต้องใส่รหัสใหม่
// =====================================================================

const PAGE_HTML = __INDEX_HTML__;
const GUIDE_HTML = __GUIDE_HTML__;

// โลโก้ KS HOME (PNG) ใช้บนหน้าเข้าสู่ระบบ
const LOGO_B64 = [
  "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",
].join('');

// เว็บที่ /proxy ดึงให้ได้ (ชื่อโฮสต์ล้วน ๆ ห้ามมีลิงก์หรือ https:// ปนอยู่)
const ALLOWED_HOSTS = new Set([
  'www.boonthavorn.com',
  'www.homepro.co.th', 'homepro.co.th', 'statice.homepro.co.th',
  'traphet.com', 'www.traphet.com',
  'www.eco-door.net', 'eco-door.net',
]);

const COOKIE = 'ks_session';
const SESSION_DAYS = 30;
const MAX_FAILS = 8;               // ใส่รหัสผิดได้กี่ครั้งต่อ IP
const LOCK_SECONDS = 15 * 60;      // แล้วรอกี่วินาที
const MAX_PROJECT_BYTES = 24 * 1024 * 1024;   // KV เก็บได้ไม่เกิน 25 MiB ต่อรายการ
const TRASH_DAYS = 30;             // โปรเจกต์ที่ลบ เก็บสำรองไว้กี่วัน
const ID_RE = /^[a-z0-9-]{3,64}$/;
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36';

const enc = new TextEncoder();
const PAGE_BYTES = enc.encode(PAGE_HTML);
const GUIDE_BYTES = GUIDE_HTML ? enc.encode(GUIDE_HTML) : null;
const LOGO_BYTES = Uint8Array.from(atob(LOGO_B64), (c) => c.charCodeAt(0));
// index.html ลิงก์ไปที่ "คู่มือการใช้งาน.html" จึงรับชื่อไทยนี้ด้วย (เทียบแบบ NFC กันสระ/วรรณยุกต์สลับลำดับ)
const GUIDE_PATHS = new Set(['/guide', '/guide.html', '/คู่มือการใช้งาน.html'].map((p) => p.normalize('NFC')));
function isGuidePath(path) {
  try { return GUIDE_PATHS.has(decodeURIComponent(path).normalize('NFC')); } catch (_) { return false; }
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ---------- Responses ----------
const SEC = { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' };
const html = (status, body, extra) => new Response(body, {
  status, headers: { 'Content-Type': 'text/html; charset=utf-8', 'X-Frame-Options': 'DENY', ...SEC, ...extra },
});
const text = (status, body, extra) => new Response(body, {
  status, headers: { 'Content-Type': 'text/plain; charset=utf-8', ...SEC, ...extra },
});
const json = (status, data) => new Response(JSON.stringify(data), {
  status, headers: { 'Content-Type': 'application/json; charset=utf-8', ...SEC },
});
const redirect = (status, location, extra) => new Response(null, { status, headers: { Location: location, ...SEC, ...extra } });

// ---------- Login pages ----------
const FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@400;600;700&display=swap" rel="stylesheet">';
const SHELL_CSS = `
:root{--bg:#f6f5f2;--surface:#fff;--text:#1d1d1b;--muted:#6b6a65;--border:#e3e0d9;--accent:#0f6e5c;--accent-hover:#0b5a4b;--accent-ink:#fff;--accent-soft:#e2f1ec;--bad:#b4321f;--bad-soft:#fbe8e4;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--surface:#1e1e1c;--text:#ecebe6;--muted:#a3a19a;--border:#363531;--accent:#4fbfa5;--accent-hover:#6fd0b9;--accent-ink:#0b1f1a;--accent-soft:#17322c;--bad:#f29482;--bad-soft:#3a1d18;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;min-height:100dvh;display:grid;place-items:center;padding:16px;background:var(--bg);color:var(--text);font:16px/1.6 "IBM Plex Sans Thai","Leelawadee UI","Noto Sans Thai",Tahoma,system-ui,sans-serif}
.card{width:100%;max-width:400px;padding:28px 24px;background:var(--surface);border:1px solid var(--border);border-radius:14px;box-shadow:0 1px 2px rgba(0,0,0,.04),0 6px 20px rgba(0,0,0,.05)}
.logo{box-sizing:content-box;display:block;width:52px;height:auto;margin:0 0 16px;padding:6px;background:#fff;border:1px solid var(--border);border-radius:12px}
.eyebrow{margin:0 0 6px;font-size:.8rem;font-weight:600;letter-spacing:.04em;color:var(--accent)}
h1{margin:0;font-size:1.5rem;line-height:1.25}
.lede{margin:8px 0 20px;color:var(--muted);font-size:.95rem}
label{display:block;margin-bottom:6px;font-weight:600}
input[type=password]{width:100%;min-height:48px;padding:11px 14px;font:inherit;color:var(--text);background:var(--surface);border:1.5px solid var(--border);border-radius:12px;outline:none}
input[type=password]:focus{border-color:var(--accent);box-shadow:0 0 0 4px var(--accent-soft)}
button{width:100%;min-height:48px;margin-top:14px;font:inherit;font-weight:600;color:var(--accent-ink);background:var(--accent);border:0;border-radius:12px;cursor:pointer}
button:hover{background:var(--accent-hover)}
button:disabled{opacity:.6;cursor:progress}
button:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.err{margin:12px 0 0;padding:10px 14px;border-radius:10px;font-size:.9rem;background:var(--bad-soft);color:var(--bad)}
code{padding:1px 6px;border-radius:5px;background:var(--accent-soft);font-size:.9em}`;

const shell = (title, body) => `<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>${title}</title>${FONTS}<style>${SHELL_CSS}</style></head><body>${body}</body></html>`;

function loginPage(error, hash) {
  return shell('เข้าสู่ระบบ · ค้นหาสินค้าวัสดุ', `<main class="card">
<img class="logo" src="/ks-home-logo.png" width="52" height="66" alt="KS HOME">
<p class="eyebrow">บุญถาวร · HomePro · ตราเพชร · Eco door</p>
<h1>เข้าสู่ระบบทีม</h1>
<p class="lede">ใส่รหัสผ่านทีมเพื่อใช้ระบบค้นหาสินค้าวัสดุและโปรเจกต์ลูกค้าออนไลน์</p>
<form method="post" action="/login" id="f">
<input type="hidden" name="h" id="h" value="${esc(hash)}">
<label for="pw">รหัสผ่านทีม</label>
<input id="pw" name="password" type="password" autocomplete="current-password" required autofocus>
${error ? `<p class="err" role="alert">${esc(error)}</p>` : ''}
<button type="submit" id="b">เข้าสู่ระบบ</button>
</form></main>
<script>var h=document.getElementById('h'),b=document.getElementById('b');if(!h.value)h.value=location.hash;document.getElementById('f').addEventListener('submit',function(){b.disabled=true});addEventListener('pageshow',function(){b.disabled=false});</script>`);
}

function setupPage() {
  return shell('ตั้งค่าครั้งแรก', `<main class="card">
<p class="eyebrow">ตั้งค่าครั้งแรก</p>
<h1>ยังไม่ได้ตั้งรหัสผ่านทีม</h1>
<p class="lede">เพิ่ม Secret ชื่อ <code>TEAM_PASSWORD</code> ที่ Worker &rarr; Settings &rarr; Variables and Secrets แล้วกด Deploy อีกครั้ง จากนั้นรีเฟรชหน้านี้</p>
</main>`);
}

// ---------- Session (cookie signed with HMAC-SHA256) ----------
function b64url(bytes) {
  let s = '';
  for (const b of new Uint8Array(bytes)) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function hmac(env, message) {
  const secret = `ks|${env.SESSION_SECRET || ''}|${env.TEAM_PASSWORD}`;
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return new Uint8Array(await crypto.subtle.sign('HMAC', key, enc.encode(message)));
}

function safeEqual(a, b) {
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a[i] ^ b[i];
  return d === 0;
}

async function passwordOk(env, given) {
  return safeEqual(await hmac(env, 'pw|' + given), await hmac(env, 'pw|' + env.TEAM_PASSWORD));
}

async function makeToken(env) {
  const exp = Math.floor(Date.now() / 1000) + SESSION_DAYS * 86400;
  return `${exp}.${b64url(await hmac(env, 'session|' + exp))}`;
}

async function tokenOk(env, token) {
  const [exp, sig] = String(token || '').split('.');
  if (!/^\d{10}$/.test(exp || '') || !sig) return false;
  if (Number(exp) < Date.now() / 1000) return false;
  return safeEqual(enc.encode(sig), enc.encode(b64url(await hmac(env, 'session|' + exp))));
}

function getCookie(request, name) {
  for (const part of (request.headers.get('Cookie') || '').split(';')) {
    const i = part.indexOf('=');
    if (i > 0 && part.slice(0, i).trim() === name) return part.slice(i + 1).trim();
  }
  return '';
}

const isAuthed = (request, env) => tokenOk(env, getCookie(request, COOKIE));
const cookieFlags = (request) => '; Path=/; HttpOnly; SameSite=Lax' + (new URL(request.url).protocol === 'https:' ? '; Secure' : '');
// A "#..." from the original link (e.g. #1015431) is carried through the login.
const safeHash = (h) => (/^#[A-Za-z0-9_%.,:~-]{1,1500}$/.test(h) ? h : '');

async function login(request, env) {
  const method = request.method;
  if (method === 'GET' || method === 'HEAD') {
    return (await isAuthed(request, env)) ? redirect(302, '/') : html(200, loginPage('', ''));
  }
  if (method !== 'POST') return text(405, 'Method not allowed');
  if (Number(request.headers.get('Content-Length') || 0) > 4096) return text(413, 'Too large');

  const params = new URLSearchParams(await request.text());
  const given = String(params.get('password') || '');
  const hash = safeHash(String(params.get('h') || ''));
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const kv = env.PROJECTS;
  const failKey = 'rl:' + ip;

  let fails = 0;
  if (kv) { try { fails = Number(await kv.get(failKey)) || 0; } catch (_) { /* ignore */ } }
  if (fails >= MAX_FAILS) {
    return html(429, loginPage('ใส่รหัสผิดหลายครั้งเกินไป กรุณารอประมาณ 15 นาทีแล้วลองใหม่', hash));
  }
  if (!given || !(await passwordOk(env, given))) {
    await sleep(600);
    if (kv) { try { await kv.put(failKey, String(fails + 1), { expirationTtl: LOCK_SECONDS }); } catch (_) { /* ignore */ } }
    return html(401, loginPage('รหัสผ่านไม่ถูกต้อง', hash));
  }
  return redirect(303, '/' + hash, {
    'Set-Cookie': `${COOKIE}=${await makeToken(env)}; Max-Age=${SESSION_DAYS * 86400}${cookieFlags(request)}`,
  });
}

// ---------- Proxy (only the allowed shop websites) ----------
const allowed = (u) => u.protocol === 'https:' && !u.port && !u.username && !u.password && ALLOWED_HOSTS.has(u.hostname);

async function proxy(request, url) {
  if (request.method !== 'GET' && request.method !== 'HEAD') return text(405, 'Method not allowed');
  let current;
  try { current = new URL(url.searchParams.get('url') || ''); } catch (_) { return text(400, 'Missing or invalid ?url='); }
  if (!allowed(current)) return text(403, 'This address is not allowed.');

  const headers = {
    'User-Agent': UA,
    'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
    Accept: request.headers.get('Accept') || '*/*',
  };
  let upstream;
  try {
    // Redirects are followed by hand so each hop is checked against the allow-list.
    for (let hop = 0; ; hop++) {
      upstream = await fetch(current, { method: request.method, headers, redirect: 'manual', signal: AbortSignal.timeout(25000) });
      const location = upstream.headers.get('Location');
      if (!(upstream.status >= 300 && upstream.status < 400 && location)) break;
      if (upstream.body) await upstream.body.cancel();
      if (hop >= 5) return text(502, 'Too many redirects');
      let next;
      try { next = new URL(location, current); } catch (_) { return text(502, 'Bad redirect'); }
      if (!allowed(next)) return text(403, 'Redirect to a blocked address.');
      current = next;
    }
  } catch (err) {
    return text(502, 'Fetch failed: ' + ((err && err.message) || err));
  }
  const type = upstream.headers.get('Content-Type') || 'application/octet-stream';
  return new Response(request.method === 'HEAD' ? null : upstream.body, {
    status: upstream.status,
    headers: {
      'Content-Type': type,
      'Cache-Control': upstream.ok && /^image\//i.test(type) ? 'private, max-age=86400' : 'no-store',
      'X-Content-Type-Options': 'nosniff',
    },
  });
}

// ---------- Projects (one KV entry per project; its summary rides along as KV metadata) ----------
const clip = (s, n) => Array.from(String(s ?? '')).slice(0, n).join('');
const count = (v) => (Number.isFinite(Number(v)) ? Math.max(0, Math.min(100000, Math.trunc(Number(v)))) : 0);

// KV metadata must stay under 1 KB, so names are shortened here (the full names stay inside the project).
function cleanMeta(raw, id) {
  const created = raw && typeof raw.createdAt === 'string' && !isNaN(Date.parse(raw.createdAt)) ? raw.createdAt.slice(0, 40) : new Date().toISOString();
  const meta = {
    id,
    project: clip(raw && raw.project, 80),
    owner: clip(raw && raw.owner, 80),
    items: count(raw && raw.items),
    pages: count(raw && raw.pages),
    createdAt: created,
    updatedAt: new Date().toISOString(),
  };
  if (enc.encode(JSON.stringify(meta)).length > 1000) {
    meta.project = clip(meta.project, 30);
    meta.owner = clip(meta.owner, 30);
  }
  return meta;
}

async function listMetas(kv, prefix) {
  const out = [];
  let cursor;
  do {
    const page = await kv.list({ prefix, cursor });
    for (const k of page.keys) if (k.metadata) out.push(k.metadata);
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  return out;
}

// KV allows about one write per second to the same key; try once more if a save lands too soon.
async function putRetry(kv, key, value, options) {
  try { await kv.put(key, value, options); } catch (_) { await sleep(1100); await kv.put(key, value, options); }
}

async function projectsApi(request, env, parts) {
  if (request.headers.get('X-KS-App') !== '1') return text(403, 'Forbidden');
  const kv = env.PROJECTS;
  if (!kv) return text(503, 'ยังไม่ได้ผูก KV namespace ชื่อ PROJECTS กับ Worker นี้ (Settings -> Bindings)');
  const method = request.method;

  if (parts[1] === 'trash') {
    return method === 'GET' && parts.length === 2 ? json(200, await listMetas(kv, 'trash:')) : text(405, 'Method not allowed');
  }
  if (parts.length === 2) {
    return method === 'GET' ? json(200, await listMetas(kv, 'p:')) : text(405, 'Method not allowed');
  }

  const id = parts[2];
  if (!ID_RE.test(id)) return text(400, 'Bad project id');
  const key = 'p:' + id;

  if (parts.length === 3 && method === 'GET') {
    const r = await kv.getWithMetadata(key, { type: 'stream' });
    if (!r.value) return text(404, 'Not found');
    return new Response(r.value, { headers: { 'Content-Type': 'application/json; charset=utf-8', ...SEC } });
  }

  if (parts.length === 3 && method === 'PUT') {
    if (Number(request.headers.get('Content-Length') || 0) > MAX_PROJECT_BYTES) return text(413, 'Project is too large');
    let raw;
    try { raw = JSON.parse(decodeURIComponent(request.headers.get('X-KS-Meta') || '')); } catch (_) { return text(400, 'Bad project summary'); }
    // The project body is stored as-is (not parsed here), which keeps big projects cheap to save.
    const body = await request.arrayBuffer();
    if (body.byteLength < 2 || body.byteLength > MAX_PROJECT_BYTES || new Uint8Array(body, 0, 1)[0] !== 0x7b) return text(400, 'Bad project data');
    await putRetry(kv, key, body, { metadata: cleanMeta(raw, id) });
    return text(200, 'saved');
  }

  if (parts.length === 3 && method === 'DELETE') {
    // Deleted projects stay in the trash for TRASH_DAYS days.
    const r = await kv.getWithMetadata(key, { type: 'arrayBuffer' });
    if (r.value) await putRetry(kv, 'trash:' + id, r.value, { metadata: r.metadata, expirationTtl: TRASH_DAYS * 86400 });
    await kv.delete(key);
    return text(200, 'deleted');
  }

  if (parts.length === 4 && parts[3] === 'restore' && method === 'POST') {
    const r = await kv.getWithMetadata('trash:' + id, { type: 'arrayBuffer' });
    if (!r.value) return text(404, `Not in the trash (kept for ${TRASH_DAYS} days)`);
    await putRetry(kv, key, r.value, { metadata: { ...r.metadata, updatedAt: new Date().toISOString() } });
    await kv.delete('trash:' + id);
    return text(200, 'restored');
  }
  return text(405, 'Method not allowed');
}

// ---------- Routing ----------
async function route(request, env) {
  const url = new URL(request.url);
  const path = url.pathname;
  if (path === '/favicon.ico') return new Response(null, { status: 204 });
  if (path === '/ks-home-logo.png' && (request.method === 'GET' || request.method === 'HEAD')) {
    return new Response(LOGO_BYTES, { headers: { 'Content-Type': 'image/png', 'Cache-Control': 'public, max-age=86400', 'X-Content-Type-Options': 'nosniff' } });
  }
  if (!env.TEAM_PASSWORD) return html(503, setupPage());

  if (path === '/login') return login(request, env);
  if (path === '/logout') {
    return redirect(302, '/login', { 'Set-Cookie': `${COOKIE}=; Max-Age=0${cookieFlags(request)}` });
  }

  const authed = await isAuthed(request, env);
  if (path === '/' || path === '/index.html') {
    if (request.method !== 'GET' && request.method !== 'HEAD') return text(405, 'Method not allowed');
    return authed ? html(200, PAGE_BYTES) : redirect(302, '/login');
  }
  if (GUIDE_BYTES && isGuidePath(path)) {
    if (request.method !== 'GET' && request.method !== 'HEAD') return text(405, 'Method not allowed');
    return authed ? html(200, GUIDE_BYTES) : redirect(302, '/login');
  }
  if (!authed) return text(401, 'Unauthorized');

  if (path === '/proxy-status') return text(200, 'ok', { 'X-KS-Host': 'cloud' });
  if (path === '/proxy') return proxy(request, url);
  const parts = path.split('/').filter(Boolean);
  if (parts[0] === 'api' && (parts[1] === 'projects' || parts[1] === 'trash')) return projectsApi(request, env, parts);
  return text(404, 'Not found');
}

export default {
  async fetch(request, env) {
    try {
      return await route(request, env);
    } catch (err) {
      return text(500, 'Server error: ' + ((err && err.message) || err));
    }
  },
};
