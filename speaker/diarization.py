"""
Speaker Diarization Module
Separates and identifies different speakers in a conversation
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SpeakerSegment:
    """Speaker segment with timing"""
    speaker_id: str
    start_time: float
    end_time: float
    duration: float
    confidence: float
    speaker_type: str  # "customer" or "salesperson"


@dataclass
class DiarizationResult:
    """Complete diarization result"""
    segments: List[SpeakerSegment]
    speaker_labels: Dict[str, str]  # speaker_id -> "customer"/"salesperson"
    total_duration: float
    customer_time: float
    salesperson_time: float
    turn_taking_count: int


class SpeakerDiarizer:
    """
    Speaker diarization using pyannote.audio
    
    Identifies and separates different speakers in a conversation
    """
    
    def __init__(self, use_auth_token: Optional[str] = None):
        """
        Initialize speaker diarizer
        
        Args:
            use_auth_token: HuggingFace auth token for pyannote models
        """
        self.use_auth_token = use_auth_token
        self.pipeline = None
        self.speaker_mapping: Dict[str, str] = {}
        
        # Try to import pyannote
        try:
            from pyannote.audio import Pipeline
            self.pyannote_available = True
            logger.info("pyannote.audio available")
        except ImportError:
            self.pyannote_available = False
            logger.warning("pyannote.audio not available. Install with: pip install pyannote.audio")
    
    def _load_pipeline(self):
        """Load pyannote diarization pipeline"""
        if not self.pyannote_available or self.pipeline is not None:
            return
        
        try:
            from pyannote.audio import Pipeline
            
            # Use pre-trained diarization model
            # Requires HuggingFace auth token
            if self.use_auth_token:
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.use_auth_token
                )
                logger.info("Loaded pyannote diarization pipeline")
            else:
                logger.warning("No auth token provided. Using fallback method.")
                self.pipeline = None
        
        except Exception as e:
            logger.error(f"Failed to load pyannote pipeline: {e}")
            self.pipeline = None
    
    def diarize(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        num_speakers: int = 2
    ) -> DiarizationResult:
        """
        Perform speaker diarization
        
        Args:
            audio: Audio signal as numpy array
            sample_rate: Sample rate
            num_speakers: Expected number of speakers (default: 2)
            
        Returns:
            DiarizationResult with speaker segments
        """
        if len(audio) == 0:
            return self._empty_result()
        
        # Try pyannote if available
        if self.pyannote_available:
            try:
                self._load_pipeline()
                if self.pipeline is not None:
                    return self._diarize_with_pyannote(audio, sample_rate, num_speakers)
            except Exception as e:
                logger.warning(f"pyannote diarization failed: {e}, using fallback")
        
        # Fallback to energy-based diarization
        return self._diarize_fallback(audio, sample_rate)
    
    def _diarize_with_pyannote(
        self,
        audio: np.ndarray,
        sample_rate: int,
        num_speakers: int
    ) -> DiarizationResult:
        """Diarize using pyannote pipeline"""
        import torch
        from pyannote.core import Annotation
        
        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio).float().unsqueeze(0)
        
        # Run diarization
        diarization = self.pipeline(
            {"waveform": audio_tensor, "sample_rate": sample_rate},
            num_speakers=num_speakers
        )
        
        # Convert to segments
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segment = SpeakerSegment(
                speaker_id=speaker,
                start_time=turn.start,
                end_time=turn.end,
                duration=turn.end - turn.start,
                confidence=0.9,  # pyannote doesn't provide confidence
                speaker_type="unknown"
            )
            segments.append(segment)
        
        # Assign speaker types (customer vs salesperson)
        result = self._assign_speaker_types(segments)
        
        return result
    
    def _diarize_fallback(self, audio: np.ndarray, sample_rate: int) -> DiarizationResult:
        """
        Fallback diarization using energy-based voice activity detection
        
        This is a simple fallback when pyannote is not available
        """
        # Calculate energy in frames
        frame_duration = 0.1  # 100ms frames
        frame_size = int(frame_duration * sample_rate)
        
        frames = []
        for i in range(0, len(audio) - frame_size, frame_size):
            frame = audio[i:i + frame_size]
            energy = np.sqrt(np.mean(frame ** 2))
            frames.append(energy)
        
        if not frames:
            return self._empty_result()
        
        # Detect speech segments
        threshold = np.mean(frames) * 1.5
        speech_frames = [e > threshold for e in frames]
        
        # Group consecutive speech frames
        segments = []
        current_start = None
        
        for i, is_speech in enumerate(speech_frames):
            if is_speech and current_start is None:
                current_start = i * frame_duration
            elif not is_speech and current_start is not None:
                end_time = i * frame_duration
                duration = end_time - current_start
                
                if duration >= 0.5:  # Minimum 0.5s segment
                    # Alternate between speakers
                    speaker_id = f"SPEAKER_{len(segments) % 2:02d}"
                    segment = SpeakerSegment(
                        speaker_id=speaker_id,
                        start_time=current_start,
                        end_time=end_time,
                        duration=duration,
                        confidence=0.7,
                        speaker_type="unknown"
                    )
                    segments.append(segment)
                
                current_start = None
        
        # Handle last segment
        if current_start is not None:
            end_time = len(speech_frames) * frame_duration
            duration = end_time - current_start
            if duration >= 0.5:
                speaker_id = f"SPEAKER_{len(segments) % 2:02d}"
                segment = SpeakerSegment(
                    speaker_id=speaker_id,
                    start_time=current_start,
                    end_time=end_time,
                    duration=duration,
                    confidence=0.7,
                    speaker_type="unknown"
                )
                segments.append(segment)
        
        # Assign speaker types
        result = self._assign_speaker_types(segments)
        
        return result
    
    def _assign_speaker_types(self, segments: List[SpeakerSegment]) -> DiarizationResult:
        """
        Assign speaker types (customer vs salesperson)
        
        Heuristic: First speaker is usually salesperson, second is customer
        """
        if not segments:
            return self._empty_result()
        
        # Get unique speakers
        unique_speakers = list(set(s.speaker_id for s in segments))
        
        # Assign types based on order
        # First speaker = salesperson, second = customer
        speaker_labels = {}
        for i, speaker_id in enumerate(unique_speakers):
            if i == 0:
                speaker_labels[speaker_id] = "salesperson"
            else:
                speaker_labels[speaker_id] = "customer"
        
        # Update segments with speaker types
        for segment in segments:
            segment.speaker_type = speaker_labels.get(segment.speaker_id, "unknown")
        
        # Calculate statistics
        total_duration = sum(s.duration for s in segments)
        customer_time = sum(s.duration for s in segments if s.speaker_type == "customer")
        salesperson_time = sum(s.duration for s in segments if s.speaker_type == "salesperson")
        
        # Count turn-taking
        turn_taking_count = 0
        prev_speaker = None
        for segment in segments:
            if segment.speaker_id != prev_speaker:
                turn_taking_count += 1
                prev_speaker = segment.speaker_id
        
        return DiarizationResult(
            segments=segments,
            speaker_labels=speaker_labels,
            total_duration=total_duration,
            customer_time=customer_time,
            salesperson_time=salesperson_time,
            turn_taking_count=turn_taking_count
        )
    
    def _empty_result(self) -> DiarizationResult:
        """Return empty diarization result"""
        return DiarizationResult(
            segments=[],
            speaker_labels={},
            total_duration=0.0,
            customer_time=0.0,
            salesperson_time=0.0,
            turn_taking_count=0
        )
    
    def get_speaker_transcript(
        self,
        segments: List[SpeakerSegment],
        transcript: str
    ) -> List[Dict]:
        """
        Map transcript to speakers
        
        Args:
            segments: Speaker segments
            transcript: Full transcript
            
        Returns:
            List of speaker-labeled transcript segments
        """
        if not segments:
            return [{"speaker": "unknown", "text": transcript}]
        
        # Simple word-based distribution
        words = transcript.split()
        total_words = len(words)
        
        if total_words == 0:
            return []
        
        # Distribute words based on segment duration
        total_duration = sum(s.duration for s in segments)
        if total_duration == 0:
            return [{"speaker": "unknown", "text": transcript}]
        
        speaker_transcripts = []
        word_index = 0
        
        for segment in segments:
            # Calculate words for this segment
            segment_ratio = segment.duration / total_duration
            num_words = int(total_words * segment_ratio)
            
            if num_words > 0 and word_index < total_words:
                segment_words = words[word_index:word_index + num_words]
                speaker_transcripts.append({
                    "speaker": segment.speaker_type,
                    "speaker_id": segment.speaker_id,
                    "text": " ".join(segment_words),
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "confidence": segment.confidence
                })
                word_index += num_words
        
        # Add remaining words to last segment
        if word_index < total_words and speaker_transcripts:
            remaining_words = words[word_index:]
            speaker_transcripts[-1]["text"] += " " + " ".join(remaining_words)
        
        return speaker_transcripts
    
    def get_speaker_statistics(self, result: DiarizationResult) -> Dict:
        """
        Get speaker statistics
        
        Args:
            result: Diarization result
            
        Returns:
            Statistics dictionary
        """
        if not result.segments:
            return {
                "total_speakers": 0,
                "customer_percentage": 0.0,
                "salesperson_percentage": 0.0,
                "avg_turn_duration": 0.0,
                "turn_taking_count": 0
            }
        
        total = result.total_duration if result.total_duration > 0 else 1
        
        return {
            "total_speakers": len(result.speaker_labels),
            "customer_percentage": round((result.customer_time / total) * 100, 1),
            "salesperson_percentage": round((result.salesperson_time / total) * 100, 1),
            "avg_turn_duration": round(total / len(result.segments), 2) if result.segments else 0,
            "turn_taking_count": result.turn_taking_count
        }


class SpeakerDiarizationFactory:
    """Factory for creating speaker diarizer instances"""
    
    @staticmethod
    def create(use_auth_token: Optional[str] = None) -> SpeakerDiarizer:
        """
        Create speaker diarizer instance
        
        Args:
            use_auth_token: HuggingFace auth token
            
        Returns:
            SpeakerDiarizer instance
        """
        return SpeakerDiarizer(use_auth_token=use_auth_token)