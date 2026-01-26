"""
Shared fixtures for unit tests
"""
import os
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the absolute path to the project root directory."""
    return Path(__file__).parent.parent.parent.absolute()


@pytest.fixture
def config_dir(project_root):
    """Return the absolute path to the config directory."""
    return project_root / "config"


@pytest.fixture
def otel_config_path(config_dir):
    """Return the path to the OTel collector config file."""
    return config_dir / "otel" / "collector.yaml"


@pytest.fixture
def prometheus_config_path(config_dir):
    """Return the path to the Prometheus config file."""
    return config_dir / "prometheus" / "prometheus.yaml"


@pytest.fixture
def grafana_datasources_path(config_dir):
    """Return the path to the Grafana datasources config file."""
    return config_dir / "grafana" / "provisioning" / "datasources" / "datasources.yaml"


@pytest.fixture
def tempo_config_path(config_dir):
    """Return the path to the Tempo config file."""
    return config_dir / "tempo" / "tempo.yaml"


@pytest.fixture
def loki_config_path(config_dir):
    """Return the path to the Loki config file."""
    return config_dir / "loki" / "loki.yaml"


@pytest.fixture
def fixtures_dir():
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"
