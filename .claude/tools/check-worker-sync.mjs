// Checks that worker.js matches worker.src.js + index.html + the guide .html (rebuilds it in memory the way
// build-worker.ps1 does). Run from anywhere: node .claude/tools/check-worker-sync.mjs <project folder>
import fs from 'fs'; import path from 'path';
const dir = process.argv[2] || process.cwd();
const rd = f => fs.readFileSync(path.join(dir, f), 'utf8');
function toJsArray(t){let out='',i=0;while(i<t.length){let n=Math.min(1000,t.length-i);const c=t.charCodeAt(i+n-1);if(n>1&&c>=0xD800&&c<=0xDBFF)n--;let ch=t.substr(i,n);i+=n;
ch=ch.replace(/\\/g,'\\\\').replace(/"/g,'\\"').replace(/\r/g,'\\r').replace(/\n/g,'\\n').replace(/[\u2028\u2029]/g,' ');out+='  "'+ch+'",\r\n';}return '[\n'+out+"].join('')";}
const guides = fs.readdirSync(dir).filter(f=>f.endsWith('.html')&&f!=='index.html');
let src = rd('worker.src.js');
src = src.replace('const PAGE_HTML = __INDEX_HTML__;', ()=>'const PAGE_HTML = '+toJsArray(rd('index.html'))+';');
src = src.replace('const GUIDE_HTML = __GUIDE_HTML__;', ()=>'const GUIDE_HTML = '+(guides.length===1?toJsArray(rd(guides[0])):"''")+';');
const disk = rd('worker.js');
const norm = s => s.replace(/\r\n/g,'\n');
const ok = norm(src) === norm(disk);
console.log(ok ? "IN SYNC: worker.js ตรงกับไฟล์ต้นฉบับ" : "OUT OF SYNC: worker.js ไม่ตรงกับไฟล์ต้นฉบับ — ต้องรัน build-worker.bat ใหม่");
process.exit(ok ? 0 : 1);
