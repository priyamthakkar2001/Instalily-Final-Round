import asyncio
from typing import Dict, Any, List, Optional, Callable
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.utils.config import get_config
from pool_equipment_agent.messaging.message_formatter import MessageFormatter

logger = get_logger()
config = get_config()

class TelegramBot:
    """Telegram bot implementation for the Pool Equipment Chat Agent"""
    
    def __init__(self, message_handler: Callable[[str, List[Dict[str, str]]], str]):
        """Initialize the Telegram bot
        
        Args:
            message_handler: Callback function to handle user messages
                Takes a message string and conversation history, returns a response string
        """
        self.token = config.telegram.bot_token
        self.message_handler = message_handler
        self.formatter = MessageFormatter()
        self.conversation_history = {}  # Dict to store conversation history by user ID
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")
        
        welcome_message = (
            f"👋 Hi {user.first_name}! I'm your Pool Equipment Assistant. \n\n"
            "I can help you with:\n"
            "- Finding pool equipment products\n"
            "- Locating nearby stores\n"
            "- Checking product pricing\n"
            "- Providing technical advice\n\n"
            "Just ask me anything about pool equipment!"
        )
        
        await update.message.reply_markdown(welcome_message)
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        help_message = (
            "🔍 *How to use the Pool Equipment Assistant*\n\n"
            "*Example questions you can ask:*\n"
            "- What pool pumps do you recommend?\n"
            "- Where is the nearest store to Atlanta, GA?\n"
            "- How much does a Hayward Super Pump cost?\n"
            "- How do I clean my pool filter?\n"
            "- What's the difference between sand and cartridge filters?\n\n"
            "*Commands:*\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/clear - Clear your conversation history"
        )
        
        await update.message.reply_markdown(help_message)
        
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /clear command to clear conversation history
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        user_id = update.effective_user.id
        if user_id in self.conversation_history:
            self.conversation_history[user_id] = []
            logger.info(f"Cleared conversation history for user {user_id}")
            
        await update.message.reply_text("Your conversation history has been cleared.")
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        user_id = update.effective_user.id
        user_message = update.message.text
        logger.info(f"Received message from user {user_id}: {user_message}")
        
        # Initialize conversation history for new users
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
            
        # Add user message to conversation history
        self.conversation_history[user_id].append({"role": "user", "content": user_message})
        
        # Limit conversation history to last 10 messages
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
            
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        try:
            # Process the message with the handler
            response = self.message_handler(user_message, self.conversation_history[user_id])
            
            # Format the response for Telegram
            formatted_response = self.formatter.format_for_telegram(response)
            
            # Truncate if necessary
            formatted_response = self.formatter.truncate_message(formatted_response)
            
            # Add assistant response to conversation history
            self.conversation_history[user_id].append({"role": "assistant", "content": response})
            
            # Send the response
            await update.message.reply_markdown(formatted_response, disable_web_page_preview=False)
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            error_message = "I'm sorry, I encountered an error while processing your request. Please try again later."
            await update.message.reply_text(error_message)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        error = context.error
        
        # Check if it's a conflict error (multiple bot instances)
        if isinstance(error, telegram.error.Conflict):
            logger.warning("Conflict error: Another bot instance is running. This instance will gracefully exit.")
            # Exit gracefully after a short delay
            import sys
            import threading
            def delayed_exit():
                import time
                time.sleep(2)  # Give time for logs to be written
                sys.exit(0)
            threading.Thread(target=delayed_exit).start()
            return
        
        # Log other errors
        logger.error(f"Update {update} caused error: {error}")
        
    def run(self) -> None:
        """Run the Telegram bot"""
        logger.info("Starting Telegram bot")
        
        # Create the Application
        application = Application.builder().token(self.token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("clear", self.clear_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Add error handler
        application.add_error_handler(self.error_handler)
        
        # Run the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
