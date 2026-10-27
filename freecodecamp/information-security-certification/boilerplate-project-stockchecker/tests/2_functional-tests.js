const chaiHttp = require('chai-http');
const chai = require('chai');
const assert = chai.assert;
const server = require('../server');

chai.use(chaiHttp);

suite('Functional Tests', function () {
  this.timeout(15000);
  let firstLikeCount;

  test('Viewing one stock: GET request to /api/stock-prices/', function (done) {
    chai.request(server)
      .get('/api/stock-prices/')
      .query({ stock: 'goog' })
      .end(function (error, response) {
        if (error) return done(error);
        assert.equal(response.status, 200);
        assert.isObject(response.body.stockData);
        assert.property(response.body.stockData, 'stock');
        assert.property(response.body.stockData, 'price');
        assert.property(response.body.stockData, 'likes');
        assert.isString(response.body.stockData.stock);
        assert.isNumber(response.body.stockData.price);
        assert.isNumber(response.body.stockData.likes);
        done();
      });
  });

  test('Viewing one stock and liking it: GET request to /api/stock-prices/', function (done) {
    chai.request(server)
      .get('/api/stock-prices/')
      .query({ stock: 'goog', like: 'true' })
      .end(function (error, response) {
        if (error) return done(error);
        assert.equal(response.status, 200);
        assert.isObject(response.body.stockData);
        assert.isNumber(response.body.stockData.likes);
        assert.isAtLeast(response.body.stockData.likes, 1);
        firstLikeCount = response.body.stockData.likes;
        done();
      });
  });

  test('Viewing the same stock and liking it again: GET request to /api/stock-prices/', function (done) {
    chai.request(server)
      .get('/api/stock-prices/')
      .query({ stock: 'goog', like: 'true' })
      .end(function (error, response) {
        if (error) return done(error);
        assert.equal(response.status, 200);
        assert.equal(response.body.stockData.likes, firstLikeCount);
        done();
      });
  });

  test('Viewing two stocks: GET request to /api/stock-prices/', function (done) {
    chai.request(server)
      .get('/api/stock-prices/')
      .query({ stock: ['goog', 'msft'] })
      .end(function (error, response) {
        if (error) return done(error);
        assert.equal(response.status, 200);
        assert.isArray(response.body.stockData);
        assert.lengthOf(response.body.stockData, 2);
        response.body.stockData.forEach(function (stockData) {
          assert.property(stockData, 'stock');
          assert.property(stockData, 'price');
          assert.property(stockData, 'rel_likes');
          assert.isNumber(stockData.price);
          assert.isNumber(stockData.rel_likes);
        });
        done();
      });
  });

  test('Viewing two stocks and liking them: GET request to /api/stock-prices/', function (done) {
    chai.request(server)
      .get('/api/stock-prices/')
      .query({ stock: ['goog', 'msft'], like: 'true' })
      .end(function (error, response) {
        if (error) return done(error);
        assert.equal(response.status, 200);
        assert.isArray(response.body.stockData);
        assert.lengthOf(response.body.stockData, 2);
        response.body.stockData.forEach(function (stockData) {
          assert.isNumber(stockData.price);
          assert.isNumber(stockData.rel_likes);
        });
        done();
      });
  });

});
