"""MQTT output module for forwarding raw UDP packets."""

import logging
import time
import threading
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
                - retry_initial_interval: Initial retry interval in seconds (default: 60)
                - retry_initial_attempts: Number of attempts before backoff (default: 15)
                - retry_long_interval: Long-term retry interval in seconds (default: 1800)
        """
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 1883)
        self.topic_prefix = config.get('topic_prefix', 'loxone')
        self.client_id = config.get('client_id', 'loxprox')
        self.keepalive = config.get('keepalive', 60)
        self.retry_initial_interval = config.get('retry_initial_interval', 60)  # 1 minute
        self.retry_initial_attempts = config.get('retry_initial_attempts', 15)  # 15 attempts
        self.retry_long_interval = config.get('retry_long_interval', 1800)  # 30 minutes

        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.reconnect_attempts = 0
        self.reconnect_thread: Optional[threading.Thread] = None
        self.stop_reconnect = threading.Event()
        self.reconnect_lock = threading.Lock()
        
    def connect(self) -> bool:
        """Connect to the MQTT broker.

        Returns:
            bool: True if connection successful, False otherwise
        """
        success = self._do_connect()
        if not success:
            self._start_reconnect_thread()
        return success

    def _do_connect(self) -> bool:
        """Internal method to perform actual connection (without starting threads).

        Returns:
            bool: True if connection successful, False otherwise
        """
        with self.reconnect_lock:
            try:
                # Clean up existing client if any
                if self.client:
                    try:
                        self.client.loop_stop()
                        self.client.disconnect()
                    except:
                        pass

                self.client = mqtt.Client(client_id=self.client_id)
                self.client.on_connect = self._on_connect
                self.client.on_disconnect = self._on_disconnect

                # Connect to broker
                self.client.connect(self.host, self.port, self.keepalive)
                self.client.loop_start()

                # Wait briefly for connection
                time.sleep(0.5)

                if self.connected:
                    logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
                    self.reconnect_attempts = 0  # Reset counter on success
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
            self.reconnect_attempts = 0
            logger.info("MQTT connection established")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the server."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection: {rc}")
            self._start_reconnect_thread()
    
    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        # Stop reconnection thread
        self.stop_reconnect.set()
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            self.reconnect_thread.join(timeout=2)

        # Disconnect MQTT client
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

    def _start_reconnect_thread(self) -> None:
        """Start the reconnection thread if not already running."""
        # Don't start if already running or if we're stopping
        if self.stop_reconnect.is_set():
            return

        # Don't start if already connected
        if self.connected:
            return

        # Only start if no thread is currently running
        if self.reconnect_thread is None or not self.reconnect_thread.is_alive():
            self.reconnect_thread = threading.Thread(
                target=self._reconnect_loop,
                daemon=True,
                name="mqtt-reconnect"
            )
            self.reconnect_thread.start()
            logger.info("Started MQTT reconnection thread")

    def _reconnect_loop(self) -> None:
        """Background thread that attempts to reconnect to MQTT broker."""
        while not self.stop_reconnect.is_set() and not self.connected:
            self.reconnect_attempts += 1

            # Determine retry interval based on attempt count
            if self.reconnect_attempts <= self.retry_initial_attempts:
                retry_interval = self.retry_initial_interval
                logger.info(
                    f"MQTT reconnection attempt {self.reconnect_attempts}/{self.retry_initial_attempts} "
                    f"(retrying every {retry_interval}s)"
                )
            else:
                retry_interval = self.retry_long_interval
                logger.info(
                    f"MQTT reconnection attempt {self.reconnect_attempts} "
                    f"(retrying every {retry_interval // 60}min)"
                )

            # Try to reconnect - use _do_connect to avoid thread recursion
            try:
                success = self._do_connect()
                if success:
                    logger.info("MQTT reconnection successful")
                    return
            except Exception as e:
                logger.error(f"MQTT reconnection failed: {e}")

            # Wait before next attempt (or until stop signal)
            self.stop_reconnect.wait(timeout=retry_interval)