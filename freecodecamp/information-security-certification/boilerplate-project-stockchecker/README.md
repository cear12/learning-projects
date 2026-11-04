# Stock Price Checker

Author: **cear12**

[Live application / Solution Link](https://cear12-stock-price-checker.ole-creative-studio.workers.dev) · [Source Code Link](https://github.com/cear12/learning-projects/tree/main/freecodecamp/information-security-certification/boilerplate-project-stockchecker) · [Assignment](https://www.freecodecamp.org/learn/information-security/information-security-projects/stock-price-checker)

A full-stack JavaScript solution based on the [official starter](https://github.com/freeCodeCamp/boilerplate-project-stockchecker). View one stock, compare two stocks and optionally like them. Prices come from the official freeCodeCamp stock proxy; successful quotes are cached for 15 seconds.

## Verified behavior

All **18 local tests passed**: 13 storage/API/provider checks and the five required functional tests using actual quotes. Public HTTP verification also passed for the page, assets, CSP, quotes, comparisons, duplicate-like prevention, invalid requests and the five hosted checks. Likes and visitor deduplication were verified to survive redeployment. `npm audit` reported **0 known vulnerabilities** with the committed dependency versions.

The API returns:

- One stock: `{ "stockData": { "stock": "GOOG", "price": number, "likes": number } }`.
- Two stocks: `{ "stockData": [{ "stock": "GOOG", "price": number, "rel_likes": number }, ...] }`.

For comparisons, each `rel_likes` is that stock's like count minus the other stock's count. Request order is preserved. Repeating a symbol still returns two comparison entries, with zero relative difference and one unique like per visitor.

## Requests

```text
/api/stock-prices?stock=GOOG
/api/stock-prices?stock=GOOG&like=true
/api/stock-prices?stock=GOOG&stock=MSFT
/api/stock-prices?stock=GOOG&stock=MSFT&like=true
```

Symbols are case-insensitive. Invalid inputs return HTTP 400. Upstream failures return a controlled error and do not create likes, including a partly failed two-stock comparison.

## Storage and privacy

The Node/Express runtime stores likes in SQLite; the public Cloudflare runtime uses D1. Both use a unique `(stock, voter_hash)` database key, so repeated and concurrent likes from the same visitor do not increment the count. Two-stock like writes are transactional.

Client addresses are normalized and converted to HMAC-SHA256 digests with a stable secret before storage. Raw IP addresses are not stored in the application's likes table. Local secrets and runtime data are excluded from Git. Keep the secret stable across restarts and deployments so visitor deduplication remains effective.

The Express app ignores forwarding headers by default. Configure `TRUST_PROXY` only for the actual trusted reverse proxy topology. The hosted Worker uses Cloudflare's platform-provided client address. The CSP permits scripts and styles only from the application; there are no external scripts or styles.

## Run locally

Use **Node.js 24 or newer**:

```powershell
npm ci
Copy-Item sample.env .env
npm start
```

Open [localhost:3000](http://localhost:3000/). The sample sets `NODE_ENV=test`, as required by the assignment. When launched directly, the server runs the five functional checks and exposes their report through `/_api/get-tests`.

When `LIKE_HASH_SECRET` is omitted, a strong random secret is generated once in `.data/like-secret`. SQLite data is stored in `.data/likes.sqlite`. To retain local-server likes on a host, mount durable storage and set `LIKE_DATA_DIR` accordingly. Never commit `.env`, `.data`, `.dev.vars` or private keys.

## Tests

```powershell
npm test
npm run verify:live -- https://cear12-stock-price-checker.ole-creative-studio.workers.dev
```

The five required tests are in `tests/2_functional-tests.js`. Independent checks cover persistence, concurrent likes, equivalent IPv4/IPv6 spellings, keyed storage, failed quotes, malformed requests, forwarding-header spoofing, CSP, response shapes, provider caching and invalid/oversized upstream data.

`verify:live` exercises real HTTP endpoints and like requests from the caller's address. In environments that require a proxy or the operating system's certificate store, set `NODE_USE_ENV_PROXY=1` and `NODE_USE_SYSTEM_CA=1` before starting Node.

## Public deployment

`wrangler.jsonc` defines the public Worker, assets and dedicated D1 binding. `deploy/worker.mjs` reuses the same parsing, quote provider, HMAC identity and stock service as Express. `/_api/get-tests` executes the five hosted scenarios against that API handler and D1 database and reports their actual states; no successful report is prefilled.

For a separate deployment in another account, create a dedicated D1 database, replace its non-secret ID in the configuration, initialize it with `deploy/schema.sql`, and set a stable `LIKE_HASH_SECRET` through Wrangler's secret input. Then run `npm run deploy`. Existing deployments retain their secret and database across updates. The build copies only the public page and assets into the deployment directory.

The original protected testing helpers remain unchanged. Runtime secrets and private database contents are excluded from published source and assets.
