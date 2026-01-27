"""
Integration tests for Grafana dashboard provisioning and validation.
Tests that all pre-built dashboards are correctly provisioned and accessible.
"""

import os
import json
import requests
import pytest
from typing import Dict, Any, List


# Configuration
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.getenv("GRAFANA_PASSWORD", "admin")

# Get the project root directory dynamically
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "config", "grafana", "dashboards")
PLATFORM_DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "dashboards", "platform")
SERVICE_DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "dashboards", "services")

# Expected dashboard files (legacy location)
DASHBOARD_FILES = [
    "observability-stack-health.json",
    "iot-devices-mqtt.json",
    "application-performance.json",
    "infrastructure-overview.json"
]

# New platform dashboards
PLATFORM_DASHBOARD_FILES = [
    "global-health.json",
    "prometheus-overview.json",
    "loki-overview.json",
    "tempo-overview.json",
    "alloy-overview.json",
    "alertmanager-overview.json",
    "storage-capacity.json",
    "ingestion-health.json"
]

# New service dashboards
SERVICE_DASHBOARD_FILES = [
    "service-overview.json",
    "service-latency.json",
    "service-errors.json",
    "service-saturation.json",
    "service-debug.json",
    "service-slo.json",
    "service-capacity.json"
]


@pytest.fixture(scope="session")
def grafana_base_url() -> str:
    """Provide Grafana base URL."""
    return GRAFANA_URL


@pytest.fixture(scope="session")
def grafana_auth() -> tuple:
    """Provide Grafana authentication credentials."""
    return (GRAFANA_USER, GRAFANA_PASSWORD)


@pytest.fixture(scope="session")
def wait_for_grafana(grafana_base_url: str) -> None:
    """Wait for Grafana to be ready."""
    import time
    max_retries = 60
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{grafana_base_url}/api/health",
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Grafana is ready after {attempt + 1} attempts")
                return
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(retry_interval)
    
    pytest.fail("Grafana did not become ready in time")


def get_dashboards(grafana_base_url: str, grafana_auth: tuple) -> List[Dict[str, Any]]:
    """
    Get list of all dashboards from Grafana API.
    
    Args:
        grafana_base_url: Base URL for Grafana
        grafana_auth: Authentication credentials tuple
        
    Returns:
        List of dashboard metadata
    """
    response = requests.get(
        f"{grafana_base_url}/api/search?type=dash-db",
        auth=grafana_auth,
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def get_dashboard_by_uid(grafana_base_url: str, grafana_auth: tuple, uid: str) -> Dict[str, Any]:
    """
    Get dashboard details by UID.
    
    Args:
        grafana_base_url: Base URL for Grafana
        grafana_auth: Authentication credentials tuple
        uid: Dashboard UID
        
    Returns:
        Dashboard details
    """
    response = requests.get(
        f"{grafana_base_url}/api/dashboards/uid/{uid}",
        auth=grafana_auth,
        timeout=10
    )
    response.raise_for_status()
    return response.json()


class TestDashboardProvisioning:
    """Test dashboard provisioning and structure."""
    
    def test_grafana_is_accessible(self, wait_for_grafana, grafana_base_url: str):
        """Test that Grafana is accessible and healthy."""
        response = requests.get(f"{grafana_base_url}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("database") == "ok", "Grafana database should be healthy"
    
    def test_all_dashboards_provisioned(self, wait_for_grafana, grafana_base_url: str, grafana_auth: tuple):
        """Test that all 4 dashboards are provisioned."""
        dashboards = get_dashboards(grafana_base_url, grafana_auth)
        
        # Expected dashboard UIDs
        expected_uids = [
            "observability-stack-health",
            "iot-devices-mqtt",
            "application-performance",
            "infrastructure-overview"
        ]
        
        # Get all dashboard UIDs
        provisioned_uids = [d["uid"] for d in dashboards]
        
        # Check all expected dashboards are present
        for uid in expected_uids:
            assert uid in provisioned_uids, f"Dashboard '{uid}' should be provisioned"
        
        print(f"✅ All {len(expected_uids)} dashboards are provisioned")
    
    def test_observability_stack_health_dashboard(self, wait_for_grafana, grafana_base_url: str, grafana_auth: tuple):
        """Test Observability Stack Health dashboard structure."""
        dashboard = get_dashboard_by_uid(grafana_base_url, grafana_auth, "observability-stack-health")
        
        assert dashboard is not None
        assert "dashboard" in dashboard
        
        dash = dashboard["dashboard"]
        assert dash["title"] == "Observability Stack Health"
        assert "observability" in dash["tags"]
        
        # Check for key panels
        panels = dash.get("panels", [])
        assert len(panels) > 0, "Dashboard should have panels"
        
        # Verify rows and panels exist
        panel_titles = [p.get("title", "") for p in panels]
        assert "Prometheus Status" in panel_titles, "Should have Prometheus status panel"
        assert "OTel Collector Status" in panel_titles, "Should have OTel Collector status panel"
        
        print("✅ Observability Stack Health dashboard validated")
    
    def test_iot_devices_mqtt_dashboard(self, wait_for_grafana, grafana_base_url: str, grafana_auth: tuple):
        """Test IoT Devices & MQTT dashboard structure."""
        dashboard = get_dashboard_by_uid(grafana_base_url, grafana_auth, "iot-devices-mqtt")
        
        assert dashboard is not None
        assert "dashboard" in dashboard
        
        dash = dashboard["dashboard"]
        assert dash["title"] == "IoT Devices & MQTT"
        assert "iot" in dash["tags"] or "mqtt" in dash["tags"]
        
        # Check for key panels
        panels = dash.get("panels", [])
        assert len(panels) > 0, "Dashboard should have panels"
        
        panel_titles = [p.get("title", "") for p in panels]
        assert "Active Connections" in panel_titles, "Should have Active Connections panel"
        assert "Message Rate by Topic" in panel_titles, "Should have Message Rate by Topic panel"
        
        # Check for variables
        templating = dash.get("templating", {})
        variables = templating.get("list", [])
        var_names = [v.get("name", "") for v in variables]
        assert "topic" in var_names, "Should have topic variable for filtering"
        
        print("✅ IoT Devices & MQTT dashboard validated")
    
    def test_application_performance_dashboard(self, wait_for_grafana, grafana_base_url: str, grafana_auth: tuple):
        """Test Application Performance dashboard structure."""
        dashboard = get_dashboard_by_uid(grafana_base_url, grafana_auth, "application-performance")
        
        assert dashboard is not None
        assert "dashboard" in dashboard
        
        dash = dashboard["dashboard"]
        assert dash["title"] == "Application Performance"
        assert "application" in dash["tags"] or "performance" in dash["tags"]
        
        # Check for key panels (RED metrics)
        panels = dash.get("panels", [])
        assert len(panels) > 0, "Dashboard should have panels"
        
        panel_titles = [p.get("title", "") for p in panels]
        assert "Total Request Rate" in panel_titles, "Should have Total Request Rate panel (R in RED)"
        assert "Error Rate" in panel_titles, "Should have Error Rate panel (E in RED)"
        assert "p95 Latency" in panel_titles, "Should have p95 Latency panel (D in RED)"
        
        # Check for variables
        templating = dash.get("templating", {})
        variables = templating.get("list", [])
        var_names = [v.get("name", "") for v in variables]
        assert "service" in var_names, "Should have service variable for filtering"
        
        print("✅ Application Performance dashboard validated")
    
    def test_infrastructure_overview_dashboard(self, wait_for_grafana, grafana_base_url: str, grafana_auth: tuple):
        """Test Infrastructure Overview dashboard structure."""
        dashboard = get_dashboard_by_uid(grafana_base_url, grafana_auth, "infrastructure-overview")
        
        assert dashboard is not None
        assert "dashboard" in dashboard
        
        dash = dashboard["dashboard"]
        assert dash["title"] == "Infrastructure Overview"
        assert "infrastructure" in dash["tags"] or "containers" in dash["tags"]
        
        # Check for key panels
        panels = dash.get("panels", [])
        assert len(panels) > 0, "Dashboard should have panels"
        
        panel_titles = [p.get("title", "") for p in panels]
        assert "Running Containers" in panel_titles, "Should have Running Containers panel"
        assert "Container CPU Usage" in panel_titles, "Should have Container CPU Usage panel"
        assert "Container Memory Usage" in panel_titles, "Should have Container Memory Usage panel"
        
        # Check for variables
        templating = dash.get("templating", {})
        variables = templating.get("list", [])
        var_names = [v.get("name", "") for v in variables]
        assert "container" in var_names, "Should have container variable for filtering"
        
        print("✅ Infrastructure Overview dashboard validated")
    
    def test_dashboard_auto_refresh(self, wait_for_grafana, grafana_base_url: str, grafana_auth: tuple):
        """Test that dashboards have auto-refresh configured."""
        expected_uids = [
            "observability-stack-health",
            "iot-devices-mqtt",
            "application-performance",
            "infrastructure-overview"
        ]
        
        for uid in expected_uids:
            dashboard = get_dashboard_by_uid(grafana_base_url, grafana_auth, uid)
            dash = dashboard["dashboard"]
            
            # Check that refresh is configured
            refresh = dash.get("refresh", "")
            assert refresh, f"Dashboard '{uid}' should have auto-refresh configured"
            assert refresh == "30s", f"Dashboard '{uid}' should have 30s refresh interval"
        
        print("✅ All dashboards have auto-refresh configured")
    
    def test_dashboard_time_range(self, wait_for_grafana, grafana_base_url: str, grafana_auth: tuple):
        """Test that dashboards have appropriate time range configured."""
        expected_uids = [
            "observability-stack-health",
            "iot-devices-mqtt",
            "application-performance",
            "infrastructure-overview"
        ]
        
        for uid in expected_uids:
            dashboard = get_dashboard_by_uid(grafana_base_url, grafana_auth, uid)
            dash = dashboard["dashboard"]
            
            # Check that time range is configured
            time_config = dash.get("time", {})
            assert time_config, f"Dashboard '{uid}' should have time range configured"
            assert "from" in time_config, f"Dashboard '{uid}' should have 'from' time"
            assert "to" in time_config, f"Dashboard '{uid}' should have 'to' time"
        
        print("✅ All dashboards have time range configured")


class TestDashboardDataSources:
    """Test that dashboards use correct datasources."""
    
    def test_prometheus_datasource_configured(self, wait_for_grafana, grafana_base_url: str, grafana_auth: tuple):
        """Test that Prometheus datasource is available."""
        response = requests.get(
            f"{grafana_base_url}/api/datasources",
            auth=grafana_auth,
            timeout=10
        )
        response.raise_for_status()
        datasources = response.json()
        
        # Check Prometheus datasource exists
        prometheus_ds = [ds for ds in datasources if ds.get("type") == "prometheus"]
        assert len(prometheus_ds) > 0, "Prometheus datasource should be configured"
        
        # Check it's set as default
        default_ds = [ds for ds in prometheus_ds if ds.get("isDefault")]
        assert len(default_ds) > 0, "Prometheus should be set as default datasource"
        
        print("✅ Prometheus datasource is configured correctly")
    
    def test_tempo_datasource_configured(self, wait_for_grafana, grafana_base_url: str, grafana_auth: tuple):
        """Test that Tempo datasource is available."""
        response = requests.get(
            f"{grafana_base_url}/api/datasources",
            auth=grafana_auth,
            timeout=10
        )
        response.raise_for_status()
        datasources = response.json()
        
        # Check Tempo datasource exists
        tempo_ds = [ds for ds in datasources if ds.get("type") == "tempo"]
        assert len(tempo_ds) > 0, "Tempo datasource should be configured"
        
        print("✅ Tempo datasource is configured correctly")
    
    def test_loki_datasource_configured(self, wait_for_grafana, grafana_base_url: str, grafana_auth: tuple):
        """Test that Loki datasource is available."""
        response = requests.get(
            f"{grafana_base_url}/api/datasources",
            auth=grafana_auth,
            timeout=10
        )
        response.raise_for_status()
        datasources = response.json()
        
        # Check Loki datasource exists
        loki_ds = [ds for ds in datasources if ds.get("type") == "loki"]
        assert len(loki_ds) > 0, "Loki datasource should be configured"
        
        print("✅ Loki datasource is configured correctly")


class TestDashboardFiles:
    """Test dashboard JSON files in the repository."""
    
    def test_dashboard_files_exist(self):
        """Test that all dashboard JSON files exist in the repository."""
        for filename in DASHBOARD_FILES:
            filepath = os.path.join(DASHBOARD_DIR, filename)
            assert os.path.exists(filepath), f"Dashboard file '{filename}' should exist"
        
        print("✅ All dashboard files exist in repository")
    
    def test_dashboard_json_valid(self):
        """Test that all dashboard JSON files are valid."""
        for filename in DASHBOARD_FILES:
            filepath = os.path.join(DASHBOARD_DIR, filename)
            
            with open(filepath, "r") as f:
                try:
                    dashboard = json.load(f)
                    assert "title" in dashboard, f"Dashboard '{filename}' should have a title"
                    assert "panels" in dashboard, f"Dashboard '{filename}' should have panels"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Dashboard '{filename}' has invalid JSON: {e}")
        
        print("✅ All dashboard JSON files are valid")
    
    def test_dashboard_uids_unique(self):
        """Test that all dashboard UIDs are unique."""
        uids = []
        for filename in DASHBOARD_FILES:
            filepath = os.path.join(DASHBOARD_DIR, filename)
            with open(filepath, "r") as f:
                dashboard = json.load(f)
                uid = dashboard.get("uid")
                assert uid, f"Dashboard '{filename}' should have a UID"
                assert uid not in uids, f"Dashboard UID '{uid}' is not unique"
                uids.append(uid)
        
        print(f"✅ All {len(uids)} dashboard UIDs are unique")


class TestNewPlatformDashboards:
    """Test new platform dashboard JSON files in the repository."""
    
    def test_platform_dashboard_files_exist(self):
        """Test that all platform dashboard JSON files exist."""
        for filename in PLATFORM_DASHBOARD_FILES:
            filepath = os.path.join(PLATFORM_DASHBOARD_DIR, filename)
            assert os.path.exists(filepath), f"Platform dashboard file '{filename}' should exist at {filepath}"
        
        print(f"✅ All {len(PLATFORM_DASHBOARD_FILES)} platform dashboard files exist")
    
    def test_platform_dashboard_json_valid(self):
        """Test that all platform dashboard JSON files are valid."""
        for filename in PLATFORM_DASHBOARD_FILES:
            filepath = os.path.join(PLATFORM_DASHBOARD_DIR, filename)
            
            with open(filepath, "r") as f:
                try:
                    dashboard = json.load(f)
                    assert "title" in dashboard, f"Dashboard '{filename}' should have a title"
                    assert "panels" in dashboard, f"Dashboard '{filename}' should have panels"
                    assert "uid" in dashboard, f"Dashboard '{filename}' should have a uid"
                    assert dashboard["uid"].startswith("platform-"), f"Dashboard '{filename}' uid should start with 'platform-'"
                    
                    # Check template variables
                    templating = dashboard.get("templating", {})
                    variables = templating.get("list", [])
                    var_names = [v.get("name", "") for v in variables]
                    assert "datasource" in var_names, f"Dashboard '{filename}' should have datasource variable"
                    
                except json.JSONDecodeError as e:
                    pytest.fail(f"Platform dashboard '{filename}' has invalid JSON: {e}")
        
        print(f"✅ All {len(PLATFORM_DASHBOARD_FILES)} platform dashboard JSON files are valid")
    
    def test_platform_dashboard_uids_unique(self):
        """Test that all platform dashboard UIDs are unique."""
        uids = []
        for filename in PLATFORM_DASHBOARD_FILES:
            filepath = os.path.join(PLATFORM_DASHBOARD_DIR, filename)
            with open(filepath, "r") as f:
                dashboard = json.load(f)
                uid = dashboard.get("uid")
                assert uid, f"Dashboard '{filename}' should have a UID"
                assert uid not in uids, f"Dashboard UID '{uid}' is not unique"
                uids.append(uid)
        
        print(f"✅ All {len(uids)} platform dashboard UIDs are unique")


class TestNewServiceDashboards:
    """Test new service dashboard JSON files in the repository."""
    
    def test_service_dashboard_files_exist(self):
        """Test that all service dashboard JSON files exist."""
        for filename in SERVICE_DASHBOARD_FILES:
            filepath = os.path.join(SERVICE_DASHBOARD_DIR, filename)
            assert os.path.exists(filepath), f"Service dashboard file '{filename}' should exist at {filepath}"
        
        print(f"✅ All {len(SERVICE_DASHBOARD_FILES)} service dashboard files exist")
    
    def test_service_dashboard_json_valid(self):
        """Test that all service dashboard JSON files are valid."""
        for filename in SERVICE_DASHBOARD_FILES:
            filepath = os.path.join(SERVICE_DASHBOARD_DIR, filename)
            
            with open(filepath, "r") as f:
                try:
                    dashboard = json.load(f)
                    assert "title" in dashboard, f"Dashboard '{filename}' should have a title"
                    assert "panels" in dashboard, f"Dashboard '{filename}' should have panels"
                    assert "uid" in dashboard, f"Dashboard '{filename}' should have a uid"
                    assert dashboard["uid"].startswith("service-"), f"Dashboard '{filename}' uid should start with 'service-'"
                    
                    # Check template variables - service dashboards should have service and instance
                    templating = dashboard.get("templating", {})
                    variables = templating.get("list", [])
                    var_names = [v.get("name", "") for v in variables]
                    assert "datasource" in var_names, f"Dashboard '{filename}' should have datasource variable"
                    assert "service" in var_names, f"Dashboard '{filename}' should have service variable"
                    
                except json.JSONDecodeError as e:
                    pytest.fail(f"Service dashboard '{filename}' has invalid JSON: {e}")
        
        print(f"✅ All {len(SERVICE_DASHBOARD_FILES)} service dashboard JSON files are valid")
    
    def test_service_dashboard_uids_unique(self):
        """Test that all service dashboard UIDs are unique."""
        uids = []
        for filename in SERVICE_DASHBOARD_FILES:
            filepath = os.path.join(SERVICE_DASHBOARD_DIR, filename)
            with open(filepath, "r") as f:
                dashboard = json.load(f)
                uid = dashboard.get("uid")
                assert uid, f"Dashboard '{filename}' should have a UID"
                assert uid not in uids, f"Dashboard UID '{uid}' is not unique"
                uids.append(uid)
        
        print(f"✅ All {len(uids)} service dashboard UIDs are unique")
    
    def test_service_overview_has_golden_signals(self):
        """Test that service-overview.json includes Golden Signals panels."""
        filepath = os.path.join(SERVICE_DASHBOARD_DIR, "service-overview.json")
        
        with open(filepath, "r") as f:
            dashboard = json.load(f)
            panels = dashboard.get("panels", [])
            panel_titles = [p.get("title", "").lower() for p in panels]
            
            # Check for Golden Signals
            has_traffic = any("traffic" in title or "request" in title or "rps" in title for title in panel_titles)
            has_latency = any("latency" in title or "duration" in title or "p99" in title or "p95" in title for title in panel_titles)
            has_errors = any("error" in title for title in panel_titles)
            has_saturation = any("saturation" in title or "cpu" in title or "memory" in title for title in panel_titles)
            
            assert has_traffic, "Service overview should have Traffic metric panel"
            assert has_latency, "Service overview should have Latency metric panel"
            assert has_errors, "Service overview should have Errors metric panel"
            assert has_saturation, "Service overview should have Saturation metric panel"
        
        print("✅ Service overview dashboard includes Golden Signals")

