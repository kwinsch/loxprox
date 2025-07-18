from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class OutputBase(ABC):
    """Base class for all output modules."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the output module with configuration.
        
        Args:
            config: Configuration dictionary for this output module
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.name = self.__class__.__name__
        
    @abstractmethod
    def send(self, data: Dict[str, Any]) -> bool:
        """Send data to the output destination.
        
        Args:
            data: Dictionary containing:
                - device_type: Type prefix (e.g., 'ph', 'pm')
                - device_id: Device identifier
                - value: Dictionary with device-specific values
                - timestamp: Timestamp string
                - source: Source identifier (e.g., 'udplight')
                
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the output destination.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the output destination."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if this output is enabled.
        
        Returns:
            bool: True if enabled, False otherwise
        """
        return self.enabled