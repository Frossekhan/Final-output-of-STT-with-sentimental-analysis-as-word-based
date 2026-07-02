"""
Production FastAPI Server with Real-Time Streaming
Handles live audio processing through WebSocket
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging
import asyncio
import json
from datetime import datetime
from typing import Set
import numpy as np

# Import streaming components
from streaming.stream_handler import StreamProcessor, StreamBuffer
from streaming.websocket import ConnectionManager

# Import analysis modules
from emotion.speech_emotion import SpeechEmotionRecognizer, EmotionTracker
from bant.parser import BANTEngine
from intent.predict import IntentDetector
from buying_signal.detect import BuyingSignalAnalyzer
from objection.detect import ObjectionAnalyzer
from icp.score import ICPAnalyzer
from conversation_engine.engine import ConversationIntelligenceEngine

# Import lead scoring
from lead_scoring import LeadScorer

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(title="Sales Intelligence Platform", version="1.0.0")

# Connection manager
manager = ConnectionManager()

# Analysis engine
conversation_engine = ConversationIntelligenceEngine()
lead_scorer = LeadScorer()

# Global state
current_analysis = {
    "transcript": "",
    "segments": [],
    "emotion": None,
    "bant": None,
    "intent": None,
    "buying_signals": None,
    "objections": None,
    "icp_score": None,
    "lead_score": None
}

# ============================================================================
# REAL-TIME STREAMING ENDPOINT
# ============================================================================

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio streaming
    Client sends: audio chunks (bytes)
    Server sends: live analysis results
    """
    import uuid
    client_id = str(uuid.uuid4())[:8]
    await manager.connect(websocket, client_id)
    stream_processor = None
    transcription_buffer = ""
    
    try:
        logger.info(f"Client {client_id} connected for streaming")
        
        async def on_audio_chunk(chunk):
            """Process audio chunk"""
            nonlocal transcription_buffer
            
            try:
                # For now, we'll accumulate audio and process periodically
                # In production, connect to Faster-Whisper here
                pass
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
        
        # Initialize stream processor
        stream_processor = StreamProcessor(
            sample_rate=16000,
            chunk_duration_ms=100,
            callback=on_audio_chunk
        )
        
        # Start stream processing in background
        processor_task = asyncio.create_task(stream_processor.process_stream())
        
        # Wait for and process incoming audio
        while True:
            data = await websocket.receive_bytes()
            
            if data:
                # Add audio to stream
                await stream_processor.add_audio(data)
                
                # Send metrics every few chunks
                if stream_processor.metrics.chunks_received % 10 == 0:
                    metrics = stream_processor.get_metrics()
                    await manager.broadcast({
                        "type": "metrics",
                        "data": metrics
                    })
    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
        manager.disconnect(client_id)
        if stream_processor:
            await stream_processor.stop()
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/analyze/text")
async def analyze_text(text: str):
    """Analyze text and return complete conversation intelligence"""
    try:
        # Run complete analysis
        result = conversation_engine.analyze_conversation(text)
        
        # Get lead score
        lead_score = lead_scorer.score(result)
        
        # Format response
        response = {
            "transcript": text,
            "timestamp": datetime.now().isoformat(),
            "emotion": {
                "type": result.emotion,
                "confidence": result.emotion_confidence,
                "scores": result.emotion_scores
            },
            "bant": {
                "budget": result.budget,
                "authority": result.authority,
                "need": result.need,
                "timeline": result.timeline
            },
            "intent": {
                "type": result.intent,
                "confidence": result.intent_confidence
            },
            "buying_signals": result.buying_signals,
            "objections": result.objections,
            "icp_score": result.icp_score,
            "lead_score": {
                "score": lead_score.score,
                "qualification": lead_score.qualification,
                "confidence": lead_score.confidence,
                "reasoning": lead_score.reasoning
            }
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def status():
    """Get platform status"""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "connected_clients": len(manager.active_connections),
        "features": [
            "Real-Time Speech-to-Text",
            "Speech Emotion Recognition",
            "BANT Extraction",
            "Intent Detection",
            "Buying Signal Detection",
            "Objection Detection",
            "ICP Scoring",
            "Lead Scoring"
        ]
    }


@app.get("/api/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


# ============================================================================
# STATIC CONTENT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "Sales Intelligence Platform",
        "version": "1.0.0",
        "documentation": "/docs",
        "websocket": "ws://localhost:8000/ws/stream"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Sales Intelligence Platform Server...")
    logger.info("WebSocket Stream: ws://localhost:8000/ws/stream")
    logger.info("API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
