CREATE TABLE IF NOT EXISTS likes (
  stock TEXT NOT NULL,
  voter_hash TEXT NOT NULL,
  PRIMARY KEY (stock, voter_hash)
);
