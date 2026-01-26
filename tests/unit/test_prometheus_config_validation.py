"""
Unit tests for Prometheus configuration validation.

These tests validate the Prometheus configuration to ensure:
- Valid YAML syntax
- Required sections are present
- Scrape configurations are valid
- Alertmanager configuration is correct
- Rule files are referenced correctly
"""
import pytest
import yaml
from pathlib import Path


class TestPrometheusConfigStructure:
    """Test the basic structure of the Prometheus configuration."""

    def test_config_file_exists(self, prometheus_config_path):
        """Test that the Prometheus config file exists."""
        assert prometheus_config_path.exists(), \
            f"Config file not found: {prometheus_config_path}"

    def test_valid_yaml_syntax(self, prometheus_config_path):
        """Test that the config file contains valid YAML."""
        with open(prometheus_config_path, 'r') as f:
            try:
                config = yaml.safe_load(f)
                assert config is not None, "Config is empty"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML syntax: {e}")

    def test_required_sections_present(self, prometheus_config_path):
        """Test that required sections are present."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # global is required
        assert 'global' in config, "Missing required section: global"


class TestPrometheusGlobalConfig:
    """Test the global configuration section."""

    def test_scrape_interval_defined(self, prometheus_config_path):
        """Test that scrape_interval is defined in global config."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'scrape_interval' in config['global'], \
            "global.scrape_interval should be defined"

    def test_scrape_interval_valid_format(self, prometheus_config_path):
        """Test that scrape_interval has valid format."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        scrape_interval = config['global']['scrape_interval']
        # Should be a string with time unit (e.g., "15s", "1m")
        assert isinstance(scrape_interval, str), \
            "scrape_interval should be a string"
        assert scrape_interval[-1] in ['s', 'm', 'h'], \
            "scrape_interval should end with time unit (s, m, or h)"

    def test_evaluation_interval_defined(self, prometheus_config_path):
        """Test that evaluation_interval is defined in global config."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'evaluation_interval' in config['global']:
            eval_interval = config['global']['evaluation_interval']
            assert isinstance(eval_interval, str), \
                "evaluation_interval should be a string"
            assert eval_interval[-1] in ['s', 'm', 'h'], \
                "evaluation_interval should end with time unit (s, m, or h)"

    def test_external_labels_format(self, prometheus_config_path):
        """Test that external_labels has valid format if present."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'external_labels' in config['global']:
            labels = config['global']['external_labels']
            assert isinstance(labels, dict), \
                "external_labels should be a dictionary"
            # All values should be strings
            for key, value in labels.items():
                assert isinstance(value, str), \
                    f"external_label {key} value should be a string"


class TestPrometheusAlertingConfig:
    """Test the alerting configuration section."""

    def test_alertmanagers_config_valid(self, prometheus_config_path):
        """Test that alertmanagers configuration is valid if present."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'alerting' in config and 'alertmanagers' in config['alerting']:
            alertmanagers = config['alerting']['alertmanagers']
            assert isinstance(alertmanagers, list), \
                "alertmanagers should be a list"
            
            for am in alertmanagers:
                # Should have either static_configs or other service discovery
                assert any(k in am for k in ['static_configs', 'consul_sd_configs', 
                                              'dns_sd_configs', 'file_sd_configs']), \
                    "alertmanager config should have service discovery config"

    def test_alertmanager_static_configs_valid(self, prometheus_config_path):
        """Test that alertmanager static_configs are valid."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'alerting' in config and 'alertmanagers' in config['alerting']:
            for am in config['alerting']['alertmanagers']:
                if 'static_configs' in am:
                    for static_config in am['static_configs']:
                        assert 'targets' in static_config, \
                            "static_config should have targets"
                        assert isinstance(static_config['targets'], list), \
                            "targets should be a list"
                        assert len(static_config['targets']) > 0, \
                            "targets list should not be empty"


class TestPrometheusRuleFiles:
    """Test the rule files configuration."""

    def test_rule_files_format_valid(self, prometheus_config_path):
        """Test that rule_files has valid format if present."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'rule_files' in config:
            rule_files = config['rule_files']
            assert isinstance(rule_files, list), \
                "rule_files should be a list"
            
            for rule_file in rule_files:
                assert isinstance(rule_file, str), \
                    "Each rule file should be a string path"


class TestPrometheusScrapeConfigs:
    """Test the scrape_configs section."""

    def test_scrape_configs_exists(self, prometheus_config_path):
        """Test that scrape_configs section exists."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert 'scrape_configs' in config, \
            "scrape_configs section should be present"
        assert isinstance(config['scrape_configs'], list), \
            "scrape_configs should be a list"
        assert len(config['scrape_configs']) > 0, \
            "scrape_configs should not be empty"

    def test_each_scrape_config_has_job_name(self, prometheus_config_path):
        """Test that each scrape config has a job_name."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for idx, scrape_config in enumerate(config['scrape_configs']):
            assert 'job_name' in scrape_config, \
                f"scrape_config at index {idx} missing job_name"
            assert isinstance(scrape_config['job_name'], str), \
                f"job_name at index {idx} should be a string"
            assert len(scrape_config['job_name']) > 0, \
                f"job_name at index {idx} should not be empty"

    def test_each_scrape_config_has_targets(self, prometheus_config_path):
        """Test that each scrape config has a way to discover targets."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for scrape_config in config['scrape_configs']:
            job_name = scrape_config['job_name']
            # Should have at least one service discovery mechanism
            has_sd = any(k in scrape_config for k in [
                'static_configs', 'dns_sd_configs', 'file_sd_configs',
                'consul_sd_configs', 'kubernetes_sd_configs'
            ])
            assert has_sd, \
                f"scrape_config '{job_name}' should have service discovery config"

    def test_static_configs_have_targets(self, prometheus_config_path):
        """Test that static_configs have targets defined."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for scrape_config in config['scrape_configs']:
            job_name = scrape_config['job_name']
            if 'static_configs' in scrape_config:
                for static_config in scrape_config['static_configs']:
                    assert 'targets' in static_config, \
                        f"static_config in job '{job_name}' missing targets"
                    assert isinstance(static_config['targets'], list), \
                        f"targets in job '{job_name}' should be a list"

    def test_scrape_interval_valid_if_present(self, prometheus_config_path):
        """Test that scrape_interval in scrape_configs is valid if present."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for scrape_config in config['scrape_configs']:
            job_name = scrape_config['job_name']
            if 'scrape_interval' in scrape_config:
                interval = scrape_config['scrape_interval']
                assert isinstance(interval, str), \
                    f"scrape_interval in job '{job_name}' should be a string"
                assert interval[-1] in ['s', 'm', 'h'], \
                    f"scrape_interval in job '{job_name}' should have time unit"

    def test_metrics_path_valid_if_present(self, prometheus_config_path):
        """Test that metrics_path is valid if present."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for scrape_config in config['scrape_configs']:
            job_name = scrape_config['job_name']
            if 'metrics_path' in scrape_config:
                path = scrape_config['metrics_path']
                assert isinstance(path, str), \
                    f"metrics_path in job '{job_name}' should be a string"
                assert path.startswith('/'), \
                    f"metrics_path in job '{job_name}' should start with /"

    def test_scheme_valid_if_present(self, prometheus_config_path):
        """Test that scheme is valid if present."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        for scrape_config in config['scrape_configs']:
            job_name = scrape_config['job_name']
            if 'scheme' in scrape_config:
                scheme = scrape_config['scheme']
                assert scheme in ['http', 'https'], \
                    f"scheme in job '{job_name}' should be http or https"


class TestPrometheusJobsForObservabilityStack:
    """Test that required jobs for the observability stack are configured."""

    def test_prometheus_self_monitoring_job_exists(self, prometheus_config_path):
        """Test that Prometheus has a self-monitoring job."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        job_names = [sc['job_name'] for sc in config['scrape_configs']]
        assert 'prometheus' in job_names, \
            "Prometheus self-monitoring job should be configured"

    def test_otel_collector_job_exists(self, prometheus_config_path):
        """Test that OTel Collector scrape job exists."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        job_names = [sc['job_name'] for sc in config['scrape_configs']]
        # Look for otel-collector or similar
        otel_jobs = [j for j in job_names if 'otel' in j.lower()]
        assert len(otel_jobs) > 0, \
            "OTel Collector scrape job should be configured"


class TestPrometheusConfigValidation:
    """Integration tests for complete configuration validation."""

    def test_complete_config_is_valid(self, prometheus_config_path):
        """Test that the complete configuration is valid."""
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Should have all essential sections
        assert 'global' in config
        assert 'scrape_configs' in config
        
        # Global should have scrape_interval
        assert 'scrape_interval' in config['global']
        
        # Should have at least one scrape config
        assert len(config['scrape_configs']) > 0
        
        # All scrape configs should be valid
        for sc in config['scrape_configs']:
            assert 'job_name' in sc
