"""
Real-time streaming audio processor with faster-whisper
"""
import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Callable
from faster_whisper import WhisperModel
from .audio_buffer import AudioBuffer, VADBuffer

logger = logging.getLogger(__name__)


class StreamProcessor:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: Optional[str] = None,
    ):
        """
        Initialize streaming processor
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            compute_type: Computation type (int8, float16, float32)
            language: Language code (None for auto-detect)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.model: Optional[WhisperModel] = None
        
        # Audio processing
        self.audio_buffer = AudioBuffer(sample_rate=16000, buffer_duration=2.0)
        self.vad_buffer = VADBuffer()
        
        # Transcription state
        self.transcription_history: List[str] = []
        self.is_processing = False
        
    async def initialize(self):
        """Load the Whisper model"""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            logger.info("Whisper model loaded successfully")
    
    def process_audio_chunk(self, audio_data: bytes) -> Optional[Dict]:
        """
        Process incoming audio chunk
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM, 16kHz)
            
        Returns:
            Transcription result if available, None otherwise
        """
        if self.model is None:
            logger.error("Model not initialized")
            return None
        
        # Add audio to buffer
        chunk = self.audio_buffer.add_audio(audio_data)
        
        if chunk is None:
            return None
        
        # Process with VAD
        speech_segment = self.vad_buffer.process_chunk(chunk)
        
        if speech_segment is None:
            return None
        
        # Transcribe speech segment
        try:
            segments, info = self.model.transcribe(
                speech_segment,
                language=self.language,
                task="transcribe",
                vad_filter=False,
                word_timestamps=True,
            )
            
            segments_list = list(segments)
            
            if not segments_list:
                return None
            
            # Extract text
            text = " ".join([seg.text for seg in segments_list]).strip()
            
            if not text:
                return None
            
            # Get timing info
            start_time = segments_list[0].start
            end_time = segments_list[-1].end
            
            # Create result
            result = {
                "type": "transcription",
                "text": text,
                "start": start_time,
                "end": end_time,
                "language": info.language,
                "language_probability": info.language_probability,
            }
            
            # Add to history
            self.transcription_history.append(text)
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def process_audio_file(self, audio_data: bytes) -> Dict:
        """
        Process complete audio file (for non-streaming mode)
        
        Args:
            audio_data: Complete audio file bytes
            
        Returns:
            Complete transcription result
        """
        if self.model is None:
            raise RuntimeError("Model not initialized")
        
        import io
        
        # Convert to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        audio_float = audio_array.astype(np.float32) / 32768.0
        
        # Transcribe
        segments, info = self.model.transcribe(
            audio_float,
            language=self.language,
            task="transcribe",
            vad_filter=True,
            word_timestamps=False,
        )
        
        segments_list = list(segments)
        text = " ".join([seg.text for seg in segments_list]).strip()
        
        return {
            "type": "transcription",
            "text": text,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "duration_after_vad": info.duration_after_vad,
            "segments": [
                {
                    "id": i,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                }
                for i, seg in enumerate(segments_list)
            ],
        }
    
    def get_full_transcript(self) -> str:
        """Get complete transcript from history"""
        return " ".join(self.transcription_history)
    
    def reset(self):
        """Reset processor state"""
        self.audio_buffer.clear()
        self.vad_buffer.reset()
        self.transcription_history = []


class StreamingTranscriptionService:
    """Service for managing multiple streaming sessions"""
    
    def __init__(self, model_size: str = "base", device: str = "cpu"):
        self.model_size = model_size
        self.device = device
        self.processors: Dict[str, StreamProcessor] = {}
        
    async def get_or_create_processor(self, session_id: str) -> StreamProcessor:
        """Get or create a processor for a session"""
        if session_id not in self.processors:
            processor = StreamProcessor(
                model_size=self.model_size,
                device=self.device,
            )
            await processor.initialize()
            self.processors[session_id] = processor
        
        return self.processors[session_id]
    
    def remove_processor(self, session_id: str):
        """Remove a processor for a session"""
        if session_id in self.processors:
            del self.processors[session_id]
    
    async def process_streaming_audio(
        self,
        session_id: str,
        audio_chunks: List[bytes],
        callback: Callable[[Dict], None],
    ):
        """
        Process streaming audio and call callback with results
        
        Args:
            session_id: Session identifier
            audio_chunks: List of audio chunks
            callback: Function to call with transcription results
        """
        processor = await self.get_or_create_processor(session_id)
        
        for chunk in audio_chunks:
            result = processor.process_audio_chunk(chunk)
            if result:
                await callback(result)
    
    def get_transcript(self, session_id: str) -> str:
        """Get full transcript for a session"""
        if session_id in self.processors:
            return self.processors[session_id].get_full_transcript()
        return ""
    
    def reset_session(self, session_id: str):
        """Reset a session"""
        if session_id in self.processors:
            self.processors[session_id].reset()