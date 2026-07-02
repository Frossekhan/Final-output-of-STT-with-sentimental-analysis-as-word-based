"""
Advanced Speech Emotion Recognition using SpeechBrain/WavLM
Replaces feature-based emotion detection with deep learning models
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EmotionResult:
    """Result of emotion detection"""
    emotion: str
    confidence: float
    all_scores: Dict[str, float]
    features: Dict[str, float]


class AdvancedSpeechEmotionRecognizer:
    """
    Advanced Speech Emotion Recognition using deep learning
    
    Supports:
    - SpeechBrain emotion models
    - WavLM-based emotion detection
    - 7 emotion categories for sales conversations
    """
    
    def __init__(self, model_name: str = "speechbrain"):
        """
        Initialize advanced emotion recognizer
        
        Args:
            model_name: Model to use ("speechbrain" or "wavlm")
        """
        self.model_name = model_name
        self.model = None
        self.emotions = [
            "interested",
            "excited",
            "confident",
            "confused",
            "frustrated",
            "happy",
            "neutral",
            "hesitant"
        ]
        
        # Try to load model
        self._load_model()
    
    def _load_model(self):
        """Load emotion recognition model"""
        if self.model_name == "speechbrain":
            self._load_speechbrain()
        elif self.model_name == "wavlm":
            self._load_wavlm()
        else:
            logger.warning(f"Unknown model: {self.model_name}, using fallback")
            self.model = None
    
    def _load_speechbrain(self):
        """Load SpeechBrain emotion model"""
        try:
            from speechbrain.pretrained import EncoderClassifier
            
            # Use SpeechBrain's emotion recognition model
            # Note: This requires downloading the model on first run
            self.model = EncoderClassifier.from_hparams(
                source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
                savedir="pretrained_models/emotion-recognition"
            )
            self.model_available = True
            logger.info("SpeechBrain emotion model loaded")
        
        except Exception as e:
            logger.warning(f"Failed to load SpeechBrain model: {e}")
            self.model = None
            self.model_available = False
    
    def _load_wavlm(self):
        """Load WavLM-based emotion model"""
        try:
            from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
            import torch
            
            # Use WavLM for emotion recognition
            model_name = "superb/wav2vec2-base-superb-er"  # Emotion recognition
            
            self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
            self.model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
            self.model_available = True
            logger.info("WavLM emotion model loaded")
        
        except Exception as e:
            logger.warning(f"Failed to load WavLM model: {e}")
            self.model = None
            self.model_available = False
    
    def detect_emotion(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000
    ) -> EmotionResult:
        """
        Detect emotion from audio
        
        Args:
            audio: Audio signal as numpy array
            sample_rate: Sample rate
            
        Returns:
            EmotionResult with detected emotion and confidence
        """
        if len(audio) == 0:
            return self._empty_result()
        
        # Try to use loaded model
        if self.model is not None:
            try:
                if self.model_name == "speechbrain":
                    return self._detect_with_speechbrain(audio, sample_rate)
                elif self.model_name == "wavlm":
                    return self._detect_with_wavlm(audio, sample_rate)
            except Exception as e:
                logger.warning(f"Model inference failed: {e}, using fallback")
        
        # Fallback to feature-based detection
        return self._detect_fallback(audio, sample_rate)
    
    def _detect_with_speechbrain(self, audio: np.ndarray, sample_rate: int) -> EmotionResult:
        """Detect emotion using SpeechBrain"""
        # Ensure correct sample rate
        if sample_rate != 16000:
            import librosa
            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=16000)
        
        # Run inference
        out_prob, score, index, text_lab = self.model.classify_batch(audio)
        
        # Map IEMOCAP emotions to our categories
        emotion_mapping = {
            "angry": "frustrated",
            "happy": "happy",
            "neutral": "neutral",
            "sad": "hesitant",
            "exc": "excited"
        }
        
        # Get probabilities
        probs = out_prob[0].cpu().numpy()
        
        # Map to our emotion categories
        emotion_scores = {emotion: 0.0 for emotion in self.emotions}
        
        for i, prob in enumerate(probs):
            original_emotion = text_lab[i]
            mapped_emotion = emotion_mapping.get(original_emotion, "neutral")
            emotion_scores[mapped_emotion] = float(prob)
        
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
            features={}
        )
    
    def _detect_with_wavlm(self, audio: np.ndarray, sample_rate: int) -> EmotionResult:
        """Detect emotion using WavLM"""
        import torch
        
        # Ensure correct sample rate
        if sample_rate != 16000:
            import librosa
            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=16000)
        
        # Prepare input
        inputs = self.feature_extractor(
            audio,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True
        )
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # Get probabilities
        probs = predictions[0].cpu().numpy()
        
        # Map to our emotion categories (simplified)
        emotion_mapping = {
            0: "neutral",
            1: "happy",
            2: "angry",  # Map to frustrated
            3: "sad",  # Map to hesitant
            4: "confused"
        }
        
        emotion_scores = {emotion: 0.0 for emotion in self.emotions}
        
        for i, prob in enumerate(probs):
            if i in emotion_mapping:
                emotion = emotion_mapping[i]
                if emotion in emotion_scores:
                    emotion_scores[emotion] = float(prob)
        
        # Normalize
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
            features={}
        )
    
    def _detect_fallback(self, audio: np.ndarray, sample_rate: int) -> EmotionResult:
        """
        Fallback to feature-based detection
        
        Uses the original feature-based method when models aren't available
        """
        from emotion.speech_emotion import SpeechEmotionRecognizer
        
        recognizer = SpeechEmotionRecognizer()
        return recognizer.detect_emotion(audio, sample_rate)
    
    def _empty_result(self) -> EmotionResult:
        """Return empty result"""
        return EmotionResult(
            emotion="neutral",
            confidence=0.0,
            all_scores={e: 0.0 for e in self.emotions},
            features={}
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
    
    def get_emotion_timeline(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        segment_duration: float = 2.0
    ) -> List[Dict]:
        """
        Get emotion timeline over the audio
        
        Args:
            audio: Complete audio signal
            sample_rate: Sample rate
            segment_duration: Duration of each segment
            
        Returns:
            List of emotion timeline entries
        """
        results = self.detect_emotion_from_segments(audio, sample_rate, segment_duration)
        
        timeline = []
        for i, result in enumerate(results):
            timeline.append({
                "segment": i,
                "start_time": i * segment_duration,
                "end_time": (i + 1) * segment_duration,
                "emotion": result.emotion,
                "confidence": result.confidence,
                "all_scores": result.all_scores
            })
        
        return timeline


class AdvancedEmotionRecognizerFactory:
    """Factory for creating advanced emotion recognizer instances"""
    
    @staticmethod
    def create(model_name: str = "speechbrain") -> AdvancedSpeechEmotionRecognizer:
        """
        Create advanced emotion recognizer
        
        Args:
            model_name: Model to use ("speechbrain" or "wavlm")
            
        Returns:
            AdvancedSpeechEmotionRecognizer instance
        """
        return AdvancedSpeechEmotionRecognizer(model_name=model_name)