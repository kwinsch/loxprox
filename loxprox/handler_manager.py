import logging
from typing import Dict, Any, Optional
from .handlers.base import HandlerBase
from .handlers.lights import LightHandler
from .handlers.power import PowerHandler

logger = logging.getLogger(__name__)


class HandlerManager:
    """Manages device type handlers for processing data."""
    
    def __init__(self):
        """Initialize handler manager with default handlers."""
        self.handlers: Dict[str, HandlerBase] = {}
        
        # Register default handlers
        self._register_default_handlers()
        
    def _register_default_handlers(self) -> None:
        """Register the default device type handlers."""
        handlers = [
            LightHandler(),
            PowerHandler(),
        ]
        
        for handler in handlers:
            self.register_handler(handler)
            
    def register_handler(self, handler: HandlerBase) -> None:
        """Register a device type handler.
        
        Args:
            handler: Handler instance to register
        """
        device_type = handler.device_type
        self.handlers[device_type] = handler
        logger.info(f"Registered handler for device type: {device_type}")
        
    def process_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process data using the appropriate handler.
        
        Args:
            data: Raw parsed data from input parser
            
        Returns:
            Processed data ready for outputs, or None if no handler
        """
        device_type = data.get('device_type')
        if not device_type:
            logger.warning("Data missing device_type")
            return None
            
        handler = self.handlers.get(device_type)
        if not handler:
            logger.warning(f"No handler registered for device type: {device_type}")
            return None
            
        try:
            return handler.process(data)
        except Exception as e:
            logger.error(f"Handler error for device type {device_type}: {e}")
            return None
    
    def get_supported_types(self) -> list:
        """Get list of supported device types.
        
        Returns:
            List of device type strings
        """
        return list(self.handlers.keys())