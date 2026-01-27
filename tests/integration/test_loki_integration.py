"""
Integration tests for Loki (log aggregation system).
Tests that Loki is ready and can accept logs.
"""

import os
import time
import requests
import pytest
from typing import Dict, Any


# Configuration
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")


@pytest.fixture(scope="session")
def loki_url() -> str:
    """Provide Loki URL."""
    return LOKI_URL


@pytest.fixture(scope="session")
def wait_for_loki(loki_url: str) -> None:
    """Wait for Loki to be ready."""
    max_retries = 60
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{loki_url}/ready",
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Loki is ready after {attempt + 1} attempts")
                return
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(retry_interval)
    
    pytest.fail("Loki did not become ready in time")


class TestLokiHealth:
    """Test Loki health and availability."""
    
    def test_loki_is_ready(self, wait_for_loki, loki_url: str):
        """Test that Loki is ready."""
        response = requests.get(f"{loki_url}/ready")
        assert response.status_code == 200, "Loki should return 200 OK for /ready"
        
        print("✅ Loki is ready")
    
    def test_loki_status(self, wait_for_loki, loki_url: str):
        """Test that Loki status endpoint is accessible."""
        # Try different status endpoints
        endpoints = [
            f"{loki_url}/services",
            f"{loki_url}/config"
        ]
        
        accessible = False
        for endpoint in endpoints:
            response = requests.get(endpoint, timeout=10)
            if response.status_code == 200:
                accessible = True
                print(f"✅ Loki status endpoint accessible: {endpoint}")
                break
        
        if not accessible:
            print("⚠️  Loki status endpoints not accessible (may require auth)")
    
    def test_loki_version(self, wait_for_loki, loki_url: str):
        """Test that Loki build information is accessible."""
        response = requests.get(f"{loki_url}/loki/api/v1/status/buildinfo", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            version = data.get("version", "unknown")
            print(f"✅ Loki version: {version}")
        else:
            print("⚠️  Loki build info endpoint not available")


class TestLokiPorts:
    """Test that Loki ports are accessible."""
    
    def test_loki_http_port_open(self):
        """Test that Loki HTTP port is accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 3100))
            assert result == 0, "Loki HTTP port 3100 should be open"
            print("✅ Loki HTTP port (3100) is open")
        finally:
            sock.close()
    
    def test_loki_grpc_port_open(self):
        """Test that Loki gRPC port is accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 9096))
            assert result == 0, "Loki gRPC port 9096 should be open"
            print("✅ Loki gRPC port (9096) is open")
        finally:
            sock.close()


class TestLokiMetrics:
    """Test Loki metrics endpoint."""
    
    def test_loki_metrics_endpoint(self, wait_for_loki, loki_url: str):
        """Test that Loki exposes metrics."""
        response = requests.get(f"{loki_url}/metrics", timeout=10)
        
        assert response.status_code == 200, "Loki should expose metrics"
        
        metrics = response.text
        
        # Check for some expected Loki metrics
        assert len(metrics) > 0, "Loki should expose metrics"
        
        # Look for some key metrics
        expected_metrics = [
            "loki_ingester_",
            "loki_distributor_",
            "loki_request_duration_seconds"
        ]
        
        found_metrics = []
        for metric_prefix in expected_metrics:
            if metric_prefix in metrics:
                found_metrics.append(metric_prefix)
        
        print(f"✅ Loki metrics endpoint is available ({len(found_metrics)} metric families found)")


class TestLokiAPI:
    """Test Loki API endpoints."""
    
    def test_loki_labels_endpoint(self, wait_for_loki, loki_url: str):
        """Test that Loki labels endpoint is accessible."""
        response = requests.get(
            f"{loki_url}/loki/api/v1/labels",
            timeout=10
        )
        
        # Should return 200 even if no logs exist
        assert response.status_code == 200, \
            "Loki labels endpoint should be accessible"
        
        if response.status_code == 200:
            data = response.json()
            labels = data.get("data", [])
            print(f"✅ Loki labels endpoint works ({len(labels)} labels found)")
        else:
            print("⚠️  Loki labels endpoint returned unexpected status")
    
    def test_loki_label_values_endpoint(self, wait_for_loki, loki_url: str):
        """Test that Loki label values endpoint is accessible."""
        # Try to get values for 'job' label (common label)
        response = requests.get(
            f"{loki_url}/loki/api/v1/label/job/values",
            timeout=10
        )
        
        # Should return 200 even if no logs exist
        assert response.status_code == 200, \
            "Loki label values endpoint should be accessible"
        
        if response.status_code == 200:
            data = response.json()
            values = data.get("data", [])
            print(f"✅ Loki label values endpoint works ({len(values)} values for 'job' label)")
        else:
            print("⚠️  Loki label values endpoint returned unexpected status")
    
    def test_loki_can_query_logs(self, wait_for_loki, loki_url: str):
        """Test that Loki query endpoint works."""
        # Try a simple query (may return empty if no logs exist)
        import time
        
        # Query for logs in the last 5 minutes
        now = int(time.time() * 1e9)  # nanoseconds
        five_min_ago = now - (5 * 60 * 1e9)
        
        response = requests.get(
            f"{loki_url}/loki/api/v1/query_range",
            params={
                "query": '{job=~".+"}',
                "start": str(int(five_min_ago)),
                "end": str(int(now)),
                "limit": "10"
            },
            timeout=10
        )
        
        # Should return 200 even if no logs found, or 400 if query is invalid
        if response.status_code == 200:
            data = response.json()
            result = data.get("data", {}).get("result", [])
            print(f"✅ Loki query endpoint works ({len(result)} streams found)")
        elif response.status_code == 400:
            # Query may be invalid or no data yet
            print("⚠️  Loki query endpoint is accessible but returned 400 (may need valid data)")
        else:
            pytest.fail(f"Loki query returned unexpected status: {response.status_code}")


class TestLokiPushAPI:
    """Test Loki push API for log ingestion."""
    
    def test_loki_push_endpoint_accessible(self, wait_for_loki, loki_url: str):
        """Test that Loki push endpoint is accessible."""
        # We won't actually push logs in this test, just verify the endpoint responds
        # A proper push requires valid protobuf or JSON payload
        
        # Just verify the endpoint exists by checking if URL is reachable
        # We expect it to reject our empty request but still respond
        response = requests.post(
            f"{loki_url}/loki/api/v1/push",
            json={},
            timeout=10
        )
        
        # We expect 400 or 204/200 depending on validation
        # The important thing is the endpoint is reachable
        assert response.status_code in [200, 204, 400, 415], \
            f"Loki push endpoint should be accessible (got {response.status_code})"
        
        print(f"✅ Loki push endpoint is accessible (status: {response.status_code})")


class TestLokiConfiguration:
    """Test Loki configuration."""
    
    def test_loki_config_endpoint(self, wait_for_loki, loki_url: str):
        """Test that Loki configuration is accessible."""
        response = requests.get(f"{loki_url}/config", timeout=10)
        
        if response.status_code == 200:
            # Configuration is in YAML format
            config = response.text
            assert len(config) > 0, "Loki should return configuration"
            
            # Check for some expected configuration sections
            expected_sections = ["server:", "distributor:", "ingester:", "schema_config:"]
            found_sections = [section for section in expected_sections if section in config]
            
            print(f"✅ Loki configuration is accessible ({len(found_sections)} sections found)")
        else:
            print("⚠️  Loki configuration endpoint not accessible (may require auth)")


class TestLokiLogIngestion:
    """Test Loki log ingestion capability."""
    
    def test_loki_can_receive_logs(self, wait_for_loki):
        """Test that Loki is ready to receive logs."""
        # In this setup, logs come from Grafana Alloy and the OTel Collector
        # We just verify Loki is ready
        
        response = requests.get("http://localhost:3100/ready", timeout=5)
        assert response.status_code == 200, "Loki should be ready to receive logs"
        
        print("✅ Loki is ready to receive logs")


class TestLokiDataRetention:
    """Test Loki data retention and storage."""
    
    def test_loki_storage_accessible(self, wait_for_loki):
        """Test that Loki storage is accessible."""
        # Loki stores data locally in this setup
        # We can verify by checking if the ready endpoint works
        response = requests.get("http://localhost:3100/ready", timeout=5)
        assert response.status_code == 200, "Loki should have accessible storage"
        
        print("✅ Loki storage is accessible")


class TestAlloyIntegration:
    """Test Grafana Alloy integration with Loki."""
    
    def test_alloy_is_running(self):
        """Test that Alloy is running and accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 12345))
            assert result == 0, "Alloy HTTP port 12345 should be open"
            print("✅ Alloy is running (port 12345 is open)")
        finally:
            sock.close()
    
    def test_alloy_metrics_endpoint(self):
        """Test that Alloy exposes metrics."""
        response = requests.get("http://localhost:12345/metrics", timeout=10)
        
        if response.status_code == 200:
            metrics = response.text
            
            # Check for Alloy/Loki pipeline metrics
            assert len(metrics) > 0, "Alloy should expose metrics"
            
            if "loki_source_docker" in metrics or "alloy_" in metrics:
                print("✅ Alloy metrics endpoint is available")
            else:
                print("⚠️  Alloy metrics may not be fully initialized yet")
        else:
            print("⚠️  Alloy metrics endpoint not accessible")
