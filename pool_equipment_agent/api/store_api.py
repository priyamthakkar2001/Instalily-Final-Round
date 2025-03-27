from typing import Dict, Any, List, Optional
from ..utils.logger import get_logger
from ..utils.cache import cached
from .base import BaseAPIClient

logger = get_logger()

class StoreAPI(BaseAPIClient):
    """Store API wrapper for searching and retrieving store information"""
    
    @cached(ttl=3600)  # Cache for 1 hour
    def search_stores(self, latitude: float, longitude: float, radius: int = 50, page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """Search for stores near a location using coordinates
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in miles (default: 50)
            page_size: Results per page (default: 10)
            page: Page number (default: 1)
            
        Returns:
            Search results with store information
        """
        logger.info(f"Searching stores at coordinates: {latitude}, {longitude}")
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "page_size": page_size,
            "page": page
        }
        return self.get("/api/stores/search", params=params)
    
    @cached(ttl=86400)  # Cache for 24 hours
    def get_store_details(self, store_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific store
        
        Args:
            store_id: Store ID
            
        Returns:
            Detailed store information
        """
        logger.info(f"Getting store details for store ID: {store_id}")
        return self.get(f"/api/stores/{store_id}")
    
    def format_store_hours(self, hours: Dict[str, Dict[str, str]]) -> str:
        """Format store hours for display
        
        Args:
            hours: Store hours dictionary
            
        Returns:
            Formatted store hours string
        """
        formatted_hours = []
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for day in days:
            day_hours = hours.get(day, {})
            open_time = day_hours.get("open")
            close_time = day_hours.get("close")
            
            if open_time and close_time:
                formatted_hours.append(f"{day.capitalize()}: {open_time} - {close_time}")
            else:
                formatted_hours.append(f"{day.capitalize()}: Closed")
                
        return "\n".join(formatted_hours)
