"""
Advanced Streaming Handler
Handles real-time audio streaming with proper buffering and processing
"""
import asyncio
import logging
from typing import Callable, Optional, Dict, Any
from collections import deque
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamBuffer:
    """Thread-safe buffer for audio streaming"""
    
    def __init__(self, max_size: int = 160000):
        self.buffer = deque(maxlen=max_size)
        self.lock = asyncio.Lock()
        
    async def add(self, data: bytes):
        """Add audio data to buffer"""
        async with self.lock:
            self.buffer.extend(np.frombuffer(data, dtype=np.float32))
    
    async def get_chunk(self, size: int) -> Optional[np.ndarray]:
        """Get chunk from buffer"""
        async with self.lock:
            if len(self.buffer) >= size:
                chunk = np.array([self.buffer.popleft() for _ in range(size)])
                return chunk
        return None
    
    async def get_all(self) -> np.ndarray:
        """Get all buffered audio"""
        async with self.lock:
            data = np.array(list(self.buffer))
            self.buffer.clear()
            return data
    
    async def size(self) -> int:
        """Get current buffer size"""
        async with self.lock:
            return len(self.buffer)
    
    async def clear(self):
        """Clear buffer"""
        async with self.lock:
            self.buffer.clear()


class StreamMetrics:
    """Track streaming performance metrics"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.chunks_received = 0
        self.bytes_received = 0
        self.processing_times = deque(maxlen=100)
        self.errors = 0
    
    def record_chunk(self, size: int, processing_time: float):
        """Record chunk statistics"""
        self.chunks_received += 1
        self.bytes_received += size
        self.processing_times.append(processing_time)
    
    def record_error(self):
        """Record error"""
        self.errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        avg_time = np.mean(list(self.processing_times)) if self.processing_times else 0
        
        return {
            "elapsed_seconds": elapsed,
            "chunks_received": self.chunks_received,
            "bytes_received": self.bytes_received,
            "avg_processing_time_ms": avg_time * 1000,
            "errors": self.errors,
            "chunks_per_second": self.chunks_received / elapsed if elapsed > 0 else 0
        }


class StreamProcessor:
    """Process audio stream with callback"""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 chunk_duration_ms: int = 100,
                 callback: Optional[Callable] = None):
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        self.callback = callback
        self.buffer = StreamBuffer()
        self.metrics = StreamMetrics()
        self.is_running = False
    
    async def add_audio(self, audio_data: bytes):
        """Add audio data to processing pipeline"""
        try:
            await self.buffer.add(audio_data)
            self.metrics.record_chunk(len(audio_data), 0)
        except Exception as e:
            logger.error(f"Error adding audio: {e}")
            self.metrics.record_error()
    
    async def process_stream(self):
        """Process audio stream"""
        self.is_running = True
        while self.is_running:
            try:
                chunk = await self.buffer.get_chunk(self.chunk_size)
                if chunk is not None and self.callback:
                    start_time = datetime.now()
                    await self.callback(chunk)
                    processing_time = (datetime.now() - start_time).total_seconds()
                    self.metrics.record_chunk(len(chunk), processing_time)
                else:
                    await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error processing stream: {e}")
                self.metrics.record_error()
                await asyncio.sleep(0.1)
    
    async def stop(self):
        """Stop processing"""
        self.is_running = False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.get_stats()
