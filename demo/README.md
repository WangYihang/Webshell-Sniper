# Demo recording

`sniper.gif` (embedded in the top-level README) is generated from `driver.py`,
which drives the REPL against the local docker target and writes an asciinema v2
cast — no `asciinema rec` needed, so it runs headless.

## Regenerate

```bash
# 1. bring up the disposable target (see ../docker/)
docker compose -f ../docker/docker-compose.yml up -d target

# 2. record the cast (spawns the REPL on a PTY and "types" the highlight reel)
python driver.py sniper.cast

# 3. render the GIF (https://github.com/asciinema/agg)
agg --theme monokai --font-size 14 --line-height 1.3 \
    --speed 1.25 --idle-time-limit 1.4 sniper.cast sniper.gif
```

Edit the `CMDS` list in `driver.py` to change the demo. The driver answers
terminal cursor-position queries so a prompt_toolkit/readline input loop never
stalls.
