"""
LLM-Powered Conversation Intelligence Engine
Replaces rule-based systems with LLM for superior accuracy
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from llm.service import LLMService, LLMServiceFactory
from memory.conversation_memory import ConversationMemory, ConversationMemoryFactory

logger = logging.getLogger(__name__)


class LLMConversationEngine:
    """
    LLM-powered conversation intelligence engine
    
    Replaces rule-based systems with LLM for:
    - BANT extraction
    - Intent detection
    - Buying signal recognition
    - Objection classification
    - Summary generation
    """
    
    def __init__(
        self,
        model_name: str = "qwen2.5:7b",
        use_memory: bool = True,
        icp_profile: Optional[Any] = None
    ):
        """
        Initialize LLM conversation engine
        
        Args:
            model_name: LLM model to use
            use_memory: Enable conversation memory
            icp_profile: ICP profile (kept for compatibility)
        """
        # Initialize LLM service
        self.llm_service = LLMServiceFactory.create(model_name=model_name)
        
        # Initialize conversation memory
        self.use_memory = use_memory
        if use_memory:
            self.memory = ConversationMemoryFactory.create(max_history=100)
        else:
            self.memory = None
        
        # Conversation state
        self.conversation_history: List[str] = []
        self.current_session_id: Optional[str] = None
        self.current_customer_id: Optional[str] = None
        
        # Analysis history
        self.analysis_history: List[Dict] = []
        
        logger.info(f"LLM Conversation Engine initialized with model: {model_name}")
    
    def start_session(self, session_id: str, customer_id: Optional[str] = None):
        """
        Start a new conversation session
        
        Args:
            session_id: Session identifier
            customer_id: Customer identifier (optional)
        """
        self.current_session_id = session_id
        self.current_customer_id = customer_id
        
        # Start session in memory
        if self.memory:
            self.memory.start_session(session_id, customer_id)
        
        # Reset LLM context
        self.llm_service.reset()
        
        logger.info(f"Started session: {session_id}")
    
    def end_session(self):
        """End current session"""
        if self.current_session_id and self.memory:
            self.memory.end_session(self.current_session_id)
        
        logger.info(f"Ended session: {self.current_session_id}")
        
        self.current_session_id = None
        self.current_customer_id = None
    
    async def analyze_segment(
        self,
        transcript: str,
        audio: Optional[Any] = None,
        sample_rate: int = 16000,
        speaker: str = "customer"
    ) -> Dict[str, Any]:
        """
        Analyze conversation segment with LLM
        
        Args:
            transcript: Conversation text
            audio: Audio data (optional, for emotion detection)
            sample_rate: Audio sample rate
            speaker: Speaker identifier ("customer" or "salesperson")
            
        Returns:
            Complete analysis dictionary
        """
        if not transcript or not transcript.strip():
            return self._empty_analysis()
        
        # Add to conversation history
        self.conversation_history.append(transcript)
        
        # Add to memory
        if self.memory and self.current_session_id:
            # Detect emotion from audio if available
            emotion = None
            emotion_confidence = None
            
            if audio is not None:
                try:
                    from emotion.speech_emotion import SpeechEmotionRecognizer
                    emotion_recognizer = SpeechEmotionRecognizer()
                    emotion_result = emotion_recognizer.detect_emotion(audio, sample_rate)
                    emotion = emotion_result.emotion
                    emotion_confidence = emotion_result.confidence
                except Exception as e:
                    logger.warning(f"Emotion detection failed: {e}")
            
            self.memory.add_turn(
                session_id=self.current_session_id,
                speaker=speaker,
                text=transcript,
                customer_id=self.current_customer_id,
                emotion=emotion,
                emotion_confidence=emotion_confidence
            )
        
        # Run LLM analysis
        try:
            analysis = await self.llm_service.analyze_conversation_complete(transcript)
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            analysis = self._empty_analysis()
        
        # Add emotion from audio if available
        if audio is not None and emotion:
            analysis["emotion"] = {
                "emotion": emotion,
                "confidence": emotion_confidence,
                "source": "audio"
            }
        else:
            analysis["emotion"] = {
                "emotion": "neutral",
                "confidence": 0.0,
                "source": "none"
            }
        
        # Add metadata
        analysis["transcript"] = transcript
        analysis["speaker"] = speaker
        analysis["analyzed_at"] = datetime.now().isoformat()
        
        # Store in history
        self.analysis_history.append(analysis)
        
        # Add insights to memory
        if self.memory and self.current_customer_id:
            if analysis.get("summary", {}).get("key_points"):
                for point in analysis["summary"]["key_points"]:
                    self.memory.add_key_insight(self.current_customer_id, point)
            
            if analysis.get("objections", {}).get("objections"):
                for objection in analysis["objections"]["objections"]:
                    self.memory.add_objection(self.current_customer_id, objection)
            
            if analysis.get("buying_signals", {}).get("signals"):
                for signal in analysis["buying_signals"]["signals"]:
                    self.memory.add_buying_signal(self.current_customer_id, signal)
        
        return analysis
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            "transcript": "",
            "speaker": "unknown",
            "emotion": {
                "emotion": "neutral",
                "confidence": 0.0,
                "source": "none"
            },
            "bant": {
                "budget": None,
                "budget_amount": None,
                "budget_currency": "INR",
                "authority": None,
                "authority_level": "unknown",
                "need": None,
                "need_category": "general",
                "timeline": None,
                "timeline_urgency": "not_mentioned",
                "confidence": 0.0,
                "evidence": []
            },
            "intent": {
                "intent": "information",
                "confidence": 0.0,
                "all_intents": {},
                "reasoning": ""
            },
            "buying_signals": {
                "signals": [],
                "readiness": "NOT_READY",
                "readiness_score": 0.0,
                "reasoning": ""
            },
            "objections": {
                "objections": [],
                "severity": "low",
                "handling_priority": [],
                "reasoning": ""
            },
            "summary": {
                "summary": "",
                "key_points": [],
                "customer_concerns": [],
                "next_actions": [],
                "risk_factors": [],
                "opportunity_score": 0.0
            },
            "analyzed_at": datetime.now().isoformat()
        }
    
    def get_lead_score(self) -> Dict[str, Any]:
        """
        Calculate lead score based on LLM analysis
        
        Returns:
            Lead score dictionary
        """
        if not self.analysis_history:
            return self._default_lead_score()
        
        # Get latest analysis
        latest = self.analysis_history[-1]
        
        # Calculate component scores
        emotion_score = self._score_emotion(latest)
        bant_score = self._score_bant(latest)
        intent_score = self._score_intent(latest)
        buying_signal_score = latest.get("buying_signals", {}).get("readiness_score", 0.0)
        objection_score = self._score_objections(latest)
        opportunity_score = latest.get("summary", {}).get("opportunity_score", 0.0)
        
        # Calculate weighted overall score
        weights = {
            "emotion": 0.15,
            "bant": 0.20,
            "intent": 0.15,
            "buying_signal": 0.25,
            "objection": 0.10,
            "opportunity": 0.15
        }
        
        overall_score = (
            emotion_score * weights["emotion"] +
            bant_score * weights["bant"] +
            intent_score * weights["intent"] +
            buying_signal_score * weights["buying_signal"] +
            objection_score * weights["objection"] +
            opportunity_score * weights["opportunity"]
        )
        
        # Determine qualification
        qualification = self._get_qualification(overall_score)
        
        # Calculate confidence
        confidence = self._calculate_confidence(latest)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            qualification, latest
        )
        
        # Generate next actions
        next_actions = self._generate_next_actions(qualification, latest)
        
        return {
            "overall_score": round(overall_score, 2),
            "qualification": qualification,
            "confidence": round(confidence, 2),
            "component_scores": {
                "emotion": round(emotion_score, 2),
                "bant": round(bant_score, 2),
                "intent": round(intent_score, 2),
                "buying_signal": round(buying_signal_score, 2),
                "objection": round(objection_score, 2),
                "opportunity": round(opportunity_score, 2)
            },
            "recommendations": recommendations,
            "next_actions": next_actions
        }
    
    def _score_emotion(self, analysis: Dict) -> float:
        """Score based on emotion"""
        emotion_data = analysis.get("emotion", {})
        emotion = emotion_data.get("emotion", "neutral")
        confidence = emotion_data.get("confidence", 0.0)
        
        positive_emotions = ["interested", "excited", "confident", "curious", "happy"]
        negative_emotions = ["frustrated", "angry", "anxious", "hesitant"]
        
        if emotion in positive_emotions:
            return 0.8 + (confidence * 0.2)
        elif emotion in negative_emotions:
            return 0.3 + (confidence * 0.2)
        else:
            return 0.5
    
    def _score_bant(self, analysis: Dict) -> float:
        """Score based on BANT"""
        bant = analysis.get("bant", {})
        confidence = bant.get("confidence", 0.0)
        
        # Count filled fields
        fields_filled = sum([
            1 for field in ["budget", "authority", "need", "timeline"]
            if bant.get(field)
        ])
        
        # Combine confidence and completeness
        completeness = fields_filled / 4.0
        score = (confidence * 0.6) + (completeness * 0.4)
        
        return min(1.0, score)
    
    def _score_intent(self, analysis: Dict) -> float:
        """Score based on intent"""
        intent_data = analysis.get("intent", {})
        intent = intent_data.get("intent", "information")
        confidence = intent_data.get("confidence", 0.0)
        
        positive_intents = ["purchase", "demo", "pricing", "negotiation"]
        neutral_intents = ["information", "support", "renewal"]
        negative_intents = ["cancellation", "objection", "competitor"]
        
        if intent in positive_intents:
            return 0.7 + (confidence * 0.3)
        elif intent in neutral_intents:
            return 0.5 + (confidence * 0.2)
        elif intent in negative_intents:
            return 0.2 + (confidence * 0.2)
        else:
            return 0.4
    
    def _score_objections(self, analysis: Dict) -> float:
        """Score based on objections (inverse - fewer objections = higher score)"""
        objections = analysis.get("objections", {})
        objection_list = objections.get("objections", [])
        severity = objections.get("severity", "low")
        
        if not objection_list:
            return 1.0
        
        # Count by severity
        severity_scores = {
            "critical": 0.0,
            "high": 0.2,
            "medium": 0.5,
            "low": 0.7
        }
        
        # More objections = lower score
        num_objections = len(objection_list)
        base_score = severity_scores.get(severity, 0.5)
        
        # Reduce score based on number of objections
        penalty = min(0.5, num_objections * 0.1)
        
        return max(0.0, base_score - penalty)
    
    def _get_qualification(self, score: float) -> str:
        """Get qualification from score"""
        if score >= 0.75:
            return "HOT"
        elif score >= 0.5:
            return "WARM"
        else:
            return "COLD"
    
    def _calculate_confidence(self, analysis: Dict) -> float:
        """Calculate confidence in lead score"""
        confidence = 0.5
        
        # BANT data available
        bant = analysis.get("bant", {})
        if bant.get("budget") and bant.get("authority") and bant.get("need"):
            confidence += 0.15
        
        # Strong buying signals
        buying_signals = analysis.get("buying_signals", {})
        if buying_signals.get("readiness_score", 0) >= 0.6:
            confidence += 0.15
        
        # Clear intent
        intent = analysis.get("intent", {})
        if intent.get("confidence", 0) >= 0.6:
            confidence += 0.1
        
        # Good opportunity score
        summary = analysis.get("summary", {})
        if summary.get("opportunity_score", 0) >= 0.6:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _generate_recommendations(self, qualification: str, analysis: Dict) -> List[str]:
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
        
        # Based on BANT
        bant = analysis.get("bant", {})
        if not bant.get("budget") or not bant.get("authority") or not bant.get("need"):
            recommendations.append("Gather missing BANT information (Budget, Authority, Need, Timeline).")
        
        # Based on objections
        objections = analysis.get("objections", {})
        if objections.get("objections"):
            num_objections = len(objections["objections"])
            recommendations.append(f"Address {num_objections} objection(s) immediately.")
        
        # Based on buying signals
        buying_signals = analysis.get("buying_signals", {})
        if buying_signals.get("readiness_score", 0) >= 0.7:
            recommendations.append("Strong buying signals detected. Accelerate sales process.")
        
        return recommendations[:5]  # Top 5
    
    def _generate_next_actions(self, qualification: str, analysis: Dict) -> List[str]:
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
        
        # Based on intent
        intent = analysis.get("intent", {}).get("intent", "")
        if intent == "pricing":
            actions.append("Prepare detailed pricing proposal")
        elif intent == "demo":
            actions.append("Schedule product demonstration")
        elif intent == "objection":
            actions.append("Prepare objection handling materials")
        
        return actions[:5]  # Top 5
    
    def _default_lead_score(self) -> Dict[str, Any]:
        """Return default lead score"""
        return {
            "overall_score": 0.0,
            "qualification": "COLD",
            "confidence": 0.0,
            "component_scores": {
                "emotion": 0.0,
                "bant": 0.0,
                "intent": 0.0,
                "buying_signal": 0.0,
                "objection": 0.0,
                "opportunity": 0.0
            },
            "recommendations": ["Start conversation to analyze lead"],
            "next_actions": ["Initiate contact"]
        }
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get summary of entire conversation
        
        Returns:
            Conversation summary dictionary
        """
        if not self.analysis_history:
            return {"message": "No conversation data"}
        
        latest = self.analysis_history[-1]
        lead_score = self.get_lead_score()
        
        return {
            "lead_qualification": {
                "score": lead_score["overall_score"],
                "qualification": lead_score["qualification"],
                "confidence": lead_score["confidence"]
            },
            "key_insights": {
                "emotion": f"{latest.get('emotion', {}).get('emotion', 'neutral')} ({latest.get('emotion', {}).get('confidence', 0.0):.0%})",
                "intent": f"{latest.get('intent', {}).get('intent', 'information')} ({latest.get('intent', {}).get('confidence', 0.0):.0%})",
                "buying_readiness": f"{latest.get('buying_signals', {}).get('readiness', 'NOT_READY')} ({latest.get('buying_signals', {}).get('readiness_score', 0.0):.0%})"
            },
            "bant_summary": {
                "budget": latest.get("bant", {}).get("budget") or "Not detected",
                "authority": latest.get("bant", {}).get("authority") or "Not detected",
                "need": latest.get("bant", {}).get("need") or "Not detected",
                "timeline": latest.get("bant", {}).get("timeline") or "Not detected"
            },
            "top_buying_signals": latest.get("buying_signals", {}).get("signals", [])[:3],
            "critical_objections": [
                o for o in latest.get("objections", {}).get("objections", [])
                if o.get("severity") == "critical"
            ],
            "recommendations": lead_score["recommendations"],
            "next_actions": lead_score["next_actions"]
        }
    
    def get_customer_context(self) -> Optional[str]:
        """
        Get customer conversation context for LLM
        
        Returns:
            Formatted context string
        """
        if not self.memory or not self.current_customer_id:
            return None
        
        return self.memory.get_conversation_context(
            self.current_customer_id,
            n_turns=10
        )
    
    def get_customer_journey(self) -> Optional[Dict]:
        """
        Get complete customer journey
        
        Returns:
            Customer journey dictionary
        """
        if not self.memory or not self.current_customer_id:
            return None
        
        return self.memory.get_customer_journey(self.current_customer_id)
    
    def reset(self):
        """Reset engine state"""
        self.conversation_history = []
        self.analysis_history = []
        self.llm_service.reset()
        
        if self.memory and self.current_session_id:
            self.memory.reset_session(self.current_session_id)
        
        logger.info("LLM Conversation Engine reset")


class LLMConversationEngineFactory:
    """Factory for creating LLM conversation engine instances"""
    
    @staticmethod
    def create(
        model_name: str = "qwen2.5:7b",
        use_memory: bool = True,
        **kwargs
    ) -> LLMConversationEngine:
        """
        Create LLM conversation engine instance
        
        Args:
            model_name: LLM model to use
            use_memory: Enable conversation memory
            **kwargs: Additional arguments
            
        Returns:
            LLMConversationEngine instance
        """
        return LLMConversationEngine(
            model_name=model_name,
            use_memory=use_memory,
            **kwargs
        )