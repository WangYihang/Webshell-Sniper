"""DB clients generate the right PHP/SQL and parse rows correctly (no network)."""

import pytest

from webshell_sniper.features.database import (
    _COL_SEP,
    _ROW_SEP,
    MysqlManager,
    PostgresManager,
    make_client,
)


class FakeWS:
    def __init__(self, response: str = ""):
        self.response = response
        self.last_code = ""

    def run_php(self, code: str) -> str:
        self.last_code = code
        return self.response


def test_mysql_query_uses_mysqli_and_parses_rows():
    ws = FakeWS(f"a{_COL_SEP}b{_ROW_SEP}c{_COL_SEP}d{_ROW_SEP}")
    rows = MysqlManager(ws, "h", "u", "p").query("SELECT 1")
    assert rows == [["a", "b"], ["c", "d"]]
    assert "new mysqli(" in ws.last_code


def test_postgres_query_uses_pdo_pgsql():
    ws = FakeWS("")
    PostgresManager(ws, "h", "u", "p", "db").query("SELECT 1")
    assert "new PDO(" in ws.last_code
    assert "pgsql:host=" in ws.last_code


def test_error_response_raises():
    ws = FakeWS("ERR:access denied")
    with pytest.raises(Exception, match="access denied"):
        MysqlManager(ws, "h", "u", "p").query("SELECT 1")


def test_identifier_quoting_per_engine():
    assert MysqlManager(FakeWS(), "h", "u", "p")._quote_ident("a`b") == "`a``b`"
    assert PostgresManager(FakeWS(), "h", "u", "p")._quote_ident('a"b') == '"a""b"'


def test_make_client_dispatch_and_unknown():
    assert isinstance(make_client("mysql", FakeWS(), "h", "u", "p"), MysqlManager)
    assert isinstance(make_client("pgsql", FakeWS(), "h", "u", "p"), PostgresManager)
    with pytest.raises(ValueError, match="unknown DB engine"):
        make_client("oracle", FakeWS(), "h", "u", "p")


class RecordingClient(MysqlManager):
    """Capture the SQL passed to query() and feed canned result pages."""

    def __init__(self, pages):
        super().__init__(FakeWS(), "h", "u", "p")
        self.pages = list(pages)
        self.sql: list[str] = []

    def query(self, sql):  # type: ignore[override]
        self.sql.append(sql)
        if "information_schema.columns" in sql:
            return [["id"], ["name"]]
        if "SELECT * FROM" in sql:
            return self.pages.pop(0) if self.pages else []
        return []


def test_export_csv_pages_and_writes_header(tmp_path):
    client = RecordingClient(pages=[[["1", "a"], ["2", "b"]], [["3", "c"]], []])
    out = tmp_path / "t.csv"
    n = client.export_csv("s", "t", out, page_size=2)
    assert n == 3
    lines = out.read_text().splitlines()
    assert lines[0] == "id,name"  # column header
    assert lines[1] == "1,a" and lines[-1] == "3,c"
    # paged: stopped only when a short/empty page arrived.
    assert sum("SELECT * FROM" in s for s in client.sql) >= 2


class _SqlCapture:
    """Mixin: capture the SQL passed to query() (it's base64'd inside the PHP)."""

    def __init__(self, *args, scalar=""):
        super().__init__(*args)
        self.sql: list[str] = []
        self._scalar_val = scalar

    def query(self, sql):  # type: ignore[override]
        self.sql.append(sql)
        return [[self._scalar_val]] if self._scalar_val else []


class CapturingMysql(_SqlCapture, MysqlManager):
    pass


class CapturingPg(_SqlCapture, PostgresManager):
    pass


def test_mysql_server_file_primitives():
    mysql = CapturingMysql(FakeWS(), "h", "u", "p", scalar="filedata")
    assert mysql.read_server_file("/etc/passwd") == "filedata"
    assert "LOAD_FILE('/etc/passwd')" in mysql.sql[-1]
    mysql.write_server_file("/tmp/x", b"\x00\xff")
    assert "0x00ff INTO DUMPFILE '/tmp/x'" in mysql.sql[-1]


def test_pg_server_file_primitives():
    pg = CapturingPg(FakeWS(), "h", "u", "p", scalar="pgdata")
    assert pg.read_server_file("/etc/hostname") == "pgdata"
    assert "pg_read_file('/etc/hostname')" in pg.sql[-1]
    pg.write_server_file("/tmp/y", b"hi")
    assert "COPY (SELECT convert_from(decode(" in pg.sql[-1]
    assert "TO '/tmp/y'" in pg.sql[-1]
