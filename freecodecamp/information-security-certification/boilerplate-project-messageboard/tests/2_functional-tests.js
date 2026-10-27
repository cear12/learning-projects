const chaiHttp = require('chai-http');
const chai = require('chai');
const assert = chai.assert;
const server = require('../server');

chai.use(chaiHttp);

suite('Functional Tests', function () {
  this.timeout(15000);
  const board = 'test';
  const threadPassword = 'thread-secret';
  const replyPassword = 'reply-secret';
  let threadId;
  let reportThreadId;
  let replyThreadId;
  let replyId;

  function createThread(password, text, callback) {
    chai.request(server)
      .post('/api/threads/' + board)
      .send({ text: text, delete_password: password })
      .end(callback);
  }

  test('Creating a new thread: POST request to /api/threads/{board}', function (done) {
    createThread(threadPassword, 'A functional test thread', function (error, response) {
      if (error) return done(error);
      assert.equal(response.status, 200);
      assert.isTrue(response.body.success);
      assert.isString(response.body.thread_id);
      threadId = response.body.thread_id;
      done();
    });
  });

  test('Viewing the 10 most recent threads with 3 replies each: GET request to /api/threads/{board}', function (done) {
    chai.request(server)
      .get('/api/threads/' + board)
      .end(function (error, response) {
        if (error) return done(error);
        assert.equal(response.status, 200);
        assert.isArray(response.body);
        assert.isAtMost(response.body.length, 10);
        const thread = response.body.find(function (item) { return item._id === threadId; });
        assert.isObject(thread);
        assert.property(thread, 'text');
        assert.property(thread, 'created_on');
        assert.property(thread, 'bumped_on');
        assert.property(thread, 'replies');
        assert.property(thread, 'replycount');
        assert.isAtMost(thread.replies.length, 3);
        done();
      });
  });

  test('Deleting a thread with the incorrect password: DELETE request to /api/threads/{board}', function (done) {
    chai.request(server)
      .delete('/api/threads/' + board)
      .send({ thread_id: threadId, delete_password: 'wrong-password' })
      .end(function (error, response) {
        if (error) return done(error);
        assert.equal(response.status, 200);
        assert.equal(response.text, 'incorrect password');
        done();
      });
  });

  test('Deleting a thread with the correct password: DELETE request to /api/threads/{board}', function (done) {
    chai.request(server)
      .delete('/api/threads/' + board)
      .send({ thread_id: threadId, delete_password: threadPassword })
      .end(function (error, response) {
        if (error) return done(error);
        assert.equal(response.status, 200);
        assert.equal(response.text, 'success');
        done();
      });
  });

  test('Reporting a thread: PUT request to /api/threads/{board}', function (done) {
    createThread(threadPassword, 'A thread to report', function (createError, createResponse) {
      if (createError) return done(createError);
      reportThreadId = createResponse.body.thread_id;
      chai.request(server)
        .put('/api/threads/' + board)
        .send({ thread_id: reportThreadId })
        .end(function (error, response) {
          if (error) return done(error);
          assert.equal(response.status, 200);
          assert.equal(response.text, 'success');
          done();
        });
    });
  });

  test('Creating a new reply: POST request to /api/replies/{board}', function (done) {
    createThread(threadPassword, 'A thread for replies', function (createError, createResponse) {
      if (createError) return done(createError);
      replyThreadId = createResponse.body.thread_id;
      chai.request(server)
        .post('/api/replies/' + board)
        .send({
          thread_id: replyThreadId,
          text: 'A functional test reply',
          delete_password: replyPassword
        })
        .end(function (error, response) {
          if (error) return done(error);
          assert.equal(response.status, 200);
          assert.isTrue(response.body.success);
          assert.isString(response.body.reply_id);
          replyId = response.body.reply_id;
          done();
        });
    });
  });

  test('Viewing a single thread with all replies: GET request to /api/replies/{board}', function (done) {
    chai.request(server)
      .get('/api/replies/' + board)
      .query({ thread_id: replyThreadId })
      .end(function (error, response) {
        if (error) return done(error);
        assert.equal(response.status, 200);
        assert.equal(response.body._id, replyThreadId);
        assert.isArray(response.body.replies);
        assert.isAtLeast(response.body.replies.length, 1);
        assert.equal(response.body.replies[0]._id, replyId);
        done();
      });
  });

  test('Deleting a reply with the incorrect password: DELETE request to /api/replies/{board}', function (done) {
    chai.request(server)
      .delete('/api/replies/' + board)
      .send({ thread_id: replyThreadId, reply_id: replyId, delete_password: 'wrong-password' })
      .end(function (error, response) {
        if (error) return done(error);
        assert.equal(response.status, 200);
        assert.equal(response.text, 'incorrect password');
        done();
      });
  });

  test('Deleting a reply with the correct password: DELETE request to /api/replies/{board}', function (done) {
    chai.request(server)
      .delete('/api/replies/' + board)
      .send({ thread_id: replyThreadId, reply_id: replyId, delete_password: replyPassword })
      .end(function (error, response) {
        if (error) return done(error);
        assert.equal(response.status, 200);
        assert.equal(response.text, 'success');
        done();
      });
  });

  test('Reporting a reply: PUT request to /api/replies/{board}', function (done) {
    chai.request(server)
      .post('/api/replies/' + board)
      .send({
        thread_id: replyThreadId,
        text: 'A reply to report',
        delete_password: replyPassword
      })
      .end(function (createError, createResponse) {
        if (createError) return done(createError);
        const reportedReplyId = createResponse.body.reply_id;
        chai.request(server)
          .put('/api/replies/' + board)
          .send({ thread_id: replyThreadId, reply_id: reportedReplyId })
          .end(function (error, response) {
            if (error) return done(error);
            assert.equal(response.status, 200);
            assert.equal(response.text, 'success');
            done();
          });
      });
  });

});
