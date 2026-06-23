-- Seed data for the benchmark MySQL service.
CREATE DATABASE IF NOT EXISTS benchmark;
USE benchmark;

CREATE TABLE IF NOT EXISTS users (
  id       INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64),
  note     VARCHAR(255)
);

-- The first row deliberately contains commas: it proves the v2 MySQL client
-- (ASCII unit/record separators) no longer corrupts values the way v1's
-- comma-join did.
INSERT INTO users (username, note) VALUES
  ('alice', 'value, with, commas'),
  ('bob',   'plain');
