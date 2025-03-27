from typing import Dict, Any, List, Optional
from pool_equipment_agent.utils.model_context import ModelContext

from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.llm.gpt4o import GPT4O
from pool_equipment_agent.llm.prompt_templates import PromptTemplates

logger = get_logger()

class MessageFormatter:
    """Utility for formatting messages for Telegram"""
    
    def __init__(self):
        """Initialize the message formatter"""
        self.llm = GPT4O()
    
    def format_for_telegram(self, message: str) -> str:
        """Format a message for Telegram using Markdown
        
        Args:
            message: Original message text
            
        Returns:
            Formatted message text with Markdown
        """
        logger.info("Formatting message for Telegram")
        
        # Create messages for the model context
        messages = [
            {"role": "system", "content": PromptTemplates.response_formatting_prompt().messages[0].content},
            {"role": "user", "content": f"Format this response for Telegram:\n\n{message}"}
        ]
        
        # Create model context
        model_context = ModelContext.from_messages(
            messages=messages,
            parameters={"temperature": 0.3}  # Lower temperature for more consistent formatting
        )
        
        # Generate formatted message
        try:
            formatted_message = self.llm.generate(model_context)
            logger.info("Message formatted for Telegram")
            return formatted_message
        except Exception as e:
            logger.error(f"Error formatting message: {str(e)}")
            # Return original message if formatting fails
            return message
    
    @staticmethod
    def truncate_message(message: str, max_length: int = 4096) -> str:
        """Truncate a message to fit Telegram's message length limit
        
        Args:
            message: Message text to truncate
            max_length: Maximum message length (default: 4096 for Telegram)
            
        Returns:
            Truncated message text
        """
        if len(message) <= max_length:
            return message
        
        # Truncate and add ellipsis
        truncated = message[:max_length - 3] + "..."
        return truncated
