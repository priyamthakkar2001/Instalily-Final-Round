from typing import Dict, Any, List, Optional, Union
import openai
from pool_equipment_agent.utils.model_context import ModelContext
from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.utils.config import get_config
from pydantic import BaseModel, Field

logger = get_logger()
config = get_config()

class GPT4O:
    """GPT-4o client implementation using our custom Model Context"""
    
    def __init__(self):
        """Initialize the GPT-4o client"""
        self.client = openai.OpenAI(api_key=config.openai.api_key)
        self.model = config.openai.model
        
    def generate(self, context: ModelContext) -> str:
        """Generate a response using GPT-4o
        
        Args:
            context: Model context containing messages and other parameters
            
        Returns:
            Generated response text
        """
        logger.debug(f"Generating response with {self.model}")
        
        # Convert ModelContext messages to OpenAI format
        messages = []
        for msg in context.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
            
        # Set default parameters if not provided
        temperature = context.parameters.get("temperature", 0.7)
        max_tokens = context.parameters.get("max_tokens", 1000)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def generate_with_json_output(self, context: ModelContext, output_class: type) -> Any:
        """Generate a response and parse it as a structured JSON object
        
        Args:
            context: Model context containing messages and other parameters
            output_class: Pydantic model class for the expected output structure
            
        Returns:
            Instance of the output_class populated with the generated data
        """
        logger.debug(f"Generating structured response with {self.model}")
        
        # Convert ModelContext messages to OpenAI format, preserving existing system messages
        messages = []
        system_content = ""
        
        # First collect any existing system messages
        for msg in context.messages:
            if msg.role == "system":
                system_content += msg.content + "\n\n"
            else:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add JSON formatting instructions to the system message
        json_schema = output_class.schema()
        schema_str = str(json_schema)
        
        system_content += f"\nYou must respond with a valid JSON object that matches this schema: {schema_str}\n"
        system_content += "\nYour response must be a properly formatted JSON object with all required fields. Do not include any explanatory text, just the JSON object."
        system_content += "\nExample of what your response should look like (but with the actual values based on the query):\n"
        
        # Create an example based on the model
        if output_class.__name__ == "QueryIntent":
            system_content += """
            {\n  "primary_intent": "product_search",\n  "confidence": 0.9,\n  "entities": {"product": "Hayward SuperPump"}\n}
            """
        
        # Add the combined system message at the beginning
        messages.insert(0, {
            "role": "system",
            "content": system_content
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,  # Lower temperature for more deterministic JSON output
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            logger.debug(f"Raw JSON response: {response_text}")
            
            # Parse the JSON response
            try:
                return output_class.parse_raw(response_text)
            except Exception as parse_error:
                logger.error(f"Error parsing JSON response: {str(parse_error)}")
                logger.error(f"Raw response: {response_text}")
                
                # Fallback for QueryIntent
                if output_class.__name__ == "QueryIntent":
                    logger.info("Using fallback for QueryIntent")
                    from pool_equipment_agent.llm.query_classifier import QueryIntent
                    return QueryIntent(
                        primary_intent="general",
                        confidence=0.5,
                        entities={}
                    )
                raise
        except Exception as e:
            logger.error(f"Error generating structured response: {str(e)}")
            
            # Fallback for QueryIntent
            if output_class.__name__ == "QueryIntent":
                logger.info("Using fallback for QueryIntent due to API error")
                from pool_equipment_agent.llm.query_classifier import QueryIntent
                return QueryIntent(
                    primary_intent="general",
                    confidence=0.5,
                    entities={}
                )
            raise
