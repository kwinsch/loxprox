import pytest
import tempfile
import yaml
from loxprox.config import load_config, validate_config


class TestConfig:
    """Test configuration loading and validation."""
    
    def test_validate_minimal_config(self):
        """Test validation of minimal configuration."""
        config = {}
        validated = validate_config(config)
        
        # Check defaults are added
        assert 'inputs' in validated
        assert 'outputs' in validated
        assert 'routing' in validated
        assert validated['inputs']['udp']['ip'] == '0.0.0.0'
        assert validated['inputs']['udp']['ports'] == [52001]
        
    def test_migrate_old_config_format(self):
        """Test migration from old to new config format."""
        old_config = {
            'udp_server': {
                'ip': '0.0.0.0',
                'ports': [52001, 12345]
            },
            'hue_bridge': {
                'ip': '192.168.1.11',
                'username': 'test-user'
            }
        }
        
        validated = validate_config(old_config)
        
        # Check migration
        assert 'udp_server' not in validated
        assert 'hue_bridge' not in validated
        assert validated['inputs']['udp']['ip'] == '0.0.0.0'
        assert validated['inputs']['udp']['ports'] == [52001, 12345]
        assert validated['outputs']['hue']['bridge_ip'] == '192.168.1.11'
        assert validated['outputs']['hue']['username'] == 'test-user'
        assert validated['outputs']['hue']['enabled'] is True
        assert validated['routing']['ph']['outputs'] == ['hue']
        
    def test_validate_new_config_format(self):
        """Test validation of new config format."""
        new_config = {
            'inputs': {
                'udp': {
                    'ip': '127.0.0.1',
                    'ports': [52001]
                }
            },
            'outputs': {
                'hue': {
                    'enabled': True,
                    'bridge_ip': '192.168.24.103',
                    'username': 'test-user'
                },
                'telegraf': {
                    'enabled': True,
                    'host': '192.168.23.7',
                    'port': 8094
                }
            },
            'routing': {
                'ph': {
                    'outputs': ['hue', 'telegraf']
                },
                'pm': {
                    'outputs': ['telegraf']
                }
            }
        }
        
        validated = validate_config(new_config)
        
        # Check everything is preserved
        assert validated['inputs']['udp']['ip'] == '127.0.0.1'
        assert validated['outputs']['hue']['enabled'] is True
        assert validated['outputs']['telegraf']['enabled'] is True
        assert validated['routing']['ph']['outputs'] == ['hue', 'telegraf']
        assert validated['routing']['pm']['outputs'] == ['telegraf']
        
    def test_output_enabled_defaults(self):
        """Test that outputs default to enabled."""
        config = {
            'outputs': {
                'hue': {
                    'bridge_ip': '192.168.1.1'
                },
                'telegraf': {
                    'enabled': False,
                    'host': '192.168.1.2'
                }
            }
        }
        
        validated = validate_config(config)
        
        assert validated['outputs']['hue']['enabled'] is True  # Default
        assert validated['outputs']['telegraf']['enabled'] is False  # Explicit
        
    def test_routing_normalization(self):
        """Test routing configuration normalization."""
        config = {
            'routing': {
                'ph': {
                    'outputs': 'hue'  # Single string instead of list
                },
                'pm': ['telegraf'],  # Direct list instead of dict
                'xx': 'invalid'  # Invalid format
            }
        }
        
        validated = validate_config(config)
        
        assert validated['routing']['ph']['outputs'] == ['hue']  # Normalized to list
        assert validated['routing']['pm']['outputs'] == []  # Invalid format cleared
        assert validated['routing']['xx']['outputs'] == []  # Invalid format cleared
        
    def test_load_config_from_file(self):
        """Test loading configuration from file."""
        config_data = {
            'inputs': {
                'udp': {
                    'ports': [52001]
                }
            },
            'outputs': {
                'hue': {
                    'bridge_ip': '192.168.1.1'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
            
        try:
            loaded = load_config(config_path)
            assert loaded['inputs']['udp']['ports'] == [52001]
            assert loaded['outputs']['hue']['bridge_ip'] == '192.168.1.1'
        finally:
            import os
            os.unlink(config_path)