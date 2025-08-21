"""MQTT output module for forwarding raw UDP packets."""

import logging
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt
from .base import OutputBase

logger = logging.getLogger(__name__)


class MQTTOutput(OutputBase):
    """Output module for sending raw UDP packets to MQTT."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MQTT output with configuration.
        
        Args:
            config: Configuration containing:
                - host: MQTT broker host
                - port: MQTT broker port (default: 1883)
                - topic_prefix: Base topic prefix (default: loxone)
                - enabled: Whether this output is enabled
                - client_id: MQTT client ID (default: loxprox)
                - keepalive: MQTT keepalive interval (default: 60)
        """
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 1883)
        self.topic_prefix = config.get('topic_prefix', 'loxone')
        self.client_id = config.get('client_id', 'loxprox')
        self.keepalive = config.get('keepalive', 60)
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to the MQTT broker.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = mqtt.Client(client_id=self.client_id)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            # Connect to broker
            self.client.connect(self.host, self.port, self.keepalive)
            self.client.loop_start()
            
            # Wait briefly for connection
            import time
            time.sleep(0.5)
            
            if self.connected:
                logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
                return True
            else:
                logger.error(f"Failed to connect to MQTT broker at {self.host}:{self.port}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response from the server."""
        if rc == 0:
            self.connected = True
            logger.info("MQTT connection established")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the server."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection: {rc}")
    
    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
            self.connected = False
            logger.info("Disconnected from MQTT broker")
            
    def send(self, data: Dict[str, Any]) -> bool:
        """Send raw UDP packet to MQTT topic based on device type.
        
        The raw packet is published to topics like:
        - loxone/type/hue for ph devices  
        - loxone/type/powermeter for pm devices
        
        Args:
            data: Dictionary containing:
                - device_type: Type of device (ph, pm, etc.)
                - raw_packet: Original UDP packet string (if available)
                - timestamp: Packet timestamp
                - source: Packet source  
                - device_id: Device identifier
                
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client or not self.connected:
            logger.error("MQTT client not connected")
            return False
            
        try:
            # Get the raw packet - it should be preserved in the data
            raw_packet = None
            
            # Look for raw packet in various places it might be stored
            if 'raw_packet' in data:
                raw_packet = data['raw_packet']
            elif '_raw_packet' in data:
                raw_packet = data['_raw_packet']
            else:
                # Reconstruct from parts if raw packet not preserved
                timestamp = data.get('timestamp', '')
                source = data.get('source', '')
                device_type = data.get('device_type', '')
                device_id = data.get('device_id', '')
                
                # Try to reconstruct the data portion
                if 'raw_data_string' in data:
                    data_string = data['raw_data_string']
                elif 'raw_value' in data:
                    data_string = f"{device_type}{device_id}.{data['raw_value']}"
                else:
                    # Can't reconstruct, skip
                    logger.warning("No raw packet data available to send to MQTT")
                    return False
                    
                raw_packet = f"{timestamp};{source};{data_string}"
            
            # Determine topic based on device type
            device_type = data.get('device_type', 'unknown')
            
            # Map device types to topic names
            type_map = {
                'ph': 'hue',
                'pm': 'powermeter',
            }
            topic_name = type_map.get(device_type, device_type)
            
            # Build full topic
            topic = f"{self.topic_prefix}/type/{topic_name}"
            
            # Publish raw packet to MQTT
            result = self.client.publish(topic, raw_packet, qos=0, retain=False)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}: {raw_packet}")
                return True
            else:
                logger.error(f"Failed to publish to MQTT: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending to MQTT: {e}")
            return False