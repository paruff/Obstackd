"""
Pytest Configuration and Fixtures for Integration Tests
Provides shared fixtures for Home Assistant integration testing
"""

import os
import time
import requests
import pytest
from typing import Dict, Any


# Configuration
HOMEASSISTANT_URL = os.getenv("HOMEASSISTANT_URL", "http://localhost:8123")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
OTEL_COLLECTOR_URL = os.getenv("OTEL_COLLECTOR_URL", "http://localhost:8888")


@pytest.fixture(scope="session")
def homeassistant_base_url() -> str:
    """Provide Home Assistant base URL."""
    return HOMEASSISTANT_URL


@pytest.fixture(scope="session")
def prometheus_base_url() -> str:
    """Provide Prometheus base URL."""
    return PROMETHEUS_URL


@pytest.fixture(scope="session")
def otel_collector_base_url() -> str:
    """Provide OpenTelemetry Collector base URL."""
    return OTEL_COLLECTOR_URL


@pytest.fixture(scope="session")
def wait_for_homeassistant(homeassistant_base_url: str) -> None:
    """Wait for Home Assistant to be ready."""
    max_retries = 30
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            # Check the Prometheus endpoint which doesn't require auth
            response = requests.get(
                f"{homeassistant_base_url}/api/prometheus",
                timeout=5
            )
            # 200 is success, 401 also means it's running (just auth required for other endpoints)
            if response.status_code in [200, 401]:
                print(f"✅ Home Assistant is ready after {attempt + 1} attempts")
                return
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(retry_interval)
    
    pytest.fail("Home Assistant did not become ready in time")


@pytest.fixture(scope="session")
def wait_for_prometheus(prometheus_base_url: str) -> None:
    """Wait for Prometheus to be ready."""
    max_retries = 30
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{prometheus_base_url}/-/healthy",
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Prometheus is ready after {attempt + 1} attempts")
                return
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(retry_interval)
    
    pytest.fail("Prometheus did not become ready in time")


@pytest.fixture(scope="session")
def wait_for_otel_collector(otel_collector_base_url: str) -> None:
    """Wait for OpenTelemetry Collector to be ready."""
    max_retries = 30
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{otel_collector_base_url}/metrics",
                timeout=5
            )
            # Check for any valid metrics response (should contain metric names)
            if response.status_code == 200 and len(response.text) > 100:
                print(f"✅ OTel Collector is ready after {attempt + 1} attempts")
                return
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(retry_interval)
    
    pytest.fail("OTel Collector did not become ready in time")


@pytest.fixture(scope="function")
def wait_for_scrape_cycle() -> None:
    """
    Wait for at least one Prometheus scrape cycle to complete.
    Default scrape interval is 30s, so we wait 35s to be safe.
    """
    print("⏳ Waiting for Prometheus scrape cycle (35 seconds)...")
    time.sleep(35)
    print("✅ Scrape cycle wait completed")


def query_prometheus(prometheus_base_url: str, query: str) -> Dict[str, Any]:
    """
    Helper function to query Prometheus.
    
    Args:
        prometheus_base_url: Base URL for Prometheus
        query: PromQL query string
        
    Returns:
        JSON response from Prometheus
    """
    response = requests.get(
        f"{prometheus_base_url}/api/v1/query",
        params={"query": query},
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def parse_prometheus_metrics(text: str) -> Dict[str, list]:
    """
    Parse Prometheus text format metrics into a dictionary.
    
    Args:
        text: Prometheus text format metrics
        
    Returns:
        Dictionary mapping metric names to lists of metric lines
    """
    metrics = {}
    for line in text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Extract metric name (before '{' or ' ')
        if '{' in line:
            metric_name = line.split('{')[0]
        elif ' ' in line:
            metric_name = line.split(' ')[0]
        else:
            continue
        
        if metric_name not in metrics:
            metrics[metric_name] = []
        metrics[metric_name].append(line)
    
    return metrics


@pytest.fixture(scope="function")
def prometheus_query(prometheus_base_url: str):
    """Fixture that provides a Prometheus query function."""
    def _query(query: str) -> Dict[str, Any]:
        return query_prometheus(prometheus_base_url, query)
    return _query


@pytest.fixture(scope="function")
def parse_metrics():
    """Fixture that provides a metric parsing function."""
    return parse_prometheus_metrics
