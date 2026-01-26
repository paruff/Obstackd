"""
Unit tests for Loki configuration validation.

These tests validate the Loki configuration to ensure:
- Valid YAML syntax
- Required sections are present
- Server configuration is valid
- Schema configuration is correct
- Storage configuration is appropriate
- Limits and retention are configured
"""
import pytest
import yaml
from pathlib import Path


class TestLokiConfigStructure:
    """Test the basic structure of the Loki configuration."""

    def test_config_file_exists(self, loki_config_path):
        """Test that the Loki config file exists."""
        assert loki_config_path.exists(), \
            f"Config file not found: {loki_config_path}"

    def test_valid_yaml_syntax(self, loki_config_path):
        """Test that the config file contains valid YAML."""
        with open(loki_config_path, 'r') as f:
            try:
                config = yaml.safe_load(f)
                assert config is not None, "Config is empty"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML syntax: {e}")

    def test_required_sections_present(self, loki_config_path):
        """Test that required sections are present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        required_sections = ['server', 'schema_config']
        for section in required_sections:
            assert section in config, \
                f"Missing required section: {section}"


class TestLokiServerConfig:
    """Test the server configuration section."""

    def test_http_listen_port_defined(self, loki_config_path):
        """Test that http_listen_port is defined."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'http_listen_port' in config['server'], \
            "server.http_listen_port should be defined"

    def test_http_listen_port_valid(self, loki_config_path):
        """Test that http_listen_port is a valid port number."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        port = config['server']['http_listen_port']
        assert isinstance(port, int), \
            "http_listen_port should be an integer"
        assert 1 <= port <= 65535, \
            "http_listen_port should be a valid port number (1-65535)"

    def test_grpc_listen_port_valid(self, loki_config_path):
        """Test that grpc_listen_port is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'grpc_listen_port' in config['server']:
            port = config['server']['grpc_listen_port']
            assert isinstance(port, int), \
                "grpc_listen_port should be an integer"
            assert 1 <= port <= 65535, \
                "grpc_listen_port should be a valid port number"

    def test_log_level_valid(self, loki_config_path):
        """Test that log_level is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'log_level' in config['server']:
            log_level = config['server']['log_level']
            valid_levels = ['debug', 'info', 'warn', 'error']
            assert log_level in valid_levels, \
                f"log_level should be one of {valid_levels}"


class TestLokiAuthConfig:
    """Test the authentication configuration."""

    def test_auth_enabled_is_boolean(self, loki_config_path):
        """Test that auth_enabled is a boolean."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'auth_enabled' in config, \
            "auth_enabled should be defined"
        assert isinstance(config['auth_enabled'], bool), \
            "auth_enabled should be a boolean"


class TestLokiSchemaConfig:
    """Test the schema configuration section."""

    def test_schema_config_has_configs(self, loki_config_path):
        """Test that schema_config has configs array."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'configs' in config['schema_config'], \
            "schema_config should have 'configs' array"
        assert isinstance(config['schema_config']['configs'], list), \
            "schema_config.configs should be a list"
        assert len(config['schema_config']['configs']) > 0, \
            "schema_config.configs should not be empty"

    def test_schema_config_entries_valid(self, loki_config_path):
        """Test that schema config entries are valid."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for idx, schema in enumerate(config['schema_config']['configs']):
            # Each schema should have required fields
            assert 'from' in schema, \
                f"Schema config at index {idx} missing 'from' date"
            assert 'store' in schema, \
                f"Schema config at index {idx} missing 'store'"
            assert 'object_store' in schema, \
                f"Schema config at index {idx} missing 'object_store'"
            assert 'schema' in schema, \
                f"Schema config at index {idx} missing 'schema' version"

    def test_schema_store_valid(self, loki_config_path):
        """Test that schema store types are valid."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        valid_stores = ['boltdb', 'boltdb-shipper', 'tsdb']
        for schema in config['schema_config']['configs']:
            store = schema['store']
            assert store in valid_stores, \
                f"Schema store '{store}' should be one of {valid_stores}"

    def test_schema_object_store_valid(self, loki_config_path):
        """Test that object store types are valid."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        valid_object_stores = ['filesystem', 's3', 'gcs', 'azure', 'swift']
        for schema in config['schema_config']['configs']:
            object_store = schema['object_store']
            assert object_store in valid_object_stores, \
                f"Object store '{object_store}' should be one of {valid_object_stores}"


class TestLokiStorageConfig:
    """Test the storage configuration section."""

    def test_storage_config_present_if_needed(self, loki_config_path):
        """Test that storage_config is present if using filesystem."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # If using filesystem in schema, storage_config should be present
        for schema in config['schema_config']['configs']:
            if schema['object_store'] == 'filesystem':
                assert 'storage_config' in config or 'common' in config, \
                    "storage_config or common should be present for filesystem storage"


class TestLokiCommonConfig:
    """Test the common configuration section if present."""

    def test_common_config_valid(self, loki_config_path):
        """Test that common configuration is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'common' in config:
            common = config['common']
            assert isinstance(common, dict), \
                "common should be a dictionary"

    def test_common_path_prefix_valid(self, loki_config_path):
        """Test that path_prefix is valid if present in common."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'common' in config and 'path_prefix' in config['common']:
            path_prefix = config['common']['path_prefix']
            assert isinstance(path_prefix, str), \
                "path_prefix should be a string"
            assert len(path_prefix) > 0, \
                "path_prefix should not be empty"

    def test_common_storage_filesystem_valid(self, loki_config_path):
        """Test that filesystem storage in common is valid."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'common' in config and 'storage' in config['common']:
            storage = config['common']['storage']
            if 'filesystem' in storage:
                fs = storage['filesystem']
                # Should have chunks_directory and/or rules_directory
                has_dirs = 'chunks_directory' in fs or 'rules_directory' in fs
                assert has_dirs, \
                    "filesystem storage should have directory configuration"


class TestLokiLimitsConfig:
    """Test the limits configuration section."""

    def test_limits_config_valid(self, loki_config_path):
        """Test that limits_config is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'limits_config' in config:
            limits = config['limits_config']
            assert isinstance(limits, dict), \
                "limits_config should be a dictionary"

    def test_retention_period_valid(self, loki_config_path):
        """Test that retention_period is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'limits_config' in config and 'retention_period' in config['limits_config']:
            retention = config['limits_config']['retention_period']
            # Should be a string with time unit or integer
            if isinstance(retention, str):
                # Should end with time unit
                assert retention[-1] in ['s', 'm', 'h', 'd'], \
                    "retention_period should have time unit (s, m, h, d)"

    def test_ingestion_rate_valid(self, loki_config_path):
        """Test that ingestion_rate_mb is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'limits_config' in config:
            limits = config['limits_config']
            if 'ingestion_rate_mb' in limits:
                rate = limits['ingestion_rate_mb']
                assert isinstance(rate, (int, float)), \
                    "ingestion_rate_mb should be a number"
                assert rate > 0, \
                    "ingestion_rate_mb should be positive"

    def test_reject_old_samples_valid(self, loki_config_path):
        """Test that reject_old_samples is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'limits_config' in config and 'reject_old_samples' in config['limits_config']:
            reject_old = config['limits_config']['reject_old_samples']
            assert isinstance(reject_old, bool), \
                "reject_old_samples should be a boolean"


class TestLokiCompactorConfig:
    """Test the compactor configuration section."""

    def test_compactor_config_valid(self, loki_config_path):
        """Test that compactor configuration is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'compactor' in config:
            compactor = config['compactor']
            assert isinstance(compactor, dict), \
                "compactor should be a dictionary"

    def test_compactor_working_directory_valid(self, loki_config_path):
        """Test that compactor working_directory is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'compactor' in config and 'working_directory' in config['compactor']:
            working_dir = config['compactor']['working_directory']
            assert isinstance(working_dir, str), \
                "working_directory should be a string"
            assert len(working_dir) > 0, \
                "working_directory should not be empty"


class TestLokiQueryConfig:
    """Test the query-related configuration sections."""

    def test_query_range_config_valid(self, loki_config_path):
        """Test that query_range configuration is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'query_range' in config:
            qr = config['query_range']
            assert isinstance(qr, dict), \
                "query_range should be a dictionary"

    def test_querier_config_valid(self, loki_config_path):
        """Test that querier configuration is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'querier' in config:
            querier = config['querier']
            assert isinstance(querier, dict), \
                "querier should be a dictionary"

    def test_frontend_config_valid(self, loki_config_path):
        """Test that frontend configuration is valid if present."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'frontend' in config:
            frontend = config['frontend']
            assert isinstance(frontend, dict), \
                "frontend should be a dictionary"


class TestLokiConfigValidation:
    """Integration tests for complete Loki configuration validation."""

    def test_complete_config_is_valid(self, loki_config_path):
        """Test that the complete configuration is valid."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Should have essential sections
        assert 'auth_enabled' in config
        assert 'server' in config
        assert 'schema_config' in config
        
        # Server should have HTTP port
        assert 'http_listen_port' in config['server']
        
        # Schema should have configs
        assert 'configs' in config['schema_config']
        assert len(config['schema_config']['configs']) > 0

    def test_schema_and_storage_compatibility(self, loki_config_path):
        """Test that schema and storage configurations are compatible."""
        with open(loki_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # If schema uses filesystem, verify storage is configured
        for schema in config['schema_config']['configs']:
            if schema['object_store'] == 'filesystem':
                # Should have storage_config or common.storage with filesystem
                has_storage = False
                
                if 'storage_config' in config and 'filesystem' in config['storage_config']:
                    has_storage = True
                
                if 'common' in config and 'storage' in config['common']:
                    if 'filesystem' in config['common']['storage']:
                        has_storage = True
                
                assert has_storage, \
                    "Filesystem object store requires filesystem storage configuration"
