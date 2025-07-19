import socket
import time
from typing import Dict, Any, Optional
import logging
from .base import OutputBase

logger = logging.getLogger(__name__)


class TelegrafOutput(OutputBase):
    """Output module for sending metrics to Telegraf."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Telegraf output with configuration.
        
        Args:
            config: Configuration containing:
                - host: Telegraf host (default: 192.168.23.7)
                - port: Telegraf UDP port (default: 8094)
                - enabled: Whether this output is enabled
        """
        super().__init__(config)
        self.host = config.get('host', '192.168.23.7')
        self.port = config.get('port', 8094)
        self.socket: Optional[socket.socket] = None
        
    def connect(self) -> bool:
        """Create UDP socket for sending to Telegraf.
        
        Returns:
            bool: True if socket created successfully
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            logger.info(f"Created UDP socket for Telegraf at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to create UDP socket: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close the UDP socket."""
        if self.socket:
            self.socket.close()
            self.socket = None
            
    def send(self, data: Dict[str, Any]) -> bool:
        """Send metrics to Telegraf in InfluxDB line protocol format.
        
        Args:
            data: Dictionary containing device data
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.socket:
            logger.error("Socket not created")
            return False
            
        try:
            line_protocol = self._format_line_protocol(data)
            if not line_protocol:
                return False
                
            self.socket.sendto(line_protocol.encode('utf-8'), (self.host, self.port))
            logger.debug(f"Sent to Telegraf: {line_protocol}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending to Telegraf: {e}")
            return False
    
    def _format_line_protocol(self, data: Dict[str, Any]) -> Optional[str]:
        """Format data as InfluxDB line protocol.
        
        Args:
            data: Device data dictionary
            
        Returns:
            Formatted line protocol string or None if invalid data
        """
        try:
            device_type = data['device_type']
            device_id = data['device_id']
            value = data['value']
            timestamp = data.get('timestamp')
            
            # Always use current server time in UTC
            # Ignore source timestamp to avoid timezone issues
            ts_ns = int(time.time() * 1e9)
            
            # Build measurement name and tags
            measurement = "loxone"
            tags = [
                f"device_type={device_type}",
                f"device_id={device_id}",
                f"source={data.get('source', 'unknown')}"
            ]
            
            # Build fields based on device type
            fields = []
            
            if device_type == 'ph':  # Philips Hue lights
                mode = value.get('mode')
                if mode == 'rgb':
                    fields.extend([
                        f"r={value.get('r', 0)}i",
                        f"g={value.get('g', 0)}i",
                        f"b={value.get('b', 0)}i",
                        f"brightness={max(value.get('r', 0), value.get('g', 0), value.get('b', 0))}i"
                    ])
                elif mode == 'cct':
                    fields.extend([
                        f"brightness={value.get('brightness', 0)}i",
                        f"kelvin={value.get('kelvin', 3000)}i"
                    ])
                fields.append(f'mode="{mode}"')
                
            elif device_type == 'pm':  # Power meters
                # Current power in kW (signed)
                if 'pf' in value:
                    fields.append(f"power_kw={value['pf']}")
                # Energy meters
                if 'mrc' in value:
                    fields.append(f"energy_consumed_kwh={value['mrc']}")
                if 'mrd' in value:
                    fields.append(f"energy_delivered_kwh={value['mrd']}")
                # Phase voltages
                if 'v1' in value:
                    fields.append(f"voltage_l1={value['v1']}")
                if 'v2' in value:
                    fields.append(f"voltage_l2={value['v2']}")
                if 'v3' in value:
                    fields.append(f"voltage_l3={value['v3']}")
                # Phase currents
                if 'i1' in value:
                    fields.append(f"current_l1={value['i1']}")
                if 'i2' in value:
                    fields.append(f"current_l2={value['i2']}")
                if 'i3' in value:
                    fields.append(f"current_l3={value['i3']}")
                    
            else:
                # Generic handling for unknown types
                for k, v in value.items():
                    if isinstance(v, (int, float)):
                        fields.append(f"{k}={v}")
                    else:
                        fields.append(f'{k}="{v}"')
            
            if not fields:
                logger.warning(f"No fields to send for device type {device_type}")
                return None
                
            # Format: measurement,tag1=value1,tag2=value2 field1=value1,field2=value2 timestamp
            line = f"{measurement},{','.join(tags)} {','.join(fields)} {ts_ns}"
            return line
            
        except Exception as e:
            logger.error(f"Error formatting line protocol: {e}")
            return None