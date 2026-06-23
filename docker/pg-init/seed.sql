-- Seed data for the benchmark PostgreSQL service (database: benchmark).
CREATE TABLE IF NOT EXISTS users (
  id       SERIAL PRIMARY KEY,
  username VARCHAR(64),
  note     VARCHAR(255)
);

-- Same comma-containing value as the MySQL seed, to prove the PostgreSQL
-- client also preserves it.
INSERT INTO users (username, note) VALUES
  ('alice', 'value, with, commas'),
  ('bob',   'plain');
