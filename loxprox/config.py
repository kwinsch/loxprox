import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_config(config_file_path: str) -> Dict[str, Any]:
    """Load and validate configuration from YAML file.
    
    Args:
        config_file_path: Path to the YAML configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        ValueError: If configuration is invalid
    """
    try:
        with open(config_file_path, "r") as file:
            config = yaml.safe_load(file)
            
        # Validate and provide defaults
        config = validate_config(config)
        return config
        
    except Exception as e:
        logger.error(f"Failed to load config from {config_file_path}: {e}")
        raise


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration and provide defaults.
    
    Args:
        config: Raw configuration dictionary
        
    Returns:
        Validated configuration with defaults
    """
    # Ensure main sections exist
    if 'inputs' not in config:
        config['inputs'] = {}
        
    if 'outputs' not in config:
        config['outputs'] = {}
        
    if 'routing' not in config:
        config['routing'] = {}
    
    # Validate inputs section
    if 'udp' not in config['inputs']:
        config['inputs']['udp'] = {}
        
    udp_config = config['inputs']['udp']
    if 'ip' not in udp_config:
        udp_config['ip'] = '0.0.0.0'
    if 'ports' not in udp_config:
        udp_config['ports'] = [52001]
    
    # Migrate old config format if present
    if 'udp_server' in config:
        logger.info("Migrating old config format")
        udp_config['ip'] = config['udp_server'].get('ip', '0.0.0.0')
        udp_config['ports'] = config['udp_server'].get('ports', [52001])
        del config['udp_server']
        
    if 'hue_bridge' in config:
        logger.info("Migrating old Hue config format")
        if 'hue' not in config['outputs']:
            config['outputs']['hue'] = {}
        config['outputs']['hue']['bridge_ip'] = config['hue_bridge'].get('ip')
        config['outputs']['hue']['username'] = config['hue_bridge'].get('username')
        config['outputs']['hue']['enabled'] = True
        del config['hue_bridge']
        
        # Add default routing for ph devices
        if 'ph' not in config['routing']:
            config['routing']['ph'] = {'outputs': ['hue']}
    
    # Validate outputs
    for output_name, output_config in config['outputs'].items():
        if not isinstance(output_config, dict):
            config['outputs'][output_name] = {'enabled': False}
        elif 'enabled' not in output_config:
            output_config['enabled'] = True
    
    # Validate routing
    for device_type, routing_config in config['routing'].items():
        if not isinstance(routing_config, dict):
            config['routing'][device_type] = {'outputs': []}
        elif 'outputs' not in routing_config:
            routing_config['outputs'] = []
        elif not isinstance(routing_config['outputs'], list):
            routing_config['outputs'] = [routing_config['outputs']]
    
    return config