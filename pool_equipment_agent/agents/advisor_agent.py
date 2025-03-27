from typing import Dict, Any, List, Optional
from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.llm.prompt_templates import PromptTemplates
from pool_equipment_agent.agents.base_agent import BaseAgent

logger = get_logger()

class AdvisorAgent(BaseAgent):
    """Agent for handling technical advice queries"""
    
    def __init__(self):
        """Initialize the technical advisor agent"""
        super().__init__(
            name="Technical Advisor",
            role="Pool equipment technical advisor",
            goal="Provide helpful advice and guidance on pool equipment installation, maintenance, and troubleshooting",
            backstory=PromptTemplates.advisor_agent_backstory(),
            prompt_template=PromptTemplates.advisor_agent_prompt()
        )
    
    def process_advice_query(self, query: str, entities: Dict[str, Any] = None) -> str:
        """Process a technical advice query
        
        Args:
            query: User query text
            entities: Extracted entities from the query
            
        Returns:
            Formatted response with technical advice
        """
        logger.info(f"Processing technical advice query: {query}")
        
        # Extract relevant information from entities if available
        context = {}
        if entities:
            context = {"entities": entities}
        
        # Process the query with the technical advisor agent
        return self.process(query, context)
