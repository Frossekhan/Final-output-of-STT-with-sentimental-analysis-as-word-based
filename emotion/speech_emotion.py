"""
Speech Emotion Recognition using audio features
Replaces word-based sentiment analysis with voice-based emotion detection
"""
import numpy as np
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmotionResult:
    """Result of emotion detection"""
    emotion: str
    confidence: float
    all_scores: Dict[str, float]
    features: Dict[str, float]


class SpeechEmotionRecognizer:
    """
    Speech Emotion Recognition using audio features
    
    Detects emotions from voice characteristics:
    - Pitch and prosody
    - Energy and intensity
    - Speaking rate
    - Voice quality
    """
    
    def __init__(self):
        # Emotion categories for sales conversations
        self.emotions = [
            "interested",
            "excited",
            "confident",
            "frustrated",
            "hesitant",
            "angry",
            "neutral",
            "skeptical",
            "curious",
            "anxious"
        ]
        
        # Feature weights for emotion detection
        self.emotion_weights = {
            "interested": {
                "energy": 0.3,
                "pitch_variation": 0.3,
                "speaking_rate": 0.2,
                "clarity": 0.2
            },
            "excited": {
                "energy": 0.4,
                "pitch_variation": 0.3,
                "speaking_rate": 0.2,
                "emphasis": 0.1
            },
            "confident": {
                "stability": 0.3,
                "clarity": 0.3,
                "energy": 0.2,
                "pace": 0.2
            },
            "frustrated": {
                "energy": 0.3,
                "tension": 0.3,
                "pace": 0.2,
                "emphasis": 0.2
            },
            "hesitant": {
                "pause_frequency": 0.4,
                "pace": 0.3,
                "stability": 0.3
            },
            "angry": {
                "energy": 0.35,
                "tension": 0.35,
                "pace": 0.2,
                "emphasis": 0.1
            },
            "neutral": {
                "stability": 0.4,
                "consistency": 0.3,
                "pace": 0.3
            },
            "skeptical": {
                "pause_frequency": 0.3,
                "pitch_variation": 0.3,
                "tone": 0.2,
                "pace": 0.2
            },
            "curious": {
                "pitch_variation": 0.3,
                "pause_frequency": 0.3,
                "energy": 0.2,
                "pace": 0.2
            },
            "anxious": {
                "tension": 0.3,
                "pace": 0.3,
                "stability": 0.2,
                "energy": 0.2
            }
        }
    
    def extract_features(self, audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, float]:
        """
        Extract audio features for emotion detection
        
        Args:
            audio: Audio signal as numpy array
            sample_rate: Sample rate of audio
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Energy (RMS)
        features["energy"] = self._calculate_energy(audio)
        
        # Pitch variation
        features["pitch_variation"] = self._calculate_pitch_variation(audio, sample_rate)
        
        # Speaking rate
        features["speaking_rate"] = self._calculate_speaking_rate(audio, sample_rate)
        
        # Stability (jitter/shimmer approximation)
        features["stability"] = self._calculate_stability(audio)
        
        # Pause frequency
        features["pause_frequency"] = self._calculate_pause_frequency(audio, sample_rate)
        
        # Pace (syllables per second approximation)
        features["pace"] = self._calculate_pace(audio, sample_rate)
        
        # Clarity (zero crossing rate)
        features["clarity"] = self._calculate_clarity(audio)
        
        # Tension (spectral features)
        features["tension"] = self._calculate_tension(audio)
        
        # Emphasis (dynamic range)
        features["emphasis"] = self._calculate_emphasis(audio)
        
        # Consistency
        features["consistency"] = self._calculate_consistency(audio)
        
        # Tone (spectral centroid)
        features["tone"] = self._calculate_tone_feature(audio, sample_rate)
        
        return features
    
    def _calculate_energy(self, audio: np.ndarray) -> float:
        """Calculate RMS energy"""
        if len(audio) == 0:
            return 0.0
        rms = np.sqrt(np.mean(audio ** 2))
        return min(1.0, rms * 10)  # Normalize
    
    def _calculate_pitch_variation(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate pitch variation using autocorrelation"""
        if len(audio) < sample_rate // 10:
            return 0.0
        
        # Simplified pitch variation using zero crossings
        zero_crossings = np.where(np.diff(np.sign(audio)))[0]
        pitch_changes = len(zero_crossings) / len(audio)
        
        return min(1.0, pitch_changes * 50)
    
    def _calculate_speaking_rate(self, audio: np.ndarray, sample_rate: int) -> float:
        """Estimate speaking rate from energy envelope"""
        if len(audio) == 0:
            return 0.0
        
        # Frame-based energy
        frame_size = int(0.025 * sample_rate)  # 25ms frames
        hop_size = int(0.010 * sample_rate)  # 10ms hop
        
        energies = []
        for i in range(0, len(audio) - frame_size, hop_size):
            frame = audio[i:i + frame_size]
            energies.append(np.sqrt(np.mean(frame ** 2)))
        
        if not energies:
            return 0.0
        
        # Count speech-like frames
        threshold = np.mean(energies) * 1.5
        speech_frames = sum(1 for e in energies if e > threshold)
        
        duration = len(audio) / sample_rate
        rate = speech_frames / max(duration, 0.1)
        
        return min(1.0, rate / 10)  # Normalize
    
    def _calculate_stability(self, audio: np.ndarray) -> float:
        """Calculate voice stability"""
        if len(audio) < 100:
            return 0.5
        
        # Calculate variance of energy in windows
        window_size = len(audio) // 10
        windows = [audio[i:i + window_size] for i in range(0, len(audio), window_size)]
        
        energies = [np.sqrt(np.mean(w ** 2)) for w in windows if len(w) > 0]
        
        if len(energies) < 2:
            return 0.5
        
        # Lower variance = more stable
        variance = np.var(energies)
        stability = 1.0 / (1.0 + variance * 100)
        
        return min(1.0, stability)
    
    def _calculate_pause_frequency(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate frequency of pauses"""
        if len(audio) == 0:
            return 0.0
        
        frame_size = int(0.1 * sample_rate)  # 100ms frames
        threshold = 0.01
        
        pauses = 0
        in_pause = False
        
        for i in range(0, len(audio) - frame_size, frame_size):
            frame = audio[i:i + frame_size]
            energy = np.sqrt(np.mean(frame ** 2))
            
            if energy < threshold:
                if not in_pause:
                    pauses += 1
                    in_pause = True
            else:
                in_pause = False
        
        duration = len(audio) / sample_rate
        pause_rate = pauses / max(duration, 0.1)
        
        return min(1.0, pause_rate / 2)
    
    def _calculate_pace(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate speaking pace"""
        if len(audio) == 0:
            return 0.0
        
        # Count energy peaks as proxy for syllables
        frame_size = int(0.05 * sample_rate)
        energies = []
        
        for i in range(0, len(audio) - frame_size, frame_size):
            frame = audio[i:i + frame_size]
            energies.append(np.sqrt(np.mean(frame ** 2)))
        
        if not energies:
            return 0.0
        
        threshold = np.mean(energies) * 1.2
        peaks = sum(1 for e in energies if e > threshold)
        
        duration = len(audio) / sample_rate
        pace = peaks / max(duration, 0.1)
        
        return min(1.0, pace / 5)
    
    def _calculate_clarity(self, audio: np.ndarray) -> float:
        """Calculate voice clarity using zero crossing rate"""
        if len(audio) < 2:
            return 0.0
        
        zero_crossings = np.sum(np.abs(np.diff(np.sign(audio))))
        zcr = zero_crossings / len(audio)
        
        # Normalize ZCR (typical speech: 0.01-0.1)
        clarity = min(1.0, zcr * 20)
        
        return clarity
    
    def _calculate_tension(self, audio: np.ndarray) -> float:
        """Calculate vocal tension"""
        if len(audio) < 100:
            return 0.0
        
        # High frequency energy ratio
        # Simplified: use variance of high-pass filtered signal
        high_pass = np.diff(audio)
        
        if len(high_pass) == 0:
            return 0.0
        
        high_freq_energy = np.sqrt(np.mean(high_pass ** 2))
        total_energy = np.sqrt(np.mean(audio ** 2))
        
        if total_energy == 0:
            return 0.0
        
        tension = (high_freq_energy / total_energy) * 10
        return min(1.0, tension)
    
    def _calculate_emphasis(self, audio: np.ndarray) -> float:
        """Calculate emphasis in speech"""
        if len(audio) == 0:
            return 0.0
        
        # Dynamic range
        max_val = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))
        
        if rms == 0:
            return 0.0
        
        dynamic_range = max_val / rms
        emphasis = min(1.0, (dynamic_range - 1) / 5)
        
        return max(0.0, emphasis)
    
    def _calculate_consistency(self, audio: np.ndarray) -> float:
        """Calculate consistency of speech"""
        if len(audio) < 200:
            return 0.5
        
        # Split into segments and compare
        segment_size = len(audio) // 5
        segments = [audio[i:i + segment_size] for i in range(0, len(audio), segment_size)]
        
        energies = [np.sqrt(np.mean(s ** 2)) for s in segments if len(s) > 0]
        
        if len(energies) < 2:
            return 0.5
        
        # Coefficient of variation (lower = more consistent)
        cv = np.std(energies) / (np.mean(energies) + 1e-6)
        consistency = 1.0 / (1.0 + cv * 5)
        
        return min(1.0, consistency)
    
    def _calculate_tone_feature(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate tone feature (spectral centroid approximation)"""
        if len(audio) < 100:
            return 0.0
        
        # Simplified spectral centroid using zero crossings
        # Higher ZCR = brighter tone
        zcr = np.sum(np.abs(np.diff(np.sign(audio)))) / len(audio)
        
        return min(1.0, zcr * 30)
    
    def detect_emotion(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> EmotionResult:
        """
        Detect emotion from audio
        
        Args:
            audio: Audio signal as numpy array
            sample_rate: Sample rate of audio
            
        Returns:
            EmotionResult with detected emotion and confidence
        """
        if len(audio) == 0:
            return EmotionResult(
                emotion="neutral",
                confidence=0.0,
                all_scores={e: 0.0 for e in self.emotions},
                features={}
            )
        
        # Extract features
        features = self.extract_features(audio, sample_rate)
        
        # Calculate emotion scores
        emotion_scores = {}
        for emotion in self.emotions:
            weights = self.emotion_weights.get(emotion, {})
            score = 0.0
            
            for feature, weight in weights.items():
                if feature in features:
                    score += features[feature] * weight
            
            emotion_scores[emotion] = min(1.0, score)
        
        # Normalize scores
        total = sum(emotion_scores.values())
        if total > 0:
            emotion_scores = {k: v / total for k, v in emotion_scores.items()}
        
        # Get top emotion
        top_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = emotion_scores[top_emotion]
        
        return EmotionResult(
            emotion=top_emotion,
            confidence=confidence,
            all_scores=emotion_scores,
            features=features
        )
    
    def detect_emotion_from_segments(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        segment_duration: float = 2.0
    ) -> List[EmotionResult]:
        """
        Detect emotion from audio segments
        
        Args:
            audio: Complete audio signal
            sample_rate: Sample rate
            segment_duration: Duration of each segment in seconds
            
        Returns:
            List of EmotionResult for each segment
        """
        segment_samples = int(segment_duration * sample_rate)
        results = []
        
        for i in range(0, len(audio), segment_samples):
            segment = audio[i:i + segment_samples]
            if len(segment) > 0:
                result = self.detect_emotion(segment, sample_rate)
                results.append(result)
        
        return results


class EmotionTracker:
    """Track emotion changes over time"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.emotion_history: List[EmotionResult] = []
        
    def add_emotion(self, result: EmotionResult):
        """Add emotion result to history"""
        self.emotion_history.append(result)
        
        # Keep only recent history
        if len(self.emotion_history) > self.window_size:
            self.emotion_history = self.emotion_history[-self.window_size:]
    
    def get_dominant_emotion(self) -> Tuple[str, float]:
        """Get dominant emotion from recent history"""
        if not self.emotion_history:
            return "neutral", 0.0
        
        # Count emotions
        emotion_counts = {}
        for result in self.emotion_history:
            emotion = result.emotion
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Get most common
        dominant = max(emotion_counts, key=emotion_counts.get)
        frequency = emotion_counts[dominant] / len(self.emotion_history)
        
        return dominant, frequency
    
    def get_emotion_trajectory(self) -> List[str]:
        """Get emotion trajectory over time"""
        return [result.emotion for result in self.emotion_history]
    
    def get_emotion_summary(self) -> Dict[str, float]:
        """Get summary of emotions"""
        if not self.emotion_history:
            return {}
        
        # Average scores for each emotion
        emotion_sums = {}
        for result in self.emotion_history:
            for emotion, score in result.all_scores.items():
                emotion_sums[emotion] = emotion_sums.get(emotion, 0.0) + score
        
        # Normalize
        n = len(self.emotion_history)
        return {k: v / n for k, v in emotion_sums.items()}