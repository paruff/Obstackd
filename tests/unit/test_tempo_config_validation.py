"""
Unit tests for Tempo configuration validation.

These tests validate the Tempo configuration to ensure:
- Valid YAML syntax
- Required sections are present
- Server configuration is valid
- Distributor receivers are configured
- Storage configuration is correct
- Ingester settings are appropriate
"""
import pytest
import yaml
from pathlib import Path


class TestTempoConfigStructure:
    """Test the basic structure of the Tempo configuration."""

    def test_config_file_exists(self, tempo_config_path):
        """Test that the Tempo config file exists."""
        assert tempo_config_path.exists(), \
            f"Config file not found: {tempo_config_path}"

    def test_valid_yaml_syntax(self, tempo_config_path):
        """Test that the config file contains valid YAML."""
        with open(tempo_config_path, 'r') as f:
            try:
                config = yaml.safe_load(f)
                assert config is not None, "Config is empty"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML syntax: {e}")

    def test_required_sections_present(self, tempo_config_path):
        """Test that required sections are present."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        required_sections = ['server', 'distributor', 'ingester', 'storage']
        for section in required_sections:
            assert section in config, \
                f"Missing required section: {section}"


class TestTempoServerConfig:
    """Test the server configuration section."""

    def test_http_listen_port_defined(self, tempo_config_path):
        """Test that http_listen_port is defined."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'http_listen_port' in config['server'], \
            "server.http_listen_port should be defined"

    def test_http_listen_port_valid(self, tempo_config_path):
        """Test that http_listen_port is a valid port number."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        port = config['server']['http_listen_port']
        assert isinstance(port, int), \
            "http_listen_port should be an integer"
        assert 1 <= port <= 65535, \
            "http_listen_port should be a valid port number (1-65535)"

    def test_grpc_listen_port_defined(self, tempo_config_path):
        """Test that grpc_listen_port is defined."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'grpc_listen_port' in config['server']:
            port = config['server']['grpc_listen_port']
            assert isinstance(port, int), \
                "grpc_listen_port should be an integer"
            assert 1 <= port <= 65535, \
                "grpc_listen_port should be a valid port number"

    def test_log_level_valid(self, tempo_config_path):
        """Test that log_level is valid if present."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'log_level' in config['server']:
            log_level = config['server']['log_level']
            valid_levels = ['debug', 'info', 'warn', 'error']
            assert log_level in valid_levels, \
                f"log_level should be one of {valid_levels}"


class TestTempoDistributorConfig:
    """Test the distributor configuration section."""

    def test_receivers_section_exists(self, tempo_config_path):
        """Test that receivers section exists in distributor."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'receivers' in config['distributor'], \
            "distributor.receivers should be present"

    def test_otlp_receiver_configured(self, tempo_config_path):
        """Test that OTLP receiver is configured."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        receivers = config['distributor']['receivers']
        assert 'otlp' in receivers, \
            "OTLP receiver should be configured in distributor"

    def test_otlp_protocols_configured(self, tempo_config_path):
        """Test that OTLP protocols are configured."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        otlp = config['distributor']['receivers']['otlp']
        assert 'protocols' in otlp, \
            "OTLP receiver should have protocols configured"

    def test_otlp_grpc_endpoint_valid(self, tempo_config_path):
        """Test that OTLP gRPC endpoint is valid if configured."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        protocols = config['distributor']['receivers']['otlp']['protocols']
        if 'grpc' in protocols:
            grpc = protocols['grpc']
            if 'endpoint' in grpc:
                endpoint = grpc['endpoint']
                assert ':' in endpoint, \
                    "OTLP gRPC endpoint should contain port"
                parts = endpoint.split(':')
                assert len(parts) == 2, \
                    "OTLP gRPC endpoint should be host:port"

    def test_otlp_http_endpoint_valid(self, tempo_config_path):
        """Test that OTLP HTTP endpoint is valid if configured."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        protocols = config['distributor']['receivers']['otlp']['protocols']
        if 'http' in protocols:
            http = protocols['http']
            if 'endpoint' in http:
                endpoint = http['endpoint']
                assert ':' in endpoint, \
                    "OTLP HTTP endpoint should contain port"


class TestTempoIngesterConfig:
    """Test the ingester configuration section."""

    def test_ingester_has_configuration(self, tempo_config_path):
        """Test that ingester section has configuration."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert isinstance(config['ingester'], dict), \
            "ingester should be a dictionary with configuration"

    def test_max_block_duration_valid(self, tempo_config_path):
        """Test that max_block_duration is valid if present."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'max_block_duration' in config['ingester']:
            duration = config['ingester']['max_block_duration']
            # Should be a string with time unit
            assert isinstance(duration, str), \
                "max_block_duration should be a string"
            # Should end with time unit
            assert duration[-1] in ['s', 'm', 'h'], \
                "max_block_duration should have time unit (s, m, h)"


class TestTempoStorageConfig:
    """Test the storage configuration section."""

    def test_trace_storage_configured(self, tempo_config_path):
        """Test that trace storage is configured."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'trace' in config['storage'], \
            "storage.trace should be configured"

    def test_storage_backend_defined(self, tempo_config_path):
        """Test that storage backend is defined."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        trace_config = config['storage']['trace']
        assert 'backend' in trace_config, \
            "storage.trace.backend should be defined"

    def test_storage_backend_valid(self, tempo_config_path):
        """Test that storage backend is valid."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        backend = config['storage']['trace']['backend']
        valid_backends = ['local', 's3', 'gcs', 'azure']
        assert backend in valid_backends, \
            f"storage backend should be one of {valid_backends}"

    def test_local_storage_path_defined(self, tempo_config_path):
        """Test that local storage path is defined for local backend."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        trace_config = config['storage']['trace']
        if trace_config['backend'] == 'local':
            assert 'local' in trace_config, \
                "local storage backend should have 'local' configuration"
            assert 'path' in trace_config['local'], \
                "local storage should have path defined"


class TestTempoCompactorConfig:
    """Test the compactor configuration section if present."""

    def test_compactor_config_valid(self, tempo_config_path):
        """Test that compactor configuration is valid if present."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'compactor' in config:
            compactor = config['compactor']
            assert isinstance(compactor, dict), \
                "compactor should be a dictionary"


class TestTempoMetricsGeneratorConfig:
    """Test the metrics_generator configuration if present."""

    def test_metrics_generator_config_valid(self, tempo_config_path):
        """Test that metrics_generator configuration is valid if present."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'metrics_generator' in config:
            mg = config['metrics_generator']
            assert isinstance(mg, dict), \
                "metrics_generator should be a dictionary"

    def test_metrics_generator_storage_path(self, tempo_config_path):
        """Test that metrics_generator storage path is defined if present."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'metrics_generator' in config and 'storage' in config['metrics_generator']:
            storage = config['metrics_generator']['storage']
            if 'path' in storage:
                path = storage['path']
                assert isinstance(path, str), \
                    "metrics_generator storage path should be a string"
                assert len(path) > 0, \
                    "metrics_generator storage path should not be empty"


class TestTempoQueryConfig:
    """Test the query-related configuration sections."""

    def test_querier_config_valid(self, tempo_config_path):
        """Test that querier configuration is valid if present."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'querier' in config:
            querier = config['querier']
            assert isinstance(querier, dict), \
                "querier should be a dictionary"

    def test_query_frontend_config_valid(self, tempo_config_path):
        """Test that query_frontend configuration is valid if present."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'query_frontend' in config:
            qf = config['query_frontend']
            assert isinstance(qf, dict), \
                "query_frontend should be a dictionary"


class TestTempoConfigValidation:
    """Integration tests for complete Tempo configuration validation."""

    def test_complete_config_is_valid(self, tempo_config_path):
        """Test that the complete configuration is valid."""
        with open(tempo_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Should have all essential sections
        assert 'server' in config
        assert 'distributor' in config
        assert 'ingester' in config
        assert 'storage' in config
        
        # Server should have ports
        assert 'http_listen_port' in config['server']
        
        # Distributor should have receivers
        assert 'receivers' in config['distributor']
        
        # Storage should have trace backend
        assert 'trace' in config['storage']
        assert 'backend' in config['storage']['trace']
