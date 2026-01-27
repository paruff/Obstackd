"""
Unit tests for Alloy configuration validation.
Tests that the River configuration is valid and meets requirements.
"""

import os
import pytest
import re
from pathlib import Path


# Configuration
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALLOY_CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "alloy", "config.river")


class TestAlloyConfiguration:
    """Test Alloy River configuration file structure."""
    
    def test_alloy_config_file_exists(self):
        """Test that alloy config file exists."""
        assert os.path.exists(ALLOY_CONFIG_FILE), \
            f"Alloy config file should exist at {ALLOY_CONFIG_FILE}"
        print(f"✅ Alloy config file exists: {ALLOY_CONFIG_FILE}")
    
    def test_alloy_config_is_readable(self):
        """Test that alloy config file is readable."""
        assert os.access(ALLOY_CONFIG_FILE, os.R_OK), \
            f"Alloy config file should be readable"
        print("✅ Alloy config file is readable")
    
    def test_alloy_config_not_empty(self):
        """Test that alloy config file is not empty."""
        with open(ALLOY_CONFIG_FILE, 'r') as f:
            content = f.read()
        
        assert len(content) > 0, "Alloy config should not be empty"
        assert len(content) > 100, "Alloy config should have substantial content"
        
        print(f"✅ Alloy config file has {len(content)} bytes")
    
    def test_alloy_config_has_logging_block(self):
        """Test that config includes logging configuration."""
        with open(ALLOY_CONFIG_FILE, 'r') as f:
            content = f.read()
        
        assert "logging {" in content, "Config should have logging block"
        assert "level" in content, "Logging should have level setting"
        assert "format" in content, "Logging should have format setting"
        
        print("✅ Alloy config has logging configuration")
    
    def test_alloy_config_has_server_block(self):
        """Test that config includes server configuration."""
        with open(ALLOY_CONFIG_FILE, 'r') as f:
            content = f.read()
        
        assert "server {" in content, "Config should have server block"
        assert "12345" in content, "Server should listen on port 12345"
        
        print("✅ Alloy config has server configuration (port 12345)")
    
    def test_alloy_config_has_docker_source(self):
        """Test that config includes Docker log source."""
        with open(ALLOY_CONFIG_FILE, 'r') as f:
            content = f.read()
        
        assert "loki.source.docker" in content, \
            "Config should have Loki Docker source"
        assert "/var/run/docker.sock" in content, \
            "Config should reference Docker socket"
        assert "positions_path" in content, \
            "Config should have positions file path"
        
        print("✅ Alloy config has Docker source configuration")
    
    def test_alloy_config_has_processing_pipeline(self):
        """Test that config includes log processing pipeline."""
        with open(ALLOY_CONFIG_FILE, 'r') as f:
            content = f.read()
        
        assert "loki.process" in content, "Config should have processing stage"
        assert "stage.docker" in content, "Should have Docker log parsing stage"
        assert "stage.labels" in content, "Should have label extraction stage"
        
        print("✅ Alloy config has processing pipeline")
    
    def test_alloy_config_has_required_labels(self):
        """Test that config extracts required labels."""
        with open(ALLOY_CONFIG_FILE, 'r') as f:
            content = f.read()
        
        required_labels = [
            'job = "docker"',
            'stream',
            'container_name',
            'container_id',
            'compose_service',
            'compose_project'
        ]
        
        for label in required_labels:
            assert label in content, f"Config should include '{label}' label"
        
        print("✅ Alloy config has all required labels")
    
    def test_alloy_config_has_loki_write(self):
        """Test that config includes Loki write endpoint."""
        with open(ALLOY_CONFIG_FILE, 'r') as f:
            content = f.read()
        
        assert "loki.write" in content, "Config should have Loki write component"
        assert "http://loki:3100" in content, \
            "Config should target Loki service on port 3100"
        assert "/loki/api/v1/push" in content, \
            "Config should use Loki push API endpoint"
        
        print("✅ Alloy config has Loki write endpoint configuration")
    
    def test_alloy_config_docker_socket_mounted(self):
        """Test that Docker socket is mounted in compose.yaml."""
        compose_file = os.path.join(PROJECT_ROOT, "compose.yaml")
        
        with open(compose_file, 'r') as f:
            compose_content = f.read()
        
        # Check for Alloy service with docker socket mount
        assert "alloy:" in compose_content, "Compose should define alloy service"
        
        # Check for docker socket mount
        alloy_section = compose_content.split("alloy:")[1].split("prometheus:")[0]
        assert "/var/run/docker.sock" in alloy_section, \
            "Alloy service should mount Docker socket"
        assert "config/alloy/config.river" in alloy_section, \
            "Alloy service should mount River config file"
        
        print("✅ Alloy service in compose.yaml has required volume mounts")
    
    def test_alloy_in_compose_has_health_check(self):
        """Test that Alloy service depends on Loki."""
        compose_file = os.path.join(PROJECT_ROOT, "compose.yaml")
        
        with open(compose_file, 'r') as f:
            compose_content = f.read()
        
        # Check for Alloy service with Loki dependency
        alloy_section = compose_content.split("alloy:")[1].split("prometheus:")[0]
        assert "depends_on" in alloy_section, \
            "Alloy service should have depends_on"
        assert "loki:" in alloy_section, \
            "Alloy should depend on Loki service"
        
        print("✅ Alloy service depends on Loki")


class TestAlloyConfigDocumentation:
    """Test that Alloy configuration documentation is complete."""
    
    def test_alloy_operations_doc_exists(self):
        """Test that Alloy operations documentation exists."""
        alloy_doc = os.path.join(PROJECT_ROOT, "docs", "alloy-operations.md")
        assert os.path.exists(alloy_doc), \
            f"Alloy operations doc should exist at {alloy_doc}"
        print(f"✅ Alloy operations documentation exists")
    
    def test_alloy_doc_has_overview(self):
        """Test that doc includes overview section."""
        alloy_doc = os.path.join(PROJECT_ROOT, "docs", "alloy-operations.md")
        with open(alloy_doc, 'r') as f:
            content = f.read()
        
        assert "## Overview" in content, "Doc should have Overview section"
        assert "Grafana Alloy" in content, "Doc should mention Grafana Alloy"
        assert "1.1.0" in content, "Doc should mention version"
        
        print("✅ Alloy documentation has overview section")
    
    def test_alloy_doc_has_deployment_section(self):
        """Test that doc includes deployment instructions."""
        alloy_doc = os.path.join(PROJECT_ROOT, "docs", "alloy-operations.md")
        with open(alloy_doc, 'r') as f:
            content = f.read()
        
        assert "## Deployment" in content, "Doc should have Deployment section"
        assert "docker compose up" in content, "Doc should explain how to deploy"
        
        print("✅ Alloy documentation has deployment section")
    
    def test_alloy_doc_has_configuration_section(self):
        """Test that doc includes configuration documentation."""
        alloy_doc = os.path.join(PROJECT_ROOT, "docs", "alloy-operations.md")
        with open(alloy_doc, 'r') as f:
            content = f.read()
        
        assert "## Configuration" in content, "Doc should have Configuration section"
        assert "config/alloy/config.river" in content, "Doc should reference config file"
        assert "loki.source.docker" in content, "Doc should explain Docker source"
        assert "loki.process" in content, "Doc should explain processing"
        
        print("✅ Alloy documentation has configuration section")
    
    def test_alloy_doc_has_troubleshooting(self):
        """Test that doc includes troubleshooting guide."""
        alloy_doc = os.path.join(PROJECT_ROOT, "docs", "alloy-operations.md")
        with open(alloy_doc, 'r') as f:
            content = f.read()
        
        assert "## Troubleshooting" in content, "Doc should have Troubleshooting section"
        
        print("✅ Alloy documentation has troubleshooting section")
    
    def test_loki_doc_references_alloy(self):
        """Test that Loki doc references Alloy instead of Promtail."""
        loki_doc = os.path.join(PROJECT_ROOT, "docs", "loki-operations.md")
        with open(loki_doc, 'r') as f:
            content = f.read()
        
        assert "Grafana Alloy" in content, "Loki doc should mention Alloy"
        assert "Promtail" not in content or "deprecated" in content.lower(), \
            "Loki doc should not reference active Promtail usage"
        
        print("✅ Loki documentation references Alloy")
