import stockModule from '../lib/stock-service.js';
import checksModule from '../lib/functional-checks.js';

const { createStockService, createQuoteProvider, RequestError } = stockModule;
const { runFunctionalChecks } = checksModule;
const quotes = createQuoteProvider();
const SECURITY = {
  'content-security-policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
  'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY',
  'referrer-policy': 'no-referrer', 'strict-transport-security': 'max-age=31536000; includeSubDomains',
  'access-control-allow-origin': '*', 'access-control-allow-methods': 'GET, OPTIONS'
};

class D1LikeStore {
  constructor(database) { this.database = database; }
  async addLikes(stocks, voter) {
    await this.database.batch(stocks.map(stock => this.database.prepare(
      'INSERT OR IGNORE INTO likes (stock, voter_hash) VALUES (?, ?)').bind(stock, voter)));
  }
  async getLikes(stock) {
    return this.database.prepare('SELECT COUNT(*) AS likes FROM likes WHERE stock = ?').bind(stock).first('likes');
  }
}

function json(body, status = 200) {
  return Response.json(body, { status, headers: { ...SECURITY, 'cache-control': 'no-store' } });
}

async function apiResponse(url, env, clientIp) {
  const stocks = url.searchParams.getAll('stock');
  const likes = url.searchParams.getAll('like');
  const service = createStockService({ store: new D1LikeStore(env.LIKES),
    secret: env.LIKE_HASH_SECRET, quoteProvider: quotes });
  try {
    return json(await service.lookup({ stock: stocks, like: likes.length > 1 ? likes : likes[0] }, clientIp));
  } catch (error) {
    console.warn('Stock request failed:', error.upstreamStatus || error.cause?.message || error.message);
    return json({ error: error instanceof RequestError ? error.message : 'Unable to process this request.' },
      error instanceof RequestError ? error.status : 500);
  }
}

export default {
  async fetch(request, env) {
    try {
      const url = new URL(request.url);
      if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: SECURITY });
      if (!['GET', 'HEAD'].includes(request.method)) return json({ error: 'Method not allowed.' }, 405);
      if (/^\/api\/stock-prices\/?$/.test(url.pathname)) {
        if (request.method !== 'GET') return json({ error: 'Method not allowed.' }, 405);
        return await apiResponse(url, env, request.headers.get('CF-Connecting-IP'));
      }
      if (url.pathname === '/health') return json({ status: 'ok' });
      if (url.pathname === '/_api/app-info') return json({ headers: SECURITY });
      if (url.pathname === '/_api/get-tests') {
        const results = await runFunctionalChecks(async query => {
          const response = await apiResponse(new URL('/api/stock-prices' + query, url), env, '127.0.0.1');
          if (!response.ok) throw new Error('Functional request failed');
          return response.json();
        });
        return json(results);
      }
      if (url.pathname !== '/' && !url.pathname.startsWith('/public/')) return json({ error: 'Not found.' }, 404);
      const asset = await env.ASSETS.fetch(request);
      const headers = new Headers(asset.headers);
      for (const [name, value] of Object.entries(SECURITY)) headers.set(name, value);
      return new Response(asset.body, { status: asset.status, headers });
    } catch {
      return json({ error: 'Unable to process this request.' }, 500);
    }
  }
};
