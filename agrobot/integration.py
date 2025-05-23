"""
Integration module for BharatAgro AI Assistant with the FastAPI server.

This module provides the necessary integration functions and classes
to connect the BharatAgro AI Assistant with the FastAPI server for
handling web requests.
"""

from typing import Dict, Any, AsyncIterable
from google.adk.agents import LiveRequestQueue
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

from .agent import root_agent

# Create a session service for managing user sessions
session_service = InMemorySessionService()
APP_NAME = "BharatAgro AI Assistant"

def start_agent_session(session_id: str, is_audio: bool = False):
    """
    Start a new agent session.
    
    Args:
        session_id: Unique identifier for the session
        is_audio: Whether this is an audio session
        
    Returns:
        A LiveRequestQueue for sending requests to the agent
    """
    # Create a session
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
    )
    
    # Create a Runner for this session
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session=session,
    )
    
    # Create a LiveRequestQueue for handling streaming requests/responses
    live_queue = LiveRequestQueue(runner=runner, session=session)
    
    return live_queue

async def handle_message(session_id: str, message: str) -> AsyncIterable[Dict[str, Any]]:
    """
    Handle an incoming message from a user.
    
    Args:
        session_id: Unique identifier for the user's session
        message: The message sent by the user
        
    Yields:
        Dictionaries containing agent responses for streaming
    """
    # Get the LiveRequestQueue for this session, creating one if it doesn't exist
    live_queue = session_service.get_session_data(session_id, "live_queue")
    if not live_queue:
        live_queue = start_agent_session(session_id)
        session_service.set_session_data(session_id, "live_queue", live_queue)
    
    # Send the message to the agent and yield responses
    async for event in live_queue.send_message(message):
        yield {
            "type": event.type,
            "content": event.content if hasattr(event, "content") else None
        }
