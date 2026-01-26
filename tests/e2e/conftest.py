"""
Pytest Configuration and Fixtures for E2E Tests
Provides shared fixtures for end-to-end telemetry testing
"""

import os
import time
import requests
import pytest
from typing import Dict, Any


# Configuration
OTEL_HTTP_ENDPOINT = os.getenv("OTEL_HTTP_ENDPOINT", "http://localhost:4318")
OTEL_GRPC_ENDPOINT = os.getenv("OTEL_GRPC_ENDPOINT", "http://localhost:4317")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
TEMPO_URL = os.getenv("TEMPO_URL", "http://localhost:3200")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.getenv("GRAFANA_PASSWORD", "admin")


@pytest.fixture(scope="session")
def otel_http_endpoint() -> str:
    """Provide OTel HTTP endpoint."""
    return OTEL_HTTP_ENDPOINT


@pytest.fixture(scope="session")
def otel_grpc_endpoint() -> str:
    """Provide OTel gRPC endpoint."""
    return OTEL_GRPC_ENDPOINT


@pytest.fixture(scope="session")
def prometheus_url() -> str:
    """Provide Prometheus URL."""
    return PROMETHEUS_URL


@pytest.fixture(scope="session")
def tempo_url() -> str:
    """Provide Tempo URL."""
    return TEMPO_URL


@pytest.fixture(scope="session")
def loki_url() -> str:
    """Provide Loki URL."""
    return LOKI_URL


@pytest.fixture(scope="session")
def grafana_url() -> str:
    """Provide Grafana URL."""
    return GRAFANA_URL


@pytest.fixture(scope="session")
def grafana_auth() -> tuple:
    """Provide Grafana authentication."""
    return (GRAFANA_USER, GRAFANA_PASSWORD)


@pytest.fixture(scope="session")
def wait_for_stack(prometheus_url: str, tempo_url: str, loki_url: str, grafana_url: str) -> None:
    """Wait for all Obstackd stack components to be ready."""
    components = [
        (f"{prometheus_url}/-/healthy", "Prometheus"),
        (f"{tempo_url}/ready", "Tempo"),
        (f"{loki_url}/ready", "Loki"),
        (f"{grafana_url}/api/health", "Grafana"),
    ]
    
    max_retries = 60
    retry_interval = 2
    
    for url, name in components:
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {name} is ready after {attempt + 1} attempts")
                    break
            except requests.exceptions.RequestException:
                pass
            
            if attempt == max_retries - 1:
                pytest.fail(f"{name} did not become ready in time")
            
            time.sleep(retry_interval)
    
    # Give extra time for datasource provisioning in Grafana
    print("⏳ Waiting for datasource provisioning (10s)...")
    time.sleep(10)
    print("✅ All stack components ready")


def query_prometheus(prometheus_url: str, query: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Query Prometheus.
    
    Args:
        prometheus_url: Prometheus base URL
        query: PromQL query
        timeout: Request timeout in seconds
        
    Returns:
        Query result
    """
    response = requests.get(
        f"{prometheus_url}/api/v1/query",
        params={"query": query},
        timeout=timeout
    )
    response.raise_for_status()
    return response.json()


def query_tempo_trace(tempo_url: str, trace_id: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Query Tempo for a trace.
    
    Args:
        tempo_url: Tempo base URL
        trace_id: Trace ID to query
        timeout: Request timeout in seconds
        
    Returns:
        Trace data
    """
    response = requests.get(
        f"{tempo_url}/api/traces/{trace_id}",
        timeout=timeout
    )
    response.raise_for_status()
    return response.json()


def query_loki(loki_url: str, query: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Query Loki.
    
    Args:
        loki_url: Loki base URL
        query: LogQL query
        timeout: Request timeout in seconds
        
    Returns:
        Query result
    """
    response = requests.get(
        f"{loki_url}/loki/api/v1/query",
        params={"query": query},
        timeout=timeout
    )
    response.raise_for_status()
    return response.json()


def query_grafana_datasource(
    grafana_url: str,
    grafana_auth: tuple,
    datasource_uid: str,
    query_params: Dict[str, Any],
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Query a Grafana datasource.
    
    Args:
        grafana_url: Grafana base URL
        grafana_auth: Authentication credentials
        datasource_uid: Datasource UID
        query_params: Query parameters
        timeout: Request timeout in seconds
        
    Returns:
        Query result
    """
    response = requests.post(
        f"{grafana_url}/api/ds/query",
        auth=grafana_auth,
        json={
            "queries": [{
                "datasource": {"uid": datasource_uid},
                **query_params
            }]
        },
        timeout=timeout
    )
    response.raise_for_status()
    return response.json()


@pytest.fixture(scope="function")
def prometheus_query(prometheus_url: str):
    """Fixture that provides Prometheus query function."""
    def _query(query: str, timeout: int = 10) -> Dict[str, Any]:
        return query_prometheus(prometheus_url, query, timeout)
    return _query


@pytest.fixture(scope="function")
def tempo_query(tempo_url: str):
    """Fixture that provides Tempo query function."""
    def _query(trace_id: str, timeout: int = 10) -> Dict[str, Any]:
        return query_tempo_trace(tempo_url, trace_id, timeout)
    return _query


@pytest.fixture(scope="function")
def loki_query(loki_url: str):
    """Fixture that provides Loki query function."""
    def _query(query: str, timeout: int = 10) -> Dict[str, Any]:
        return query_loki(loki_url, query, timeout)
    return _query


@pytest.fixture(scope="function")
def grafana_query(grafana_url: str, grafana_auth: tuple):
    """Fixture that provides Grafana datasource query function."""
    def _query(datasource_uid: str, query_params: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
        return query_grafana_datasource(grafana_url, grafana_auth, datasource_uid, query_params, timeout)
    return _query
