from typing import Dict, Any, List, Optional
from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.api.pricing_api import PricingAPI
from pool_equipment_agent.llm.prompt_templates import PromptTemplates
from pool_equipment_agent.agents.base_agent import BaseAgent

logger = get_logger()

class PricingAgent(BaseAgent):
    """Agent for handling pricing queries"""
    
    def __init__(self):
        """Initialize the pricing agent"""
        super().__init__(
            name="Pricing Specialist",
            role="Pool equipment pricing specialist",
            goal="Provide accurate pricing information to customers",
            backstory=PromptTemplates.pricing_agent_backstory(),
            prompt_template=PromptTemplates.pricing_agent_prompt()
        )
        self.pricing_api = PricingAPI()
    
    def get_pricing(self, items: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get pricing information for multiple items
        
        Args:
            items: List of items with item_code and unit
                Example: [{"item_code": "LZA406103A", "unit": "EA"}]
            
        Returns:
            Pricing information for the requested items
        """
        return self.pricing_api.get_pricing(items)
    
    def get_single_item_pricing(self, item_code: str, unit: str = "EA") -> Dict[str, Any]:
        """Get pricing information for a single item
        
        Args:
            item_code: Item code/part number
            unit: Unit of measure (default: "EA")
            
        Returns:
            Pricing information for the requested item
        """
        return self.pricing_api.get_single_item_pricing(item_code, unit)
    
    def process_pricing_query(self, query: str, entities: Dict[str, Any] = None) -> str:
        """Process a pricing query
        
        Args:
            query: User query text
            entities: Extracted entities from the query
            
        Returns:
            Formatted response with pricing information
        """
        logger.info(f"Processing pricing query: {query}")
        
        # Extract item parameters from entities if available
        item_codes = []
        unit = "EA"  # Default unit
        
        if entities:
            if "part_number" in entities:
                item_codes.append(entities["part_number"])
            if "part_numbers" in entities and isinstance(entities["part_numbers"], list):
                item_codes.extend(entities["part_numbers"])
            if "unit" in entities:
                unit = entities["unit"]
        
        # If we don't have any item codes, return a helpful message
        if not item_codes:
            return "I need a product part number to provide pricing information. Could you please specify which product you're interested in?"
        
        # Get pricing for the items
        try:
            items = [{"item_code": code, "unit": unit} for code in item_codes]
            pricing_results = self.get_pricing(items)
            context = {"pricing_results": pricing_results}
            return self.process(f"Provide pricing information for the following part numbers: {', '.join(item_codes)}", context)
        except Exception as e:
            logger.error(f"Error getting pricing information: {str(e)}")
            return f"I'm sorry, I encountered an error while retrieving pricing information: {str(e)}"
