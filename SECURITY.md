# Security Policy

## Authorized use

Webshell-Sniper is an offensive-security tool intended **only** for use against
systems you own or are explicitly authorized to test (penetration testing
engagements, CTFs, security research, lab environments). Unauthorized access to
computer systems is illegal in most jurisdictions. You are responsible for
complying with all applicable laws; the authors accept no liability for misuse.

## Reporting a vulnerability *in the tool*

If you find a security issue in Webshell-Sniper itself (for example, something
that could harm the **operator** — a path traversal when downloading from a
malicious/honeypot target, unsafe handling of server-controlled data, etc.),
please report it privately to the maintainer (wangyihanger@gmail.com) rather
than opening a public issue. We aim to acknowledge reports within a few days.

## Operator-side hardening

- Run against untrusted/honeypot targets from a disposable VM or container.
- Downloads are confined to the output directory; path-traversal attempts in a
  target's file listing are flattened to a basename.
- Use `--proxy` to route traffic through your own tooling, and `-o` to keep
  loot scoped to a known directory.
