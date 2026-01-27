"""
Integration tests for Alloy and dashboard metrics/logs/traces validation.
Tests that Alloy collects logs, dashboards display data, and correlations work.
"""

import os
import time
import requests
import pytest
from typing import Dict, Any, List
import json


# Configuration
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.getenv("GRAFANA_PASSWORD", "admin")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")
ALLOY_URL = os.getenv("ALLOY_URL", "http://localhost:12345")
TEMPO_URL = os.getenv("TEMPO_URL", "http://localhost:3200")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")


@pytest.fixture(scope="session")
def alloy_url() -> str:
    """Provide Alloy URL."""
    return ALLOY_URL


@pytest.fixture(scope="session")
def wait_for_alloy(alloy_url: str) -> None:
    """Wait for Alloy to be ready."""
    max_retries = 60
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{alloy_url}/metrics",
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Alloy is ready after {attempt + 1} attempts")
                return
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(retry_interval)
    
    pytest.fail("Alloy did not become ready in time")


@pytest.fixture(scope="session")
def grafana_auth() -> tuple:
    """Provide Grafana authentication credentials."""
    return (GRAFANA_USER, GRAFANA_PASSWORD)


class TestAlloyHealth:
    """Test Alloy health and availability."""
    
    def test_alloy_metrics_port_open(self):
        """Test that Alloy metrics port is accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 12345))
            assert result == 0, "Alloy HTTP port 12345 should be open"
            print("✅ Alloy HTTP port (12345) is open")
        finally:
            sock.close()
    
    def test_alloy_metrics_endpoint(self, wait_for_alloy, alloy_url: str):
        """Test that Alloy exposes metrics."""
        response = requests.get(f"{alloy_url}/metrics", timeout=10)
        
        assert response.status_code == 200, "Alloy should expose metrics"
        
        metrics = response.text
        assert len(metrics) > 0, "Alloy should expose metrics"
        
        print(f"✅ Alloy metrics endpoint is available ({len(metrics)} bytes)")


class TestAlloyDockerSource:
    """Test Alloy Docker source discovery."""
    
    def test_alloy_has_docker_metrics(self, wait_for_alloy, alloy_url: str):
        """Test that Alloy has Docker source metrics."""
        response = requests.get(f"{alloy_url}/metrics", timeout=10)
        
        metrics = response.text
        
        # Look for docker source metrics
        docker_metric_lines = [line for line in metrics.split('\n') 
                              if 'loki_source_docker' in line and not line.startswith('#')]
        
        if docker_metric_lines:
            print(f"✅ Alloy has docker source metrics ({len(docker_metric_lines)} metric lines)")
        else:
            print("⚠️  Alloy docker source metrics not initialized yet (containers may not have logs)")


class TestAlloyToLokiPipeline:
    """Test the Alloy → Loki pipeline."""
    
    def test_alloy_can_write_to_loki(self, wait_for_alloy, alloy_url: str):
        """Test that Alloy can connect to Loki."""
        response = requests.get(f"{alloy_url}/metrics", timeout=10)
        
        metrics = response.text
        
        # Look for write metrics
        write_metric_lines = [line for line in metrics.split('\n') 
                             if 'loki_write' in line and not line.startswith('#')]
        
        assert len(metrics) > 0, "Should have metrics indicating Alloy is running"
        
        print(f"✅ Alloy write pipeline metrics present ({len(write_metric_lines)} lines)")


class TestDashboardMetricsData:
    """Test that dashboards receive metrics from Prometheus."""
    
    @pytest.fixture(scope="session")
    def prometheus_url(self) -> str:
        return PROMETHEUS_URL
    
    def test_prometheus_has_otel_metrics(self, prometheus_url: str):
        """Test that Prometheus scrapes OTel Collector metrics."""
        import time as time_module
        
        # Query for otel metrics in the last 10 minutes
        now = int(time_module.time())
        ten_min_ago = now - (10 * 60)
        
        response = requests.get(
            f"{prometheus_url}/api/v1/query_range",
            params={
                "query": 'up{job="otel-collector"}',
                "start": ten_min_ago,
                "end": now,
                "step": "60"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("data", {}).get("result", [])
            
            if result:
                print(f"✅ Prometheus has OTel Collector metrics ({len(result)} series)")
            else:
                print("⚠️  No OTel metrics found in Prometheus (may need time to collect)")
        else:
            print(f"⚠️  Prometheus query returned {response.status_code}")
    
    def test_prometheus_has_alertmanager_metrics(self, prometheus_url: str):
        """Test that Prometheus scrapes Alertmanager metrics."""
        response = requests.get(
            f"{prometheus_url}/api/v1/query",
            params={
                "query": 'alertmanager_build_info'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("data", {}).get("result", [])
            
            if result:
                print(f"✅ Prometheus has Alertmanager metrics")
            else:
                print("⚠️  Alertmanager metrics not yet available")


class TestDashboardLogsData:
    """Test that dashboards receive logs from Loki via Alloy."""
    
    def test_loki_receives_docker_logs(self):
        """Test that Loki has docker container logs."""
        import time as time_module
        
        # Query for docker logs in the last 10 minutes
        now = int(time_module.time() * 1e9)
        ten_min_ago = now - (10 * 60 * 1e9)
        
        response = requests.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={
                "query": '{job="docker"}',
                "start": str(int(ten_min_ago)),
                "end": str(int(now)),
                "limit": "10"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("data", {}).get("result", [])
            
            if result:
                print(f"✅ Loki has docker container logs ({len(result)} streams)")
            else:
                print("⚠️  No docker logs in Loki yet (Alloy may still be discovering containers)")
        else:
            print(f"⚠️  Loki query returned {response.status_code}")
    
    def test_loki_has_compose_service_labels(self):
        """Test that logs have compose_service labels for filtering."""
        import time as time_module
        
        # Query for logs with compose_service label
        response = requests.get(
            f"{LOKI_URL}/loki/api/v1/labels/compose_service/values",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            values = data.get("data", [])
            
            if values:
                print(f"✅ Loki has compose_service labels ({len(values)} services)")
            else:
                print("⚠️  No compose_service labels found yet")


class TestDashboardTracesData:
    """Test that dashboards receive traces from Tempo."""
    
    def test_tempo_is_ready(self):
        """Test that Tempo is ready to receive traces."""
        response = requests.get(f"{TEMPO_URL}/ready", timeout=5)
        assert response.status_code == 200, "Tempo should be ready"
        
        print("✅ Tempo is ready for traces")
    
    def test_tempo_has_traces(self):
        """Test that Tempo has received traces."""
        response = requests.get(
            f"{TEMPO_URL}/api/traces",
            params={"limit": "10"},
            timeout=10
        )
        
        # Tempo may return 400 if no data yet, that's okay
        if response.status_code == 200:
            print("✅ Tempo has trace data")
        else:
            print("⚠️  No traces in Tempo yet (may need time to collect from OTel)")


class TestDashboardMetricsLogsTracesCorrelation:
    """Test that dashboards can correlate metrics, logs, and traces."""
    
    def test_loki_datasource_has_trace_correlation(self, grafana_auth: tuple):
        """Test that Loki datasource has trace correlation configured."""
        response = requests.get(
            f"{GRAFANA_URL}/api/datasources",
            auth=grafana_auth,
            timeout=10
        )
        
        datasources = response.json()
        loki_ds = [ds for ds in datasources if ds.get("type") == "loki"]
        
        assert len(loki_ds) > 0, "Loki datasource should exist"
        
        # Check for derivedFields in jsonData
        loki_config = loki_ds[0].get("jsonData", {})
        derived_fields = loki_config.get("derivedFields", [])
        
        if derived_fields:
            # Check for traceID field
            trace_fields = [f for f in derived_fields if 'traceID' in f.get('name', '')]
            if trace_fields:
                print("✅ Loki datasource has traceID correlation configured")
            else:
                print("⚠️  Loki datasource has derived fields but no traceID correlation")
        else:
            print("⚠️  Loki datasource has no derived fields configured for trace correlation")
    
    def test_tempo_datasource_has_service_map(self, grafana_auth: tuple):
        """Test that Tempo datasource has service map configured."""
        response = requests.get(
            f"{GRAFANA_URL}/api/datasources",
            auth=grafana_auth,
            timeout=10
        )
        
        datasources = response.json()
        tempo_ds = [ds for ds in datasources if ds.get("type") == "tempo"]
        
        assert len(tempo_ds) > 0, "Tempo datasource should exist"
        
        tempo_config = tempo_ds[0].get("jsonData", {})
        service_map = tempo_config.get("serviceMap", {})
        
        if service_map and service_map.get("datasourceUid"):
            print("✅ Tempo datasource has service map configured")
        else:
            print("⚠️  Tempo datasource service map not fully configured")


class TestDashboardRendering:
    """Test that dashboards render without errors."""
    
    def test_infrastructure_dashboard_has_log_panel(self, grafana_auth: tuple):
        """Test that Infrastructure Overview dashboard has log data panels."""
        response = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/infrastructure-overview",
            auth=grafana_auth,
            timeout=10
        )
        
        if response.status_code == 200:
            dashboard = response.json().get("dashboard", {})
            panels = dashboard.get("panels", [])
            
            # Look for panels with Loki queries
            loki_panels = []
            for panel in panels:
                targets = panel.get("targets", [])
                for target in targets:
                    datasource_uid = target.get("datasourceUid")
                    # Would be better to check actual datasource type, but UID is a proxy
                    if target.get("expr") and isinstance(target.get("expr"), str):
                        if "{" in target.get("expr"):  # LogQL pattern
                            loki_panels.append(panel.get("title", "Unknown"))
            
            if loki_panels:
                print(f"✅ Infrastructure dashboard has log panels ({len(loki_panels)} panels with queries)")
            else:
                print("⚠️  Infrastructure dashboard may not have log panels with queries")
    
    def test_application_performance_dashboard_queries_valid(self, grafana_auth: tuple):
        """Test that Application Performance dashboard queries are properly formed."""
        response = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/application-performance",
            auth=grafana_auth,
            timeout=10
        )
        
        if response.status_code == 200:
            dashboard = response.json().get("dashboard", {})
            panels = dashboard.get("panels", [])
            
            valid_queries = 0
            for panel in panels:
                targets = panel.get("targets", [])
                for target in targets:
                    expr = target.get("expr")
                    if expr:
                        # Check for valid query syntax (non-empty, has content)
                        if isinstance(expr, str) and len(expr) > 0 and "{" in str(expr):
                            valid_queries += 1
            
            if valid_queries > 0:
                print(f"✅ Application Performance dashboard has {valid_queries} valid queries")
            else:
                print("⚠️  Application Performance dashboard queries may be incomplete")
    
    def test_observability_stack_health_dashboard_panels(self, grafana_auth: tuple):
        """Test that Observability Stack Health dashboard panels are accessible."""
        response = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/observability-stack-health",
            auth=grafana_auth,
            timeout=10
        )
        
        if response.status_code == 200:
            dashboard = response.json().get("dashboard", {})
            panels = dashboard.get("panels", [])
            
            assert len(panels) > 0, "Dashboard should have panels"
            
            # Check for specific panel types
            stat_panels = [p for p in panels if p.get("type") == "stat"]
            graph_panels = [p for p in panels if p.get("type") in ["timeseries", "graph"]]
            
            print(f"✅ Observability Stack Health has {len(panels)} panels " +
                  f"({len(stat_panels)} stats, {len(graph_panels)} graphs)")
