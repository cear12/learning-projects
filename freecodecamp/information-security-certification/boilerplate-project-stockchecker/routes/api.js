'use strict';

const crypto = require('crypto');
const https = require('https');

const PROXY_BASE_URL = 'https://stock-price-checker-proxy.freecodecamp.rocks/v1/stock';
const STOCK_PATTERN = /^[A-Za-z][A-Za-z0-9.-]{0,9}$/;
const likesByStock = new Map();

function parseStocks(value) {
  const values = Array.isArray(value) ? value : [value];
  const stocks = values
    .flatMap(function (item) { return String(item || '').split(','); })
    .map(function (item) { return item.trim().toUpperCase(); })
    .filter(Boolean);

  if (stocks.length < 1 || stocks.length > 2) return null;
  if (stocks.some(function (stock) { return !STOCK_PATTERN.test(stock); })) return null;
  return Array.from(new Set(stocks));
}

function getClientIp(req) {
  return req.ip || (req.socket && req.socket.remoteAddress) || 'unknown';
}

function anonymizeIp(ip) {
  const secret = process.env.LIKE_HASH_SECRET || 'stock-price-checker-local-secret';
  return crypto.createHash('sha256').update(secret + ':' + ip).digest('hex');
}

function addLike(stock, ip) {
  if (!likesByStock.has(stock)) likesByStock.set(stock, new Set());
  likesByStock.get(stock).add(anonymizeIp(ip));
}

function getLikes(stock) {
  return likesByStock.has(stock) ? likesByStock.get(stock).size : 0;
}

function getJson(url) {
  return new Promise(function (resolve, reject) {
    const request = https.get(url, {
      headers: { accept: 'application/json' }
    }, function (response) {
      let data = '';
      response.setEncoding('utf8');
      response.on('data', function (chunk) { data += chunk; });
      response.on('end', function () {
        if (response.statusCode < 200 || response.statusCode >= 300) {
          return reject(new Error('Stock proxy returned ' + response.statusCode));
        }
        try {
          resolve(JSON.parse(data));
        } catch (error) {
          reject(error);
        }
      });
    });

    request.setTimeout(10000, function () {
      request.destroy(new Error('Stock proxy timed out'));
    });
    request.on('error', reject);
  });
}

async function getStockData(stock) {
  const quote = await getJson(PROXY_BASE_URL + '/' + encodeURIComponent(stock) + '/quote');
  const price = Number(quote.latestPrice);
  if (!Number.isFinite(price)) throw new Error('Stock proxy returned an invalid price');
  return { stock: stock, price: price, likes: getLikes(stock) };
}

module.exports = function (app) {

  app.route('/api/stock-prices')
    .get(async function (req, res) {
      const stocks = parseStocks(req.query.stock);
      if (!stocks) {
        return res.status(400).json({ error: 'Provide one or two valid stock symbols.' });
      }

      const shouldLike = req.query.like === 'true' || req.query.like === true;
      if (shouldLike) {
        const ip = getClientIp(req);
        stocks.forEach(function (stock) { addLike(stock, ip); });
      }

      try {
        const stockData = await Promise.all(stocks.map(getStockData));
        if (stockData.length === 1) {
          return res.json({
            stockData: {
              stock: stockData[0].stock,
              price: stockData[0].price,
              likes: stockData[0].likes
            }
          });
        }

        const difference = stockData[0].likes - stockData[1].likes;
        return res.json({
          stockData: stockData.map(function (data, index) {
            return {
              stock: data.stock,
              price: data.price,
              rel_likes: index === 0 ? difference : -difference
            };
          })
        });
      } catch (error) {
        return res.status(502).json({ error: 'Unable to retrieve stock data right now.' });
      }
    });
};
