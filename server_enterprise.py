"""
Enterprise AI Sales Conversation Intelligence Platform
FastAPI Server with LLM-Powered Analysis
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import base64
import numpy as np

from streaming.audio_buffer import AudioBuffer, VADBuffer
from streaming.stream_processor import StreamProcessor

# Import both engines
from conversation_engine.engine import ConversationIntelligenceEngine as RuleBasedEngine
from conversation_engine.llm_engine import LLMConversationEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Toggle between rule-based and LLM-powered engine
USE_LLM_ENGINE = True  # Set to False to use rule-based engine
LLM_MODEL_NAME = "qwen2.5:7b"  # Options: qwen2.5:7b, qwen2.5:14b, llama3.1:8b
ENABLE_CONVERSATION_MEMORY = True

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Enterprise AI Sales Intelligence Platform",
    description="Real-time AI-powered sales conversation analysis with LLM",
    version="2.0.0"
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
        
        # Initialize engines
        if USE_LLM_ENGINE:
            logger.info(f"🚀 Initializing LLM-Powered Engine with {LLM_MODEL_NAME}")
            self.llm_engine = LLMConversationEngine(
                model_name=LLM_MODEL_NAME,
                use_memory=ENABLE_CONVERSATION_MEMORY
            )
            self.rule_engine = None
        else:
            logger.info("📊 Initializing Rule-Based Engine")
            self.rule_engine = RuleBasedEngine()
            self.llm_engine = None
        
        # Audio processing components (shared)
        self.processors: Dict[str, StreamProcessor] = {}
        self.audio_buffers: Dict[str, AudioBuffer] = {}
        self.vad_buffers: Dict[str, VADBuffer] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """Register a new connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Initialize session
        self.sessions[session_id] = {
            "connected_at": datetime.now().isoformat(),
            "messages_received": 0,
            "transcriptions": [],
            "engine_type": "LLM" if USE_LLM_ENGINE else "Rule-Based"
        }
        
        # Initialize audio processing
        self.processors[session_id] = StreamProcessor()
        self.audio_buffers[session_id] = AudioBuffer()
        self.vad_buffers[session_id] = VADBuffer()
        
        # Start session in LLM engine if using LLM
        if self.llm_engine:
            self.llm_engine.start_session(session_id, customer_id=session_id)
        
        logger.info(f"✅ Client connected: {session_id} (Engine: {'LLM' if USE_LLM_ENGINE else 'Rule-Based'})")
        
        # Send connection confirmation
        await self.broadcast_to_session(session_id, {
            "type": "connection_established",
            "session_id": session_id,
            "engine": "LLM" if USE_LLM_ENGINE else "Rule-Based",
            "model": LLM_MODEL_NAME if USE_LLM_ENGINE else "N/A",
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
        if session_id in self.audio_buffers:
            del self.audio_buffers[session_id]
        if session_id in self.vad_buffers:
            del self.vad_buffers[session_id]
        
        logger.info(f"❌ Client disconnected: {session_id}")
    
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
    """Root endpoint"""
    return {
        "message": "Enterprise AI Sales Intelligence Platform",
        "version": "2.0.0",
        "engine": "LLM" if USE_LLM_ENGINE else "Rule-Based",
        "model": LLM_MODEL_NAME if USE_LLM_ENGINE else "N/A",
        "features": [
            "LLM-Powered BANT Extraction",
            "Context-Aware Intent Detection",
            "Intelligent Buying Signal Recognition",
            "Sophisticated Objection Classification",
            "Automatic Summary Generation",
            "Conversation Memory",
            "Real-time Lead Scoring"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "engine": "LLM" if USE_LLM_ENGINE else "Rule-Based",
        "model": LLM_MODEL_NAME if USE_LLM_ENGINE else "N/A",
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/sessions")
async def get_sessions():
    """Get all active sessions"""
    return {
        "sessions": list(manager.sessions.keys()),
        "count": len(manager.sessions),
        "engine": "LLM" if USE_LLM_ENGINE else "Rule-Based",
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
        "engine_type": session["engine_type"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return {
        "engine_type": "LLM" if USE_LLM_ENGINE else "Rule-Based",
        "model_name": LLM_MODEL_NAME if USE_LLM_ENGINE else "N/A",
        "conversation_memory": ENABLE_CONVERSATION_MEMORY,
        "features": {
            "llm_powered": USE_LLM_ENGINE,
            "conversation_memory": ENABLE_CONVERSATION_MEMORY,
            "speaker_diarization": False,  # Phase 3
            "advanced_emotion": False,  # Phase 4
            "ml_lead_scoring": False,  # Phase 5
        }
    }

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time audio streaming and analysis
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
                await manager.broadcast_to_session(session_id, {
                    "type": "session_started",
                    "session_id": session_id,
                    "engine": "LLM" if USE_LLM_ENGINE else "Rule-Based",
                    "model": LLM_MODEL_NAME if USE_LLM_ENGINE else "N/A",
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Session started: {session_id}")
            
            elif message_type == "audio":
                # Process audio chunk
                try:
                    manager.sessions[session_id]["messages_received"] += 1
                    audio_data = data.get("audio_data")
                    
                    if not audio_data:
                        logger.warning(f"Empty audio data from {session_id}")
                        continue
                    
                    # Process audio
                    await process_audio_chunk(session_id, audio_data)
                
                except Exception as e:
                    logger.error(f"Error processing audio: {e}")
                    await manager.broadcast_to_session(session_id, {
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            elif message_type == "session_stop":
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
    Process an audio chunk with selected engine
    """
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0
        
        # Get components
        processor = manager.get_processor(session_id)
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
        
        # Process with selected engine
        if USE_LLM_ENGINE and manager.llm_engine:
            # Use LLM engine
            analysis = await manager.llm_engine.analyze_segment(
                transcript=transcription,
                audio=buffered_audio,
                sample_rate=16000,
                speaker="customer"
            )
            lead_score = manager.llm_engine.get_lead_score()
        else:
            # Use rule-based engine
            analysis = manager.rule_engine.process_conversation(
                transcript=transcription,
                audio=buffered_audio,
                sample_rate=16000
            )
            lead_score = manager.rule_engine.calculate_lead_score()
            
            # Convert to dict for consistency
            analysis = {
                "bant": {
                    "budget": analysis.budget,
                    "budget_amount": analysis.budget_amount,
                    "authority": analysis.authority,
                    "authority_level": analysis.authority_level,
                    "need": analysis.need,
                    "need_category": analysis.need_category,
                    "timeline": analysis.timeline,
                    "timeline_urgency": analysis.timeline_urgency.value,
                    "confidence": analysis.bant_qualification_score
                },
                "intent": {
                    "intent": analysis.intent,
                    "confidence": analysis.intent_confidence
                },
                "emotion": {
                    "emotion": analysis.emotion,
                    "confidence": analysis.emotion_confidence
                },
                "buying_signals": {
                    "signals": analysis.buying_signals,
                    "readiness_score": analysis.buying_readiness_score,
                    "readiness_level": analysis.readiness_level
                },
                "objections": {
                    "objections": analysis.objections,
                    "severity": "medium" if analysis.objection_count > 0 else "low"
                }
            }
        
        # Create response
        response = {
            "type": "transcription",
            "text": transcription,
            "start": float(start_time),
            "end": float(end_time),
            "analysis": analysis,
            "lead_score": lead_score,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send response
        await manager.broadcast_to_session(session_id, response)
        
        logger.info(f"📊 Processed: {session_id} - '{transcription[:50]}...'")
    
    except Exception as e:
        logger.error(f"Error in process_audio_chunk: {e}")
        raise


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("=" * 80)
    logger.info("🚀 Enterprise AI Sales Intelligence Platform v2.0")
    logger.info("=" * 80)
    logger.info(f"Engine: {'LLM-Powered (' + LLM_MODEL_NAME + ')' if USE_LLM_ENGINE else 'Rule-Based'}")
    logger.info(f"Conversation Memory: {'Enabled' if ENABLE_CONVERSATION_MEMORY else 'Disabled'}")
    logger.info("=" * 80)
    
    if USE_LLM_ENGINE:
        logger.info("⚠️  Make sure Ollama is running with the selected model")
        logger.info(f"   Run: ollama pull {LLM_MODEL_NAME}")
        logger.info(f"   Then: ollama run {LLM_MODEL_NAME}")
    
    logger.info("✅ Platform ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Enterprise AI Sales Intelligence Platform...")
    for session_id in list(manager.active_connections.keys()):
        manager.disconnect(session_id)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server_enterprise:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )