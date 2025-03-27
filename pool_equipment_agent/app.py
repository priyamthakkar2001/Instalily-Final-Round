from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
import json
from typing import Dict, Any

from pool_equipment_agent.utils.logger import get_logger
from pool_equipment_agent.utils.config import get_config
from pool_equipment_agent.agents.coordinator import CoordinatorAgent

logger = get_logger()
config = get_config()

# Create FastAPI app
app = FastAPI(
    title="Pool Equipment Chat Agent API",
    description="API for the Pool Equipment Chat Agent",
    version="1.0.0"
)

# Initialize coordinator agent
coordinator = CoordinatorAgent()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Webhook endpoint for Telegram
    
    This endpoint is used for webhook-based Telegram integration as an alternative
    to the polling-based approach used in main.py.
    """
    try:
        # Parse the incoming webhook data
        data = await request.json()
        logger.debug(f"Received Telegram webhook: {data}")
        
        # Extract message data
        if "message" not in data:
            return JSONResponse(content={"status": "ok"})
            
        message = data["message"]
        if "text" not in message:
            return JSONResponse(content={"status": "ok"})
            
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        text = message["text"]
        
        # Process the message with the coordinator agent
        response = coordinator.process_query(text)
        
        # Send the response back to Telegram
        # In a webhook-based approach, you would use the Telegram API to send messages
        # This is just a placeholder - in a real implementation, you would make an HTTP request to the Telegram API
        logger.info(f"Processed message from user {user_id}, sending response")
        
        return JSONResponse(content={"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)})

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """Chat API endpoint for direct integration
    
    This endpoint allows direct integration with the chat agent from other applications.
    """
    try:
        # Parse the incoming request data
        data = await request.json()
        logger.debug(f"Received chat API request: {data}")
        
        # Extract message data
        if "message" not in data:
            raise HTTPException(status_code=400, detail="Message is required")
            
        message = data["message"]
        conversation_history = data.get("conversation_history", [])
        
        # Process the message with the coordinator agent
        response = coordinator.process_query(message, conversation_history)
        
        return JSONResponse(content={"response": response})
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
