# Benchmark environment

A disposable, self-contained stack for exercising Webshell-Sniper end to end:

- **target** — PHP 8.3 + Apache with a known one-line webshell (`webroot/index.php`,
  password `c`, method `POST`) and the `mysqli` extension built in.
- **db** — MySQL 8.4 seeded with a `benchmark` database (`mysql-init/seed.sql`),
  reachable from the target over the compose network as host `db`.

> ⚠️ **Intentionally vulnerable.** The compose file binds the target to
> `127.0.0.1` only. Never expose it to a network.

## Usage

```bash
docker compose -f docker/docker-compose.yml up -d --build

# drive it interactively
webshell-sniper http://127.0.0.1:8080/index.php POST c
#   in the REPL:  db   ->   host=db   user=root   password=root

# or run the automated benchmark suite against it
uv run pytest -m benchmark

docker compose -f docker/docker-compose.yml down -v
```

## Behind Docker Hub's pull rate limit?

Override the base images with the AWS ECR public mirror (no anonymous limit):

```bash
cp docker/.env.example docker/.env      # then uncomment the mirror lines
docker compose -f docker/docker-compose.yml --env-file docker/.env up -d --build
```

## Notes

- The default `pytest` run **excludes** these (`-m 'not benchmark'`), so neither
  CI nor a plain `uv run pytest` needs Docker.
- The lightweight `integration` tests (`tests/integration/`) spin up their own
  `php -S` target and need only `php` on `PATH` — they cover the wire protocol
  without Docker. The benchmark stack additionally covers the **MySQL client**
  against a real database.
