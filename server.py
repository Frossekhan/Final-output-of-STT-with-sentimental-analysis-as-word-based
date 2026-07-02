"""
Real-Time AI Sales Conversation Intelligence Platform
FastAPI Server with WebSocket Support
"""

import asyncio
import json
import logging
from typing import Dict, Set
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from streaming.audio_buffer import AudioBuffer, VADBuffer
from streaming.stream_processor import StreamProcessor
from conversation_engine.engine import ConversationEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sales Intelligence Platform",
    description="Real-time AI-powered sales conversation analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections and sessions"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.sessions: Dict[str, Dict] = {}
        self.processors: Dict[str, StreamProcessor] = {}
        self.engines: Dict[str, ConversationEngine] = {}
        self.audio_buffers: Dict[str, AudioBuffer] = {}
        self.vad_buffers: Dict[str, VADBuffer] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """Register a new connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Initialize session components
        self.sessions[session_id] = {
            "connected_at": datetime.now(),
            "messages_received": 0,
            "transcriptions": []
        }
        
        # Initialize audio processing components
        self.processors[session_id] = StreamProcessor()
        self.engines[session_id] = ConversationEngine()
        self.audio_buffers[session_id] = AudioBuffer()
        self.vad_buffers[session_id] = VADBuffer()
        
        logger.info(f"Client connected: {session_id}")
        
        # Send connection confirmation
        await self.broadcast_to_session(session_id, {
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, session_id: str):
        """Unregister a connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.processors:
            del self.processors[session_id]
        if session_id in self.engines:
            del self.engines[session_id]
        if session_id in self.audio_buffers:
            del self.audio_buffers[session_id]
        if session_id in self.vad_buffers:
            del self.vad_buffers[session_id]
        
        logger.info(f"Client disconnected: {session_id}")
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """Send message to specific session"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)
    
    def get_processor(self, session_id: str) -> StreamProcessor:
        """Get processor for session"""
        if session_id not in self.processors:
            self.processors[session_id] = StreamProcessor()
        return self.processors[session_id]
    
    def get_engine(self, session_id: str) -> ConversationEngine:
        """Get conversation engine for session"""
        if session_id not in self.engines:
            self.engines[session_id] = ConversationEngine()
        return self.engines[session_id]
    
    def get_audio_buffer(self, session_id: str) -> AudioBuffer:
        """Get audio buffer for session"""
        if session_id not in self.audio_buffers:
            self.audio_buffers[session_id] = AudioBuffer()
        return self.audio_buffers[session_id]
    
    def get_vad_buffer(self, session_id: str) -> VADBuffer:
        """Get VAD buffer for session"""
        if session_id not in self.vad_buffers:
            self.vad_buffers[session_id] = VADBuffer()
        return self.vad_buffers[session_id]


# Initialize connection manager
manager = ConnectionManager()

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - serve index.html"""
    return FileResponse("static/index.html", media_type="text/html")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/sessions")
async def get_sessions():
    """Get all active sessions"""
    return {
        "sessions": list(manager.sessions.keys()),
        "count": len(manager.sessions),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get specific session details"""
    if session_id not in manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = manager.sessions[session_id]
    return {
        "session_id": session_id,
        "connected_at": session["connected_at"],
        "messages_received": session["messages_received"],
        "transcription_count": len(session["transcriptions"]),
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time audio streaming and analysis
    
    Message types:
    - session_start: Initialize session
    - audio: Audio chunk (base64 encoded PCM)
    - session_stop: End session
    """
    
    try:
        # Connect client
        await manager.connect(session_id, websocket)
        
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            data = json.loads(message)
            
            message_type = data.get("type")
            
            if message_type == "session_start":
                # Session started
                await manager.broadcast_to_session(session_id, {
                    "type": "session_started",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Session started: {session_id}")
            
            elif message_type == "audio":
                # Process audio chunk
                try:
                    # Update session stats
                    manager.sessions[session_id]["messages_received"] += 1
                    
                    # Decode audio
                    audio_data = data.get("audio_data")
                    if not audio_data:
                        logger.warning(f"Empty audio data from {session_id}")
                        continue
                    
                    # Process audio asynchronously
                    await process_audio_chunk(session_id, audio_data)
                
                except Exception as e:
                    logger.error(f"Error processing audio: {e}")
                    await manager.broadcast_to_session(session_id, {
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            elif message_type == "session_stop":
                # Session ended
                await manager.broadcast_to_session(session_id, {
                    "type": "session_ended",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Session ended: {session_id}")
                break
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)


async def process_audio_chunk(session_id: str, audio_data: str):
    """
    Process an audio chunk:
    1. Decode audio
    2. Transcribe with Whisper
    3. Run conversation intelligence
    4. Calculate lead score
    5. Send response
    """
    import base64
    import numpy as np
    
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0
        
        # Get components
        processor = manager.get_processor(session_id)
        engine = manager.get_engine(session_id)
        audio_buffer = manager.get_audio_buffer(session_id)
        
        # Add to buffer
        audio_buffer.add_chunk(audio_float)
        
        # Get buffered audio
        buffered_audio, start_time, end_time = audio_buffer.get_chunk()
        
        if buffered_audio is None:
            return
        
        # Transcribe audio
        transcription = processor.transcribe(buffered_audio)
        
        if not transcription:
            return
        
        # Store transcription
        manager.sessions[session_id]["transcriptions"].append({
            "text": transcription,
            "timestamp": datetime.now().isoformat()
        })
        
        # Run conversation intelligence analysis
        analysis = engine.analyze_segment(transcription, buffered_audio)
        
        # Create response
        response = {
            "type": "transcription",
            "text": transcription,
            "start": float(start_time),
            "end": float(end_time),
            "analysis": analysis,
            "lead_score": engine.get_lead_score(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Send response
        await manager.broadcast_to_session(session_id, response)
        
        logger.info(f"Processed audio: {session_id} - '{transcription}'")
    
    except Exception as e:
        logger.error(f"Error in process_audio_chunk: {e}")
        raise


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    logger.info("Starting up Sales Intelligence Platform...")
    try:
        # Pre-load models to check for issues
        logger.info("Loading Faster-Whisper model...")
        # Models will be lazy-loaded on first use
        logger.info("Platform ready!")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Sales Intelligence Platform...")
    # Disconnect all clients
    for session_id in list(manager.active_connections.keys()):
        manager.disconnect(session_id)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
