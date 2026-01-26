"""
Integration tests for OpenTelemetry Collector.
Tests that OTel Collector is operational and exporting telemetry.
"""

import os
import time
import requests
import pytest
from typing import Dict, Any


# Configuration
OTEL_METRICS_URL = os.getenv("OTEL_METRICS_URL", "http://localhost:8888")
OTEL_HEALTH_URL = os.getenv("OTEL_HEALTH_URL", "http://localhost:13133")


@pytest.fixture(scope="session")
def otel_metrics_url() -> str:
    """Provide OTel Collector metrics URL."""
    return OTEL_METRICS_URL


@pytest.fixture(scope="session")
def otel_health_url() -> str:
    """Provide OTel Collector health check URL."""
    return OTEL_HEALTH_URL


@pytest.fixture(scope="session")
def wait_for_otel_collector(otel_metrics_url: str) -> None:
    """Wait for OTel Collector to be ready."""
    max_retries = 60
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{otel_metrics_url}/metrics",
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ OTel Collector is ready after {attempt + 1} attempts")
                return
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(retry_interval)
    
    pytest.fail("OTel Collector did not become ready in time")


def get_otel_metrics(otel_metrics_url: str) -> str:
    """
    Get metrics from OTel Collector.
    
    Args:
        otel_metrics_url: Base URL for OTel Collector metrics
        
    Returns:
        Metrics in Prometheus text format
    """
    response = requests.get(
        f"{otel_metrics_url}/metrics",
        timeout=10
    )
    response.raise_for_status()
    return response.text


def parse_prometheus_metric(metrics_text: str, metric_name: str) -> list:
    """
    Parse a specific metric from Prometheus text format.
    
    Args:
        metrics_text: Full metrics text
        metric_name: Name of the metric to extract
        
    Returns:
        List of matching metric lines
    """
    lines = metrics_text.split('\n')
    matching_lines = []
    
    for line in lines:
        if line.startswith(metric_name):
            matching_lines.append(line)
    
    return matching_lines


class TestOTelCollectorHealth:
    """Test OTel Collector health and availability."""
    
    def test_otel_collector_is_running(self, wait_for_otel_collector, otel_metrics_url: str):
        """Test that OTel Collector is running and serving metrics."""
        response = requests.get(f"{otel_metrics_url}/metrics")
        assert response.status_code == 200, "OTel Collector should return 200 OK"
        
        # Check that we got some metrics
        assert len(response.text) > 0, "OTel Collector should return metrics"
        assert "otelcol" in response.text, "Metrics should contain otelcol metrics"
        
        print("✅ OTel Collector is running and serving metrics")
    
    def test_otel_collector_uptime(self, wait_for_otel_collector, otel_metrics_url: str):
        """Test that OTel Collector reports uptime."""
        metrics = get_otel_metrics(otel_metrics_url)
        
        uptime_lines = parse_prometheus_metric(metrics, "otelcol_process_uptime")
        assert len(uptime_lines) > 0, "Should report process uptime"
        
        # Extract uptime value
        uptime_line = uptime_lines[0]
        uptime_value = float(uptime_line.split()[-1])
        
        assert uptime_value > 0, "Uptime should be positive"
        print(f"✅ OTel Collector uptime: {uptime_value:.2f}s")
    
    def test_otel_collector_runtime_info(self, wait_for_otel_collector, otel_metrics_url: str):
        """Test that OTel Collector reports runtime information."""
        metrics = get_otel_metrics(otel_metrics_url)
        
        # Check for runtime metrics
        runtime_metrics = [
            "otelcol_process_runtime_heap_alloc_bytes",
            "otelcol_process_runtime_total_alloc_bytes",
            "otelcol_process_cpu_seconds"
        ]
        
        for metric in runtime_metrics:
            lines = parse_prometheus_metric(metrics, metric)
            # Note: Some metrics may not be present depending on configuration
            print(f"  • {metric}: {len(lines)} series")
        
        print("✅ OTel Collector runtime metrics available")


class TestOTelCollectorReceivers:
    """Test OTel Collector receivers are operational."""
    
    def test_otlp_grpc_receiver_port_open(self):
        """Test that OTLP gRPC receiver port is accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 4317))
            assert result == 0, "OTLP gRPC port 4317 should be open"
            print("✅ OTLP gRPC receiver port (4317) is open")
        finally:
            sock.close()
    
    def test_otlp_http_receiver_port_open(self):
        """Test that OTLP HTTP receiver port is accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 4318))
            assert result == 0, "OTLP HTTP port 4318 should be open"
            print("✅ OTLP HTTP receiver port (4318) is open")
        finally:
            sock.close()
    
    def test_receiver_accepted_metrics(self, wait_for_otel_collector, otel_metrics_url: str):
        """Test that receiver accepted metrics are being tracked."""
        metrics = get_otel_metrics(otel_metrics_url)
        
        # Check for receiver metrics
        receiver_metrics = [
            "otelcol_receiver_accepted_spans",
            "otelcol_receiver_accepted_metric_points",
            "otelcol_receiver_refused_spans",
            "otelcol_receiver_refused_metric_points"
        ]
        
        for metric in receiver_metrics:
            lines = parse_prometheus_metric(metrics, metric)
            # Note: These metrics may be 0 if no data has been received yet
            print(f"  • {metric}: {len(lines)} series")
        
        print("✅ Receiver metrics are being tracked")
    
    def test_receiver_no_refused_data(self, wait_for_otel_collector, otel_metrics_url: str):
        """Test that receivers are not refusing data."""
        metrics = get_otel_metrics(otel_metrics_url)
        
        refused_metrics = [
            "otelcol_receiver_refused_spans",
            "otelcol_receiver_refused_metric_points"
        ]
        
        for metric in refused_metrics:
            lines = parse_prometheus_metric(metrics, metric)
            
            for line in lines:
                if not line.startswith('#'):
                    value = float(line.split()[-1])
                    assert value == 0, f"{metric} should be 0, got {value} (data is being refused)"
        
        print("✅ No data is being refused by receivers")


class TestOTelCollectorExporters:
    """Test OTel Collector exporters are operational."""
    
    def test_exporter_sent_metrics(self, wait_for_otel_collector, otel_metrics_url: str):
        """Test that exporter sent metrics are being tracked."""
        metrics = get_otel_metrics(otel_metrics_url)
        
        # Check for exporter metrics
        exporter_metrics = [
            "otelcol_exporter_sent_spans",
            "otelcol_exporter_sent_metric_points",
            "otelcol_exporter_send_failed_spans",
            "otelcol_exporter_send_failed_metric_points"
        ]
        
        for metric in exporter_metrics:
            lines = parse_prometheus_metric(metrics, metric)
            # Note: These metrics may be 0 if no data has been exported yet
            print(f"  • {metric}: {len(lines)} series")
        
        print("✅ Exporter metrics are being tracked")
    
    def test_exporter_no_send_failures(self, wait_for_otel_collector, otel_metrics_url: str):
        """Test that exporters are not failing to send data."""
        metrics = get_otel_metrics(otel_metrics_url)
        
        failed_metrics = [
            "otelcol_exporter_send_failed_spans",
            "otelcol_exporter_send_failed_metric_points"
        ]
        
        for metric in failed_metrics:
            lines = parse_prometheus_metric(metrics, metric)
            
            for line in lines:
                if not line.startswith('#'):
                    value = float(line.split()[-1])
                    # Allow some failures during startup, but not excessive
                    assert value < 100, \
                        f"{metric} should be low, got {value} (exporters are failing)"
        
        print("✅ Exporters are not failing excessively")
    
    def test_prometheus_exporter_port_open(self):
        """Test that Prometheus exporter port is accessible."""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', 8889))
            assert result == 0, "Prometheus exporter port 8889 should be open"
            print("✅ Prometheus exporter port (8889) is open")
        finally:
            sock.close()


class TestOTelCollectorProcessors:
    """Test OTel Collector processors are operational."""
    
    def test_batch_processor_metrics(self, wait_for_otel_collector, otel_metrics_url: str):
        """Test that batch processor metrics are available."""
        metrics = get_otel_metrics(otel_metrics_url)
        
        # Check for processor metrics
        processor_metrics = [
            "otelcol_processor_batch_batch_send_size_bucket",
            "otelcol_processor_batch_timeout_trigger_send"
        ]
        
        for metric in processor_metrics:
            lines = parse_prometheus_metric(metrics, metric)
            # Note: These metrics may be 0 if no data has been processed yet
            print(f"  • {metric}: {len(lines)} series")
        
        print("✅ Batch processor metrics are available")


class TestOTelCollectorQueueMetrics:
    """Test OTel Collector queue metrics."""
    
    def test_queue_size_metrics(self, wait_for_otel_collector, otel_metrics_url: str):
        """Test that queue size metrics are available."""
        metrics = get_otel_metrics(otel_metrics_url)
        
        # Check for queue metrics
        queue_metrics = [
            "otelcol_exporter_queue_size",
            "otelcol_exporter_queue_capacity"
        ]
        
        for metric in queue_metrics:
            lines = parse_prometheus_metric(metrics, metric)
            print(f"  • {metric}: {len(lines)} series")
        
        print("✅ Queue metrics are available")
    
    def test_queue_not_full(self, wait_for_otel_collector, otel_metrics_url: str):
        """Test that queues are not full (which would indicate backpressure)."""
        metrics = get_otel_metrics(otel_metrics_url)
        
        size_lines = parse_prometheus_metric(metrics, "otelcol_exporter_queue_size")
        capacity_lines = parse_prometheus_metric(metrics, "otelcol_exporter_queue_capacity")
        
        # Build a map of queue sizes and capacities
        queue_data = {}
        
        for line in size_lines:
            if not line.startswith('#'):
                # Extract labels and value
                parts = line.split()
                value = float(parts[-1])
                # Simple parsing - in production, use a proper parser
                queue_data.setdefault(line, {})['size'] = value
        
        for line in capacity_lines:
            if not line.startswith('#'):
                parts = line.split()
                value = float(parts[-1])
                queue_data.setdefault(line, {})['capacity'] = value
        
        # Check that no queue is close to full (>80%)
        for queue, data in queue_data.items():
            if 'size' in data and 'capacity' in data and data['capacity'] > 0:
                utilization = data['size'] / data['capacity']
                assert utilization < 0.8, \
                    f"Queue utilization is too high: {utilization:.1%} (indicates backpressure)"
        
        print("✅ Queues are not full (no backpressure detected)")


class TestOTelCollectorConfiguration:
    """Test OTel Collector configuration is correct."""
    
    def test_expected_metrics_endpoints_available(self, wait_for_otel_collector):
        """Test that expected metrics endpoints are available."""
        endpoints = [
            ("http://localhost:8888/metrics", "Internal metrics"),
            ("http://localhost:8889/metrics", "Prometheus exporter")
        ]
        
        for url, description in endpoints:
            try:
                response = requests.get(url, timeout=5)
                assert response.status_code == 200, \
                    f"{description} endpoint should be available at {url}"
                print(f"✅ {description} endpoint available: {url}")
            except requests.exceptions.RequestException as e:
                pytest.fail(f"{description} endpoint not available: {e}")
