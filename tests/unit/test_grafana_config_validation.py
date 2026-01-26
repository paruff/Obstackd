"""
Unit tests for Grafana configuration validation.

These tests validate the Grafana datasources configuration to ensure:
- Valid YAML syntax
- Required datasources are present
- Datasource configurations are valid
- URLs are properly formatted
- jsonData configurations are correct
"""
import pytest
import yaml
from pathlib import Path


class TestGrafanaConfigStructure:
    """Test the basic structure of the Grafana datasources configuration."""

    def test_config_file_exists(self, grafana_datasources_path):
        """Test that the Grafana datasources config file exists."""
        assert grafana_datasources_path.exists(), \
            f"Config file not found: {grafana_datasources_path}"

    def test_valid_yaml_syntax(self, grafana_datasources_path):
        """Test that the config file contains valid YAML."""
        with open(grafana_datasources_path, 'r') as f:
            try:
                config = yaml.safe_load(f)
                assert config is not None, "Config is empty"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML syntax: {e}")

    def test_api_version_present(self, grafana_datasources_path):
        """Test that apiVersion is present."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'apiVersion' in config, "apiVersion should be present"
        assert config['apiVersion'] == 1, "apiVersion should be 1"

    def test_datasources_section_exists(self, grafana_datasources_path):
        """Test that datasources section exists."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'datasources' in config, "datasources section should be present"
        assert isinstance(config['datasources'], list), \
            "datasources should be a list"
        assert len(config['datasources']) > 0, \
            "datasources should not be empty"


class TestGrafanaDatasourceBasics:
    """Test basic datasource configuration requirements."""

    def test_each_datasource_has_name(self, grafana_datasources_path):
        """Test that each datasource has a name."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for idx, ds in enumerate(config['datasources']):
            assert 'name' in ds, \
                f"Datasource at index {idx} missing name"
            assert isinstance(ds['name'], str), \
                f"Datasource name at index {idx} should be a string"
            assert len(ds['name']) > 0, \
                f"Datasource name at index {idx} should not be empty"

    def test_each_datasource_has_type(self, grafana_datasources_path):
        """Test that each datasource has a type."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for ds in config['datasources']:
            name = ds.get('name', 'unknown')
            assert 'type' in ds, \
                f"Datasource '{name}' missing type"
            assert isinstance(ds['type'], str), \
                f"Datasource '{name}' type should be a string"

    def test_each_datasource_has_url(self, grafana_datasources_path):
        """Test that each datasource has a URL."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for ds in config['datasources']:
            name = ds.get('name', 'unknown')
            assert 'url' in ds, \
                f"Datasource '{name}' missing url"
            assert isinstance(ds['url'], str), \
                f"Datasource '{name}' url should be a string"

    def test_datasource_urls_valid_format(self, grafana_datasources_path):
        """Test that datasource URLs have valid format."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for ds in config['datasources']:
            name = ds.get('name', 'unknown')
            url = ds['url']
            # Should start with http:// or https://
            assert url.startswith('http://') or url.startswith('https://'), \
                f"Datasource '{name}' URL should start with http:// or https://"
            # Should contain a hostname
            assert len(url.split('://')[1]) > 0, \
                f"Datasource '{name}' URL should contain a hostname"

    def test_access_mode_valid(self, grafana_datasources_path):
        """Test that access mode is valid if present."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        valid_access_modes = ['proxy', 'direct']
        for ds in config['datasources']:
            name = ds.get('name', 'unknown')
            if 'access' in ds:
                access = ds['access']
                assert access in valid_access_modes, \
                    f"Datasource '{name}' access should be 'proxy' or 'direct'"


class TestGrafanaRequiredDatasources:
    """Test that required datasources for the observability stack are present."""

    def test_prometheus_datasource_exists(self, grafana_datasources_path):
        """Test that Prometheus datasource is configured."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        ds_names = [ds['name'] for ds in config['datasources']]
        assert 'Prometheus' in ds_names, \
            "Prometheus datasource should be configured"

    def test_tempo_datasource_exists(self, grafana_datasources_path):
        """Test that Tempo datasource is configured."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        ds_names = [ds['name'] for ds in config['datasources']]
        assert 'Tempo' in ds_names, \
            "Tempo datasource should be configured"

    def test_loki_datasource_exists(self, grafana_datasources_path):
        """Test that Loki datasource is configured."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        ds_names = [ds['name'] for ds in config['datasources']]
        assert 'Loki' in ds_names, \
            "Loki datasource should be configured"

    def test_one_datasource_is_default(self, grafana_datasources_path):
        """Test that at least one datasource is set as default."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        default_datasources = [ds for ds in config['datasources'] 
                               if ds.get('isDefault', False)]
        assert len(default_datasources) >= 1, \
            "At least one datasource should be set as default"


class TestGrafanaPrometheusDatasource:
    """Test Prometheus datasource specific configuration."""

    def test_prometheus_type_correct(self, grafana_datasources_path):
        """Test that Prometheus datasource has correct type."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        prom_ds = [ds for ds in config['datasources'] if ds['name'] == 'Prometheus']
        assert len(prom_ds) > 0, "Prometheus datasource not found"
        
        assert prom_ds[0]['type'] == 'prometheus', \
            "Prometheus datasource type should be 'prometheus'"

    def test_prometheus_url_format(self, grafana_datasources_path):
        """Test that Prometheus URL is correctly formatted."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        prom_ds = [ds for ds in config['datasources'] if ds['name'] == 'Prometheus']
        if prom_ds:
            url = prom_ds[0]['url']
            # Should point to prometheus service
            assert 'prometheus' in url.lower(), \
                "Prometheus URL should reference prometheus service"


class TestGrafanaTempoDatasource:
    """Test Tempo datasource specific configuration."""

    def test_tempo_type_correct(self, grafana_datasources_path):
        """Test that Tempo datasource has correct type."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        tempo_ds = [ds for ds in config['datasources'] if ds['name'] == 'Tempo']
        assert len(tempo_ds) > 0, "Tempo datasource not found"
        
        assert tempo_ds[0]['type'] == 'tempo', \
            "Tempo datasource type should be 'tempo'"

    def test_tempo_url_format(self, grafana_datasources_path):
        """Test that Tempo URL is correctly formatted."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        tempo_ds = [ds for ds in config['datasources'] if ds['name'] == 'Tempo']
        if tempo_ds:
            url = tempo_ds[0]['url']
            # Should point to tempo service
            assert 'tempo' in url.lower(), \
                "Tempo URL should reference tempo service"


class TestGrafanaLokiDatasource:
    """Test Loki datasource specific configuration."""

    def test_loki_type_correct(self, grafana_datasources_path):
        """Test that Loki datasource has correct type."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        loki_ds = [ds for ds in config['datasources'] if ds['name'] == 'Loki']
        assert len(loki_ds) > 0, "Loki datasource not found"
        
        assert loki_ds[0]['type'] == 'loki', \
            "Loki datasource type should be 'loki'"

    def test_loki_url_format(self, grafana_datasources_path):
        """Test that Loki URL is correctly formatted."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        loki_ds = [ds for ds in config['datasources'] if ds['name'] == 'Loki']
        if loki_ds:
            url = loki_ds[0]['url']
            # Should point to loki service
            assert 'loki' in url.lower(), \
                "Loki URL should reference loki service"


class TestGrafanaJsonDataConfiguration:
    """Test jsonData configuration for datasources."""

    def test_jsondata_is_dict_if_present(self, grafana_datasources_path):
        """Test that jsonData is a dictionary if present."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for ds in config['datasources']:
            name = ds.get('name', 'unknown')
            if 'jsonData' in ds:
                assert isinstance(ds['jsonData'], dict), \
                    f"Datasource '{name}' jsonData should be a dictionary"


class TestGrafanaConfigValidation:
    """Integration tests for complete Grafana configuration validation."""

    def test_complete_config_is_valid(self, grafana_datasources_path):
        """Test that the complete configuration is valid."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Should have apiVersion
        assert 'apiVersion' in config
        assert config['apiVersion'] == 1
        
        # Should have datasources
        assert 'datasources' in config
        assert len(config['datasources']) > 0
        
        # All datasources should be valid
        for ds in config['datasources']:
            assert 'name' in ds
            assert 'type' in ds
            assert 'url' in ds

    def test_no_duplicate_datasource_names(self, grafana_datasources_path):
        """Test that there are no duplicate datasource names."""
        with open(grafana_datasources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        ds_names = [ds['name'] for ds in config['datasources']]
        unique_names = set(ds_names)
        
        assert len(ds_names) == len(unique_names), \
            "Datasource names should be unique"
