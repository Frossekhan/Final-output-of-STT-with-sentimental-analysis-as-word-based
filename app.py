"""
AI Sales Conversation Intelligence Platform
Main FastAPI application with WebSocket support for real-time analysis
"""
import asyncio
import logging
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from streaming.websocket import manager
from streaming.stream_processor import StreamingTranscriptionService
from conversation_engine.engine import ConversationIntelligenceEngine
from emotion.speech_emotion import SpeechEmotionRecognizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Sales Intelligence Platform",
    description="Real-time conversation intelligence with speech emotion, BANT, intent, buying signals, and lead scoring",
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

# Initialize services
streaming_service = StreamingTranscriptionService(model_size="base", device="cpu")
conversation_engine = ConversationIntelligenceEngine()
emotion_recognizer = SpeechEmotionRecognizer()

# Store active sessions
active_sessions: dict = {}


class AudioChunk(BaseModel):
    """Audio chunk from WebSocket"""
    audio_data: str  # Base64 encoded audio
    session_id: str


class SessionRequest(BaseModel):
    """Session initialization request"""
    session_id: str
    icp_profile: Optional[dict] = None


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    logger.info("Starting AI Sales Intelligence Platform...")
    await streaming_service.get_or_create_processor("default")
    logger.info("Models loaded successfully")
    logger.info("Platform ready!")


@app.get("/")
async def root():
    """Serve dashboard"""
    return FileResponse("dashboard/index.html")


@app.get("/chatbot")
async def chatbot():
    """Serve chatbot interface"""
    return FileResponse("faster-whisper/chatbot.html")


@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio file with full analysis
    (Legacy endpoint - use WebSocket for real-time)
    """
    try:
        # Read audio file
        audio_bytes = await audio.read()
        
        # Process with streaming service
        processor = await streaming_service.get_or_create_processor("default")
        result = processor.process_audio_file(audio_bytes)
        
        # Extract text
        transcript = result.get("text", "")
        segments = result.get("segments", [])
        
        # Convert segments to format expected by conversation engine
        segment_dicts = [
            {"start": seg["start"], "end": seg["end"], "text": seg["text"]}
            for seg in segments
        ]
        
        # Process with conversation intelligence engine
        features = conversation_engine.process_conversation(
            transcript=transcript,
            segments=segment_dicts
        )
        
        # Calculate lead score
        lead_score = conversation_engine.calculate_lead_score()
        
        # Get conversation summary
        summary = conversation_engine.get_conversation_summary()
        
        return {
            "transcript": transcript,
            "segments": segments,
            "analysis": summary,
            "lead_score": {
                "score": lead_score.overall_score,
                "qualification": lead_score.qualification,
                "confidence": lead_score.confidence,
                "strengths": lead_score.strengths,
                "weaknesses": lead_score.weaknesses,
                "recommendations": lead_score.recommendations,
                "next_actions": lead_score.next_actions
            }
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/start")
async def start_session(request: SessionRequest):
    """Start a new analysis session"""
    session_id = request.session_id
    
    # Create processor for session
    processor = await streaming_service.get_or_create_processor(session_id)
    
    # Create conversation engine for session
    if request.icp_profile:
        engine = ConversationIntelligenceEngine(icp_profile=request.icp_profile)
    else:
        engine = ConversationIntelligenceEngine()
    
    active_sessions[session_id] = {
        "processor": processor,
        "engine": engine
    }
    
    return {
        "session_id": session_id,
        "status": "started",
        "message": "Session initialized successfully"
    }


@app.post("/api/session/stop")
async def stop_session(session_id: str):
    """Stop an analysis session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        streaming_service.remove_processor(session_id)
        return {"status": "stopped", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/session/{session_id}/analysis")
async def get_session_analysis(session_id: str):
    """Get current analysis for a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    engine = active_sessions[session_id]["engine"]
    summary = engine.get_conversation_summary()
    lead_score = engine.calculate_lead_score()
    
    return {
        "session_id": session_id,
        "analysis": summary,
        "lead_score": {
            "score": lead_score.overall_score,
            "qualification": lead_score.qualification,
            "confidence": lead_score.confidence
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio streaming and analysis
    """
    await manager.connect(websocket, "default")
    
    try:
        while True:
            # Receive message
            message = await websocket.receive_text()
            data = json.loads(message)
            
            message_type = data.get("type")
            
            if message_type == "audio":
                # Process audio chunk
                import base64
                import numpy as np
                
                audio_b64 = data.get("audio_data")
                session_id = data.get("session_id", "default")
                
                if audio_b64:
                    # Decode audio
                    audio_bytes = base64.b64decode(audio_b64)
                    
                    # Get or create processor
                    processor = await streaming_service.get_or_create_processor(session_id)
                    
                    # Process audio chunk
                    result = processor.process_audio_chunk(audio_bytes)
                    
                    if result:
                        # Get or create conversation engine
                        if session_id not in active_sessions:
                            active_sessions[session_id] = {
                                "processor": processor,
                                "engine": ConversationIntelligenceEngine()
                            }
                        
                        engine = active_sessions[session_id]["engine"]
                        
                        # Process with conversation engine
                        features = engine.process_conversation(
                            transcript=result["text"],
                            segments=[{
                                "start": result["start"],
                                "end": result["end"],
                                "text": result["text"]
                            }]
                        )
                        
                        # Calculate lead score
                        lead_score = engine.calculate_lead_score()
                        
                        # Get summary
                        summary = engine.get_conversation_summary()
                        
                        # Send result back
                        response = {
                            "type": "transcription",
                            "text": result["text"],
                            "start": result["start"],
                            "end": result["end"],
                            "analysis": summary,
                            "lead_score": {
                                "score": lead_score.overall_score,
                                "qualification": lead_score.qualification,
                                "confidence": lead_score.confidence
                            }
                        }
                        
                        await manager.send_message("default", response)
            
            elif message_type == "session_start":
                # Initialize session
                session_id = data.get("session_id", "default")
                await streaming_service.get_or_create_processor(session_id)
                
                if session_id not in active_sessions:
                    active_sessions[session_id] = {
                        "processor": await streaming_service.get_or_create_processor(session_id),
                        "engine": ConversationIntelligenceEngine()
                    }
                
                await manager.send_message("default", {
                    "type": "session_started",
                    "session_id": session_id
                })
            
            elif message_type == "session_stop":
                # Stop session
                session_id = data.get("session_id", "default")
                if session_id in active_sessions:
                    del active_sessions[session_id]
                    streaming_service.remove_processor(session_id)
                
                await manager.send_message("default", {
                    "type": "session_stopped",
                    "session_id": session_id
                })
    
    except WebSocketDisconnect:
        manager.disconnect("default")
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect("default")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": {
            "speech_emotion": True,
            "bant_extraction": True,
            "intent_detection": True,
            "buying_signals": True,
            "objection_detection": True,
            "icp_scoring": True,
            "lead_scoring": True
        }
    }


@app.get("/api/test")
async def test_endpoint():
    """Test endpoint with sample analysis"""
    sample_text = """
    Hello, I'm the CEO of a technology company in Bangalore. We're looking for a CRM solution 
    and have a budget of around 20 lakhs. We need to implement it within 3 months. 
    Can you send us a quotation? We're ready to proceed if the pricing works for us.
    """
    
    # Process with conversation engine
    features = conversation_engine.process_conversation(transcript=sample_text)
    lead_score = conversation_engine.calculate_lead_score()
    summary = conversation_engine.get_conversation_summary()
    
    return {
        "sample_transcript": sample_text.strip(),
        "analysis": summary,
        "lead_score": {
            "score": lead_score.overall_score,
            "qualification": lead_score.qualification,
            "confidence": lead_score.confidence,
            "strengths": lead_score.strengths,
            "weaknesses": lead_score.weaknesses,
            "recommendations": lead_score.recommendations,
            "next_actions": lead_score.next_actions
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)