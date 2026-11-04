'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = (process.argv[2] || 'http://localhost:3000').replace(/\/$/, '');

async function request(route, status = 200, headers = {}) {
  const response = await fetch(base + route, { headers, signal: AbortSignal.timeout(40000) });
  assert.equal(response.status, status, route);
  return response;
}

async function main() {
  const page = await request('/');
  assert.match(await page.text(), /Stock Price Checker/);
  for (const asset of ['/public/script.js', '/public/style.css', '/public/favicon.svg', '/health']) await request(asset);
  const infoResponse = await request('/_api/app-info');
  const info = await infoResponse.json();
  for (const rule of ["script-src 'self'", "style-src 'self'"]) {
    assert.ok(info.headers['content-security-policy'].includes(rule));
    assert.ok(infoResponse.headers.get('content-security-policy').includes(rule));
  }
  const quote = (await (await request('/api/stock-prices?stock=goog')).json()).stockData;
  assert.equal(quote.stock, 'GOOG');
  assert.ok(Number.isFinite(quote.price));
  const liked = (await (await request('/api/stock-prices?stock=GOOG&like=true')).json()).stockData;
  const repeated = (await (await request('/api/stock-prices?stock=GOOG&like=true', 200,
    { 'X-Forwarded-For': '192.0.2.123' })).json()).stockData;
  assert.equal(repeated.likes, liked.likes);
  const comparison = (await (await request('/api/stock-prices?stock=GOOG&stock=MSFT&like=true')).json()).stockData;
  assert.equal(comparison.length, 2);
  assert.ok(comparison.every(stock => Number.isFinite(stock.price) && Number.isInteger(stock.rel_likes) && !('likes' in stock)));
  assert.equal(comparison[0].rel_likes + comparison[1].rel_likes, 0);
  await request('/api/stock-prices?stock=GOOG&stock=MSFT&stock=AAPL', 400);
  await request('/api/stock-prices?stock=GOOG&like=yes', 400);
  const tests = await (await request('/_api/get-tests')).json();
  assert.equal(tests.length, 5);
  assert.ok(tests.every(test => test.state === 'passed'));
  const snapshot = (await (await request('/api/stock-prices?stock=GOOG')).json()).stockData.likes;
  const cache = path.resolve(__dirname, '../.cache');
  fs.mkdirSync(cache, { recursive: true });
  fs.writeFileSync(path.join(cache, 'live-verification.json'), JSON.stringify({ base, googLikes: snapshot, tests: 5 }, null, 2));
  console.log('Live page, assets, CSP, quotes, unique likes, comparisons, errors and five hosted checks: passed.');
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
