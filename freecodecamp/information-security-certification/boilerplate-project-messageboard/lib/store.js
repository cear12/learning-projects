'use strict';

const crypto = require('crypto');
const { MongoClient, ObjectId } = require('mongodb');

const secret = process.env.DELETE_PASSWORD_SECRET || 'message-board-local-secret';

function hashPassword(password) {
  return crypto.createHash('sha256').update(secret + ':' + password).digest('hex');
}

function newId() {
  return crypto.randomBytes(12).toString('hex');
}

function publicReply(reply) {
  return {
    _id: String(reply._id),
    text: reply.text,
    created_on: reply.created_on
  };
}

function publicThread(thread, replyLimit) {
  const replies = (thread.replies || []).slice(-(replyLimit || 0)).map(publicReply);
  return {
    _id: String(thread._id),
    text: thread.text,
    created_on: thread.created_on,
    bumped_on: thread.bumped_on,
    replies: replies,
    replycount: (thread.replies || []).length
  };
}

class MemoryStore {
  constructor() {
    this.threads = new Map();
  }

  boardThreads(board) {
    if (!this.threads.has(board)) this.threads.set(board, []);
    return this.threads.get(board);
  }

  async createThread(board, text, password) {
    const now = new Date();
    const thread = {
      _id: newId(),
      board: board,
      text: text,
      delete_password: hashPassword(password),
      created_on: now,
      bumped_on: now,
      reported: false,
      replies: []
    };
    this.boardThreads(board).push(thread);
    return { success: true, thread_id: thread._id };
  }

  async getThreads(board) {
    return this.boardThreads(board)
      .slice()
      .sort(function (a, b) { return b.bumped_on - a.bumped_on; })
      .slice(0, 10)
      .map(function (thread) { return publicThread(thread, 3); });
  }

  findThread(board, threadId) {
    return this.boardThreads(board).find(function (thread) {
      return String(thread._id) === String(threadId);
    });
  }

  async deleteThread(board, threadId, password) {
    const threads = this.boardThreads(board);
    const index = threads.findIndex(function (thread) {
      return String(thread._id) === String(threadId);
    });
    if (index < 0) return 'not found';
    if (threads[index].delete_password !== hashPassword(password)) return 'incorrect password';
    threads.splice(index, 1);
    return 'success';
  }

  async reportThread(board, threadId) {
    const thread = this.findThread(board, threadId);
    if (!thread) return 'not found';
    thread.reported = true;
    return 'success';
  }

  async createReply(board, threadId, text, password) {
    const thread = this.findThread(board, threadId);
    if (!thread) return { success: false, error: 'thread not found' };
    const reply = {
      _id: newId(),
      text: text,
      delete_password: hashPassword(password),
      created_on: new Date(),
      reported: false
    };
    thread.replies.push(reply);
    thread.bumped_on = new Date();
    return { success: true, reply_id: reply._id };
  }

  async getThread(board, threadId) {
    const thread = this.findThread(board, threadId);
    return thread ? publicThread(thread, thread.replies.length) : null;
  }

  async deleteReply(board, threadId, replyId, password) {
    const thread = this.findThread(board, threadId);
    if (!thread) return 'thread not found';
    const index = thread.replies.findIndex(function (reply) {
      return String(reply._id) === String(replyId);
    });
    if (index < 0) return 'reply not found';
    if (thread.replies[index].delete_password !== hashPassword(password)) return 'incorrect password';
    thread.replies.splice(index, 1);
    return 'success';
  }

  async reportReply(board, threadId, replyId) {
    const thread = this.findThread(board, threadId);
    if (!thread) return 'thread not found';
    const reply = thread.replies.find(function (item) {
      return String(item._id) === String(replyId);
    });
    if (!reply) return 'reply not found';
    reply.reported = true;
    return 'success';
  }
}

class MongoStore {
  constructor(client, collection) {
    this.client = client;
    this.threads = collection;
  }

  static async connect(connectionString) {
    const client = new MongoClient(connectionString, { serverSelectionTimeoutMS: 5000 });
    await client.connect();
    let db;
    try {
      db = client.db();
    } catch (error) {
      db = client.db('messageboard');
    }
    return new MongoStore(client, db.collection('threads'));
  }

  objectId(value) {
    return ObjectId.isValid(value) ? new ObjectId(value) : null;
  }

  async createThread(board, text, password) {
    const now = new Date();
    const thread = {
      board: board,
      text: text,
      delete_password: hashPassword(password),
      created_on: now,
      bumped_on: now,
      reported: false,
      replies: []
    };
    const result = await this.threads.insertOne(thread);
    return { success: true, thread_id: String(result.insertedId) };
  }

  async getThreads(board) {
    const threads = await this.threads.find({ board }).sort({ bumped_on: -1 }).limit(10).toArray();
    return threads.map(function (thread) { return publicThread(thread, 3); });
  }

  async findThread(board, threadId) {
    const id = this.objectId(threadId);
    return id ? this.threads.findOne({ _id: id, board }) : null;
  }

  async deleteThread(board, threadId, password) {
    const thread = await this.findThread(board, threadId);
    if (!thread) return 'not found';
    if (thread.delete_password !== hashPassword(password)) return 'incorrect password';
    await this.threads.deleteOne({ _id: thread._id, board });
    return 'success';
  }

  async reportThread(board, threadId) {
    const thread = await this.findThread(board, threadId);
    if (!thread) return 'not found';
    await this.threads.updateOne({ _id: thread._id, board }, { $set: { reported: true } });
    return 'success';
  }

  async createReply(board, threadId, text, password) {
    const thread = await this.findThread(board, threadId);
    if (!thread) return { success: false, error: 'thread not found' };
    const reply = {
      _id: new ObjectId(),
      text: text,
      delete_password: hashPassword(password),
      created_on: new Date(),
      reported: false
    };
    await this.threads.updateOne(
      { _id: thread._id, board },
      { $push: { replies: reply }, $set: { bumped_on: new Date() } }
    );
    return { success: true, reply_id: String(reply._id) };
  }

  async getThread(board, threadId) {
    const thread = await this.findThread(board, threadId);
    return thread ? publicThread(thread, thread.replies.length) : null;
  }

  async deleteReply(board, threadId, replyId, password) {
    const thread = await this.findThread(board, threadId);
    if (!thread) return 'thread not found';
    const id = this.objectId(replyId);
    const reply = id && (thread.replies || []).find(function (item) {
      return String(item._id) === String(id);
    });
    if (!reply) return 'reply not found';
    if (reply.delete_password !== hashPassword(password)) return 'incorrect password';
    await this.threads.updateOne({ _id: thread._id, board }, { $pull: { replies: { _id: id } } });
    return 'success';
  }

  async reportReply(board, threadId, replyId) {
    const thread = await this.findThread(board, threadId);
    const id = this.objectId(replyId);
    if (!thread) return 'thread not found';
    if (!id || !(thread.replies || []).some(function (item) { return String(item._id) === String(id); })) {
      return 'reply not found';
    }
    await this.threads.updateOne(
      { _id: thread._id, board, 'replies._id': id },
      { $set: { 'replies.$.reported': true } }
    );
    return 'success';
  }
}

async function createStore() {
  if (!process.env.DB) return new MemoryStore();
  try {
    return await MongoStore.connect(process.env.DB);
  } catch (error) {
    if (process.env.NODE_ENV === 'test') {
      console.warn('MongoDB unavailable in test mode; using an in-memory store.');
      return new MemoryStore();
    }
    throw error;
  }
}

module.exports = { createStore, hashPassword, MemoryStore, MongoStore };
