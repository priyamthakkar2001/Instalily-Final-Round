from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class Message(BaseModel):
    """Message model for conversation context"""
    role: str  # 'system', 'user', or 'assistant'
    content: str

class ModelContext(BaseModel):
    """Simple implementation of Model Context Protocol"""
    messages: List[Message]
    parameters: Dict[str, Any] = {}
    
    @classmethod
    def from_messages(cls, messages: List[Dict[str, str]], parameters: Optional[Dict[str, Any]] = None):
        """Create a ModelContext from a list of message dictionaries
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            parameters: Optional parameters for the model
            
        Returns:
            ModelContext instance
        """
        model_messages = [Message(role=msg["role"], content=msg["content"]) for msg in messages]
        return cls(messages=model_messages, parameters=parameters or {})
