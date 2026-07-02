"""
Microphone Client for Sales Intelligence Platform
Captures audio and streams to WebSocket server
"""

import asyncio
import websockets
import json
import base64
import logging
from datetime import datetime
import sounddevice as sd
import numpy as np
from typing import Optional
import uuid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MicrophoneClient:
    """
    Records audio from microphone and streams to server via WebSocket
    """
    
    def __init__(
        self,
        server_url: str = "ws://localhost:8000/ws",
        sample_rate: int = 16000,
        chunk_duration: float = 2.0,
        channels: int = 1
    ):
        """
        Initialize microphone client
        
        Args:
            server_url: WebSocket server URL
            sample_rate: Audio sample rate (Hz)
            chunk_duration: Duration of each chunk (seconds)
            channels: Number of audio channels (1=mono)
        """
        self.server_url = server_url
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.channels = channels
        
        # Calculate chunk size
        self.chunk_size = int(sample_rate * chunk_duration)
        
        # Session management
        self.session_id = str(uuid.uuid4())
        self.is_recording = False
        self.stream = None
        self.websocket = None
        
        logger.info(f"MicrophoneClient initialized (Session: {self.session_id})")
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            logger.info(f"Connecting to {self.server_url}")
            self.websocket = await websockets.connect(self.server_url + f"/{self.session_id}")
            logger.info("Connected to server")
            
            # Send session start message
            await self.websocket.send(json.dumps({
                "type": "session_start",
                "session_id": self.session_id
            }))
            
            logger.info("Session started")
        
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        try:
            if self.websocket:
                await self.websocket.send(json.dumps({
                    "type": "session_stop",
                    "session_id": self.session_id
                }))
                await self.websocket.close()
            
            logger.info("Disconnected from server")
        
        except Exception as e:
            logger.error(f"Disconnection error: {e}")
    
    def audio_callback(self, indata: np.ndarray, frames: int, time, status):
        """Callback for audio stream"""
        if status:
            logger.warning(f"Audio status: {status}")
        
        # Process audio data
        audio_chunk = indata[:, 0].copy()  # Get first channel
        
        # Queue for sending (would normally use a queue here for production)
        asyncio.create_task(self._send_audio_chunk(audio_chunk))
    
    async def _send_audio_chunk(self, audio_chunk: np.ndarray):
        """Send audio chunk to server"""
        try:
            if not self.websocket or self.websocket.closed:
                return
            
            # Convert float32 to int16
            audio_int16 = (audio_chunk * 32768).astype(np.int16)
            
            # Encode to bytes
            audio_bytes = audio_int16.tobytes()
            
            # Base64 encode
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Send via WebSocket
            message = {
                "type": "audio",
                "audio_data": audio_b64,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent audio chunk ({len(audio_b64)} bytes)")
        
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
    
    async def receive_messages(self):
        """Receive and display messages from server"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self._display_message(data)
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
    
    def _display_message(self, data: dict):
        """Display server message"""
        msg_type = data.get('type')
        
        if msg_type == 'transcription':
            self._display_transcription(data)
        elif msg_type == 'error':
            logger.error(f"Server error: {data.get('error')}")
        elif msg_type == 'connection_established':
            logger.info(f"Connection established: {data.get('session_id')}")
        elif msg_type == 'session_ended':
            logger.info("Session ended")
        else:
            logger.debug(f"Received: {msg_type}")
    
    def _display_transcription(self, data: dict):
        """Display transcription and analysis"""
        text = data.get('text', '')
        analysis = data.get('analysis', {})
        lead_score = data.get('lead_score', {})
        
        print("\n" + "="*80)
        print("TRANSCRIPTION UPDATE")
        print("="*80)
        
        print(f"\nText: {text}")
        
        # Lead score
        score = lead_score.get('score', 0)
        qualification = lead_score.get('qualification', 'UNKNOWN')
        print(f"\nLead Score: {score:.0f}% - {qualification}")
        
        # Emotion
        emotion = analysis.get('emotion', {})
        if emotion:
            print(f"\nEmotion: {emotion.get('emoji', '😐')} {emotion.get('emotion', 'neutral').title()} ({emotion.get('confidence', 'N/A')})")
        
        # BANT
        bant = analysis.get('bant_summary', {})
        if bant:
            print("\nBANT:")
            print(f"  Budget: {bant.get('budget', 'Not detected')}")
            print(f"  Authority: {bant.get('authority', 'Not detected')}")
            print(f"  Need: {bant.get('need', 'Not detected')}")
            print(f"  Timeline: {bant.get('timeline', 'Not detected')}")
        
        # Intent
        intent = analysis.get('intent', {})
        if intent:
            print(f"\nIntent: {intent.get('intent', 'Unknown').title()} ({intent.get('confidence', 'N/A')})")
        
        # Buying Readiness
        readiness = analysis.get('buying_readiness', {})
        if readiness:
            print(f"\nBuying Readiness: {readiness.get('readiness', 'UNKNOWN')} ({readiness.get('score', 0):.0%})")
        
        # Objections
        objections = analysis.get('objections', {})
        if objections and objections.get('count', 0) > 0:
            print(f"\nObjections ({objections.get('count')}):")
            for obj in objections.get('objections', [])[:3]:
                print(f"  • {obj.get('type')} ({obj.get('severity')})")
        
        # ICP Match
        icp = analysis.get('icp_match', {})
        if icp:
            print(f"\nICP Match: Tier {icp.get('tier', 'N/A')} ({icp.get('score', 'N/A')})")
        
        # Key Insights
        insights = analysis.get('key_insights', [])
        if insights:
            print("\nKey Insights:")
            for insight in insights[:3]:
                print(f"  • {insight}")
        
        # Recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            print("\nRecommendations:")
            for rec in recommendations[:3]:
                print(f"  • {rec}")
        
        print("="*80 + "\n")
    
    async def start_recording(self):
        """Start recording from microphone"""
        try:
            logger.info("Starting recording...")
            
            # Connect to server
            await self.connect()
            
            # Start audio stream
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                blocksize=self.chunk_size,
                callback=self.audio_callback
            )
            
            self.stream.start()
            self.is_recording = True
            
            logger.info("Recording started. Listening to microphone...")
            
            # Receive messages from server
            await self.receive_messages()
        
        except KeyboardInterrupt:
            logger.info("Recording stopped by user")
        except Exception as e:
            logger.error(f"Recording error: {e}")
        finally:
            await self.stop_recording()
    
    async def stop_recording(self):
        """Stop recording"""
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.is_recording = False
            
            await self.disconnect()
            logger.info("Recording stopped")
        
        except Exception as e:
            logger.error(f"Stop recording error: {e}")


async def main():
    """Main entry point"""
    client = MicrophoneClient(
        server_url="ws://localhost:8000/ws",
        sample_rate=16000,
        chunk_duration=2.0
    )
    
    try:
        await client.start_recording()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
