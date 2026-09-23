"""Configuration validation tests."""

import pytest

from driftsentinel.config import Config, ConfigError, HelmConfig, validate_config


def test_validate_config_rejects_missing_chart(tmp_path):
    config = Config(helm=HelmConfig(chart_path=str(tmp_path / "missing")))

    with pytest.raises(ConfigError, match="Helm chart path does not exist"):
        validate_config(config)


def test_validate_config_rejects_non_positive_timeout(tmp_path):
    config = Config(helm=HelmConfig(chart_path=str(tmp_path)))
    config.auto_heal.timeout = 0

    with pytest.raises(ConfigError, match="timeout"):
        validate_config(config)