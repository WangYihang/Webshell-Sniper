# Benchmark environment

A disposable, self-contained stack for exercising Webshell-Sniper end to end:

- **target** — PHP 8.3 + Apache with a known one-line webshell (`webroot/index.php`,
  password `c`, method `POST`) and the `mysqli` extension built in.
- **db** — MySQL 8.4 seeded with a `benchmark` database (`mysql-init/seed.sql`),
  reachable from the target over the compose network as host `db`.
- **pg** — PostgreSQL 16, similarly seeded (`pg-init/seed.sql`), host `pg`.
- **jsp** — a JSP/Tomcat **command** webshell (`jsp/webapp/cmd.jsp`, param `c`)
  at `:8081/cmd.jsp`. A second-language target: Java has no `eval()`, so it is a
  command-only shell — the validation case for the command-shell backend.

> ⚠️ **Intentionally vulnerable.** The compose file binds the target to
> `127.0.0.1` only. Never expose it to a network.

## Usage

```bash
docker compose -f docker/docker-compose.yml up -d --build

# drive it interactively
webshell-sniper http://127.0.0.1:8080/index.php POST c
#   in the REPL:  db   ->   host=db   user=root   password=root

# the JSP command shell (param `c`)
curl 'http://127.0.0.1:8081/cmd.jsp?c=id'

# or run the automated benchmark suite against it
uv run pytest -m benchmark

docker compose -f docker/docker-compose.yml down -v
```

Start just one target with e.g. `docker compose -f docker/docker-compose.yml up -d jsp`.

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
