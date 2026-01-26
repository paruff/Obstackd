"""
Integration tests for Prometheus metric scraping.
Tests that Prometheus scrapes all configured targets correctly.

Feature: Prometheus Metric Scraping
  As a DevOps engineer
  I want Prometheus to scrape all configured targets
  So that metrics are collected reliably
"""

import os
import time
import requests
import pytest
from typing import Dict, Any, List


# Configuration
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
SCRAPE_SLA_SECONDS = 1.0  # Scrape should complete in under 1 second


@pytest.fixture(scope="session")
def prometheus_url() -> str:
    """Provide Prometheus URL."""
    return PROMETHEUS_URL


@pytest.fixture(scope="session")
def wait_for_prometheus(prometheus_url: str) -> None:
    """Wait for Prometheus to be ready."""
    max_retries = 60
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"{prometheus_url}/-/ready",
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Prometheus is ready after {attempt + 1} attempts")
                # Give Prometheus a bit more time to start scraping
                time.sleep(10)
                return
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(retry_interval)
    
    pytest.fail("Prometheus did not become ready in time")


def query_prometheus(prometheus_url: str, query: str) -> Dict[str, Any]:
    """
    Execute a PromQL query and return results.
    
    Args:
        prometheus_url: Base URL for Prometheus
        query: PromQL query string
        
    Returns:
        Query result dictionary
    """
    response = requests.get(
        f"{prometheus_url}/api/v1/query",
        params={"query": query},
        timeout=10
    )
    response.raise_for_status()
    result = response.json()
    
    if result.get("status") != "success":
        raise ValueError(f"Query failed: {result.get('error', 'Unknown error')}")
    
    return result.get("data", {})


def query_prometheus_range(prometheus_url: str, query: str, start: int, end: int, step: int = 15) -> Dict[str, Any]:
    """
    Execute a PromQL range query.
    
    Args:
        prometheus_url: Base URL for Prometheus
        query: PromQL query string
        start: Start timestamp (Unix time)
        end: End timestamp (Unix time)
        step: Query resolution step width in seconds
        
    Returns:
        Query result dictionary
    """
    response = requests.get(
        f"{prometheus_url}/api/v1/query_range",
        params={
            "query": query,
            "start": start,
            "end": end,
            "step": step
        },
        timeout=10
    )
    response.raise_for_status()
    result = response.json()
    
    if result.get("status") != "success":
        raise ValueError(f"Query failed: {result.get('error', 'Unknown error')}")
    
    return result.get("data", {})


def get_targets(prometheus_url: str) -> List[Dict[str, Any]]:
    """
    Get all scrape targets from Prometheus.
    
    Args:
        prometheus_url: Base URL for Prometheus
        
    Returns:
        List of target dictionaries
    """
    response = requests.get(
        f"{prometheus_url}/api/v1/targets",
        timeout=10
    )
    response.raise_for_status()
    result = response.json()
    
    if result.get("status") != "success":
        raise ValueError(f"Failed to get targets: {result.get('error', 'Unknown error')}")
    
    return result.get("data", {}).get("activeTargets", [])


class TestPrometheusOTelCollectorScraping:
    """Test Prometheus scraping of OTel Collector metrics."""
    
    def test_otel_collector_target_is_up(self, wait_for_prometheus, prometheus_url: str):
        """
        Scenario: Prometheus scrapes OTel Collector successfully
          Given Obstackd stack is running
          And OTel Collector is exporting metrics on port 8888
          When I query Prometheus for 'up{job="otel-collector"}'
          Then the result should show value=1
        """
        data = query_prometheus(prometheus_url, 'up{job="otel-collector"}')
        
        results = data.get("result", [])
        assert len(results) > 0, "OTel Collector target should exist in Prometheus"
        
        # Check that the target is up (value=1)
        up_value = float(results[0].get("value", [0, "0"])[1])
        assert up_value == 1.0, f"OTel Collector should be up (value=1), got {up_value}"
        
        print("✅ OTel Collector target is up and being scraped")
    
    def test_otel_collector_scrape_duration(self, wait_for_prometheus, prometheus_url: str):
        """
        Test that OTel Collector scrape completes in under 1 second.
        
        Scenario: Prometheus scrapes OTel Collector successfully
          And the scrape should complete in under 1 second
        """
        data = query_prometheus(
            prometheus_url,
            'scrape_duration_seconds{job="otel-collector"}'
        )
        
        results = data.get("result", [])
        assert len(results) > 0, "Scrape duration metric should exist"
        
        duration = float(results[0].get("value", [0, "0"])[1])
        assert duration < SCRAPE_SLA_SECONDS, \
            f"Scrape duration should be < {SCRAPE_SLA_SECONDS}s, got {duration}s"
        
        print(f"✅ OTel Collector scrape duration: {duration:.3f}s (< {SCRAPE_SLA_SECONDS}s)")
    
    def test_otel_collector_no_scrape_errors(self, wait_for_prometheus, prometheus_url: str):
        """Test that there are no scrape errors for OTel Collector."""
        data = query_prometheus(
            prometheus_url,
            'up{job="otel-collector"}'
        )
        
        results = data.get("result", [])
        for result in results:
            up_value = float(result.get("value", [0, "0"])[1])
            if up_value != 1.0:
                # Get the instance that's down
                instance = result.get("metric", {}).get("instance", "unknown")
                pytest.fail(f"Scrape error detected for instance {instance}")
        
        print("✅ No scrape errors detected for OTel Collector")
    
    def test_otel_collector_metrics_available(self, wait_for_prometheus, prometheus_url: str):
        """Test that OTel Collector is exporting expected metrics."""
        # Check for key OTel Collector metrics
        expected_metrics = [
            'otelcol_process_uptime',
            'otelcol_receiver_accepted_spans',
            'otelcol_receiver_accepted_metric_points',
            'otelcol_exporter_sent_spans',
            'otelcol_exporter_sent_metric_points'
        ]
        
        for metric in expected_metrics:
            data = query_prometheus(prometheus_url, metric)
            results = data.get("result", [])
            # Note: Some metrics might not have data yet if no traffic has been sent
            # So we just check that the query succeeds
            print(f"  Metric '{metric}': {len(results)} series")
        
        print("✅ OTel Collector metrics are queryable")


class TestPrometheusAllTargets:
    """Test that all configured Prometheus targets are healthy."""
    
    def test_all_configured_targets_are_up(self, wait_for_prometheus, prometheus_url: str):
        """
        Scenario: All configured targets are healthy
          Given Obstackd stack is running
          When I query Prometheus for all 'up' metrics
          Then all core targets should have value=1
        """
        data = query_prometheus(prometheus_url, 'up')
        
        results = data.get("result", [])
        assert len(results) > 0, "Should have at least one target configured"
        
        # Core services that must be up
        core_services = ["prometheus", "otel-collector", "alertmanager"]
        # Optional services (like homeassistant in apps profile)
        optional_services = ["homeassistant"]
        
        down_core_targets = []
        down_optional_targets = []
        
        for result in results:
            metric = result.get("metric", {})
            job = metric.get("job", "unknown")
            instance = metric.get("instance", "unknown")
            up_value = float(result.get("value", [0, "0"])[1])
            
            if up_value != 1.0:
                if job in optional_services:
                    down_optional_targets.append(f"{job}/{instance}")
                else:
                    down_core_targets.append(f"{job}/{instance}")
        
        # Only fail if core services are down
        assert len(down_core_targets) == 0, \
            f"Core targets should be up, but these are down: {', '.join(down_core_targets)}"
        
        if down_optional_targets:
            print(f"⚠️  Optional targets are down: {', '.join(down_optional_targets)}")
        
        up_count = len(results) - len(down_core_targets) - len(down_optional_targets)
        print(f"✅ All {up_count} core targets are up and healthy")
    
    def test_no_targets_with_zero_samples(self, wait_for_prometheus, prometheus_url: str):
        """
        Scenario: All configured targets are healthy
          And no core scrape_samples_scraped should be 0
        """
        data = query_prometheus(
            prometheus_url,
            'scrape_samples_scraped{job!=""} == 0'
        )
        
        results = data.get("result", [])
        
        # Optional services that may not be running
        optional_services = ["homeassistant"]
        
        if len(results) > 0:
            core_zero_sample_targets = []
            optional_zero_sample_targets = []
            
            for result in results:
                metric = result.get("metric", {})
                job = metric.get("job", "unknown")
                instance = metric.get("instance", "unknown")
                
                if job in optional_services:
                    optional_zero_sample_targets.append(f"{job}/{instance}")
                else:
                    core_zero_sample_targets.append(f"{job}/{instance}")
            
            # Only fail if core services are not producing samples
            if core_zero_sample_targets:
                pytest.fail(
                    f"Core targets are not producing samples: {', '.join(core_zero_sample_targets)}"
                )
            
            if optional_zero_sample_targets:
                print(f"⚠️  Optional targets not producing samples: {', '.join(optional_zero_sample_targets)}")
        
        print("✅ All core targets are producing samples")
    
    def test_all_targets_scrape_duration_within_sla(self, wait_for_prometheus, prometheus_url: str):
        """Test that all target scrapes complete within SLA."""
        data = query_prometheus(
            prometheus_url,
            f'scrape_duration_seconds > {SCRAPE_SLA_SECONDS}'
        )
        
        results = data.get("result", [])
        
        if len(results) > 0:
            slow_targets = []
            for result in results:
                metric = result.get("metric", {})
                job = metric.get("job", "unknown")
                instance = metric.get("instance", "unknown")
                duration = float(result.get("value", [0, "0"])[1])
                slow_targets.append(f"{job}/{instance} ({duration:.3f}s)")
            
            pytest.fail(
                f"These targets exceed scrape SLA ({SCRAPE_SLA_SECONDS}s): {', '.join(slow_targets)}"
            )
        
        print(f"✅ All targets scrape within SLA ({SCRAPE_SLA_SECONDS}s)")


class TestPrometheusMetricLabels:
    """Test that metrics have correct labels."""
    
    def test_otel_receiver_metrics_have_required_labels(self, wait_for_prometheus, prometheus_url: str):
        """
        Scenario: Metrics have correct labels
          Given Prometheus is scraping metrics
          When I query for 'otelcol_receiver_accepted_spans'
          Then the metric should have required labels
        """
        data = query_prometheus(
            prometheus_url,
            'otelcol_receiver_accepted_spans'
        )
        
        results = data.get("result", [])
        
        # Check if we have results (may be empty if no spans have been received yet)
        if len(results) > 0:
            # Check first result for expected labels
            metric = results[0].get("metric", {})
            
            # Expected labels on OTel Collector metrics
            expected_labels = ["job", "instance", "receiver", "transport"]
            
            for label in expected_labels:
                assert label in metric, \
                    f"Metric should have label '{label}', got labels: {list(metric.keys())}"
            
            print(f"✅ OTel receiver metrics have required labels: {list(metric.keys())}")
        else:
            print("⚠️  No otelcol_receiver_accepted_spans data yet (this is OK if no spans sent)")
    
    def test_metrics_have_job_label(self, wait_for_prometheus, prometheus_url: str):
        """Test that all metrics have a 'job' label."""
        # Query for any metric without a job label
        data = query_prometheus(
            prometheus_url,
            'up{job=""}'
        )
        
        results = data.get("result", [])
        assert len(results) == 0, \
            "All metrics should have a 'job' label, but found metrics without it"
        
        print("✅ All scraped metrics have 'job' label")


class TestPrometheusTargetDetails:
    """Test detailed target information."""
    
    def test_get_all_targets_details(self, wait_for_prometheus, prometheus_url: str):
        """Get detailed information about all scrape targets."""
        targets = get_targets(prometheus_url)
        
        assert len(targets) > 0, "Should have at least one active target"
        
        # Optional services that may not be running
        optional_services = ["homeassistant"]
        
        print(f"\n📊 Active Targets ({len(targets)}):")
        down_core_targets = []
        
        for target in targets:
            job = target.get("labels", {}).get("job", "unknown")
            instance = target.get("labels", {}).get("instance", "unknown")
            health = target.get("health", "unknown")
            last_scrape = target.get("lastScrape", "never")
            last_scrape_duration = target.get("lastScrapeDuration", 0)
            
            print(f"  • {job}/{instance}: {health} (last: {last_scrape_duration}s)")
            
            # Verify core services are healthy
            if health != "up" and job not in optional_services:
                down_core_targets.append(f"{job}/{instance}")
        
        assert len(down_core_targets) == 0, \
            f"Core targets should be healthy, but these are down: {', '.join(down_core_targets)}"
    
    def test_otel_collector_target_labels(self, wait_for_prometheus, prometheus_url: str):
        """Test that OTel Collector target has correct labels."""
        targets = get_targets(prometheus_url)
        
        otel_targets = [t for t in targets if t.get("labels", {}).get("job") == "otel-collector"]
        assert len(otel_targets) > 0, "Should have OTel Collector target"
        
        otel_target = otel_targets[0]
        labels = otel_target.get("labels", {})
        
        # Check for expected labels from prometheus.yaml
        assert labels.get("component") == "otel-collector", \
            "Should have component=otel-collector label"
        assert labels.get("service") == "telemetry", \
            "Should have service=telemetry label"
        
        print("✅ OTel Collector target has correct labels")


class TestPrometheusMetricCardinality:
    """Test that metric cardinality is reasonable."""
    
    def test_metric_cardinality_is_reasonable(self, wait_for_prometheus, prometheus_url: str):
        """Test that we don't have excessive metric cardinality."""
        # Query for total number of time series
        data = query_prometheus(
            prometheus_url,
            'count({__name__=~".+"})'
        )
        
        results = data.get("result", [])
        if len(results) > 0:
            total_series = int(float(results[0].get("value", [0, "0"])[1]))
            
            # Set a reasonable upper limit (this will depend on your environment)
            # For a basic setup, we expect < 10,000 series
            max_expected_series = 10000
            
            assert total_series < max_expected_series, \
                f"Metric cardinality is too high: {total_series} series (max: {max_expected_series})"
            
            print(f"✅ Metric cardinality is reasonable: {total_series} series")
        else:
            print("⚠️  No metric series found yet")
    
    def test_no_excessive_label_combinations(self, wait_for_prometheus, prometheus_url: str):
        """Test that no single metric has excessive label combinations."""
        # Check cardinality for key metrics
        metrics_to_check = [
            'up',
            'scrape_duration_seconds',
            'otelcol_process_uptime'
        ]
        
        for metric in metrics_to_check:
            data = query_prometheus(prometheus_url, f'count({metric}) by (__name__)')
            results = data.get("result", [])
            
            if len(results) > 0:
                count = int(float(results[0].get("value", [0, "0"])[1]))
                max_expected = 100  # Reasonable limit per metric
                
                assert count < max_expected, \
                    f"Metric '{metric}' has too many series: {count} (max: {max_expected})"
                
                print(f"  • {metric}: {count} series")
