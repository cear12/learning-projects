'use strict';

require('dotenv').config();

const path = require('path');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

const apiRoutes         = require('./routes/api.js');
const fccTestingRoutes  = require('./routes/fcctesting.js');
const runner            = require('./test-runner');

const app = express();

app.disable('x-powered-by');
app.set('trust proxy', 1);

app.use(cors({ origin: '*', methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'] }));
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'"],
      imgSrc: ["'self'", 'data:'],
      connectSrc: ["'self'"],
      objectSrc: ["'none'"],
      baseUri: ["'self'"],
      frameAncestors: ["'none'"]
    }
  }
}));

app.use(express.json({ limit: '20kb' }));
app.use(express.urlencoded({ extended: false, limit: '20kb' }));
app.use('/public', express.static(path.join(__dirname, 'public')));

app.get('/b/:board/', function (req, res) {
  res.sendFile(path.join(__dirname, 'views', 'board.html'));
});
app.get('/b/:board/:threadid', function (req, res) {
  res.sendFile(path.join(__dirname, 'views', 'thread.html'));
});

app.get('/', function (req, res) {
  res.sendFile(path.join(__dirname, 'views', 'index.html'));
});

//For FCC testing purposes
fccTestingRoutes(app);

apiRoutes(app);

app.use(function (req, res) {
  res.status(404)
    .type('text')
    .send('Not Found');
});

app.use(function (error, req, res, next) {
  if (res.headersSent) return next(error);
  res.status(500).json({ error: 'Internal server error' });
});

//Start our server and tests!
const listener = app.listen(process.env.PORT || 3000, function () {
  console.log('Your app is listening on port ' + listener.address().port);
  if(process.env.NODE_ENV==='test') {
    console.log('Running Tests...');
    setTimeout(function () {
      try {
        runner.run();
      } catch(e) {
        console.log('Tests are not valid:');
        console.error(e);
      }
    }, 1500);
  }
});

module.exports = app; //for testing
