# Local test target

A throwaway PHP+Apache container with a known one-line webshell, for
exercising Webshell-Sniper end to end.

> ⚠️ This container is **intentionally vulnerable**. Bind it to localhost only
> (the compose file already does) and never expose it to a network.

```bash
docker compose -f docker/docker-compose.yml up -d

# password is `c`, method POST
webshell-sniper http://127.0.0.1:8080/index.php POST c

docker compose -f docker/docker-compose.yml down
```

The integration test-suite does **not** need Docker — it spins up its own
`php -S` target (see `tests/conftest.py`) and is skipped automatically when
`php` is not installed.
