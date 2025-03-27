from typing import Dict, Any, List
from ..utils.logger import get_logger
from ..utils.cache import cached
from .base import BaseAPIClient

logger = get_logger()

class PricingAPI(BaseAPIClient):
    """Pricing API wrapper for retrieving product pricing information"""
    
    @cached(ttl=1800)  # Cache for 30 minutes
    def get_pricing(self, items: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get pricing information for multiple items
        
        Args:
            items: List of items with item_code and unit
                Example: [{"item_code": "LZA406103A", "unit": "EA"}]
            
        Returns:
            Pricing information for the requested items
        """
        logger.info(f"Getting pricing for {len(items)} items")
        
        # Create the request body according to the API documentation
        data = {"items": items}
        
        try:
            # Make the API request
            return self.post("/api/pricing", data=data)
        except Exception as e:
            logger.error(f"Error in pricing API: {str(e)}")
            # Return a fallback response with empty items
            return {"items": [], "error": str(e)}
    
    def get_single_item_pricing(self, item_code: str, unit: str = "EA") -> Dict[str, Any]:
        """Get pricing information for a single item
        
        Args:
            item_code: Item code/part number
            unit: Unit of measure (default: "EA")
            
        Returns:
            Pricing information for the requested item
        """
        logger.info(f"Getting pricing for item: {item_code}")
        items = [{"item_code": item_code, "unit": unit}]
        result = self.get_pricing(items)
        
        # Extract the single item from the response
        if result.get("items") and len(result["items"]) > 0:
            return result["items"][0]
        return {}
