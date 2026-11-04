'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { randomBytes } = require('node:crypto');
const { DatabaseSync } = require('node:sqlite');

class LikeStore {
  constructor(filename) {
    this.database = new DatabaseSync(filename);
    this.database.exec(`CREATE TABLE IF NOT EXISTS likes (
      stock TEXT NOT NULL,
      voter_hash TEXT NOT NULL,
      PRIMARY KEY (stock, voter_hash)
    )`);
    this.insert = this.database.prepare('INSERT OR IGNORE INTO likes (stock, voter_hash) VALUES (?, ?)');
    this.count = this.database.prepare('SELECT COUNT(*) AS likes FROM likes WHERE stock = ?');
  }

  addLikes(stocks, voter) {
    this.database.exec('BEGIN IMMEDIATE');
    try {
      for (const stock of stocks) this.insert.run(stock, voter);
      this.database.exec('COMMIT');
    } catch (error) {
      this.database.exec('ROLLBACK');
      throw error;
    }
  }

  getLikes(stock) { return this.count.get(stock).likes; }
  close() { this.database.close(); }
}

function persistentStorage() {
  const directory = path.resolve(process.env.LIKE_DATA_DIR || path.join(__dirname, '..', '.data'));
  fs.mkdirSync(directory, { recursive: true });
  let secret = process.env.LIKE_HASH_SECRET;
  if (!secret) {
    const filename = path.join(directory, 'like-secret');
    try { fs.writeFileSync(filename, randomBytes(32).toString('hex'), { flag: 'wx', mode: 0o600 }); }
    catch (error) { if (error.code !== 'EEXIST') throw error; }
    secret = fs.readFileSync(filename, 'utf8');
  }
  return { store: new LikeStore(path.join(directory, 'likes.sqlite')), secret };
}

module.exports = { LikeStore, persistentStorage };
