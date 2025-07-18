from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HandlerBase(ABC):
    """Base class for device type handlers."""
    
    def __init__(self, device_type: str):
        """Initialize handler for specific device type.
        
        Args:
            device_type: Device type prefix this handler manages
        """
        self.device_type = device_type
        
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process device data and return standardized format.
        
        Args:
            data: Raw parsed data from input parser
            
        Returns:
            Processed data ready for outputs, or None if invalid
        """
        pass
    
    def can_handle(self, device_type: str) -> bool:
        """Check if this handler can process the given device type.
        
        Args:
            device_type: Device type to check
            
        Returns:
            bool: True if this handler can process the type
        """
        return device_type == self.device_type