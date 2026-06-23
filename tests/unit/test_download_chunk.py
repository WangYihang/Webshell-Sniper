"""Chunked/ranged download reassembles correctly (no network)."""

import base64
import re

from webshell_sniper.features import files


class FileWS:
    """Serves ``content`` via filesize + ranged fread, like a real PHP target."""

    def __init__(self, content: bytes):
        self.content = content
        self.url = "http://t/c.php"
        self.reads = 0

    def run_php(self, code: str) -> str:
        if "filesize(" in code:
            return str(len(self.content))
        ranged = re.search(r"fseek\(\$f,(\d+)\);echo base64_encode\(fread\(\$f,(\d+)\)\)", code)
        if ranged:
            self.reads += 1
            off, length = int(ranged.group(1)), int(ranged.group(2))
            return base64.b64encode(self.content[off : off + length]).decode()
        if "file_get_contents(" in code:  # single-shot path
            return base64.b64encode(self.content).decode()
        return ""


def test_large_file_downloads_in_chunks(tmp_path):
    content = bytes(range(256)) * 64  # 16384 bytes
    ws = FileWS(content)
    files.download(ws, "/big.bin", tmp_path, chunk_size=1000)
    saved = tmp_path / "t" / "big.bin"
    assert saved.read_bytes() == content
    assert ws.reads >= 16  # actually chunked, not one shot


def test_small_file_uses_single_shot(tmp_path):
    ws = FileWS(b"hello world")
    files.download(ws, "/s.txt", tmp_path, chunk_size=1_000_000)
    assert (tmp_path / "t" / "s.txt").read_bytes() == b"hello world"
    assert ws.reads == 0  # never hit the ranged path
