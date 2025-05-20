import asyncio
import base64
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import AsyncIterable, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Query, WebSocket, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.events.event import Event
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from customer_service.agent import root_agent

from .log import logger

#
# ADK Streaming
#

# Load Gemini API Key
load_dotenv()
logger.info("Environment variables loaded")

APP_NAME = "ADK Streaming example"
session_service = InMemorySessionService()


def start_agent_session(session_id, is_audio=False):
    """Starts an agent session"""
    logger.info(f"Starting agent session for {session_id}, audio mode: {is_audio}")

    # Create a Session
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
    )

    # Create a Runner
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
    )

    # Set response modality
    modality = "AUDIO" if is_audio else "TEXT"

    # Create speech config with voice settings
    speech_config = types.SpeechConfig(
        voice_config=types.VoiceConfig(
            # Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, and Zephyr
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
        )
    )

    # Create run config with basic settings
    config = {"response_modalities": [modality], "speech_config": speech_config}

    # Add output_audio_transcription when audio is enabled to get both audio and text
    if is_audio:
        config["output_audio_transcription"] = {}

    run_config = RunConfig(**config)

    # Create a LiveRequestQueue for this session
    live_request_queue = LiveRequestQueue()

    # Start agent session
    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    logger.info(f"Agent session started successfully for {session_id}")
    return live_events, live_request_queue


async def agent_to_client_messaging(
    websocket: WebSocket, live_events: AsyncIterable[Event | None]
):
    """Agent to client communication"""
    logger.debug("Starting agent to client messaging loop")
    while True:
        async for event in live_events:
            if event is None:
                continue

            # If the turn complete or interrupted, send it
            if event.turn_complete or event.interrupted:
                message = {
                    "turn_complete": event.turn_complete,
                    "interrupted": event.interrupted,
                }
                await websocket.send_text(json.dumps(message))
                logger.debug(f"Agent to client: Turn status update sent")
                continue

            # Read the Content and its first Part
            part = event.content and event.content.parts and event.content.parts[0]
            if not part:
                continue

            # Make sure we have a valid Part
            if not isinstance(part, types.Part):
                continue

            # Only send text if it's a partial response (streaming)
            # Skip the final complete message to avoid duplication
            if part.text and event.partial:
                message = {
                    "mime_type": "text/plain",
                    "data": part.text,
                    "role": "model",
                }
                await websocket.send_text(json.dumps(message))
                logger.debug(f"Agent to client: Sent text response (streaming)")

            # If it's audio, send Base64 encoded audio data
            is_audio = (
                part.inline_data
                and part.inline_data.mime_type
                and part.inline_data.mime_type.startswith("audio/pcm")
            )
            if is_audio:
                audio_data = part.inline_data and part.inline_data.data
                if audio_data:
                    message = {
                        "mime_type": "audio/pcm",
                        "data": base64.b64encode(audio_data).decode("ascii"),
                        "role": "model",
                    }
                    await websocket.send_text(json.dumps(message))
                    logger.debug(f"Agent to client: Sent audio response ({len(audio_data)} bytes)")


async def client_to_agent_messaging(
    websocket: WebSocket, live_request_queue: LiveRequestQueue
):
    """Client to agent communication"""
    logger.debug("Starting client to agent messaging loop")
    try:
        while True:
            # Decode JSON message
            message_json = await websocket.receive_text()
            message = json.loads(message_json)
            mime_type = message["mime_type"]
            data = message["data"]
            role = message.get("role", "user")  # Default to 'user' if role is not provided

            # Send the message to the agent
            if mime_type == "text/plain":
                # Send a text message
                content = types.Content(role=role, parts=[types.Part.from_text(text=data)])
                live_request_queue.send_content(content=content)
                logger.info(f"Client to agent: Received text query: {data[:50]}{'...' if len(data) > 50 else ''}")
            elif mime_type == "audio/pcm":
                # Send audio data
                decoded_data = base64.b64decode(data)

                # Send the audio data - note that ActivityStart/End and transcription
                # handling is done automatically by the ADK when input_audio_transcription
                # is enabled in the config
                live_request_queue.send_realtime(
                    types.Blob(data=decoded_data, mime_type=mime_type)
                )
                logger.info(f"Client to agent: Received audio data ({len(decoded_data)} bytes)")
            else:
                error_msg = f"Mime type not supported: {mime_type}"
                logger.error(error_msg)
                raise ValueError(error_msg)
    except Exception as e:
        logger.error(f"Error in client_to_agent_messaging: {str(e)}")
        raise


#
# FastAPI web app
#

app = FastAPI(
    title="BAgro Chatbot",
    description="BAgro customer service chatbot API",
    version="0.1.0"
)

# Add CORS middleware to allow WebSocket connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, you can use "*" to allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)



@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> JSONResponse:
    """
    Health check endpoint to verify if the service is running.
    
    Returns:
        JSONResponse: Status information about the service
    """
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "uptime": "N/A"  # You could track server start time and calculate uptime if needed
    })


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    is_audio: str = Query(...),
):
    """Client websocket endpoint"""
    # Add more debug logging
    logger.info(f"WebSocket connection attempt from {session_id} with protocol {websocket.headers.get('sec-websocket-protocol', 'none')}")
    logger.info(f"Client using: {websocket.headers.get('user-agent')}")
    logger.info(f"Connection headers: {dict(websocket.headers)}")
    
    try:
        # Wait for client connection
        await websocket.accept()
        logger.info(f"Client #{session_id} connected, audio mode: {is_audio}")

        # Start agent session
        live_events, live_request_queue = start_agent_session(
            session_id, is_audio == "true"
        )

        # Start tasks
        agent_to_client_task = asyncio.create_task(
            agent_to_client_messaging(websocket, live_events)
        )
        client_to_agent_task = asyncio.create_task(
            client_to_agent_messaging(websocket, live_request_queue)
        )
        await asyncio.gather(agent_to_client_task, client_to_agent_task)
    except Exception as e:
        logger.error(f"Error in websocket endpoint for session {session_id}: {str(e)}")
        raise
    finally:
        # Disconnected
        logger.info(f"Client #{session_id} disconnected")


# Mounting Static files later
STATIC_DIR = Path("fastapi_server/static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serves the index.html"""
    logger.debug("Serving index.html")
    try:
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        raise








# Testing Websocket
@app.get("/websocket-test")
async def websocket_test():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
        <script>
            window.onload = function() {
                const isSecure = window.location.protocol === "https:";
                const wsProtocol = isSecure ? "wss://" : "ws://";
                const wsUrl = wsProtocol + window.location.host + "/ws/test-session?is_audio=false";
                
                document.getElementById("wsurl").textContent = wsUrl;
                document.getElementById("protocol").textContent = window.location.protocol;
                
                document.getElementById("testBtn").onclick = function() {
                    try {
                        const ws = new WebSocket(wsUrl);
                        
                        ws.onopen = function() {
                            document.getElementById("status").textContent = "Connected!";
                            document.getElementById("status").style.color = "green";
                        };
                        
                        ws.onerror = function(error) {
                            document.getElementById("status").textContent = "Error: " + error;
                            document.getElementById("status").style.color = "red";
                        };
                        
                        ws.onclose = function() {
                            document.getElementById("status").textContent = "Connection closed";
                            document.getElementById("status").style.color = "orange";
                        };
                    } catch(e) {
                        document.getElementById("status").textContent = "Exception: " + e.message;
                        document.getElementById("status").style.color = "red";
                    }
                };
            };
        </script>
    </head>
    <body>
        <h1>WebSocket Connection Test</h1>
        <p>Page Protocol: <span id="protocol"></span></p>
        <p>WebSocket URL: <span id="wsurl"></span></p>
        <button id="testBtn">Test Connection</button>
        <p>Status: <span id="status">Not connected</span></p>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)