"""Chunked/ranged download reassembles correctly (no network)."""

from webshell_sniper.features import files


class FileExecutor:
    """Serves ``content`` via fs_size + ranged fs_read_range, like a real target."""

    def __init__(self, content: bytes):
        self.content = content
        self.ranged_reads = 0
        self.single_reads = 0

    def fs_size(self, path: str) -> int:
        return len(self.content)

    def fs_read_bytes(self, path: str) -> bytes:
        self.single_reads += 1
        return self.content

    def fs_read_range(self, path: str, offset: int, length: int) -> bytes:
        self.ranged_reads += 1
        return self.content[offset : offset + length]

    def fs_md5(self, path: str) -> str:
        return ""


class FileWS:
    def __init__(self, content: bytes):
        self.url = "http://t/c.php"
        self.executor = FileExecutor(content)


def test_large_file_downloads_in_chunks(tmp_path):
    content = bytes(range(256)) * 64  # 16384 bytes
    ws = FileWS(content)
    files.download(ws, "/big.bin", tmp_path, chunk_size=1000)
    saved = tmp_path / "t" / "big.bin"
    assert saved.read_bytes() == content
    assert ws.executor.ranged_reads >= 16  # actually chunked, not one shot
    assert ws.executor.single_reads == 0


def test_small_file_uses_single_shot(tmp_path):
    ws = FileWS(b"hello world")
    files.download(ws, "/s.txt", tmp_path, chunk_size=1_000_000)
    assert (tmp_path / "t" / "s.txt").read_bytes() == b"hello world"
    assert ws.executor.ranged_reads == 0  # never hit the ranged path
    assert ws.executor.single_reads == 1
