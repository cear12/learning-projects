'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const chai = require('chai');
chai.use(require('chai-http'));
const { LikeStore } = require('../../lib/like-store');
const { createApp } = require('../../server');
const { normalizeIp, fingerprint, createQuoteProvider, createStockService, RequestError } = require('../../lib/stock-service');
const { runFunctionalChecks } = require('../../lib/functional-checks');
const SECRET = 'test-fixture-secret-with-at-least-32-characters';
const quote = async stock => ({ stock, price: stock === 'GOOG' ? 100 : 50 });

suite('Storage and API checks', function () {
  let store;
  setup(() => { store = new LikeStore(':memory:'); });
  teardown(() => { store.close(); });

  test('counts unique visitors separately for each stock', async () => {
    const service = createStockService({ store, secret: SECRET, quoteProvider: quote });
    assert.equal((await service.lookup({ stock: 'goog', like: 'true' }, '192.0.2.1')).stockData.likes, 1);
    assert.equal((await service.lookup({ stock: 'GOOG', like: 'true' }, '192.0.2.1')).stockData.likes, 1);
    assert.equal((await service.lookup({ stock: 'GOOG', like: true }, '192.0.2.2')).stockData.likes, 2);
    const result = await service.lookup({ stock: ['GOOG', 'MSFT'], like: true }, '192.0.2.1');
    assert.deepEqual(result.stockData.map(item => item.rel_likes), [1, -1]);
  });

  test('does not record any like when a comparison quote fails', async () => {
    const service = createStockService({ store, secret: SECRET, quoteProvider: async stock => {
      if (stock === 'MSFT') throw new RequestError(502, 'Unavailable');
      return quote(stock);
    } });
    await assert.rejects(service.lookup({ stock: ['GOOG', 'MSFT'], like: true }, '192.0.2.1'));
    assert.equal(store.getLikes('GOOG'), 0);
    assert.equal(store.getLikes('MSFT'), 0);
  });

  test('preserves a two-stock response for duplicate symbols without adding two likes', async () => {
    const service = createStockService({ store, secret: SECRET, quoteProvider: quote });
    const result = await service.lookup({ stock: ['GOOG', 'goog'], like: true }, '192.0.2.1');
    assert.equal(result.stockData.length, 2);
    assert.deepEqual(result.stockData.map(item => item.rel_likes), [0, 0]);
    assert.equal(store.getLikes('GOOG'), 1);
  });

  test('deduplicates concurrent requests from the same visitor', async () => {
    const service = createStockService({ store, secret: SECRET, quoteProvider: quote });
    await Promise.all(Array.from({ length: 20 }, () => service.lookup({ stock: 'GOOG', like: true }, '192.0.2.1')));
    assert.equal(store.getLikes('GOOG'), 1);
  });

  test('normalizes equivalent IP spellings and stores only keyed hashes', () => {
    assert.equal(normalizeIp('::ffff:192.0.2.1'), '192.0.2.1');
    assert.equal(fingerprint('192.0.2.1', SECRET), fingerprint('::ffff:c000:201', SECRET));
    assert.equal(fingerprint('2001:0db8:0:0:0:0:0:1', SECRET), fingerprint('2001:db8::1', SECRET));
    store.addLikes(['GOOG'], fingerprint('192.0.2.1', SECRET));
    const row = store.database.prepare('SELECT * FROM likes').get();
    assert.match(row.voter_hash, /^[a-f0-9]{64}$/);
    assert.equal(JSON.stringify(row).includes('192.0.2.1'), false);
  });

  test('retains unique likes after closing and reopening a database', () => {
    const cache = path.resolve(__dirname, '../../.cache');
    fs.mkdirSync(cache, { recursive: true });
    const folder = fs.mkdtempSync(path.join(cache, 'store-'));
    const filename = path.join(folder, 'likes.sqlite');
    let persistent = new LikeStore(filename);
    persistent.addLikes(['GOOG'], fingerprint('192.0.2.1', SECRET));
    persistent.close();
    persistent = new LikeStore(filename);
    persistent.addLikes(['GOOG'], fingerprint('192.0.2.1', SECRET));
    assert.equal(persistent.getLikes('GOOG'), 1);
    persistent.close();
  });

  test('rejects malformed stock and like parameters without writes', async () => {
    const app = createApp({ store, secret: SECRET, quoteProvider: quote, fccTesting: false });
    for (const query of [{}, { stock: ['GOOG', 'MSFT', 'AAPL'] }, { stock: '../secret' },
      { stock: 'GOOG', like: 'yes' }, { stock: '' }]) {
      const response = await chai.request(app).get('/api/stock-prices').query(query);
      assert.equal(response.status, 400);
      assert.equal(typeof response.body.error, 'string');
    }
    assert.equal(store.getLikes('GOOG'), 0);
  });

  test('ignores forged forwarding headers unless proxies are explicitly trusted', async () => {
    const app = createApp({ store, secret: SECRET, quoteProvider: quote, fccTesting: false, trustProxy: false });
    const first = await chai.request(app).get('/api/stock-prices?stock=GOOG&like=true').set('X-Forwarded-For', '192.0.2.1');
    const second = await chai.request(app).get('/api/stock-prices?stock=GOOG&like=true').set('X-Forwarded-For', '192.0.2.2');
    assert.equal(first.body.stockData.likes, 1);
    assert.equal(second.body.stockData.likes, 1);
  });

  test('returns CSP restricting scripts and styles to the application', async () => {
    const app = createApp({ store, secret: SECRET, quoteProvider: quote, fccTesting: false });
    const response = await chai.request(app).get('/_api/app-info');
    assert.equal(response.status, 200);
    assert.match(response.body.headers['content-security-policy'], /script-src 'self'/);
    assert.match(response.body.headers['content-security-policy'], /style-src 'self'/);
    assert.equal(response.headers['x-powered-by'], undefined);
  });

  test('returns successful live-handler functional reports rather than fixed states', async () => {
    const service = createStockService({ store, secret: SECRET, quoteProvider: quote });
    const report = await runFunctionalChecks(query => {
      const params = new URLSearchParams(query);
      return service.lookup({ stock: params.getAll('stock'), like: params.get('like') || undefined }, '127.0.0.1');
    });
    assert.equal(report.length, 5);
    assert.equal(report.every(item => item.state === 'passed'), true);
    const failed = await runFunctionalChecks(async () => { throw new Error('Unavailable'); });
    assert.equal(failed.every(item => item.state === 'failed'), true);
  });
});

suite('Quote provider checks', function () {
  test('reuses and deduplicates successful upstream requests', async () => {
    let calls = 0;
    const provider = createQuoteProvider(async () => { calls++; return Response.json({ symbol: 'GOOG', latestPrice: 123.45 }); });
    const values = await Promise.all([provider('GOOG'), provider('GOOG')]);
    assert.equal(calls, 1);
    assert.deepEqual(values[0], { stock: 'GOOG', price: 123.45 });
  });
  test('rejects missing, null, malformed, negative and mismatched quote values', async () => {
    for (const body of [{}, { latestPrice: null }, { latestPrice: '' }, { latestPrice: -1 },
      { latestPrice: 'not-a-price' }, { latestPrice: 100, symbol: 'MSFT' }]) {
      const provider = createQuoteProvider(async () => Response.json(body));
      await assert.rejects(provider('GOOG'), error => error.status === 502);
    }
  });
  test('retries errors and rejects oversized responses', async () => {
    let calls = 0;
    const provider = createQuoteProvider(async () => { calls++; return new Response('unavailable', { status: 503 }); });
    await assert.rejects(provider('GOOG'));
    await assert.rejects(provider('GOOG'));
    assert.equal(calls, 2);
    await assert.rejects(createQuoteProvider(async () => new Response('x'.repeat(65537)))('GOOG'));
  });
});
