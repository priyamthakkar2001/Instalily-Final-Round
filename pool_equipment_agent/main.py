import os
import uvicorn
import asyncio
from threading import Thread

from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.utils.config import get_config
from pool_equipment_agent.agents.coordinator import CoordinatorAgent
from pool_equipment_agent.messaging.telegram_bot import TelegramBot
from pool_equipment_agent.api.health_api import HealthAPI

logger = get_logger()
config = get_config()

def run_api_server():
    """Run the FastAPI server in a separate thread"""
    logger.info("Starting API server")
    uvicorn.run("pool_equipment_agent.app:app", host="0.0.0.0", port=8000, log_level="info")

def main():
    """Main entry point for the application"""
    logger.info("Starting Pool Equipment Chat Agent")
    
    # Check API health
    try:
        health_api = HealthAPI()
        health_status = health_api.check_health()
        logger.info(f"API health check: {health_status}")
    except Exception as e:
        logger.error(f"API health check failed: {str(e)}")
        logger.warning("Continuing despite API health check failure")
    
    # Initialize coordinator agent
    coordinator = CoordinatorAgent()
    
    # Define message handler function for the Telegram bot
    def handle_message(message: str, conversation_history=None):
        """Handle incoming messages from Telegram
        
        Args:
            message: User message text
            conversation_history: Conversation history
            
        Returns:
            Response text
        """
        try:
            return coordinator.process_query(message, conversation_history)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request. Please try again later."
    
    # Start API server in a separate thread
    api_thread = Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Initialize and run Telegram bot
    telegram_bot = TelegramBot(handle_message)
    telegram_bot.run()

if __name__ == "__main__":
    main()
