from typing import Dict, Any, List, Optional
from ..utils.logger import get_logger
from ..utils.cache import cached
from .base import BaseAPIClient

logger = get_logger()

class ProductAPI(BaseAPIClient):
    """Product API wrapper for searching and retrieving product details"""
    
    @cached(ttl=1800)  # Cache for 30 minutes
    def search_klevu(self, term: str, page_size: int = 5, page: int = 1) -> Dict[str, Any]:
        """Search for products using the Klevu search engine
        
        Args:
            term: Search term
            page_size: Results per page (default: 5)
            page: Page number (default: 1)
            
        Returns:
            Search results with product information
        """
        logger.info(f"Searching products with Klevu: {term}")
        params = {
            "term": term,
            "page_size": page_size,
            "page": page
        }
        return self.get("/api/search", params=params)
    
    @cached(ttl=1800)  # Cache for 30 minutes
    def search_azure(self, query: str, limit: int = 3) -> Dict[str, Any]:
        """Search for products using Azure Cognitive Search with vector enhancement
        
        Args:
            query: Search query
            limit: Maximum number of results (default: 3)
            
        Returns:
            Search results with detailed product information
        """
        logger.info(f"Searching products with Azure: {query}")
        params = {
            "query": query,
            "limit": limit
        }
        return self.get("/api/products/search", params=params)
    
    @cached(ttl=3600)  # Cache for 1 hour
    def get_product_details(self, part_number: str) -> Dict[str, Any]:
        """Get detailed information about a specific product
        
        Args:
            part_number: Product part number
            
        Returns:
            Detailed product information
        """
        logger.info(f"Getting product details for part number: {part_number}")
        return self.get(f"/api/products/{part_number}")
    
    def determine_search_method(self, query: str) -> str:
        """Determine which search method to use based on the query
        
        This is a simple heuristic that can be improved with ML-based classification.
        For now, we'll use Azure for longer, more complex queries, and Klevu for simpler ones.
        
        Args:
            query: User search query
            
        Returns:
            Search method to use: 'klevu' or 'azure'
        """
        # Simple heuristic: use Azure for longer, more complex queries
        words = query.split()
        if len(words) >= 4 or any(keyword in query.lower() for keyword in ["recommend", "best", "difference", "versus", "vs", "compatible", "alternative"]):
            return "azure"
        return "klevu"
    
    def search_products(self, query: str, use_method: Optional[str] = None) -> Dict[str, Any]:
        """Search for products using the appropriate search method
        
        Args:
            query: Search query
            use_method: Force a specific search method ('klevu' or 'azure')
            
        Returns:
            Search results with product information
        """
        method = use_method or self.determine_search_method(query)
        
        if method == "azure":
            return self.search_azure(query)
        else:  # Default to Klevu
            return self.search_klevu(query)
