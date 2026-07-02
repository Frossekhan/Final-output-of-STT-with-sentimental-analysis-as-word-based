"""
Audio buffer management for streaming transcription
"""
import numpy as np
import io
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class AudioBuffer:
    def __init__(self, sample_rate: int = 16000, buffer_duration: float = 2.0):
        """
        Audio buffer for streaming transcription
        
        Args:
            sample_rate: Audio sample rate (Whisper uses 16kHz)
            buffer_duration: Duration of audio chunks in seconds
        """
        self.sample_rate = sample_rate
        self.buffer_duration = buffer_duration
        self.buffer_size = int(sample_rate * buffer_duration)
        self.buffer: List[float] = []
        self.overlap_size = int(sample_rate * 0.5)  # 0.5 second overlap
        
    def add_audio(self, audio_data: bytes) -> Optional[np.ndarray]:
        """
        Add audio data to buffer and return chunk if buffer is full
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM)
            
        Returns:
            numpy array of audio samples if buffer is full, None otherwise
        """
        # Convert bytes to numpy array (16-bit PCM)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Convert to float32 and normalize
        audio_float = audio_array.astype(np.float32) / 32768.0
        
        # Add to buffer
        self.buffer.extend(audio_float.tolist())
        
        # Check if buffer is full
        if len(self.buffer) >= self.buffer_size:
            return self._get_chunk()
        
        return None
    
    def _get_chunk(self) -> np.ndarray:
        """Extract chunk from buffer with overlap"""
        chunk = np.array(self.buffer[:self.buffer_size], dtype=np.float32)
        
        # Keep overlap for next chunk
        self.buffer = self.buffer[self.buffer_size - self.overlap_size:]
        
        return chunk
    
    def get_remaining(self) -> np.ndarray:
        """Get remaining audio in buffer"""
        if len(self.buffer) > 0:
            return np.array(self.buffer, dtype=np.float32)
        return np.array([], dtype=np.float32)
    
    def clear(self):
        """Clear the buffer"""
        self.buffer = []
    
    def get_duration(self) -> float:
        """Get current buffer duration in seconds"""
        return len(self.buffer) / self.sample_rate
    
    def is_ready(self) -> bool:
        """Check if buffer has enough audio for transcription"""
        return len(self.buffer) >= self.buffer_size


class VADBuffer:
    """Voice Activity Detection buffer"""
    
    def __init__(self, energy_threshold: float = 0.01, min_speech_duration: float = 0.5):
        self.energy_threshold = energy_threshold
        self.min_speech_duration = min_speech_duration
        self.speech_frames: List[np.ndarray] = []
        self.is_speaking = False
        self.silence_frames = 0
        self.max_silence_frames = int(1.0 * 16000 / 1024)  # 1 second of silence
        
    def detect_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Simple energy-based VAD
        
        Args:
            audio_chunk: numpy array of audio samples
            
        Returns:
            True if speech detected, False otherwise
        """
        # Calculate RMS energy
        energy = np.sqrt(np.mean(audio_chunk ** 2))
        return energy > self.energy_threshold
    
    def process_chunk(self, audio_chunk: np.ndarray) -> Optional[np.ndarray]:
        """
        Process audio chunk with VAD
        
        Returns:
            Audio chunk if speech segment is complete, None otherwise
        """
        has_speech = self.detect_speech(audio_chunk)
        
        if has_speech:
            self.speech_frames.append(audio_chunk)
            self.silence_frames = 0
            self.is_speaking = True
        elif self.is_speaking:
            self.silence_frames += 1
            
            # End of speech segment
            if self.silence_frames >= self.max_silence_frames:
                if len(self.speech_frames) > 0:
                    # Combine all speech frames
                    speech_audio = np.concatenate(self.speech_frames)
                    self.speech_frames = []
                    self.is_speaking = False
                    return speech_audio
        
        return None
    
    def reset(self):
        """Reset VAD state"""
        self.speech_frames = []
        self.is_speaking = False
        self.silence_frames = 0