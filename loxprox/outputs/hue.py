from typing import Dict, Any, Optional, Tuple
import logging
from phue import Bridge
from .base import OutputBase

logger = logging.getLogger(__name__)


class HueOutput(OutputBase):
    """Output module for Philips Hue lights."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Hue output with configuration.
        
        Args:
            config: Configuration containing:
                - bridge_ip: IP address of Hue bridge
                - username: Hue bridge username
                - enabled: Whether this output is enabled
        """
        super().__init__(config)
        self.bridge_ip = config.get('bridge_ip', '192.168.24.103')
        self.username = config.get('username')
        self.bridge: Optional[Bridge] = None
        
    def connect(self) -> bool:
        """Connect to the Philips Hue bridge.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.bridge = Bridge(self.bridge_ip, username=self.username)
            logger.info(f"Connected to Philips Hue bridge at {self.bridge_ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Hue bridge: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Hue bridge (no-op for Hue)."""
        self.bridge = None
        
    def send(self, data: Dict[str, Any]) -> bool:
        """Send light command to Hue bridge.
        
        Args:
            data: Dictionary containing:
                - device_type: Should be 'ph' for Hue lights
                - device_id: Light ID (e.g., '9')
                - value: Dict with 'mode' and light parameters
                
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.bridge:
            logger.error("Hue bridge not connected")
            return False
            
        if data.get('device_type') != 'ph':
            logger.debug(f"Ignoring non-Hue device type: {data.get('device_type')}")
            return True
            
        try:
            light_id = int(data['device_id'])
            value = data['value']
            mode = value.get('mode')
            
            if mode == 'rgb':
                return self._set_rgb_light(light_id, value)
            elif mode == 'cct':
                return self._set_cct_light(light_id, value)
            else:
                logger.warning(f"Unknown light mode: {mode}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending to Hue: {e}")
            return False
    
    def _set_rgb_light(self, light_id: int, value: Dict[str, Any]) -> bool:
        """Set RGB color on Hue light.
        
        Args:
            light_id: Hue light ID
            value: Dict containing r, g, b values (0-255)
            
        Returns:
            bool: True if successful
        """
        try:
            r = value.get('r', 0)
            g = value.get('g', 0)
            b = value.get('b', 0)
            
            brightness = max(r, g, b)
            logger.debug(f"Lamp {light_id}: RGB({r}, {g}, {b}), Brightness: {brightness} ({round(brightness/255*100)}%)")
            
            if (r + g + b) == 0:
                self.bridge.set_light(light_id, 'on', False)
            else:
                x, y = self._rgb_to_xy(r, g, b)
                self.bridge.set_light(light_id, 'on', True)
                self.bridge.set_light(light_id, {'bri': int(brightness), 'xy': [x, y]})
            
            return True
        except Exception as e:
            logger.error(f"Failed to set RGB light {light_id}: {e}")
            return False
    
    def _set_cct_light(self, light_id: int, value: Dict[str, Any]) -> bool:
        """Set color temperature on Hue light.
        
        Args:
            light_id: Hue light ID
            value: Dict containing brightness (0-100) and kelvin values
            
        Returns:
            bool: True if successful
        """
        try:
            brightness_percent = value.get('brightness', 0)
            kelvin = value.get('kelvin', 3000)
            
            brightness = int(brightness_percent * 254 / 100)
            logger.debug(f"Lamp {light_id}: CCT {kelvin}K, Brightness: {brightness} ({round(brightness/255*100)}%)")
            
            # Convert Kelvin to Hue ct value (mireds)
            ct = int(1000000 / kelvin)
            # Clamp to Hue accepted range
            ct = max(min(ct, 500), 153)
            
            if brightness == 0:
                self.bridge.set_light(light_id, 'on', False)
            else:
                self.bridge.set_light(light_id, 'on', True)
                self.bridge.set_light(light_id, {'bri': brightness, 'ct': ct})
            
            return True
        except Exception as e:
            logger.error(f"Failed to set CCT light {light_id}: {e}")
            return False
    
    def _rgb_to_xy(self, r: int, g: int, b: int) -> Tuple[float, float]:
        """Convert RGB to XY color space for Hue.
        
        Args:
            r, g, b: RGB values (0-255)
            
        Returns:
            Tuple of (x, y) coordinates
        """
        # Normalize RGB values
        r = r / 255.0
        g = g / 255.0
        b = b / 255.0
        
        # RGB to XYZ conversion
        X = r * 0.664511 + g * 0.154324 + b * 0.162028
        Y = r * 0.283881 + g * 0.668433 + b * 0.047685
        Z = r * 0.000088 + g * 0.072310 + b * 0.986039
        
        # XYZ to xy conversion
        total = X + Y + Z
        if total == 0:
            return 0.0, 0.0
            
        x = X / total
        y = Y / total
        
        return x, y