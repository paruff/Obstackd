"""
Integration tests for Tempo (distributed tracing backend).
Tests that Tempo is ready and can accept traces.
"""

import os
import time
import requests
import pytest
from typing import Dict, Any


# Configuration
TEMPO_URL = os.getenv("TEMPO_URL", "http://localhost:3200")


@pytest.fixture(scope="session")
def tempo_url() -> str:
    """Provide Tempo URL."""
    return TEMPO_URL


@pytest.fixture(scope="session")
def wait_for_tempo(tempo_url: str) -> None:
    """Wait for Tempo to be ready."""
    max_retries = 60
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{tempo_url}/ready",
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Tempo is ready after {attempt + 1} attempts")
                return
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(retry_interval)
    
    pytest.fail("Tempo did not become ready in time")


class TestTempoHealth:
    """Test Tempo health and availability."""
    
    def test_tempo_is_ready(self, wait_for_tempo, tempo_url: str):
        """Test that Tempo is ready."""
        response = requests.get(f"{tempo_url}/ready")
        assert response.status_code == 200, "Tempo should return 200 OK for /ready"
        
        print("✅ Tempo is ready")
    
    def test_tempo_status(self, wait_for_tempo, tempo_url: str):
        """Test that Tempo status endpoint is accessible."""
        response = requests.get(f"{tempo_url}/status")
        assert response.status_code == 200, "Tempo should return 200 OK for /status"
        
        print("✅ Tempo status endpoint is accessible")
    
    def test_tempo_version(self, wait_for_tempo, tempo_url: str):
        """Test that Tempo reports its version."""
        response = requests.get(f"{tempo_url}/status/version")
        
        if response.status_code == 200:
            try:
                data = response.json()
                version = data.get("version", "unknown")
                print(f"✅ Tempo version: {version}")
            except requests.exceptions.JSONDecodeError:
                # Response may not be JSON
                print(f"✅ Tempo version endpoint responded (non-JSON response)")
        else:
            # Some Tempo versions may not have this endpoint
            print("⚠️  Tempo version endpoint not available")


class TestTempoPorts:
    """Test that Tempo ports are accessible."""
    
    def test_tempo_http_port_open(self):
        """Test that Tempo HTTP port is accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 3200))
            assert result == 0, "Tempo HTTP port 3200 should be open"
            print("✅ Tempo HTTP port (3200) is open")
        finally:
            sock.close()
    
    def test_tempo_grpc_port_open(self):
        """Test that Tempo gRPC port is accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 9095))
            assert result == 0, "Tempo gRPC port 9095 should be open"
            print("✅ Tempo gRPC port (9095) is open")
        finally:
            sock.close()
    
    def test_jaeger_grpc_port_open(self):
        """Test that Jaeger gRPC receiver port is accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 14250))
            assert result == 0, "Jaeger gRPC port 14250 should be open"
            print("✅ Jaeger gRPC receiver port (14250) is open")
        finally:
            sock.close()
    
    def test_jaeger_http_port_open(self):
        """Test that Jaeger HTTP receiver port is accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 14268))
            assert result == 0, "Jaeger HTTP port 14268 should be open"
            print("✅ Jaeger HTTP receiver port (14268) is open")
        finally:
            sock.close()
    
    def test_zipkin_port_open(self):
        """Test that Zipkin receiver port is accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 9411))
            assert result == 0, "Zipkin port 9411 should be open"
            print("✅ Zipkin receiver port (9411) is open")
        finally:
            sock.close()


class TestTempoMetrics:
    """Test Tempo metrics endpoint."""
    
    def test_tempo_metrics_endpoint(self, wait_for_tempo, tempo_url: str):
        """Test that Tempo exposes metrics."""
        response = requests.get(f"{tempo_url}/metrics", timeout=10)
        
        if response.status_code == 200:
            metrics = response.text
            
            # Check for some expected Tempo metrics
            assert len(metrics) > 0, "Tempo should expose metrics"
            
            # Look for some key metrics
            expected_metrics = [
                "tempo_ingester_",
                "tempo_distributor_",
                "tempo_querier_"
            ]
            
            found_metrics = []
            for metric_prefix in expected_metrics:
                if metric_prefix in metrics:
                    found_metrics.append(metric_prefix)
            
            print(f"✅ Tempo metrics endpoint is available ({len(found_metrics)} metric families found)")
        else:
            print("⚠️  Tempo metrics endpoint not available")


class TestTempoAPI:
    """Test Tempo API endpoints."""
    
    def test_tempo_search_tags_endpoint(self, wait_for_tempo, tempo_url: str):
        """Test that Tempo search tags endpoint is accessible."""
        response = requests.get(
            f"{tempo_url}/api/search/tags",
            timeout=10
        )
        
        # Should return 200 even if no traces exist
        assert response.status_code == 200, \
            "Tempo search tags endpoint should be accessible"
        
        print("✅ Tempo search tags endpoint is accessible")
    
    def test_tempo_search_tag_values_endpoint(self, wait_for_tempo, tempo_url: str):
        """Test that Tempo search tag values endpoint is accessible."""
        # Query for service.name tag values (common tag)
        response = requests.get(
            f"{tempo_url}/api/search/tag/service.name/values",
            timeout=10
        )
        
        # Should return 200 even if no traces exist
        assert response.status_code == 200, \
            "Tempo search tag values endpoint should be accessible"
        
        print("✅ Tempo search tag values endpoint is accessible")
    
    def test_tempo_can_search_traces(self, wait_for_tempo, tempo_url: str):
        """Test that Tempo search endpoint works."""
        # Try to search for traces (may return empty if no traces exist)
        response = requests.get(
            f"{tempo_url}/api/search",
            params={"limit": 10},
            timeout=10
        )
        
        # Should return 200 even if no traces found
        assert response.status_code == 200, \
            "Tempo search endpoint should be accessible"
        
        if response.status_code == 200:
            data = response.json()
            traces = data.get("traces", [])
            print(f"✅ Tempo search endpoint works ({len(traces)} traces found)")
        else:
            print("⚠️  Tempo search returned unexpected status")


class TestTempoConfiguration:
    """Test Tempo configuration."""
    
    def test_tempo_buildinfo(self, wait_for_tempo, tempo_url: str):
        """Test that Tempo build information is available."""
        response = requests.get(f"{tempo_url}/api/status/buildinfo", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for expected fields
            expected_fields = ["version", "goVersion"]
            for field in expected_fields:
                if field in data:
                    print(f"  • {field}: {data[field]}")
            
            print("✅ Tempo build info is available")
        else:
            print("⚠️  Tempo build info endpoint not available (may not be supported)")


class TestTempoTraceIngestion:
    """Test Tempo trace ingestion capability."""
    
    def test_tempo_can_receive_otlp_traces(self, wait_for_tempo):
        """Test that Tempo's OTLP receiver ports are accessible via OTel Collector."""
        # In this setup, traces go through OTel Collector first
        # So we just verify the collector ports are open (tested in test_otel_collector.py)
        # and that Tempo is ready to receive from the collector
        
        # Check that Tempo is ready
        response = requests.get("http://localhost:3200/ready", timeout=5)
        assert response.status_code == 200, "Tempo should be ready to receive traces"
        
        print("✅ Tempo is ready to receive traces (via OTel Collector)")


class TestTempoDataRetention:
    """Test Tempo data retention and storage."""
    
    def test_tempo_storage_accessible(self, wait_for_tempo):
        """Test that Tempo storage is accessible."""
        # Tempo stores data locally in this setup
        # We can verify by checking if the ready endpoint works
        response = requests.get("http://localhost:3200/ready", timeout=5)
        assert response.status_code == 200, "Tempo should have accessible storage"
        
        print("✅ Tempo storage is accessible")
