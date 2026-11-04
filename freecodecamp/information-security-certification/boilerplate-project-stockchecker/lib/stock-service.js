'use strict';

const { createHmac } = require('node:crypto');
const { isIP } = require('node:net');

const PROXY_URL = 'https://stock-price-checker-proxy.freecodecamp.rocks/v1/stock';
const STOCK_PATTERN = /^[A-Z][A-Z0-9.-]{0,9}$/;

class RequestError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function parseStocks(value) {
  const input = Array.isArray(value) ? value : [value];
  if (input.some(item => typeof item !== 'string')) {
    throw new RequestError(400, 'Provide one or two valid stock symbols.');
  }
  const stocks = input.flatMap(item => item.split(',')).map(item => item.trim().toUpperCase());
  if (stocks.length < 1 || stocks.length > 2 || stocks.some(stock => !STOCK_PATTERN.test(stock))) {
    throw new RequestError(400, 'Provide one or two valid stock symbols.');
  }
  return stocks;
}

function parseLike(value) {
  if (value === undefined || value === false || value === 'false') return false;
  if (value === true || value === 'true') return true;
  throw new RequestError(400, 'Like must be true or false.');
}

function normalizeIp(value) {
  if (typeof value !== 'string' || !isIP(value)) throw new RequestError(400, 'Unable to identify the client.');
  if (isIP(value) === 4) return value;
  const normalized = new URL('http://[' + value + ']/').hostname.slice(1, -1);
  if (normalized.startsWith('::ffff:')) {
    const parts = normalized.slice(7).split(':').map(part => parseInt(part, 16));
    return [parts[0] >> 8, parts[0] & 255, parts[1] >> 8, parts[1] & 255].join('.');
  }
  return normalized;
}

function fingerprint(ip, secret) {
  return createHmac('sha256', secret).update(normalizeIp(ip)).digest('hex');
}

function createQuoteProvider(fetcher = globalThis.fetch) {
  const cache = new Map();
  return async function quote(stock) {
    const previous = cache.get(stock);
    if (previous && previous.expires > Date.now()) return previous.promise;
    const promise = (async () => {
      let response;
      try {
        response = await fetcher(PROXY_URL + '/' + encodeURIComponent(stock) + '/quote', {
          headers: { accept: 'application/json', 'user-agent': 'Mozilla/5.0' },
          redirect: 'manual', signal: AbortSignal.timeout(10000)
        });
      } catch (cause) {
        const error = new RequestError(502, 'Unable to retrieve stock data right now.');
        error.cause = cause;
        throw error;
      }
      if (!response.ok) {
        const error = new RequestError(response.status === 404 ? 404 : 502, 'Unable to retrieve stock data right now.');
        error.upstreamStatus = response.status;
        throw error;
      }
      if (!response.body) throw new RequestError(502, 'Stock service returned an invalid quote.');
      const reader = response.body.getReader();
      const chunks = [];
      let size = 0;
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > 65536) {
          await reader.cancel();
          throw new RequestError(502, 'Stock service returned an invalid quote.');
        }
        chunks.push(value);
      }
      let data;
      try {
        const bytes = new Uint8Array(size);
        let offset = 0;
        for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
        data = JSON.parse(new TextDecoder().decode(bytes));
      } catch {
        throw new RequestError(502, 'Stock service returned an invalid quote.');
      }
      const value = data && data.latestPrice;
      const price = typeof value === 'number' || (typeof value === 'string' && value.trim() !== '') ? Number(value) : NaN;
      if (!Number.isFinite(price) || price < 0 || (data.symbol &&
        (typeof data.symbol !== 'string' || data.symbol.toUpperCase() !== stock))) {
        throw new RequestError(502, 'Stock service returned an invalid quote.');
      }
      return { stock, price };
    })();
    cache.set(stock, { promise, expires: Date.now() + 15000 });
    if (cache.size > 500) cache.delete(cache.keys().next().value);
    try { return await promise; } catch (error) {
      cache.delete(stock);
      throw error instanceof RequestError ? error : new RequestError(502, 'Unable to retrieve stock data right now.');
    }
  };
}

function createStockService({ store, quoteProvider = createQuoteProvider(), secret }) {
  if (!secret || secret.length < 32) throw new Error('A stable like-hash secret of at least 32 characters is required.');
  return {
    async lookup(query, clientIp) {
      const stocks = parseStocks(query.stock);
      const shouldLike = parseLike(query.like);
      const voter = shouldLike ? fingerprint(clientIp, secret) : null;
      const quotes = await Promise.all(stocks.map(quoteProvider));
      // A failed quote must not create likes, including partially failed comparisons.
      if (shouldLike) await store.addLikes(stocks, voter);
      const likes = await Promise.all(stocks.map(stock => store.getLikes(stock)));
      if (quotes.length === 1) return { stockData: { ...quotes[0], likes: likes[0] } };
      return { stockData: quotes.map((quote, index) => ({
        ...quote, rel_likes: likes[index] - likes[1 - index]
      })) };
    }
  };
}

module.exports = { RequestError, parseStocks, parseLike, normalizeIp, fingerprint, createQuoteProvider, createStockService };
