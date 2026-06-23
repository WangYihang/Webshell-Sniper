"""Layered configuration: defaults < file < env < CLI."""

from pathlib import Path

from webshell_sniper.config import Config, default_config_path, resolve_config


def test_defaults_when_nothing_set(tmp_path):
    cfg = resolve_config({}, config_path=tmp_path / "none.toml", env={})
    assert cfg == Config()


def test_env_overrides_file(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text('timeout = 5.0\nencoder = "gzip"\nworkers = 2\n')
    env = {"WEBSHELL_SNIPER_ENCODER": "xor", "WEBSHELL_SNIPER_WORKERS": "8"}
    cfg = resolve_config({}, config_path=toml, env=env)
    assert cfg.timeout == 5.0  # from file
    assert cfg.encoder == "xor"  # env wins over file
    assert cfg.workers == 8  # env (coerced to int)


def test_cli_overrides_everything(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text('lang = "command"\n')
    env = {"WEBSHELL_SNIPER_LANG": "php", "WEBSHELL_SNIPER_TIMEOUT": "30"}
    cfg = resolve_config({"lang": "php", "timeout": 99.0}, config_path=toml, env=env)
    assert cfg.lang == "php"
    assert cfg.timeout == 99.0  # CLI wins


def test_none_cli_values_do_not_override(tmp_path):
    env = {"WEBSHELL_SNIPER_PROXY": "http://127.0.0.1:8080"}
    cfg = resolve_config({"proxy": None}, config_path=tmp_path / "x.toml", env=env)
    assert cfg.proxy == "http://127.0.0.1:8080"  # env retained; None ignored


def test_env_bool_and_path_coercion(tmp_path):
    env = {
        "WEBSHELL_SNIPER_VERIFY_SSL": "false",
        "WEBSHELL_SNIPER_OUTPUT_DIR": "/tmp/loot",
    }
    cfg = resolve_config({}, config_path=tmp_path / "x.toml", env=env)
    assert cfg.verify_ssl is False
    assert cfg.output_dir == Path("/tmp/loot")


def test_default_path_respects_xdg(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/cfg")
    assert default_config_path() == Path("/cfg/webshell-sniper/config.toml")
