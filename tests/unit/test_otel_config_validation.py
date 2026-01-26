"""
Unit tests for OpenTelemetry Collector configuration validation.

These tests validate the OTel Collector configuration to ensure:
- Valid YAML syntax
- Required receivers are defined
- Processor pipeline order is logical
- Exporters have valid endpoints
- Resource attributes schema is correct
- Common misconfigurations are caught
"""
import pytest
import yaml
from pathlib import Path


class TestOTelConfigStructure:
    """Test the basic structure of the OTel Collector configuration."""

    def test_config_file_exists(self, otel_config_path):
        """Test that the OTel Collector config file exists."""
        assert otel_config_path.exists(), f"Config file not found: {otel_config_path}"

    def test_valid_yaml_syntax(self, otel_config_path):
        """Test that the config file contains valid YAML."""
        with open(otel_config_path, 'r') as f:
            try:
                config = yaml.safe_load(f)
                assert config is not None, "Config is empty"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML syntax: {e}")

    def test_all_required_sections_present(self, otel_config_path):
        """Test that all required top-level sections are present."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        required_sections = ['receivers', 'processors', 'exporters', 'service']
        for section in required_sections:
            assert section in config, f"Missing required section: {section}"


class TestOTelReceivers:
    """Test the receivers configuration."""

    def test_otlp_receiver_exists(self, otel_config_path):
        """Test that the OTLP receiver is defined."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'receivers' in config, "Missing receivers section"
        assert 'otlp' in config['receivers'], "Missing required receiver: otlp"

    def test_otlp_receiver_has_protocols(self, otel_config_path):
        """Test that the OTLP receiver defines protocols."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        otlp = config['receivers']['otlp']
        assert 'protocols' in otlp, "OTLP receiver missing protocols"
        
        # At least one protocol should be defined
        protocols = otlp['protocols']
        assert len(protocols) > 0, "OTLP receiver has no protocols defined"

    def test_otlp_grpc_endpoint_valid(self, otel_config_path):
        """Test that OTLP gRPC endpoint is valid."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'grpc' in config['receivers']['otlp']['protocols']:
            grpc = config['receivers']['otlp']['protocols']['grpc']
            assert 'endpoint' in grpc, "OTLP gRPC missing endpoint"
            endpoint = grpc['endpoint']
            assert ':' in endpoint, "OTLP gRPC endpoint should contain port"
            # Validate it's a valid host:port format
            parts = endpoint.split(':')
            assert len(parts) == 2, "OTLP gRPC endpoint should be host:port"
            assert parts[1].isdigit(), "OTLP gRPC port should be numeric"

    def test_otlp_http_endpoint_valid(self, otel_config_path):
        """Test that OTLP HTTP endpoint is valid."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'http' in config['receivers']['otlp']['protocols']:
            http = config['receivers']['otlp']['protocols']['http']
            assert 'endpoint' in http, "OTLP HTTP missing endpoint"
            endpoint = http['endpoint']
            assert ':' in endpoint, "OTLP HTTP endpoint should contain port"
            # Validate it's a valid host:port format
            parts = endpoint.split(':')
            assert len(parts) == 2, "OTLP HTTP endpoint should be host:port"
            assert parts[1].isdigit(), "OTLP HTTP port should be numeric"


class TestOTelProcessors:
    """Test the processors configuration."""

    def test_processors_section_exists(self, otel_config_path):
        """Test that processors section exists."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'processors' in config, "Missing processors section"
        assert len(config['processors']) > 0, "Processors section is empty"

    def test_memory_limiter_exists(self, otel_config_path):
        """Test that memory_limiter processor exists."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'memory_limiter' in config['processors'], \
            "memory_limiter processor should be defined for production safety"

    def test_batch_processor_exists(self, otel_config_path):
        """Test that batch processor exists."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'batch' in config['processors'], \
            "batch processor should be defined for efficiency"

    def test_memory_limiter_has_valid_config(self, otel_config_path):
        """Test that memory_limiter has valid configuration."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'memory_limiter' in config['processors']:
            mem_limiter = config['processors']['memory_limiter']
            # Check for required fields
            if 'limit_mib' in mem_limiter:
                assert isinstance(mem_limiter['limit_mib'], int), \
                    "memory_limiter limit_mib should be an integer"
                assert mem_limiter['limit_mib'] > 0, \
                    "memory_limiter limit_mib should be positive"


class TestOTelExporters:
    """Test the exporters configuration."""

    def test_exporters_section_exists(self, otel_config_path):
        """Test that exporters section exists."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'exporters' in config, "Missing exporters section"
        assert len(config['exporters']) > 0, "Exporters section is empty"

    def test_prometheus_exporter_endpoint_valid(self, otel_config_path):
        """Test that Prometheus exporter has valid endpoint."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'prometheus' in config['exporters']:
            prom = config['exporters']['prometheus']
            assert 'endpoint' in prom, "Prometheus exporter missing endpoint"
            endpoint = prom['endpoint']
            assert ':' in endpoint, "Prometheus exporter endpoint should contain port"

    def test_tempo_exporter_endpoint_valid(self, otel_config_path):
        """Test that Tempo exporter has valid endpoint."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for otlp/tempo exporter
        tempo_exporters = [k for k in config['exporters'].keys() if 'tempo' in k.lower()]
        
        for exporter_name in tempo_exporters:
            exporter = config['exporters'][exporter_name]
            assert 'endpoint' in exporter, f"{exporter_name} exporter missing endpoint"
            endpoint = exporter['endpoint']
            # Should be either host:port or a valid service name
            assert len(endpoint) > 0, f"{exporter_name} endpoint cannot be empty"

    def test_loki_exporter_endpoint_valid(self, otel_config_path):
        """Test that Loki exporter has valid endpoint."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'loki' in config['exporters']:
            loki = config['exporters']['loki']
            assert 'endpoint' in loki, "Loki exporter missing endpoint"
            endpoint = loki['endpoint']
            # Should be a valid URL
            assert endpoint.startswith('http://') or endpoint.startswith('https://'), \
                "Loki exporter endpoint should be a valid HTTP URL"


class TestOTelServicePipelines:
    """Test the service pipelines configuration."""

    def test_service_section_exists(self, otel_config_path):
        """Test that service section exists."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'service' in config, "Missing service section"

    def test_pipelines_section_exists(self, otel_config_path):
        """Test that pipelines section exists in service."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'pipelines' in config['service'], "Missing pipelines section in service"

    def test_metrics_pipeline_exists(self, otel_config_path):
        """Test that metrics pipeline is defined."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'metrics' in config['service']['pipelines'], \
            "Metrics pipeline should be defined"

    def test_traces_pipeline_exists(self, otel_config_path):
        """Test that traces pipeline is defined."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'traces' in config['service']['pipelines'], \
            "Traces pipeline should be defined"

    def test_logs_pipeline_exists(self, otel_config_path):
        """Test that logs pipeline is defined."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'logs' in config['service']['pipelines'], \
            "Logs pipeline should be defined"

    def test_pipeline_has_receivers(self, otel_config_path):
        """Test that each pipeline has receivers defined."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for pipeline_name, pipeline in config['service']['pipelines'].items():
            assert 'receivers' in pipeline, \
                f"Pipeline {pipeline_name} missing receivers"
            assert len(pipeline['receivers']) > 0, \
                f"Pipeline {pipeline_name} has no receivers"

    def test_pipeline_has_exporters(self, otel_config_path):
        """Test that each pipeline has exporters defined."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for pipeline_name, pipeline in config['service']['pipelines'].items():
            assert 'exporters' in pipeline, \
                f"Pipeline {pipeline_name} missing exporters"
            assert len(pipeline['exporters']) > 0, \
                f"Pipeline {pipeline_name} has no exporters"

    def test_pipeline_processor_order_logical(self, otel_config_path):
        """Test that processor order is logical (memory_limiter before batch)."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for pipeline_name, pipeline in config['service']['pipelines'].items():
            if 'processors' in pipeline and len(pipeline['processors']) > 1:
                processors = pipeline['processors']
                # If both memory_limiter and batch are present,
                # memory_limiter should come before batch
                if 'memory_limiter' in processors and 'batch' in processors:
                    mem_idx = processors.index('memory_limiter')
                    batch_idx = processors.index('batch')
                    assert mem_idx < batch_idx, \
                        f"In pipeline {pipeline_name}, memory_limiter should come before batch"

    def test_pipeline_references_valid(self, otel_config_path):
        """Test that pipeline references valid receivers, processors, and exporters."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Get all defined components
        defined_receivers = set(config.get('receivers', {}).keys())
        defined_processors = set(config.get('processors', {}).keys())
        defined_exporters = set(config.get('exporters', {}).keys())
        
        # Check each pipeline
        for pipeline_name, pipeline in config['service']['pipelines'].items():
            # Check receivers
            for receiver in pipeline.get('receivers', []):
                assert receiver in defined_receivers, \
                    f"Pipeline {pipeline_name} references undefined receiver: {receiver}"
            
            # Check processors
            for processor in pipeline.get('processors', []):
                assert processor in defined_processors, \
                    f"Pipeline {pipeline_name} references undefined processor: {processor}"
            
            # Check exporters
            for exporter in pipeline.get('exporters', []):
                assert exporter in defined_exporters, \
                    f"Pipeline {pipeline_name} references undefined exporter: {exporter}"


class TestOTelConfigValidationWithFixtures:
    """Test validation with fixture configurations."""

    def test_valid_config_passes_all_checks(self, otel_config_path):
        """Test that the current valid config passes all validation checks."""
        with open(otel_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Basic structure
        assert 'receivers' in config
        assert 'processors' in config
        assert 'exporters' in config
        assert 'service' in config
        
        # Required receiver
        assert 'otlp' in config['receivers']
        
        # Recommended processors
        assert 'memory_limiter' in config['processors']
        assert 'batch' in config['processors']
        
        # Service configuration
        assert 'pipelines' in config['service']
        assert len(config['service']['pipelines']) > 0
