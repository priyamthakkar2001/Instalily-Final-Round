from typing import Dict, Any, List, Optional
from crewai import Agent
from pool_equipment_agent.utils.model_context import ModelContext

from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.utils.config import get_config
from pool_equipment_agent.llm.gpt4o import GPT4O

logger = get_logger()
config = get_config()

class BaseAgent:
    """Base agent class for all specialized agents"""
    
    def __init__(self, name: str, role: str, goal: str, backstory: str, prompt_template: ModelContext = None):
        """Initialize the base agent
        
        Args:
            name: Agent name
            role: Agent role description
            goal: Agent goal
            backstory: Agent backstory as a string
            prompt_template: System prompt template for the agent (optional)
        """
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.prompt_template = prompt_template
        self.llm = GPT4O()
        
        # Create CrewAI agent
        self.agent = Agent(
            name=name,
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
    
    def process(self, query: str, context: Dict[str, Any] = None) -> str:
        """Process a user query with the agent
        
        Args:
            query: User query text
            context: Additional context information
            
        Returns:
            Agent response text
        """
        logger.info(f"{self.name} processing query: {query}")
        
        # Create messages for the model context
        messages = []
        
        # Add system message - either from prompt_template or use backstory
        if self.prompt_template:
            if isinstance(self.prompt_template, ModelContext):
                # If it's a ModelContext, extract the system message content
                for msg in self.prompt_template.messages:
                    if msg.role == "system":
                        messages.append({"role": "system", "content": msg.content})
                        break
            else:
                # If it's already a string, use it directly
                messages.append({"role": "system", "content": self.prompt_template})
        else:
            # Fallback to backstory if no prompt_template
            messages.append({"role": "system", "content": self.backstory})
        
        # Add user message
        user_message = {"role": "user", "content": query}
        
        # Add context to user message if provided
        if context:
            context_str = "\n\nContext:\n" + "\n".join([f"{k}: {v}" for k, v in context.items()])
            user_message["content"] += context_str
        
        messages.append(user_message)
        
        # Create model context
        model_context = ModelContext.from_messages(
            messages=messages,
            parameters={"temperature": 0.7}
        )
        
        # Generate response
        try:
            response = self.llm.generate(model_context)
            logger.info(f"{self.name} generated response")
            return response
        except Exception as e:
            logger.error(f"Error processing query with {self.name}: {str(e)}")
            return f"I'm sorry, I encountered an error while processing your request: {str(e)}"
