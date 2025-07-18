import json
import re
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class InputParser:
    """Parse incoming UDP packets from Loxone."""
    
    def __init__(self):
        """Initialize the input parser."""
        # Pattern to extract device type prefix and id from legacy format
        self.device_pattern = re.compile(r'^([a-z]+)(\d+)$')
        
    def parse_packet(self, packet: str) -> Optional[Dict[str, Any]]:
        """Parse a complete UDP packet.
        
        Args:
            packet: Raw UDP packet string, e.g.:
                    "2025-07-18 12:03:06;udplight;ph9.200453430"
                    
        Returns:
            Parsed data dict or None if invalid
        """
        try:
            # Split packet into components
            parts = packet.strip().split(';')
            if len(parts) < 3:
                logger.warning(f"Invalid packet format (not enough parts): {packet}")
                return None
                
            timestamp = parts[0]
            source = parts[1]
            data = parts[2]
            
            # Parse the data portion
            parsed_data = self._parse_data(data)
            if not parsed_data:
                return None
                
            # Add packet metadata
            parsed_data['timestamp'] = timestamp
            parsed_data['source'] = source
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing packet '{packet}': {e}")
            return None
    
    def _parse_data(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse the data portion of a packet.
        
        Args:
            data: Data string, either legacy format or JSON
            
        Returns:
            Parsed data with device_type, device_id, and value
        """
        # Check if it's JSON format
        if data.strip().startswith('{'):
            return self._parse_json_data(data)
        else:
            return self._parse_legacy_data(data)
    
    def _parse_json_data(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse JSON formatted data.
        
        Args:
            data: JSON string
            
        Returns:
            Parsed data dict
        """
        try:
            json_data = json.loads(data)
            
            # Validate required fields
            if 'type' not in json_data or 'id' not in json_data:
                logger.warning(f"JSON data missing required fields: {data}")
                return None
                
            # Transform to standard format
            result = {
                'device_type': json_data['type'],
                'device_id': str(json_data['id']),
                'value': json_data.get('value', {})
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON data: {e}")
            return None
    
    def _parse_legacy_data(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse legacy format data (e.g., ph9.200453430).
        
        Args:
            data: Legacy format string
            
        Returns:
            Parsed data dict
        """
        try:
            # Split by dot to separate device and payload
            parts = data.split('.')
            if len(parts) != 2:
                logger.warning(f"Invalid legacy format (expected device.payload): {data}")
                return None
                
            device_str, payload_str = parts
            
            # Extract device type and id
            match = self.device_pattern.match(device_str)
            if not match:
                logger.warning(f"Invalid device format: {device_str}")
                return None
                
            device_type = match.group(1)
            device_id = match.group(2)
            
            # Check if payload is key:value format (for power meters)
            if ':' in payload_str and device_type == 'pm':
                value = self._parse_power_meter_payload(payload_str)
                if value is None:
                    return None
            else:
                # Parse payload as integer (for lights)
                try:
                    payload = int(payload_str)
                except ValueError:
                    logger.warning(f"Invalid payload (not a number): {payload_str}")
                    return None
                
                # Convert payload based on device type
                value = self._convert_payload(device_type, payload)
                if value is None:
                    return None
                
            return {
                'device_type': device_type,
                'device_id': device_id,
                'value': value
            }
            
        except Exception as e:
            logger.error(f"Error parsing legacy data '{data}': {e}")
            return None
    
    def _convert_payload(self, device_type: str, payload: int) -> Optional[Dict[str, Any]]:
        """Convert numeric payload to structured value based on device type.
        
        Args:
            device_type: Device type prefix (e.g., 'ph', 'pm')
            payload: Numeric payload value
            
        Returns:
            Converted value dict
        """
        if device_type == 'ph':
            # Philips Hue light payload
            if 0 <= payload <= 100100100:
                # RGB format: BBBGGGRRR
                return {
                    'mode': 'rgb',
                    'b': int((payload // 1000000) * 255 / 100),
                    'g': int(((payload // 1000) % 1000) * 255 / 100),
                    'r': int((payload % 1000) * 255 / 100)
                }
            elif 200002700 <= payload <= 201006500:
                # CCT format: 2BBBTTTT (brightness + color temp)
                return {
                    'mode': 'cct',
                    'brightness': (payload // 10000) % 1000,
                    'kelvin': payload % 10000
                }
            else:
                logger.warning(f"Unknown Hue payload range: {payload}")
                return None
                
        elif device_type == 'pm':
            # Power meter - format TBD
            # For now, return raw value
            return {
                'raw_value': payload
            }
            
        else:
            logger.warning(f"Unknown device type: {device_type}")
            return None
    
    def _parse_power_meter_payload(self, payload_str: str) -> Optional[Dict[str, Any]]:
        """Parse power meter key:value payload.
        
        Args:
            payload_str: String like "pf:5.220,mrc:34169,mrd:0,v1:241.0,v2:240.0,v3:238.0,i1:15.3,i2:5.1,i3:2.1"
            
        Returns:
            Dict with parsed power meter values
        """
        try:
            result = {}
            
            # Split by comma to get key:value pairs
            pairs = payload_str.split(',')
            
            for pair in pairs:
                if ':' not in pair:
                    logger.warning(f"Invalid key:value pair in power meter data: {pair}")
                    continue
                    
                key, value_str = pair.split(':', 1)
                
                try:
                    # Parse as float
                    value = float(value_str)
                    result[key] = value
                except ValueError:
                    logger.warning(f"Invalid numeric value for key {key}: {value_str}")
                    continue
            
            # Validate we have at least some expected fields
            if not result or 'pf' not in result:
                logger.warning(f"Power meter data missing required fields: {result}")
                return None
                
            return result
            
        except Exception as e:
            logger.error(f"Error parsing power meter payload '{payload_str}': {e}")
            return None