"""
Audio Buffer and Voice Activity Detection (VAD)
Handles buffering and speech detection for streaming audio
"""

import numpy as np
from typing import Tuple, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)

class AudioBuffer:
    """
    Buffers incoming audio chunks and provides continuous audio with overlap
    """
    
    def __init__(self, sample_rate: int = 16000, chunk_duration: float = 2.0, overlap: float = 0.5):
        """
        Initialize audio buffer
        
        Args:
            sample_rate: Audio sample rate (Hz)
            chunk_duration: Duration of each chunk (seconds)
            overlap: Overlap between chunks (seconds)
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.overlap = overlap
        
        self.chunk_size = int(sample_rate * chunk_duration)
        self.overlap_size = int(sample_rate * overlap)
        self.step_size = self.chunk_size - self.overlap_size
        
        # Buffer to hold audio
        self.buffer = deque(maxlen=int(sample_rate * (chunk_duration + overlap)))
        
        # Timestamps
        self.chunk_count = 0
    
    def add_chunk(self, audio_chunk: np.ndarray) -> None:
        """Add audio chunk to buffer"""
        for sample in audio_chunk:
            self.buffer.append(sample)
    
    def get_chunk(self) -> Tuple[Optional[np.ndarray], float, float]:
        """
        Get buffered audio chunk if enough data
        
        Returns:
            Tuple of (audio_array, start_time, end_time) or (None, None, None)
        """
        if len(self.buffer) < self.chunk_size:
            return None, None, None
        
        # Get chunk
        audio = np.array(list(self.buffer)[:self.chunk_size])
        
        # Calculate timestamps
        start_time = self.chunk_count * (self.step_size / self.sample_rate)
        end_time = start_time + (self.chunk_size / self.sample_rate)
        
        # Increment chunk counter
        self.chunk_count += 1
        
        return audio, start_time, end_time
    
    def clear(self) -> None:
        """Clear buffer"""
        self.buffer.clear()


class VADBuffer:
    """
    Voice Activity Detection Buffer
    Detects speech and groups frames
    """
    
    def __init__(self, sample_rate: int = 16000, frame_duration: float = 0.02):
        """
        Initialize VAD buffer
        
        Args:
            sample_rate: Audio sample rate (Hz)
            frame_duration: Duration of each frame (seconds)
        """
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.frame_size = int(sample_rate * frame_duration)
        
        # Energy thresholds
        self.silence_threshold = -40  # dB
        self.noise_threshold = -30    # dB
        
        # Speech detection state
        self.is_speech = False
        self.speech_frames = []
        self.silence_count = 0
        self.silence_duration_threshold = 0.5  # seconds
        self.silence_frame_threshold = int(self.silence_duration_threshold / frame_duration)
    
    def is_silence(self, audio_frame: np.ndarray) -> bool:
        """
        Determine if frame is silence
        
        Args:
            audio_frame: Audio frame (numpy array)
        
        Returns:
            True if silence, False if speech
        """
        # Calculate energy
        energy = np.mean(audio_frame ** 2)
        
        if energy == 0:
            energy_db = -np.inf
        else:
            energy_db = 10 * np.log10(energy)
        
        return energy_db < self.silence_threshold
    
    def process_frame(self, audio_frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Process audio frame and detect speech segments
        
        Args:
            audio_frame: Audio frame to process
        
        Returns:
            Speech segment if detected, None otherwise
        """
        # Check for speech
        if not self.is_silence(audio_frame):
            self.is_speech = True
            self.silence_count = 0
            self.speech_frames.append(audio_frame)
        else:
            if self.is_speech:
                self.silence_count += 1
            
            # Check if silence is long enough to end speech
            if self.silence_count >= self.silence_frame_threshold and self.speech_frames:
                # End of speech segment
                speech_audio = np.concatenate(self.speech_frames)
                self.speech_frames = []
                self.is_speech = False
                self.silence_count = 0
                return speech_audio
        
        return None
    
    def get_speech_segment(self) -> Optional[np.ndarray]:
        """Get current speech segment if enough frames"""
        if len(self.speech_frames) > 0:
            return np.concatenate(self.speech_frames)
        return None
    
    def clear(self) -> None:
        """Clear state"""
        self.speech_frames = []
        self.is_speech = False
        self.silence_count = 0
