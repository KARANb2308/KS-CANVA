// Optional Cloudflare Worker for using index.html from a website (e.g. GitHub Pages)
// instead of start.bat. It fetches only the shop websites below and adds the
// cross-site header the page needs. Deploy it, then paste
//   https://<your-worker>.workers.dev/?url=
// into "ตั้งค่า Proxy" on the page.

const ALLOWED_HOSTS = new Set([
  'www.boonthavorn.com',
  'www.homepro.co.th', 'homepro.co.th', 'statice.homepro.co.th',
  'traphet.com', 'www.traphet.com',
  'www.eco-door.net', 'eco-door.net',
]);

const CORS = { 'Access-Control-Allow-Origin': '*' };

export default {
  async fetch(request) {
    let target;
    try {
      target = new URL(new URL(request.url).searchParams.get('url') || '');
    } catch {
      return new Response('Missing or invalid ?url=', { status: 400, headers: CORS });
    }
    if (target.protocol !== 'https:' || !ALLOWED_HOSTS.has(target.hostname)) {
      return new Response('This address is not allowed.', { status: 403, headers: CORS });
    }
    const upstream = await fetch(target, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36',
        'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
      },
    });
    const response = new Response(upstream.body, upstream);
    response.headers.set('Access-Control-Allow-Origin', '*');
    return response;
  },
};
