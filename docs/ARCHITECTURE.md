# Architecture & abstraction plan

## Current layering

```
Transport (HTTP)            how a payload string reaches the shell parameter
  └ Executor                sentinels, encode, exec-fn probe/fallback
      └ features/*           recon / files / database / revshell / inject / portscan
          └ log (rich)       presentation
```

`Transport` is already language-agnostic (it just POSTs/GETs a string). Almost
everything above it, however, hard-codes **PHP**:

| Where | PHP-specific bit |
|-------|------------------|
| `core/php.py` | `base64_decode('…')` string literal |
| `core/executor.py` | `echo 'TOK';…;echo 'TOK';` sentinel; `_EXEC_BUILDERS` (`system`/`shell_exec`/…); `ini_get('disable_functions')` |
| `encoders.py` | `eval(base64_decode(…))`, `gzinflate`, the xor decoder loop |
| `core/webshell.py` | `$_SERVER['DOCUMENT_ROOT']`, `phpversion()` |
| `features/*` | `file_get_contents`, `scandir`, `stat`, `mysqli`, `PDO`, `fsockopen`, … |

## The language abstraction: `Backend`

Introduce a `Backend` (per language) that owns *every* language-specific code
fragment. The `Executor` becomes language-agnostic orchestration; features stop
emitting raw PHP and instead ask the backend/executor for **primitives**.

```python
class Backend(ABC):
    name: str
    capabilities: frozenset[str]          # {"command","fs","mysql","portscan",...}

    # code generation
    def literal(self, value: str) -> str           # safe string expr   (php: base64_decode('…'))
    def sentinel(self, token: str, code: str) -> str  # print TOK; run code; print TOK
    def command_builders(self) -> dict[str, Builder]  # ordered exec-fn candidates
    def disabled_functions_code(self) -> str | None   # how to detect disabled fns (or None)
    def webroot_code(self) -> str
    def version_code(self) -> str

    # filesystem primitives (return language code that prints the result)
    def read_file_code(self, path) -> str
    def write_file_code(self, path, data_b64) -> str
    def exists_code(self, path) -> str
    def list_dir_code(self, path) -> str
    def stat_code(self, path) -> str
    def read_range_code(self, path, offset, length) -> str
```

Layering becomes:

```
Channel (HTTP)  →  Backend (php | jsp | …)  →  Executor (lang-agnostic)
                                                   →  Features (lang-agnostic via primitives;
                                                       PHP-only ones gated by `capabilities`)
                                                          →  Renderer (rich | json | quiet)
```

### What generalizes vs stays language-specific
- **Generalize** (express via primitives): command exec, recon (mostly OS
  commands), file read/write/list/stat/upload/download, cwd shell, enum.
- **Stay backend-specific, gated by `capabilities`**: DB clients (`mysqli`/PDO),
  port-scan (`fsockopen`), in-language webshell injection, FUSE mount. A feature
  checks `if "mysql" in backend.capabilities` and degrades gracefully elsewhere.

### Migration (behaviour-preserving, incremental)
1. **Extract `PHPBackend`** holding today's fragments; route `Executor`,
   `core/php.py`, `core/webshell.py` through it. No behaviour change — tests
   stay green. *(first step)*
2. **Primitive-ize files/recon**: features call `executor.read_file()` /
   `list_dir()` etc., which delegate to `backend.*_code`. Now those features are
   language-agnostic.
3. **Backend-aware encoders** (see below).
4. **Add a second backend** (e.g. a generic *command-only* shell, then JSP) to
   prove the seam; select with `--lang`.
5. **Shell type** (eval vs command-only, the `CMDSHELL` backlog item) becomes a
   backend variant rather than a special case.

## Other components worth abstracting

1. **Encoder → byte-transform + decode-wrapper.** Today `Encoder` emits PHP
   (`eval(base64_decode(…))`). Split into a language-neutral **byte transform**
   (base64/gzip/xor of bytes) plus a per-backend **decode expression**, so the
   same evasion strategies work on every backend. → `encoders.py` + `Backend`.
2. **Channel (transport).** Formalize `Transport` as a `Channel` protocol
   (`send(payload) -> str`), so non-HTTP channels (raw socket, alternate request
   shapes, even a stored-file relay) can plug in without touching the executor.
3. **Renderer / Reporter.** Features currently call `log.*` directly (mixing
   compute + presentation — the `PURE` backlog item). Introduce a `Renderer`
   (console-rich / json / quiet) and have features **return structured data**;
   the REPL/CLI/batch render. Unlocks clean JSON output and library use.
4. **Database backend — already the template.** `SqlClient` (MySQL/PostgreSQL)
   is exactly this pattern; extend it (SQLite/MSSQL) the same way and mirror its
   shape for the language `Backend`.
5. **Session.** `cwd`, the loaded shells and history live as `Repl` attributes;
   a `Session` object would enable save/restore and scripting.
6. **Config sources.** Layer CLI flags over env vars over a config file behind a
   single resolver (ties to the `CFG` backlog item).

## Non-goals (unchanged)
GUI; Windows *target* support. (Multi-language is now in-scope via `Backend`,
but each new language backend is opt-in work.)
