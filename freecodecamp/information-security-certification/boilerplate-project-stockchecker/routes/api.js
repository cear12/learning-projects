'use strict';

const { RequestError } = require('../lib/stock-service');

module.exports = function (app, service) {
  app.get('/api/stock-prices', async function (req, res) {
    res.set('Cache-Control', 'no-store');
    try {
      res.json(await service.lookup(req.query, req.ip));
    } catch (error) {
      res.status(error instanceof RequestError ? error.status : 500).json({
        error: error instanceof RequestError ? error.message : 'Unable to process this request.'
      });
    }
  });
};
