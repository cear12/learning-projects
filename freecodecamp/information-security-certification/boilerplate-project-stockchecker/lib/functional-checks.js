'use strict';

// The hosted runtime executes these checks against its actual API handler and database.
async function runFunctionalChecks(request) {
  let firstLikeCount;
  function check(condition, message) { if (!condition) throw new Error(message); }
  function single(body) {
    const data = body.stockData;
    check(data && !Array.isArray(data) && data.stock === 'GOOG', 'Expected one GOOG quote');
    check(Number.isFinite(data.price) && Number.isInteger(data.likes), 'Expected numeric price and likes');
    return data;
  }
  function pair(body) {
    const data = body.stockData;
    check(Array.isArray(data) && data.length === 2, 'Expected two quotes');
    check(data[0].stock === 'GOOG' && data[1].stock === 'MSFT', 'Expected request order');
    check(data.every(item => Number.isFinite(item.price) && Number.isInteger(item.rel_likes) && !('likes' in item)),
      'Expected prices and relative likes');
    check(data[0].rel_likes + data[1].rel_likes === 0, 'Relative likes must be opposites');
  }
  const cases = [
    ['Viewing one stock: GET request to /api/stock-prices/', async () => single(await request('?stock=goog'))],
    ['Viewing one stock and liking it: GET request to /api/stock-prices/', async () => {
      firstLikeCount = single(await request('?stock=goog&like=true')).likes;
      check(firstLikeCount >= 1, 'Expected a like');
    }],
    ['Viewing the same stock and liking it again: GET request to /api/stock-prices/', async () => {
      check(single(await request('?stock=goog&like=true')).likes === firstLikeCount, 'Duplicate like was counted');
    }],
    ['Viewing two stocks: GET request to /api/stock-prices/', async () => pair(await request('?stock=goog&stock=msft'))],
    ['Viewing two stocks and liking them: GET request to /api/stock-prices/',
      async () => pair(await request('?stock=goog&stock=msft&like=true'))]
  ];
  const results = [];
  for (const [title, run] of cases) {
    try {
      await run();
      results.push({ title, context: 'Functional Tests', state: 'passed', assertions: [] });
    } catch {
      results.push({ title, context: 'Functional Tests', state: 'failed', assertions: [] });
    }
  }
  return results;
}

module.exports = { runFunctionalChecks };
