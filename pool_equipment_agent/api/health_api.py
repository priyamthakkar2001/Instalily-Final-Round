from typing import Dict, Any
from ..utils.logger import get_logger
from .base import BaseAPIClient

logger = get_logger()

class HealthAPI(BaseAPIClient):
    """Health API wrapper for checking API status"""
    
    def check_health(self) -> Dict[str, Any]:
        """Check if the API is running
        
        Returns:
            Health status information
        """
        logger.info("Checking API health status")
        return self.get("/health")
