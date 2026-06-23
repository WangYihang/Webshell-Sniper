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
