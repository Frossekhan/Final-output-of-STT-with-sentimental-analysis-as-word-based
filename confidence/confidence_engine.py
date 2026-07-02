"""
Confidence Scoring Engine
Provides confidence scores for all predictions and analysis
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BANTConfidence:
    """Confidence scores for BANT fields"""
    budget: float
    authority: float
    need: float
    timeline: float
    overall: float


@dataclass
class IntentConfidence:
    """Confidence scores for intent detection"""
    primary_intent: str
    primary_confidence: float
    all_intents: Dict[str, float]
    certainty_score: float


@dataclass
class BuyingSignalConfidence:
    """Confidence scores for buying signals"""
    signal_count: int
    average_strength: float
    strongest_signal: str
    strongest_signal_confidence: float
    overall_confidence: float


@dataclass
class ObjectionConfidence:
    """Confidence scores for objection detection"""
    objection_count: int
    critical_count: int
    average_confidence: float
    severity_confidence: float
    overall_confidence: float


@dataclass
class EmotionConfidence:
    """Confidence scores for emotion detection"""
    detected_emotion: str
    emotion_confidence: float
    emotion_stability: float
    overall_confidence: float


@dataclass
class LeadScoreConfidence:
    """Confidence scores for lead scoring"""
    overall_confidence: float
    data_completeness: float
    prediction_reliability: float
    calibration_score: float


class ConfidenceEngine:
    """
    Confidence scoring engine for all predictions
    
    Provides:
    - BANT field confidence
    - Intent detection confidence
    - Buying signal confidence
    - Objection confidence
    - Emotion detection confidence
    - Overall lead score confidence
    """
    
    def __init__(self):
        """Initialize confidence engine"""
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
    
    def calculate_bant_confidence(self, bant: Dict) -> BANTConfidence:
        """
        Calculate confidence scores for BANT extraction
        
        Args:
            bant: BANT analysis dictionary
            
        Returns:
            BANTConfidence with scores for each field
        """
        # Budget confidence
        budget_confidence = 0.0
        if bant.get("budget"):
            budget_confidence = 0.7
            if bant.get("budget_amount"):
                budget_confidence = 0.9
            if bant.get("budget_currency"):
                budget_confidence = min(1.0, budget_confidence + 0.1)
        
        # Authority confidence
        authority_confidence = 0.0
        if bant.get("authority"):
            authority_confidence = 0.7
            if bant.get("authority_level") in ["decision_maker", "ceo_cfo"]:
                authority_confidence = 0.95
            elif bant.get("authority_level") in ["vp_director", "manager"]:
                authority_confidence = 0.85
        
        # Need confidence
        need_confidence = 0.0
        if bant.get("need"):
            need_confidence = 0.6
            if bant.get("need_category") and bant.get("need_category") != "general":
                need_confidence = 0.85
            if len(bant.get("need", "")) > 20:  # Detailed need description
                need_confidence = min(1.0, need_confidence + 0.1)
        
        # Timeline confidence
        timeline_confidence = 0.0
        if bant.get("timeline"):
            timeline_confidence = 0.7
            if bant.get("timeline_urgency") and bant.get("timeline_urgency") != "not_mentioned":
                timeline_confidence = 0.9
        
        # Overall BANT confidence
        overall = (budget_confidence + authority_confidence + need_confidence + timeline_confidence) / 4.0
        
        return BANTConfidence(
            budget=round(budget_confidence, 2),
            authority=round(authority_confidence, 2),
            need=round(need_confidence, 2),
            timeline=round(timeline_confidence, 2),
            overall=round(overall, 2)
        )
    
    def calculate_intent_confidence(self, intent: Dict) -> IntentConfidence:
        """
        Calculate confidence scores for intent detection
        
        Args:
            intent: Intent analysis dictionary
            
        Returns:
            IntentConfidence with scores
        """
        primary_intent = intent.get("intent", "information")
        primary_confidence = intent.get("confidence", 0.0)
        all_intents = intent.get("all_intents", {})
        
        # Calculate certainty score (how much the primary intent dominates)
        if all_intents and primary_confidence > 0:
            # Sort intents by confidence
            sorted_intents = sorted(all_intents.items(), key=lambda x: x[1], reverse=True)
            
            if len(sorted_intents) >= 2:
                top_two_diff = sorted_intents[0][1] - sorted_intents[1][1]
                certainty_score = min(1.0, primary_confidence + (top_two_diff * 0.5))
            else:
                certainty_score = primary_confidence
        else:
            certainty_score = 0.0
        
        return IntentConfidence(
            primary_intent=primary_intent,
            primary_confidence=round(primary_confidence, 2),
            all_intents={k: round(v, 2) for k, v in all_intents.items()},
            certainty_score=round(certainty_score, 2)
        )
    
    def calculate_buying_signal_confidence(self, buying_signals: Dict) -> BuyingSignalConfidence:
        """
        Calculate confidence scores for buying signals
        
        Args:
            buying_signals: Buying signals analysis dictionary
            
        Returns:
            BuyingSignalConfidence with scores
        """
        signals = buying_signals.get("signals", [])
        signal_count = len(signals)
        
        if signal_count == 0:
            return BuyingSignalConfidence(
                signal_count=0,
                average_strength=0.0,
                strongest_signal="none",
                strongest_signal_confidence=0.0,
                overall_confidence=0.0
            )
        
        # Calculate average strength
        strengths = [s.get("strength", 0.0) for s in signals]
        average_strength = sum(strengths) / len(strengths)
        
        # Find strongest signal
        strongest_signal = max(signals, key=lambda s: s.get("strength", 0.0))
        strongest_signal_name = strongest_signal.get("type", "unknown")
        strongest_signal_confidence = strongest_signal.get("strength", 0.0)
        
        # Overall confidence based on number and strength of signals
        count_factor = min(1.0, signal_count / 5.0)  # Normalize to 5 signals
        strength_factor = average_strength
        overall_confidence = (count_factor * 0.4) + (strength_factor * 0.6)
        
        return BuyingSignalConfidence(
            signal_count=signal_count,
            average_strength=round(average_strength, 2),
            strongest_signal=strongest_signal_name,
            strongest_signal_confidence=round(strongest_signal_confidence, 2),
            overall_confidence=round(overall_confidence, 2)
        )
    
    def calculate_objection_confidence(self, objections: Dict) -> ObjectionConfidence:
        """
        Calculate confidence scores for objection detection
        
        Args:
            objections: Objections analysis dictionary
            
        Returns:
            ObjectionConfidence with scores
        """
        objection_list = objections.get("objections", [])
        objection_count = len(objection_list)
        critical_count = sum(1 for o in objection_list if o.get("severity") == "critical")
        
        if objection_count == 0:
            return ObjectionConfidence(
                objection_count=0,
                critical_count=0,
                average_confidence=0.0,
                severity_confidence=0.0,
                overall_confidence=1.0  # High confidence that there are no objections
            )
        
        # Average confidence
        confidences = [o.get("confidence", 0.0) for o in objection_list]
        average_confidence = sum(confidences) / len(confidences)
        
        # Severity confidence (higher if there are critical objections)
        severity_confidence = 0.5
        if critical_count > 0:
            severity_confidence = 0.9
        elif objection_count >= 3:
            severity_confidence = 0.7
        
        # Overall confidence
        overall_confidence = (average_confidence * 0.6) + (severity_confidence * 0.4)
        
        return ObjectionConfidence(
            objection_count=objection_count,
            critical_count=critical_count,
            average_confidence=round(average_confidence, 2),
            severity_confidence=round(severity_confidence, 2),
            overall_confidence=round(overall_confidence, 2)
        )
    
    def calculate_emotion_confidence(self, emotion: Dict) -> EmotionConfidence:
        """
        Calculate confidence scores for emotion detection
        
        Args:
            emotion: Emotion analysis dictionary
            
        Returns:
            EmotionConfidence with scores
        """
        detected_emotion = emotion.get("emotion", "neutral")
        emotion_confidence = emotion.get("confidence", 0.0)
        all_scores = emotion.get("all_scores", {})
        
        # Calculate stability (how dominant is the detected emotion)
        if all_scores and emotion_confidence > 0:
            sorted_scores = sorted(all_scores.values(), reverse=True)
            if len(sorted_scores) >= 2:
                stability = sorted_scores[0] - sorted_scores[1]
            else:
                stability = emotion_confidence
        else:
            stability = 0.0
        
        # Overall confidence
        overall_confidence = (emotion_confidence * 0.7) + (stability * 0.3)
        
        return EmotionConfidence(
            detected_emotion=detected_emotion,
            emotion_confidence=round(emotion_confidence, 2),
            emotion_stability=round(stability, 2),
            overall_confidence=round(overall_confidence, 2)
        )
    
    def calculate_lead_score_confidence(
        self,
        bant_conf: BANTConfidence,
        intent_conf: IntentConfidence,
        buying_signal_conf: BuyingSignalConfidence,
        objection_conf: ObjectionConfidence,
        emotion_conf: EmotionConfidence,
        data_completeness: float
    ) -> LeadScoreConfidence:
        """
        Calculate overall lead score confidence
        
        Args:
            bant_conf: BANT confidence
            intent_conf: Intent confidence
            buying_signal_conf: Buying signal confidence
            objection_conf: Objection confidence
            emotion_conf: Emotion confidence
            data_completeness: How complete is the data (0-1)
            
        Returns:
            LeadScoreConfidence with overall scores
        """
        # Weighted average of all confidences
        component_confidences = [
            (bant_conf.overall, 0.25),
            (intent_conf.certainty_score, 0.20),
            (buying_signal_conf.overall_confidence, 0.25),
            (objection_conf.overall_confidence, 0.15),
            (emotion_conf.overall_confidence, 0.15)
        ]
        
        weighted_sum = sum(conf * weight for conf, weight in component_confidences)
        prediction_reliability = weighted_sum
        
        # Calibration score (how well we can trust the prediction)
        # Higher when we have more data and higher confidence
        calibration_score = (prediction_reliability * 0.7) + (data_completeness * 0.3)
        
        # Overall confidence
        overall_confidence = (prediction_reliability * 0.6) + (data_completeness * 0.4)
        
        return LeadScoreConfidence(
            overall_confidence=round(overall_confidence, 2),
            data_completeness=round(data_completeness, 2),
            prediction_reliability=round(prediction_reliability, 2),
            calibration_score=round(calibration_score, 2)
        )
    
    def calculate_data_completeness(self, analysis: Dict) -> float:
        """
        Calculate how complete the analysis data is
        
        Args:
            analysis: Complete analysis dictionary
            
        Returns:
            Completeness score (0-1)
        """
        completeness_checks = []
        
        # Check BANT
        bant = analysis.get("bant", {})
        bant_fields = sum([1 for f in ["budget", "authority", "need", "timeline"] if bant.get(f)])
        completeness_checks.append(bant_fields / 4.0)
        
        # Check intent
        intent = analysis.get("intent", {})
        if intent.get("intent") and intent.get("confidence", 0) > 0.5:
            completeness_checks.append(1.0)
        else:
            completeness_checks.append(0.0)
        
        # Check buying signals
        buying_signals = analysis.get("buying_signals", {})
        if buying_signals.get("signals"):
            completeness_checks.append(1.0)
        else:
            completeness_checks.append(0.0)
        
        # Check objections
        objections = analysis.get("objections", {})
        if objections.get("objections") is not None:
            completeness_checks.append(1.0)
        else:
            completeness_checks.append(0.0)
        
        # Check emotion
        emotion = analysis.get("emotion", {})
        if emotion.get("emotion") and emotion.get("emotion") != "neutral":
            completeness_checks.append(1.0)
        else:
            completeness_checks.append(0.5)
        
        # Check summary
        summary = analysis.get("summary", {})
        if summary.get("summary"):
            completeness_checks.append(1.0)
        else:
            completeness_checks.append(0.0)
        
        # Average completeness
        overall_completeness = sum(completeness_checks) / len(completeness_checks) if completeness_checks else 0.0
        
        return round(overall_completeness, 2)
    
    def get_confidence_level(self, confidence: float) -> str:
        """
        Get confidence level label
        
        Args:
            confidence: Confidence score (0-1)
            
        Returns:
            Confidence level label
        """
        if confidence >= self.confidence_thresholds["high"]:
            return "HIGH"
        elif confidence >= self.confidence_thresholds["medium"]:
            return "MEDIUM"
        elif confidence >= self.confidence_thresholds["low"]:
            return "LOW"
        else:
            return "VERY_LOW"
    
    def calculate_all_confidences(self, analysis: Dict) -> Dict[str, Any]:
        """
        Calculate all confidence scores for an analysis
        
        Args:
            analysis: Complete analysis dictionary
            
        Returns:
            Dictionary with all confidence scores
        """
        # Calculate individual confidences
        bant_conf = self.calculate_bant_confidence(analysis.get("bant", {}))
        intent_conf = self.calculate_intent_confidence(analysis.get("intent", {}))
        buying_signal_conf = self.calculate_buying_signal_confidence(analysis.get("buying_signals", {}))
        objection_conf = self.calculate_objection_confidence(analysis.get("objections", {}))
        emotion_conf = self.calculate_emotion_confidence(analysis.get("emotion", {}))
        
        # Calculate data completeness
        data_completeness = self.calculate_data_completeness(analysis)
        
        # Calculate overall lead score confidence
        lead_score_conf = self.calculate_lead_score_confidence(
            bant_conf,
            intent_conf,
            buying_signal_conf,
            objection_conf,
            emotion_conf,
            data_completeness
        )
        
        return {
            "bant": {
                "budget": bant_conf.budget,
                "authority": bant_conf.authority,
                "need": bant_conf.need,
                "timeline": bant_conf.timeline,
                "overall": bant_conf.overall,
                "level": self.get_confidence_level(bant_conf.overall)
            },
            "intent": {
                "primary_confidence": intent_conf.primary_confidence,
                "certainty_score": intent_conf.certainty_score,
                "level": self.get_confidence_level(intent_conf.certainty_score)
            },
            "buying_signals": {
                "signal_count": buying_signal_conf.signal_count,
                "average_strength": buying_signal_conf.average_strength,
                "overall_confidence": buying_signal_conf.overall_confidence,
                "level": self.get_confidence_level(buying_signal_conf.overall_confidence)
            },
            "objections": {
                "objection_count": objection_conf.objection_count,
                "critical_count": objection_conf.critical_count,
                "overall_confidence": objection_conf.overall_confidence,
                "level": self.get_confidence_level(objection_conf.overall_confidence)
            },
            "emotion": {
                "detected_emotion": emotion_conf.detected_emotion,
                "emotion_confidence": emotion_conf.emotion_confidence,
                "overall_confidence": emotion_conf.overall_confidence,
                "level": self.get_confidence_level(emotion_conf.overall_confidence)
            },
            "lead_score": {
                "overall_confidence": lead_score_conf.overall_confidence,
                "data_completeness": lead_score_conf.data_completeness,
                "prediction_reliability": lead_score_conf.prediction_reliability,
                "calibration_score": lead_score_conf.calibration_score,
                "level": self.get_confidence_level(lead_score_conf.overall_confidence)
            },
            "data_completeness": data_completeness,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_confidence_summary(self, confidences: Dict) -> Dict:
        """
        Get human-readable confidence summary
        
        Args:
            confidences: Confidence scores dictionary
            
        Returns:
            Summary dictionary
        """
        lead_score_conf = confidences.get("lead_score", {})
        overall_conf = lead_score_conf.get("overall_confidence", 0.0)
        overall_level = lead_score_conf.get("level", "UNKNOWN")
        
        # Identify weak areas
        weak_areas = []
        
        bant_conf = confidences.get("bant", {})
        if bant_conf.get("overall", 0) < 0.6:
            weak_areas.append("BANT extraction")
        
        if confidences.get("buying_signals", {}).get("overall_confidence", 0) < 0.5:
            weak_areas.append("buying signal detection")
        
        if confidences.get("objections", {}).get("overall_confidence", 0) < 0.5:
            weak_areas.append("objection detection")
        
        return {
            "overall_confidence": overall_conf,
            "confidence_level": overall_level,
            "data_completeness": confidences.get("data_completeness", 0.0),
            "weak_areas": weak_areas,
            "recommendation": self._get_confidence_recommendation(overall_level, weak_areas)
        }
    
    def _get_confidence_recommendation(self, level: str, weak_areas: List[str]) -> str:
        """Get recommendation based on confidence level"""
        if level == "HIGH":
            return "High confidence in predictions. Safe to act on insights."
        elif level == "MEDIUM":
            return "Medium confidence. Use insights as guidance but verify key points."
        elif level == "LOW":
            if weak_areas:
                return f"Low confidence. Improve data quality in: {', '.join(weak_areas)}."
            else:
                return "Low confidence. Gather more conversation data."
        else:
            return "Very low confidence. Continue conversation to gather more data."


class ConfidenceEngineFactory:
    """Factory for creating confidence engine instances"""
    
    @staticmethod
    def create() -> ConfidenceEngine:
        """
        Create confidence engine
        
        Returns:
            ConfidenceEngine instance
        """
        return ConfidenceEngine()