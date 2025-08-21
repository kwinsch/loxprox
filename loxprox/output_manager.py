import logging
from typing import Dict, List, Any, Optional
from .outputs.base import OutputBase
from .outputs.hue import HueOutput
from .outputs.telegraf import TelegrafOutput
from .outputs.mqtt import MQTTOutput

logger = logging.getLogger(__name__)


class OutputManager:
    """Manages output modules and routes data based on device type."""
    
    # Registry of available output types
    OUTPUT_CLASSES = {
        'hue': HueOutput,
        'telegraf': TelegrafOutput,
        'mqtt': MQTTOutput,
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize output manager with configuration.
        
        Args:
            config: Full configuration dictionary
        """
        self.config = config
        self.outputs: Dict[str, OutputBase] = {}
        self.routing = config.get('routing', {})
        
        # Initialize configured outputs
        self._initialize_outputs()
        
    def _initialize_outputs(self) -> None:
        """Initialize all configured output modules."""
        outputs_config = self.config.get('outputs', {})
        
        for output_name, output_config in outputs_config.items():
            if not output_config.get('enabled', True):
                logger.info(f"Output '{output_name}' is disabled")
                continue
                
            if output_name not in self.OUTPUT_CLASSES:
                logger.warning(f"Unknown output type: {output_name}")
                continue
                
            try:
                # Create instance of the output class
                output_class = self.OUTPUT_CLASSES[output_name]
                output_instance = output_class(output_config)
                
                # Connect to the output
                if output_instance.connect():
                    self.outputs[output_name] = output_instance
                    logger.info(f"Initialized output: {output_name}")
                else:
                    logger.error(f"Failed to connect to output: {output_name}")
                    
            except Exception as e:
                logger.error(f"Failed to initialize output '{output_name}': {e}")
    
    def route_data(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """Route data to appropriate outputs based on device type.
        
        Args:
            data: Processed data with device_type field
            
        Returns:
            Dictionary mapping output names to success status
        """
        device_type = data.get('device_type')
        if not device_type:
            logger.warning("Data missing device_type field")
            return {}
            
        # Get routing configuration for this device type
        routing_config = self.routing.get(device_type, {})
        target_outputs = routing_config.get('outputs', [])
        
        if not target_outputs:
            logger.debug(f"No outputs configured for device type: {device_type}")
            return {}
            
        results = {}
        
        for output_name in target_outputs:
            if output_name not in self.outputs:
                logger.warning(f"Output '{output_name}' not available for routing")
                results[output_name] = False
                continue
                
            try:
                output = self.outputs[output_name]
                success = output.send(data)
                results[output_name] = success
                
                if not success:
                    logger.warning(f"Failed to send data to output: {output_name}")
                    
            except Exception as e:
                logger.error(f"Error sending to output '{output_name}': {e}")
                results[output_name] = False
                
        return results
    
    def shutdown(self) -> None:
        """Disconnect all outputs and clean up."""
        for output_name, output in self.outputs.items():
            try:
                output.disconnect()
                logger.info(f"Disconnected output: {output_name}")
            except Exception as e:
                logger.error(f"Error disconnecting output '{output_name}': {e}")
                
        self.outputs.clear()
    
    def get_active_outputs(self) -> List[str]:
        """Get list of currently active output names.
        
        Returns:
            List of output names
        """
        return list(self.outputs.keys())
    
    def register_output_type(self, name: str, output_class: type) -> None:
        """Register a new output type (for extensions).
        
        Args:
            name: Name of the output type
            output_class: Class that inherits from OutputBase
        """
        if not issubclass(output_class, OutputBase):
            raise ValueError(f"Output class must inherit from OutputBase")
            
        self.OUTPUT_CLASSES[name] = output_class
        logger.info(f"Registered new output type: {name}")