"""CLI argument handling and the no-network paths."""

import json

from webshell_sniper.cli import main


def test_no_target_prints_help_and_returns_1(capsys):
    assert main([]) == 1
    assert "usage" in capsys.readouterr().out.lower()


def test_generate_writes_shell_and_exits(tmp_path):
    rc = main(["--generate", "pw123", "-o", str(tmp_path), "--encoder", "b64var"])
    assert rc == 0
    shells = list(tmp_path.glob("shell_*.php"))
    assert shells and shells[0].read_text().startswith("<?php ")


def test_json_output_flushes_events(tmp_path, capsys):
    # No working shells -> returns 2, but the JSON renderer must still flush.
    rc = main(
        ["http://127.0.0.1:1/nope.php", "POST", "c", "-o", str(tmp_path), "--output", "json"]
    )
    assert rc == 2
    events = json.loads(capsys.readouterr().out)
    assert any(e["type"] == "message" for e in events)


def test_load_from_json_file(tmp_path):
    cfg = tmp_path / "shells.json"
    cfg.write_text(json.dumps([{"url": "http://127.0.0.1:1/x.php", "method": "POST",
                                "password": "c"}]))
    # Unreachable -> rc 2, but exercises the file-loading branch.
    assert main(["-f", str(cfg), "-o", str(tmp_path)]) == 2
