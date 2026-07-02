"""
Conversation Intelligence Engine
Central orchestrator that combines all analysis modules
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from emotion.speech_emotion import SpeechEmotionRecognizer, EmotionTracker, EmotionResult
from bant.parser import BANTEngine, BANTResult
from intent.predict import IntentDetector, IntentResult
from buying_signal.detect import BuyingSignalDetector, BuyingSignalAnalyzer
from objection.detect import ObjectionDetector, ObjectionAnalyzer
from icp.score import ICPScorer, ICPAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class ConversationFeatures:
    """Complete feature set from conversation analysis"""
    # Transcript
    transcript: str
    segments: List[Dict]
    
    # Speech Emotion
    emotion: str
    emotion_confidence: float
    emotion_scores: Dict[str, float]
    emotion_trajectory: List[str]
    
    # BANT
    budget: Optional[str]
    budget_amount: Optional[float]
    authority: Optional[str]
    authority_level: str
    need: Optional[str]
    need_category: str
    timeline: Optional[str]
    timeline_urgency: str
    bant_qualification_score: float
    
    # Intent
    intent: str
    intent_confidence: float
    intent_progression: List[str]
    
    # Buying Signals
    buying_signals: List[Dict]
    buying_readiness_score: float
    readiness_level: str
    
    # Objections
    objections: List[Dict]
    objection_count: int
    critical_objections: int
    
    # ICP
    icp_score: float
    icp_tier: str
    icp_matched_criteria: List[str]
    
    # Conversation Metrics
    speaking_duration: float
    silence_duration: float
    interruption_count: int
    turn_taking_count: int
    words_per_minute: float


@dataclass
class LeadScore:
    """Lead scoring result"""
    overall_score: float
    qualification: str  # HOT, WARM, COLD
    confidence: float
    
    # Component scores
    emotion_score: float
    bant_score: float
    intent_score: float
    buying_signal_score: float
    icp_score: float
    conversation_quality_score: float
    
    # Insights
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    next_actions: List[str]
    
    # Metadata
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ConversationIntelligenceEngine:
    """
    Central Conversation Intelligence Engine
    
    Orchestrates all analysis modules and produces comprehensive insights:
    - Speech Emotion Recognition
    - BANT Extraction
    - Intent Detection
    - Buying Signal Detection
    - Objection Detection
    - ICP Scoring
    - Lead Scoring
    """
    
    def __init__(self, icp_profile: Optional[Any] = None):
        """Initialize all analysis modules"""
        # Core analyzers
        self.emotion_recognizer = SpeechEmotionRecognizer()
        self.emotion_tracker = EmotionTracker(window_size=10)
        self.bant_engine = BANTEngine()
        self.intent_detector = IntentDetector()
        self.buying_signal_analyzer = BuyingSignalAnalyzer()
        self.objection_analyzer = ObjectionAnalyzer()
        self.icp_analyzer = ICPAnalyzer(icp_profile)
        
        # Conversation state
        self.conversation_history: List[str] = []
        self.audio_segments: List[Dict] = []
        self.features_history: List[ConversationFeatures] = []
        
    def process_conversation(
        self,
        transcript: str,
        audio: Optional[Any] = None,
        sample_rate: int = 16000,
        segments: Optional[List[Dict]] = None
    ) -> ConversationFeatures:
        """
        Process complete conversation and extract all features
        
        Args:
            transcript: Full conversation transcript
            audio: Audio data as numpy array (optional, for emotion detection)
            sample_rate: Audio sample rate
            segments: List of transcript segments with timestamps
            
        Returns:
            ConversationFeatures with all analysis results
        """
        # Add to history
        self.conversation_history.append(transcript)
        
        # 1. Speech Emotion Recognition
        emotion_result = self._analyze_emotion(audio, sample_rate)
        self.emotion_tracker.add_emotion(emotion_result)
        
        # 2. BANT Extraction
        bant_result = self._extract_bant(transcript)
        
        # 3. Intent Detection
        intent_result = self._detect_intent(transcript)
        
        # 4. Buying Signal Detection
        buying_signals = self._detect_buying_signals(transcript)
        buying_readiness = self._get_buying_readiness()
        
        # 5. Objection Detection
        objections = self._detect_objections(transcript)
        
        # 6. ICP Scoring
        icp_result = self._score_icp(transcript)
        
        # 7. Conversation Metrics
        conv_metrics = self._calculate_conversation_metrics(transcript, segments)
        
        # Create features
        features = ConversationFeatures(
            transcript=transcript,
            segments=segments or [],
            emotion=emotion_result.emotion,
            emotion_confidence=emotion_result.confidence,
            emotion_scores=emotion_result.all_scores,
            emotion_trajectory=self.emotion_tracker.get_emotion_trajectory(),
            budget=bant_result.budget,
            budget_amount=bant_result.budget_amount,
            authority=bant_result.authority,
            authority_level=bant_result.authority_level.value,
            need=bant_result.need,
            need_category=bant_result.need_category,
            timeline=bant_result.timeline,
            timeline_urgency=bant_result.timeline_urgency.value,
            bant_qualification_score=bant_result.confidence_scores.get("budget", 0.0),
            intent=intent_result.intent.value,
            intent_confidence=intent_result.confidence,
            intent_progression=[r.intent.value for r in self.intent_detector.intent_history],
            buying_signals=buying_signals,
            buying_readiness_score=buying_readiness["buying_readiness_score"],
            readiness_level=buying_readiness["readiness_level"],
            objections=objections,
            objection_count=len(objections),
            critical_objections=len([o for o in objections if o.get("severity") == "critical"]),
            icp_score=icp_result.overall_score,
            icp_tier=self.icp_analyzer.scorer.get_icp_tier(icp_result.overall_score),
            icp_matched_criteria=icp_result.matched_criteria,
            speaking_duration=conv_metrics["speaking_duration"],
            silence_duration=conv_metrics["silence_duration"],
            interruption_count=conv_metrics["interruption_count"],
            turn_taking_count=conv_metrics["turn_taking_count"],
            words_per_minute=conv_metrics["words_per_minute"]
        )
        
        self.features_history.append(features)
        
        return features
    
    def _analyze_emotion(
        self,
        audio: Optional[Any],
        sample_rate: int
    ) -> EmotionResult:
        """Analyze emotion from audio"""
        if audio is not None:
            return self.emotion_recognizer.detect_emotion(audio, sample_rate)
        else:
            # Return neutral if no audio
            return EmotionResult(
                emotion="neutral",
                confidence=0.0,
                all_scores={e: 0.0 for e in self.emotion_recognizer.emotions},
                features={}
            )
    
    def _extract_bant(self, transcript: str) -> BANTResult:
        """Extract BANT information"""
        return self.bant_engine.extract_bant(transcript)
    
    def _detect_intent(self, transcript: str) -> IntentResult:
        """Detect customer intent"""
        return self.intent_detector.detect_intent(transcript)
    
    def _detect_buying_signals(self, transcript: str) -> List[Dict]:
        """Detect buying signals"""
        signals = self.buying_signal_analyzer.detector.detect_signals(transcript)
        return [
            {
                "type": s.signal_type,
                "strength": round(s.strength, 2),
                "level": s.strength_level.value,
                "recommendation": s.recommendation
            }
            for s in signals[:5]  # Top 5 signals
        ]
    
    def _get_buying_readiness(self) -> Dict:
        """Get buying readiness analysis"""
        detector = self.buying_signal_analyzer.detector
        score = detector.get_buying_readiness_score()
        return {
            "buying_readiness_score": score,
            "readiness_level": self.buying_signal_analyzer._get_readiness_level(score)
        }
    
    def _detect_objections(self, transcript: str) -> List[Dict]:
        """Detect objections"""
        objections = self.objection_analyzer.detector.detect_objections(transcript)
        return [
            {
                "type": o.objection_type.value,
                "severity": o.severity.value,
                "confidence": round(o.confidence, 2),
                "suggested_response": o.suggested_response
            }
            for o in objections[:5]  # Top 5 objections
        ]
    
    def _score_icp(self, transcript: str) -> Any:
        """Score against ICP"""
        return self.icp_analyzer.analyze_customer({"text": transcript})
    
    def _calculate_conversation_metrics(
        self,
        transcript: str,
        segments: Optional[List[Dict]]
    ) -> Dict:
        """Calculate conversation metrics"""
        # Word count
        words = transcript.split()
        word_count = len(words)
        
        # Speaking duration (estimate from segments or transcript)
        if segments:
            speaking_duration = sum(
                seg.get("end", 0) - seg.get("start", 0)
                for seg in segments
            )
        else:
            # Estimate: ~150 words per minute
            speaking_duration = (word_count / 150) * 60
        
        # Words per minute
        words_per_minute = (word_count / speaking_duration * 60) if speaking_duration > 0 else 0
        
        # Estimate silence (20% of total time typically)
        silence_duration = speaking_duration * 0.2
        
        # Estimate interruptions (based on sentence patterns)
        sentences = transcript.split('.')
        interruption_count = sum(1 for s in sentences if s.strip().startswith(('-', 'but', 'however', 'no', 'wait')))
        
        # Turn taking (estimate from segments)
        turn_taking_count = len(segments) if segments else max(1, word_count // 50)
        
        return {
            "speaking_duration": round(speaking_duration, 2),
            "silence_duration": round(silence_duration, 2),
            "interruption_count": interruption_count,
            "turn_taking_count": turn_taking_count,
            "words_per_minute": round(words_per_minute, 2)
        }
    
    def calculate_lead_score(self) -> LeadScore:
        """
        Calculate comprehensive lead score
        
        Returns:
            LeadScore with qualification and recommendations
        """
        if not self.features_history:
            return self._default_lead_score()
        
        # Get latest features
        latest = self.features_history[-1]
        
        # Calculate component scores
        emotion_score = self._score_emotion(latest)
        bant_score = self._score_bant(latest)
        intent_score = self._score_intent(latest)
        buying_signal_score = latest.buying_readiness_score
        icp_score = latest.icp_score
        conv_quality_score = self._score_conversation_quality(latest)
        
        # Calculate weighted overall score
        weights = {
            "emotion": 0.15,
            "bant": 0.20,
            "intent": 0.15,
            "buying_signal": 0.25,
            "icp": 0.15,
            "conv_quality": 0.10
        }
        
        overall_score = (
            emotion_score * weights["emotion"] +
            bant_score * weights["bant"] +
            intent_score * weights["intent"] +
            buying_signal_score * weights["buying_signal"] +
            icp_score * weights["icp"] +
            conv_quality_score * weights["conv_quality"]
        )
        
        # Determine qualification
        qualification = self._get_qualification(overall_score)
        
        # Identify strengths and weaknesses
        strengths, weaknesses = self._identify_strengths_weaknesses(
            emotion_score, bant_score, intent_score,
            buying_signal_score, icp_score, conv_quality_score
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            qualification, strengths, weaknesses, latest
        )
        
        # Generate next actions
        next_actions = self._generate_next_actions(qualification, latest)
        
        return LeadScore(
            overall_score=round(overall_score, 2),
            qualification=qualification,
            confidence=round(self._calculate_confidence(latest), 2),
            emotion_score=round(emotion_score, 2),
            bant_score=round(bant_score, 2),
            intent_score=round(intent_score, 2),
            buying_signal_score=round(buying_signal_score, 2),
            icp_score=round(icp_score, 2),
            conversation_quality_score=round(conv_quality_score, 2),
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            next_actions=next_actions
        )
    
    def _score_emotion(self, features: ConversationFeatures) -> float:
        """Score based on emotion"""
        positive_emotions = ["interested", "excited", "confident", "curious"]
        negative_emotions = ["frustrated", "angry", "anxious", "hesitant"]
        
        if features.emotion in positive_emotions:
            return 0.8 + (features.emotion_confidence * 0.2)
        elif features.emotion in negative_emotions:
            return 0.3 + (features.emotion_confidence * 0.2)
        else:
            return 0.5
    
    def _score_bant(self, features: ConversationFeatures) -> float:
        """Score based on BANT"""
        return features.bant_qualification_score
    
    def _score_intent(self, features: ConversationFeatures) -> float:
        """Score based on intent"""
        positive_intents = ["purchase", "demo", "pricing", "negotiation"]
        neutral_intents = ["information", "support", "renewal"]
        negative_intents = ["cancellation", "objection", "competitor"]
        
        if features.intent in positive_intents:
            return 0.7 + (features.intent_confidence * 0.3)
        elif features.intent in neutral_intents:
            return 0.5 + (features.intent_confidence * 0.2)
        elif features.intent in negative_intents:
            return 0.2 + (features.intent_confidence * 0.2)
        else:
            return 0.4
    
    def _score_conversation_quality(self, features: ConversationFeatures) -> float:
        """Score based on conversation quality metrics"""
        score = 0.5  # Base score
        
        # Good speaking rate (120-180 WPM)
        if 120 <= features.words_per_minute <= 180:
            score += 0.2
        elif features.words_per_minute > 0:
            score += 0.1
        
        # Low interruptions (good sign)
        if features.interruption_count <= 2:
            score += 0.15
        elif features.interruption_count <= 5:
            score += 0.1
        
        # Good turn taking
        if features.turn_taking_count >= 5:
            score += 0.15
        
        return min(1.0, score)
    
    def _get_qualification(self, score: float) -> str:
        """Get qualification from score"""
        if score >= 0.75:
            return "HOT"
        elif score >= 0.5:
            return "WARM"
        else:
            return "COLD"
    
    def _identify_strengths_weaknesses(
        self,
        emotion_score: float,
        bant_score: float,
        intent_score: float,
        buying_signal_score: float,
        icp_score: float,
        conv_quality_score: float
    ) -> Tuple[List[str], List[str]]:
        """Identify strengths and weaknesses"""
        strengths = []
        weaknesses = []
        
        scores = {
            "Emotion": emotion_score,
            "BANT": bant_score,
            "Intent": intent_score,
            "Buying Signals": buying_signal_score,
            "ICP Match": icp_score,
            "Conversation Quality": conv_quality_score
        }
        
        for name, score in scores.items():
            if score >= 0.7:
                strengths.append(f"Strong {name} ({score:.0%})")
            elif score <= 0.4:
                weaknesses.append(f"Weak {name} ({score:.0%})")
        
        return strengths, weaknesses
    
    def _generate_recommendations(
        self,
        qualification: str,
        strengths: List[str],
        weaknesses: List[str],
        latest: ConversationFeatures
    ) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        # Based on qualification
        if qualification == "HOT":
            recommendations.append("URGENT: Lead is highly qualified. Initiate closing sequence immediately.")
            recommendations.append("Schedule final presentation with decision makers.")
        elif qualification == "WARM":
            recommendations.append("Lead shows promise. Continue nurturing and addressing gaps.")
            recommendations.append("Focus on strengthening weak areas.")
        else:
            recommendations.append("Lead needs more qualification. Continue discovery process.")
            recommendations.append("Identify and address key objections.")
        
        # Based on weaknesses
        if "BANT" in " ".join(weaknesses):
            recommendations.append("Gather missing BANT information (Budget, Authority, Need, Timeline).")
        
        if "Buying Signals" in " ".join(weaknesses):
            recommendations.append("Look for stronger buying signals. Provide case studies and references.")
        
        if "ICP Match" in " ".join(weaknesses):
            recommendations.append("Lead doesn't match ICP well. Consider if this is worth pursuing.")
        
        # Based on objections
        if latest.critical_objections > 0:
            recommendations.append(f"Address {latest.critical_objections} critical objection(s) immediately.")
        
        return recommendations
    
    def _generate_next_actions(self, qualification: str, latest: ConversationFeatures) -> List[str]:
        """Generate next actions"""
        actions = []
        
        if qualification == "HOT":
            actions.append("Send proposal/quote")
            actions.append("Schedule contract review meeting")
            actions.append("Connect with decision makers")
        elif qualification == "WARM":
            actions.append("Schedule demo/presentation")
            actions.append("Send relevant case studies")
            actions.append("Follow up within 24 hours")
        else:
            actions.append("Schedule discovery call")
            actions.append("Send introductory materials")
            actions.append("Qualify further before proceeding")
        
        # Add specific actions based on intent
        if latest.intent == "pricing":
            actions.append("Prepare detailed pricing proposal")
        elif latest.intent == "demo":
            actions.append("Schedule product demonstration")
        elif latest.intent == "objection":
            actions.append("Prepare objection handling materials")
        
        return actions[:5]  # Top 5 actions
    
    def _calculate_confidence(self, latest: ConversationFeatures) -> float:
        """Calculate confidence in the lead score"""
        # Higher confidence when we have more data
        confidence = 0.5
        
        # BANT data available
        if latest.budget and latest.authority and latest.need and latest.timeline:
            confidence += 0.2
        
        # Strong buying signals
        if latest.buying_readiness_score >= 0.6:
            confidence += 0.15
        
        # Clear intent
        if latest.intent_confidence >= 0.6:
            confidence += 0.1
        
        # Good ICP match
        if latest.icp_score >= 0.6:
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _default_lead_score(self) -> LeadScore:
        """Return default lead score when no data"""
        return LeadScore(
            overall_score=0.0,
            qualification="COLD",
            confidence=0.0,
            emotion_score=0.0,
            bant_score=0.0,
            intent_score=0.0,
            buying_signal_score=0.0,
            icp_score=0.0,
            conversation_quality_score=0.0,
            strengths=[],
            weaknesses=["No conversation data"],
            recommendations=["Start conversation to analyze lead"],
            next_actions=["Initiate contact"]
        )
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of entire conversation analysis"""
        if not self.features_history:
            return {"message": "No conversation data"}
        
        latest = self.features_history[-1]
        lead_score = self.calculate_lead_score()
        
        return {
            "lead_qualification": {
                "score": lead_score.overall_score,
                "qualification": lead_score.qualification,
                "confidence": lead_score.confidence
            },
            "key_insights": {
                "emotion": f"{latest.emotion} ({latest.emotion_confidence:.0%})",
                "intent": f"{latest.intent} ({latest.intent_confidence:.0%})",
                "buying_readiness": f"{latest.readiness_level} ({latest.buying_readiness_score:.0%})",
                "icp_tier": latest.icp_tier
            },
            "bant_summary": {
                "budget": latest.budget or "Not detected",
                "authority": latest.authority or "Not detected",
                "need": latest.need or "Not detected",
                "timeline": latest.timeline or "Not detected"
            },
            "top_buying_signals": latest.buying_signals[:3],
            "critical_objections": [
                o for o in latest.objections
                if o.get("severity") == "critical"
            ],
            "recommendations": lead_score.recommendations,
            "next_actions": lead_score.next_actions
        }
    
    def reset(self):
        """Reset engine state"""
        self.conversation_history = []
        self.audio_segments = []
        self.features_history = []
        self.emotion_tracker = EmotionTracker(window_size=10)
        self.intent_detector.reset()
        self.buying_signal_analyzer.detector.reset()
        self.objection_analyzer.detector.reset()
        self.icp_analyzer.reset()