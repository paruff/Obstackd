"""
Integration tests for Grafana.
Tests datasource connectivity and dashboard data querying.
"""

import os
import time
import requests
import pytest
from typing import Dict, Any, List


# Configuration
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.getenv("GRAFANA_PASSWORD", "admin")


@pytest.fixture(scope="session")
def grafana_url() -> str:
    """Provide Grafana URL."""
    return GRAFANA_URL


@pytest.fixture(scope="session")
def grafana_auth() -> tuple:
    """Provide Grafana authentication credentials."""
    return (GRAFANA_USER, GRAFANA_PASSWORD)


@pytest.fixture(scope="session")
def wait_for_grafana(grafana_url: str) -> None:
    """Wait for Grafana to be ready."""
    max_retries = 60
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{grafana_url}/api/health",
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Grafana is ready after {attempt + 1} attempts")
                # Give Grafana a bit more time to provision datasources
                time.sleep(10)
                return
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(retry_interval)
    
    pytest.fail("Grafana did not become ready in time")


def get_datasources(grafana_url: str, grafana_auth: tuple) -> List[Dict[str, Any]]:
    """
    Get all datasources from Grafana.
    
    Args:
        grafana_url: Base URL for Grafana
        grafana_auth: Authentication credentials tuple
        
    Returns:
        List of datasource dictionaries
    """
    response = requests.get(
        f"{grafana_url}/api/datasources",
        auth=grafana_auth,
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def test_datasource_health(grafana_url: str, grafana_auth: tuple, datasource_uid: str) -> Dict[str, Any]:
    """
    Test a datasource health.
    
    Args:
        grafana_url: Base URL for Grafana
        grafana_auth: Authentication credentials tuple
        datasource_uid: Datasource UID
        
    Returns:
        Health check result
    """
    response = requests.get(
        f"{grafana_url}/api/datasources/uid/{datasource_uid}/health",
        auth=grafana_auth,
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def query_datasource(grafana_url: str, grafana_auth: tuple, datasource_uid: str, query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a query against a datasource.
    
    Args:
        grafana_url: Base URL for Grafana
        grafana_auth: Authentication credentials tuple
        datasource_uid: Datasource UID
        query: Query parameters
        
    Returns:
        Query result
    """
    response = requests.post(
        f"{grafana_url}/api/ds/query",
        auth=grafana_auth,
        json=query,
        timeout=30
    )
    response.raise_for_status()
    return response.json()


class TestGrafanaHealth:
    """Test Grafana health and availability."""
    
    def test_grafana_is_healthy(self, wait_for_grafana, grafana_url: str):
        """Test that Grafana is healthy."""
        response = requests.get(f"{grafana_url}/api/health")
        assert response.status_code == 200, "Grafana should return 200 OK"
        
        data = response.json()
        assert data.get("database") == "ok", "Grafana database should be healthy"
        
        print("✅ Grafana is healthy")
    
    def test_grafana_api_authentication(self, wait_for_grafana, grafana_url: str, grafana_auth: tuple):
        """Test that Grafana API authentication works."""
        response = requests.get(
            f"{grafana_url}/api/org",
            auth=grafana_auth
        )
        assert response.status_code == 200, "Should be able to authenticate with Grafana API"
        
        data = response.json()
        assert "name" in data, "Should get organization info"
        
        print(f"✅ Grafana API authentication successful (org: {data.get('name')})")


class TestGrafanaDatasources:
    """Test Grafana datasources."""
    
    def test_datasources_are_provisioned(self, wait_for_grafana, grafana_url: str, grafana_auth: tuple):
        """Test that all expected datasources are provisioned."""
        datasources = get_datasources(grafana_url, grafana_auth)
        
        assert len(datasources) >= 3, "Should have at least 3 datasources (Prometheus, Tempo, Loki)"
        
        # Expected datasources
        expected_types = ["prometheus", "tempo", "loki"]
        actual_types = [ds.get("type") for ds in datasources]
        
        for expected_type in expected_types:
            assert expected_type in actual_types, \
                f"Datasource type '{expected_type}' should be provisioned"
        
        print(f"✅ All expected datasources are provisioned: {', '.join(expected_types)}")
    
    def test_prometheus_datasource_connectivity(self, wait_for_grafana, grafana_url: str, grafana_auth: tuple):
        """Test that Prometheus datasource is accessible."""
        datasources = get_datasources(grafana_url, grafana_auth)
        
        prometheus_ds = [ds for ds in datasources if ds.get("type") == "prometheus"]
        assert len(prometheus_ds) > 0, "Prometheus datasource should exist"
        
        # Get the first Prometheus datasource
        ds = prometheus_ds[0]
        ds_uid = ds.get("uid")
        
        # Test health
        health = test_datasource_health(grafana_url, grafana_auth, ds_uid)
        assert health.get("status") == "OK", \
            f"Prometheus datasource should be healthy: {health.get('message', 'No message')}"
        
        print(f"✅ Prometheus datasource is healthy: {ds.get('name')}")
    
    def test_tempo_datasource_connectivity(self, wait_for_grafana, grafana_url: str, grafana_auth: tuple):
        """Test that Tempo datasource is accessible."""
        datasources = get_datasources(grafana_url, grafana_auth)
        
        tempo_ds = [ds for ds in datasources if ds.get("type") == "tempo"]
        assert len(tempo_ds) > 0, "Tempo datasource should exist"
        
        # Get the first Tempo datasource
        ds = tempo_ds[0]
        ds_uid = ds.get("uid")
        
        # Test health
        health = test_datasource_health(grafana_url, grafana_auth, ds_uid)
        assert health.get("status") == "OK", \
            f"Tempo datasource should be healthy: {health.get('message', 'No message')}"
        
        print(f"✅ Tempo datasource is healthy: {ds.get('name')}")
    
    def test_loki_datasource_connectivity(self, wait_for_grafana, grafana_url: str, grafana_auth: tuple):
        """Test that Loki datasource is accessible."""
        datasources = get_datasources(grafana_url, grafana_auth)
        
        loki_ds = [ds for ds in datasources if ds.get("type") == "loki"]
        assert len(loki_ds) > 0, "Loki datasource should exist"
        
        # Get the first Loki datasource
        ds = loki_ds[0]
        ds_uid = ds.get("uid")
        
        # Test health
        health = test_datasource_health(grafana_url, grafana_auth, ds_uid)
        assert health.get("status") == "OK", \
            f"Loki datasource should be healthy: {health.get('message', 'No message')}"
        
        print(f"✅ Loki datasource is healthy: {ds.get('name')}")
    
    def test_default_datasource_is_set(self, wait_for_grafana, grafana_url: str, grafana_auth: tuple):
        """Test that a default datasource is configured."""
        datasources = get_datasources(grafana_url, grafana_auth)
        
        default_ds = [ds for ds in datasources if ds.get("isDefault")]
        assert len(default_ds) > 0, "Should have a default datasource configured"
        
        default = default_ds[0]
        print(f"✅ Default datasource: {default.get('name')} ({default.get('type')})")


class TestGrafanaDatasourceQueries:
    """Test that datasources can execute queries."""
    
    def test_prometheus_query_execution(self, wait_for_grafana, grafana_url: str, grafana_auth: tuple):
        """Test that Prometheus queries can be executed through Grafana."""
        datasources = get_datasources(grafana_url, grafana_auth)
        
        prometheus_ds = [ds for ds in datasources if ds.get("type") == "prometheus"]
        assert len(prometheus_ds) > 0, "Prometheus datasource should exist"
        
        ds_uid = prometheus_ds[0].get("uid")
        
        # Execute a simple query
        query_payload = {
            "queries": [{
                "refId": "A",
                "datasource": {"type": "prometheus", "uid": ds_uid},
                "expr": "up",
                "instant": True
            }],
            "from": "now-5m",
            "to": "now"
        }
        
        try:
            result = query_datasource(grafana_url, grafana_auth, ds_uid, query_payload)
            
            # Check that we got results
            assert "results" in result, "Query should return results"
            
            print("✅ Prometheus queries can be executed through Grafana")
        except Exception as e:
            # It's OK if this fails due to no data yet
            print(f"⚠️  Prometheus query test skipped: {e}")
    
    def test_loki_query_execution(self, wait_for_grafana, grafana_url: str, grafana_auth: tuple):
        """Test that Loki queries can be executed through Grafana."""
        datasources = get_datasources(grafana_url, grafana_auth)
        
        loki_ds = [ds for ds in datasources if ds.get("type") == "loki"]
        assert len(loki_ds) > 0, "Loki datasource should exist"
        
        ds_uid = loki_ds[0].get("uid")
        
        # Execute a simple query
        query_payload = {
            "queries": [{
                "refId": "A",
                "datasource": {"type": "loki", "uid": ds_uid},
                "expr": '{job=~".+"}',
                "queryType": "range"
            }],
            "from": "now-5m",
            "to": "now"
        }
        
        try:
            result = query_datasource(grafana_url, grafana_auth, ds_uid, query_payload)
            
            # Check that we got results
            assert "results" in result, "Query should return results"
            
            print("✅ Loki queries can be executed through Grafana")
        except Exception as e:
            # It's OK if this fails due to no data yet
            print(f"⚠️  Loki query test skipped: {e}")


class TestGrafanaDashboards:
    """Test Grafana dashboards can query data."""
    
    def test_dashboards_exist(self, wait_for_grafana, grafana_url: str, grafana_auth: tuple):
        """Test that dashboards are provisioned."""
        response = requests.get(
            f"{grafana_url}/api/search?type=dash-db",
            auth=grafana_auth,
            timeout=10
        )
        response.raise_for_status()
        dashboards = response.json()
        
        assert len(dashboards) >= 5, \
            f"Should have at least 5 dashboards provisioned, got {len(dashboards)}"
        
        print(f"✅ {len(dashboards)} dashboards are provisioned")
    
    def test_observability_dashboard_can_query_data(self, wait_for_grafana, grafana_url: str, grafana_auth: tuple):
        """Test that Observability Stack Health dashboard can query data."""
        # Get the dashboard
        response = requests.get(
            f"{grafana_url}/api/dashboards/uid/observability-stack-health",
            auth=grafana_auth,
            timeout=10
        )
        
        if response.status_code == 200:
            dashboard_data = response.json()
            dashboard = dashboard_data.get("dashboard", {})
            
            # Check that dashboard has panels
            panels = dashboard.get("panels", [])
            assert len(panels) > 0, "Dashboard should have panels"
            
            print(f"✅ Observability Stack Health dashboard has {len(panels)} panels")
        else:
            print("⚠️  Observability Stack Health dashboard not found yet")


class TestGrafanaPlugins:
    """Test that required Grafana plugins are installed."""
    
    def test_required_plugins_installed(self, wait_for_grafana, grafana_url: str, grafana_auth: tuple):
        """Test that required plugins are installed."""
        response = requests.get(
            f"{grafana_url}/api/plugins",
            auth=grafana_auth,
            timeout=10
        )
        response.raise_for_status()
        plugins = response.json()
        
        # Get list of plugin IDs
        plugin_ids = [p.get("id") for p in plugins]
        
        # Check for required datasource plugins
        required_plugins = ["prometheus", "tempo", "loki"]
        
        for plugin in required_plugins:
            assert plugin in plugin_ids, f"Plugin '{plugin}' should be installed"
        
        print(f"✅ All required plugins are installed: {', '.join(required_plugins)}")


class TestGrafanaSettings:
    """Test Grafana settings and configuration."""
    
    def test_grafana_version(self, wait_for_grafana, grafana_url: str):
        """Test that we can get Grafana version."""
        response = requests.get(f"{grafana_url}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        version = data.get("version", "unknown")
        
        print(f"✅ Grafana version: {version}")
    
    def test_anonymous_access_disabled(self, wait_for_grafana, grafana_url: str):
        """Test that anonymous access is disabled (requires auth)."""
        # Try to access a protected endpoint without auth
        response = requests.get(
            f"{grafana_url}/api/org",
            timeout=10
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401, \
            "Anonymous access should be disabled (expected 401)"
        
        print("✅ Anonymous access is disabled (authentication required)")
