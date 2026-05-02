"""Tests for ``config.settings.ClickHouseConfig`` and ``load_config``.

The Pydantic model itself is mostly validated by Pydantic, so the model
tests focus on defaults and the small amount of custom behaviour
clickr layers on top. The ``load_config`` tests exercise the four
input sources it merges — file, environment, CLI args, and the
"clickhouse_*" key normalisation that comes from the onboarding flow —
and the precedence between them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from config.settings import ClickHouseConfig, create_sample_config, load_config

# ---------------------------------------------------------------------------
# ClickHouseConfig defaults
# ---------------------------------------------------------------------------


class TestClickHouseConfigDefaults:
    def test_host_defaults_to_localhost(self) -> None:
        assert ClickHouseConfig().host == "localhost"

    def test_port_defaults_to_8123(self) -> None:
        assert ClickHouseConfig().port == 8123

    def test_username_defaults_to_default(self) -> None:
        assert ClickHouseConfig().username == "default"

    def test_password_defaults_to_empty_string(self) -> None:
        assert ClickHouseConfig().password == ""

    def test_database_defaults_to_default(self) -> None:
        assert ClickHouseConfig().database == "default"

    def test_secure_defaults_to_false(self) -> None:
        assert ClickHouseConfig().secure is False

    def test_provider_defaults_to_local(self) -> None:
        assert ClickHouseConfig().provider == "local"

    def test_local_llm_url_defaults_to_loopback(self) -> None:
        # Loopback so that out-of-the-box clickr never accidentally
        # reaches a non-local LLM.
        cfg = ClickHouseConfig()
        assert cfg.local_llm_base_url.startswith("http://127.0.0.1")

    def test_temperature_defaults_low(self) -> None:
        # Low temperature is intentional for SQL generation determinism.
        assert ClickHouseConfig().temperature <= 0.2


class TestClickHouseConfigValidation:
    def test_explicit_values_are_kept(self) -> None:
        cfg = ClickHouseConfig(
            host="ch.example.com",
            port=9000,
            username="reader",
            password="secret",
            database="analytics",
            secure=True,
        )
        assert cfg.host == "ch.example.com"
        assert cfg.port == 9000
        assert cfg.username == "reader"
        assert cfg.password == "secret"
        assert cfg.database == "analytics"
        assert cfg.secure is True

    def test_port_must_be_an_integer(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ClickHouseConfig(port="not-a-port")  # type: ignore[arg-type]

    def test_secure_string_coerces_via_pydantic(self) -> None:
        # Pydantic v2 coerces "true"/"false" strings to bool by default;
        # this asserts that contract so an upstream Pydantic change
        # that breaks env-var parsing surfaces here.
        assert ClickHouseConfig(secure="true").secure is True  # type: ignore[arg-type]
        assert ClickHouseConfig(secure="false").secure is False  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# load_config: file source
# ---------------------------------------------------------------------------


class TestLoadConfigFromFile:
    def test_explicit_config_file_overrides_defaults(
        self, tmp_path: Path, cwd: Path
    ) -> None:
        cfg_path = tmp_path / "clickr.json"
        cfg_path.write_text(
            json.dumps(
                {
                    "host": "from-file.example.com",
                    "port": 9001,
                    "database": "events",
                }
            )
        )
        cfg = load_config(config_file=cfg_path)
        assert cfg.host == "from-file.example.com"
        assert cfg.port == 9001
        assert cfg.database == "events"

    def test_legacy_proto_config_in_cwd_is_picked_up(self, cwd: Path) -> None:
        (cwd / "proto-config.json").write_text(
            json.dumps({"host": "legacy.example.com", "port": 9002})
        )
        cfg = load_config()
        assert cfg.host == "legacy.example.com"
        assert cfg.port == 9002

    def test_default_config_in_xdg_home_is_picked_up(
        self, tmp_path: Path, cwd: Path
    ) -> None:
        # ``$HOME`` is patched by the autouse fixture to ``tmp_path``.
        target = tmp_path / ".config" / "proto"
        target.mkdir(parents=True)
        (target / "proto-config.json").write_text(
            json.dumps({"host": "xdg.example.com"})
        )
        cfg = load_config()
        assert cfg.host == "xdg.example.com"

    def test_missing_explicit_file_falls_through_to_default(self, cwd: Path) -> None:
        # Pointing at a non-existent path must not raise; the loader
        # silently falls through to the next source.
        cfg = load_config(config_file=Path("/nonexistent/clickr.json"))
        assert cfg.host == "localhost"


# ---------------------------------------------------------------------------
# load_config: environment variables
# ---------------------------------------------------------------------------


class TestLoadConfigFromEnv:
    def test_clickhouse_env_vars_are_read(
        self, monkeypatch: pytest.MonkeyPatch, cwd: Path
    ) -> None:
        monkeypatch.setenv("CLICKHOUSE_HOST", "env.example.com")
        monkeypatch.setenv("CLICKHOUSE_PORT", "9003")
        monkeypatch.setenv("CLICKHOUSE_DATABASE", "metrics")
        cfg = load_config()
        assert cfg.host == "env.example.com"
        assert cfg.port == 9003
        assert cfg.database == "metrics"

    def test_openrouter_api_key_env_var_is_read(
        self, monkeypatch: pytest.MonkeyPatch, cwd: Path
    ) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-12345")
        cfg = load_config()
        assert cfg.openrouter_api_key == "sk-test-12345"

    def test_openrouter_model_env_var_is_read(
        self, monkeypatch: pytest.MonkeyPatch, cwd: Path
    ) -> None:
        monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-haiku")
        cfg = load_config()
        assert cfg.openrouter_model == "anthropic/claude-haiku"


# ---------------------------------------------------------------------------
# load_config: precedence
# ---------------------------------------------------------------------------


class TestLoadConfigPrecedence:
    def test_cli_args_override_env(
        self, monkeypatch: pytest.MonkeyPatch, cwd: Path
    ) -> None:
        monkeypatch.setenv("CLICKHOUSE_HOST", "from-env")
        cfg = load_config(host="from-cli")
        assert cfg.host == "from-cli"

    def test_cli_args_override_file(self, tmp_path: Path, cwd: Path) -> None:
        cfg_path = tmp_path / "clickr.json"
        cfg_path.write_text(json.dumps({"host": "from-file", "port": 9000}))
        cfg = load_config(config_file=cfg_path, port=9999)
        assert cfg.host == "from-file"  # not overridden
        assert cfg.port == 9999  # CLI wins

    def test_env_overrides_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cwd: Path
    ) -> None:
        cfg_path = tmp_path / "clickr.json"
        cfg_path.write_text(json.dumps({"host": "from-file"}))
        monkeypatch.setenv("CLICKHOUSE_HOST", "from-env")
        cfg = load_config(config_file=cfg_path)
        assert cfg.host == "from-env"


# ---------------------------------------------------------------------------
# load_config: onboarding key normalisation
# ---------------------------------------------------------------------------


class TestKeyNormalization:
    def test_clickhouse_prefixed_keys_in_file_are_normalised(
        self, tmp_path: Path, cwd: Path
    ) -> None:
        # The onboarding flow writes "clickhouse_host" etc. into the
        # config file; the loader must normalise these to bare keys
        # (matching the ``ClickHouseConfig`` field names).
        cfg_path = tmp_path / "clickr.json"
        cfg_path.write_text(
            json.dumps(
                {
                    "clickhouse_host": "norm.example.com",
                    "clickhouse_port": 9004,
                    "clickhouse_database": "raw",
                    "clickhouse_secure": True,
                }
            )
        )
        cfg = load_config(config_file=cfg_path)
        assert cfg.host == "norm.example.com"
        assert cfg.port == 9004
        assert cfg.database == "raw"
        assert cfg.secure is True

    def test_normalisation_does_not_clobber_already_normalised_key(
        self, tmp_path: Path, cwd: Path
    ) -> None:
        # If both the prefixed and the bare key are present, the bare
        # key wins (loader treats the prefixed one as a fallback).
        cfg_path = tmp_path / "clickr.json"
        cfg_path.write_text(
            json.dumps({"clickhouse_host": "fallback", "host": "primary"})
        )
        cfg = load_config(config_file=cfg_path)
        assert cfg.host == "primary"


# ---------------------------------------------------------------------------
# load_config: provider enforcement
# ---------------------------------------------------------------------------


class TestProviderEnforcement:
    def test_explicit_local_provider_is_kept(self, tmp_path: Path, cwd: Path) -> None:
        cfg_path = tmp_path / "clickr.json"
        cfg_path.write_text(json.dumps({"provider": "local"}))
        cfg = load_config(config_file=cfg_path)
        assert cfg.provider == "local"

    def test_non_local_provider_is_force_switched_to_local(
        self, tmp_path: Path, cwd: Path
    ) -> None:
        # Only the local provider is supported today; the loader must
        # silently coerce other values rather than raise (so an old
        # config file with provider=openrouter still boots).
        cfg_path = tmp_path / "clickr.json"
        cfg_path.write_text(json.dumps({"provider": "openrouter"}))
        cfg = load_config(config_file=cfg_path)
        assert cfg.provider == "local"


# ---------------------------------------------------------------------------
# create_sample_config
# ---------------------------------------------------------------------------


class TestCreateSampleConfig:
    def test_writes_a_loadable_json_file(self, cwd: Path) -> None:
        # The sample config should round-trip through load_config
        # without errors — it is the on-ramp for new users.
        create_sample_config()
        sample_path = cwd / "proto-config.json"
        assert sample_path.exists()
        data = json.loads(sample_path.read_text())
        # Spot-check a few fields the sample is documented to set.
        assert data["host"] == "localhost"
        assert data["port"] == 8123
        # The sample should load cleanly into a ClickHouseConfig.
        cfg = load_config(config_file=sample_path)
        assert cfg.host == "localhost"
