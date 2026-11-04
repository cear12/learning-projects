'use strict';

require('dotenv').config();
const path = require('node:path');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const { createStockService } = require('./lib/stock-service');
const { persistentStorage } = require('./lib/like-store');
const apiRoutes = require('./routes/api');

function proxySetting(value) {
  if (!value || value === 'false') return false;
  if (/^\d+$/.test(value)) return Number(value);
  return value.split(',').map(part => part.trim());
}

function createApp(options = {}) {
  const storage = options.store ? options : persistentStorage();
  const app = express();
  app.disable('x-powered-by');
  app.set('trust proxy', options.trustProxy === undefined ? proxySetting(process.env.TRUST_PROXY) : options.trustProxy);
  app.use(cors({ origin: '*', methods: ['GET', 'OPTIONS'] }));
  app.use(helmet({ contentSecurityPolicy: { directives: {
    defaultSrc: ["'self'"], scriptSrc: ["'self'"], styleSrc: ["'self'"],
    imgSrc: ["'self'", 'data:'], connectSrc: ["'self'"], objectSrc: ["'none'"],
    baseUri: ["'self'"], frameAncestors: ["'none'"], upgradeInsecureRequests: null
  } } }));
  app.use('/public', express.static(path.join(__dirname, 'public')));
  app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'views', 'index.html')));
  app.get('/health', (req, res) => res.json({ status: 'ok' }));
  // Preserve the supplied testing router while providing current Express header access.
  app.get('/_api/app-info', (req, res) => res.json({ headers: res.getHeaders() }));
  app.get('/_api/server.js', (req, res) => res.type('text').sendFile(path.join(__dirname, 'server.js')));
  app.get('/_api/routes/api.js', (req, res) => res.type('text').sendFile(path.join(__dirname, 'routes', 'api.js')));
  if (options.fccTesting !== false) require('./routes/fcctesting')(app);
  const service = createStockService({ ...storage, quoteProvider: options.quoteProvider });
  apiRoutes(app, service);
  app.locals.likeStore = storage.store;
  app.use((req, res) => res.status(404).json({ error: 'Not found.' }));
  app.use((error, req, res, next) => {
    if (res.headersSent) return next(error);
    res.status(500).json({ error: 'Unable to process this request.' });
  });
  return app;
}

const app = createApp();
module.exports = app;
module.exports.createApp = createApp;

if (require.main === module) {
  const listener = app.listen(process.env.PORT || 3000, () => {
    console.log('Stock Price Checker listening on port ' + listener.address().port);
    if (process.env.NODE_ENV === 'test') setTimeout(() => require('./test-runner').run(), 100);
  });
}
