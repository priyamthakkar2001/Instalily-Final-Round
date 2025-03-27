from typing import Dict, Any, List, Optional
from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.api.product_api import ProductAPI
from pool_equipment_agent.llm.prompt_templates import PromptTemplates
from pool_equipment_agent.agents.base_agent import BaseAgent

logger = get_logger()

class ProductAgent(BaseAgent):
    """Agent for handling product search queries"""
    
    def __init__(self):
        """Initialize the product agent"""
        super().__init__(
            name="Product Expert",
            role="Pool equipment product expert",
            goal="Help customers find the right pool equipment products based on their needs",
            backstory=PromptTemplates.product_agent_backstory(),
            prompt_template=PromptTemplates.product_agent_prompt()
        )
        self.product_api = ProductAPI()
    
    def search_products(self, query: str, search_method: Optional[str] = None) -> Dict[str, Any]:
        """Search for products using the appropriate search method
        
        Args:
            query: Search query
            search_method: Optional search method to use ('klevu' or 'azure')
            
        Returns:
            Search results with product information
        """
        return self.product_api.search_products(query, search_method)
    
    def get_product_details(self, part_number: str) -> Dict[str, Any]:
        """Get detailed information about a specific product
        
        Args:
            part_number: Product part number
            
        Returns:
            Detailed product information
        """
        return self.product_api.get_product_details(part_number)
    
    def process_product_query(self, query: str, entities: Dict[str, Any] = None) -> str:
        """Process a product search query
        
        Args:
            query: User query text
            entities: Extracted entities from the query
            
        Returns:
            Formatted response with product information
        """
        logger.info(f"Processing product query: {query}")
        
        # Extract search parameters from entities if available
        search_term = query
        search_method = None
        part_number = None
        
        if entities:
            if "product_name" in entities:
                search_term = entities["product_name"]
            if "search_method" in entities:
                search_method = entities["search_method"]
            if "part_number" in entities:
                part_number = entities["part_number"]
        
        # If we have a specific part number, get product details
        if part_number:
            try:
                product_details = self.get_product_details(part_number)
                context = {"product_details": product_details}
                return self.process(f"Provide information about product with part number {part_number}", context)
            except Exception as e:
                logger.error(f"Error getting product details: {str(e)}")
                # Fall back to search if product details fail
        
        # Otherwise, search for products
        try:
            search_results = self.search_products(search_term, search_method)
            context = {"search_results": search_results}
            return self.process(f"Provide information about products matching '{search_term}'", context)
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return f"I'm sorry, I encountered an error while searching for products: {str(e)}"
