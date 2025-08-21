from typing import Dict, Any, Optional
import logging
from .base import HandlerBase

logger = logging.getLogger(__name__)


class LightHandler(HandlerBase):
    """Handler for Philips Hue light devices (ph prefix)."""
    
    def __init__(self):
        """Initialize light handler."""
        super().__init__('ph')
        
    def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process light data, ensuring it's in the correct format.
        
        Args:
            data: Parsed data containing device info and values
            
        Returns:
            Processed data with validated light parameters
        """
        if data.get('device_type') != self.device_type:
            return None
            
        try:
            # Data should already be mostly processed by the parser
            # Just validate and ensure correct structure
            value = data.get('value', {})
            mode = value.get('mode')
            
            if mode == 'rgb':
                # Validate RGB values
                r = max(0, min(255, value.get('r', 0)))
                g = max(0, min(255, value.get('g', 0)))
                b = max(0, min(255, value.get('b', 0)))
                
                value['r'] = r
                value['g'] = g
                value['b'] = b
                
                logger.debug(f"Light {data['device_id']}: RGB mode - R:{r} G:{g} B:{b}")
                
            elif mode == 'cct':
                # Validate CCT values
                brightness = max(0, min(100, value.get('brightness', 0)))
                kelvin = max(2700, min(6500, value.get('kelvin', 3000)))
                
                value['brightness'] = brightness
                value['kelvin'] = kelvin
                
                logger.debug(f"Light {data['device_id']}: CCT mode - {kelvin}K @ {brightness}%")
                
            else:
                logger.warning(f"Unknown light mode: {mode}")
                return None
                
            # Return validated data, preserving raw packet
            result = {
                'device_type': data['device_type'],
                'device_id': data['device_id'],
                'value': value,
                'timestamp': data.get('timestamp'),
                'source': data.get('source')
            }
            
            # Preserve raw packet data for MQTT forwarding
            if 'raw_packet' in data:
                result['raw_packet'] = data['raw_packet']
            if 'raw_data_string' in data:
                result['raw_data_string'] = data['raw_data_string']
                
            return result
            
        except Exception as e:
            logger.error(f"Error processing light data: {e}")
            return None