from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum
from pool_equipment_agent.utils.model_context import ModelContext

from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.utils.config import get_config
from pool_equipment_agent.llm.gpt4o import GPT4O
from pool_equipment_agent.llm.prompt_templates import PromptTemplates

logger = get_logger()
config = get_config()

class QueryIntent(BaseModel):
    """Model for query intent classification"""
    primary_intent: Literal["product_search", "store_location", "pricing", "technical_advice", "general"] = Field(
        description="The primary intent of the user's query"
    )
    secondary_intent: Optional[Literal["product_search", "store_location", "pricing", "technical_advice", "general"]] = Field(
        None, description="Secondary intent if the query has multiple intents"
    )
    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Entities extracted from the query (e.g., product names, part numbers, locations)"
    )
    confidence: float = Field(
        description="Confidence score for the classification (0.0 to 1.0)"
    )

class QueryClassifier:
    """Classifier for determining user query intent"""
    
    def __init__(self):
        """Initialize the query classifier"""
        self.llm = GPT4O()
    
    def classify(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> QueryIntent:
        """Classify the intent of a user query
        
        Args:
            query: User query text
            conversation_history: Optional conversation history for context
            
        Returns:
            QueryIntent object with classification results
        """
        logger.info(f"Classifying query: {query}")
        
        # Create system prompt
        system_prompt = """
        You are an expert query classifier for a pool equipment chat agent. Your task is to analyze the user's query and determine:
        1. The primary intent (product_search, store_location, pricing, technical_advice, or general)
        2. Secondary intent if applicable (same options as primary)
        3. Extract relevant entities (product names, part numbers, locations, etc.)
        4. Assign a confidence score (0.0 to 1.0)
        
        Examples:
        - "Where can I find pool pumps?" → product_search (primary), store_location (secondary)
        - "What's the price of a Hayward Super Pump?" → pricing (primary), product_search (secondary)
        - "How do I fix my pool filter?" → technical_advice (primary)
        - "Where is the nearest store?" → store_location (primary)
        - "Hello, how are you?" → general (primary)
        
        For entities, extract specific information like:
        - Product names (e.g., "Super Pump", "Sand Filter")
        - Part numbers if mentioned
        - Locations (city names, zip codes)
        - Technical issues or requirements
        """
        
        # Create messages
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                messages.append(msg)
        
        # Add the current query
        messages.append({"role": "user", "content": query})
        
        # Create model context
        context = ModelContext.from_messages(
            messages=messages,
            parameters={"temperature": 0.1}  # Low temperature for more deterministic classification
        )
        
        # Generate classification
        try:
            result = self.llm.generate_with_json_output(context, QueryIntent)
            logger.info(f"Query classified as: {result.primary_intent} (confidence: {result.confidence})")
            return result
        except Exception as e:
            logger.error(f"Error classifying query: {str(e)}")
            # Return default classification on error
            return QueryIntent(
                primary_intent="general",
                confidence=0.5,
                entities={}
            )
