"""
Production Real-Time Audio Client
Captures live audio from microphone and streams to WebSocket
"""
import asyncio
import websockets
import sounddevice as sd
import numpy as np
import logging
from typing import Optional, Callable
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeAudioClient:
    """
    Real-time audio capture and streaming client
    Streams audio from microphone to WebSocket server
    """
    
    def __init__(self, 
                 server_url: str = "ws://localhost:8000/ws/stream",
                 sample_rate: int = 16000,
                 chunk_duration_ms: int = 100,
                 channels: int = 1):
        """
        Initialize audio client
        
        Args:
            server_url: WebSocket server URL
            sample_rate: Audio sample rate (Hz)
            chunk_duration_ms: Chunk duration in milliseconds
            channels: Number of audio channels
        """
        self.server_url = server_url
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.channels = channels
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        
        self.websocket = None
        self.stream = None
        self.is_running = False
        self.chunks_sent = 0
        self.start_time = None
        
        # Metrics
        self.audio_queue = asyncio.Queue()
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio input (synchronous)"""
        if status:
            logger.warning(f"Audio status: {status}")
        
        # Convert audio to bytes
        audio_data = indata.astype(np.float32).tobytes()
        # Use thread-safe put_nowait instead of await
        try:
            self.audio_queue.put_nowait(audio_data)
        except asyncio.QueueFull:
            pass  # Skip if queue is full
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            logger.info(f"Connecting to {self.server_url}...")
            self.websocket = await websockets.connect(self.server_url)
            logger.info("✓ Connected to server")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from server")
    
    async def capture_audio(self):
        """Capture audio from microphone"""
        try:
            logger.info("🎤 Starting audio capture...")
            
            # Start audio stream
            self.stream = sd.InputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                dtype=np.float32,
                callback=self.audio_callback
            )
            self.stream.start()
            logger.info(f"✓ Audio capture started ({self.sample_rate}Hz, {self.channels}ch)")
            
        except Exception as e:
            logger.error(f"Audio capture error: {e}")
            raise
    
    async def send_audio_chunks(self):
        """Send audio chunks to server"""
        self.is_running = True
        self.start_time = datetime.now()
        
        try:
            while self.is_running:
                try:
                    # Get audio chunk from queue
                    audio_data = await asyncio.wait_for(
                        self.audio_queue.get(), 
                        timeout=1.0
                    )
                    
                    # Send to server
                    if self.websocket:
                        await self.websocket.send(audio_data)
                        self.chunks_sent += 1
                        
                        # Log progress every 10 chunks
                        if self.chunks_sent % 10 == 0:
                            elapsed = (datetime.now() - self.start_time).total_seconds()
                            rate = self.chunks_sent / elapsed if elapsed > 0 else 0
                            logger.info(f"Sent {self.chunks_sent} chunks ({rate:.1f} chunks/sec)")
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Send error: {e}")
                    break
        
        finally:
            self.is_running = False
    
    async def receive_analysis(self):
        """Receive and display analysis results"""
        try:
            while self.is_running:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=2.0
                    )
                    
                    # Parse message
                    data = json.loads(message)
                    
                    if data.get("type") == "metrics":
                        self._display_metrics(data.get("data", {}))
                    elif data.get("type") == "analysis":
                        self._display_analysis(data.get("data", {}))
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Receive error: {e}")
                    break
        
        finally:
            pass
    
    def _display_metrics(self, metrics: dict):
        """Display streaming metrics"""
        logger.info(f"📊 Metrics: {metrics}")
    
    def _display_analysis(self, analysis: dict):
        """Display analysis results"""
        logger.info(f"📈 Analysis: {analysis}")
    
    async def run(self):
        """Main run loop"""
        try:
            # Connect to server
            if not await self.connect():
                return
            
            # Capture audio
            await self.capture_audio()
            
            # Run concurrent tasks
            await asyncio.gather(
                self.send_audio_chunks(),
                self.receive_analysis()
            )
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Runtime error: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🛑 Cleaning up...")
        
        self.is_running = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            logger.info("Audio stream closed")
        
        await self.disconnect()
        
        # Print final stats
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"Total session time: {elapsed:.1f}s")
            logger.info(f"Total chunks sent: {self.chunks_sent}")
            logger.info(f"Average rate: {self.chunks_sent/elapsed:.1f} chunks/sec")


async def main():
    """Main entry point"""
    client = RealtimeAudioClient(
        server_url="ws://localhost:8000/ws/stream",
        sample_rate=16000,
        chunk_duration_ms=100
    )
    
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
