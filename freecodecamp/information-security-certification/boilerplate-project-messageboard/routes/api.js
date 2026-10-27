'use strict';

const { createStore } = require('../lib/store');

const BOARD_PATTERN = /^[A-Za-z0-9_-]{1,50}$/;

function validBoard(board) {
  return typeof board === 'string' && BOARD_PATTERN.test(board);
}

function nonEmpty(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

module.exports = function (app) {
  const storePromise = createStore();

  app.post('/api/threads/:board', async function (req, res) {
    if (!validBoard(req.params.board) || !nonEmpty(req.body.text) || !nonEmpty(req.body.delete_password)) {
      return res.status(400).json({ error: 'board, text and delete_password are required' });
    }
    try {
      const store = await storePromise;
      return res.json(await store.createThread(req.params.board, req.body.text.trim(), req.body.delete_password));
    } catch (error) {
      return res.status(503).json({ error: 'Database unavailable' });
    }
  });

  app.get('/api/threads/:board', async function (req, res) {
    if (!validBoard(req.params.board)) return res.status(400).json({ error: 'Invalid board' });
    try {
      const store = await storePromise;
      return res.json(await store.getThreads(req.params.board));
    } catch (error) {
      return res.status(503).json({ error: 'Database unavailable' });
    }
  });

  app.delete('/api/threads/:board', async function (req, res) {
    if (!validBoard(req.params.board) || !nonEmpty(req.body.thread_id) || !nonEmpty(req.body.delete_password)) {
      return res.status(400).send('Invalid request');
    }
    try {
      const store = await storePromise;
      return res.send(await store.deleteThread(req.params.board, req.body.thread_id, req.body.delete_password));
    } catch (error) {
      return res.status(503).send('Database unavailable');
    }
  });

  app.put('/api/threads/:board', async function (req, res) {
    const threadId = req.body.thread_id || req.body.report_id;
    if (!validBoard(req.params.board) || !nonEmpty(threadId)) return res.status(400).send('Invalid request');
    try {
      const store = await storePromise;
      return res.send(await store.reportThread(req.params.board, threadId));
    } catch (error) {
      return res.status(503).send('Database unavailable');
    }
  });

  app.post('/api/replies/:board', async function (req, res) {
    if (!validBoard(req.params.board) || !nonEmpty(req.body.thread_id) || !nonEmpty(req.body.text) || !nonEmpty(req.body.delete_password)) {
      return res.status(400).json({ error: 'thread_id, text and delete_password are required' });
    }
    try {
      const store = await storePromise;
      const result = await store.createReply(req.params.board, req.body.thread_id, req.body.text.trim(), req.body.delete_password);
      return result.success ? res.json(result) : res.status(404).json(result);
    } catch (error) {
      return res.status(503).json({ error: 'Database unavailable' });
    }
  });

  app.get('/api/replies/:board', async function (req, res) {
    if (!validBoard(req.params.board) || !nonEmpty(req.query.thread_id)) {
      return res.status(400).json({ error: 'thread_id is required' });
    }
    try {
      const store = await storePromise;
      const thread = await store.getThread(req.params.board, req.query.thread_id);
      return thread ? res.json(thread) : res.status(404).json({ error: 'thread not found' });
    } catch (error) {
      return res.status(503).json({ error: 'Database unavailable' });
    }
  });

  app.delete('/api/replies/:board', async function (req, res) {
    if (!validBoard(req.params.board) || !nonEmpty(req.body.thread_id) || !nonEmpty(req.body.reply_id) || !nonEmpty(req.body.delete_password)) {
      return res.status(400).send('Invalid request');
    }
    try {
      const store = await storePromise;
      return res.send(await store.deleteReply(req.params.board, req.body.thread_id, req.body.reply_id, req.body.delete_password));
    } catch (error) {
      return res.status(503).send('Database unavailable');
    }
  });

  app.put('/api/replies/:board', async function (req, res) {
    if (!validBoard(req.params.board) || !nonEmpty(req.body.thread_id) || !nonEmpty(req.body.reply_id)) {
      return res.status(400).send('Invalid request');
    }
    try {
      const store = await storePromise;
      return res.send(await store.reportReply(req.params.board, req.body.thread_id, req.body.reply_id));
    } catch (error) {
      return res.status(503).send('Database unavailable');
    }
  });

};
