"""Output renderers: console/quiet/json modes via the log facade."""

import json

import pytest

from webshell_sniper import log


@pytest.fixture(autouse=True)
def _reset_renderer():
    yield
    log.set_renderer("console")  # don't leak mode across tests


def test_get_renderer_default_is_console():
    log.set_renderer("console")
    assert log.get_renderer().name == "console"


def test_unknown_mode_raises():
    with pytest.raises(ValueError, match="unknown output mode"):
        log.set_renderer("yaml")


def test_quiet_suppresses_status_but_keeps_output_and_errors(capsys):
    log.set_renderer("quiet")
    log.info("chatter")
    log.success("more chatter")
    log.raw("real-output")
    log.error("boom")
    out, err = capsys.readouterr()
    assert "chatter" not in out
    assert "real-output" in out
    assert "boom" in err  # errors still surface (on stderr)


def test_quiet_table_is_plain_tsv(capsys):
    log.set_renderer("quiet")
    log.table(["a", "b"], [[1, 2], [3, 4]])
    out, _ = capsys.readouterr()
    assert "a\tb" in out
    assert "1\t2" in out


def test_json_buffers_then_flushes_valid_json(capsys):
    log.set_renderer("json")
    log.info("hello")
    log.raw("output-line")
    log.table(["c"], [["x"]], title="t")
    # Nothing emitted until flush.
    assert capsys.readouterr().out == ""
    log.flush()
    out = capsys.readouterr().out
    events = json.loads(out)
    kinds = [e["type"] for e in events]
    assert kinds == ["message", "output", "table"]
    assert events[0]["level"] == "info" and events[0]["text"] == "hello"
    assert events[2]["columns"] == ["c"] and events[2]["rows"] == [["x"]]


def test_track_returns_items_in_non_console_modes():
    log.set_renderer("quiet")
    assert list(log.track([1, 2, 3], "x")) == [1, 2, 3]
