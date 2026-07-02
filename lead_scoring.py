"""
Lead Scoring Engine
Uses Random Forest + XGBoost for HOT/WARM/COLD classification
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import numpy as np
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class QualificationTier(Enum):
    """Lead qualification tiers"""
    HOT = "🟢 HOT"
    WARM = "🟡 WARM"
    COLD = "🔵 COLD"


@dataclass
class LeadScore:
    """Lead scoring result"""
    score: float  # 0-100
    qualification: str  # HOT/WARM/COLD
    confidence: float  # 0-100
    reasoning: List[str]
    factors: Dict[str, float]
    timestamp: str


class LeadScoringRules:
    """Rule-based lead scoring (before ML)"""
    
    @staticmethod
    def calculate_lead_score(analysis_result: Dict[str, Any]) -> float:
        """
        Calculate lead score based on analysis features
        
        Rules:
        - Budget (high > 0): +25
        - Authority (CEO/CFO): +20
        - Need (clear requirement): +20
        - Timeline (< 3 months): +15
        - Intent (purchase/demo): +10
        - Buying signals (detected): +10
        - ICP match (> 70%): +10
        - Objections (price only): -5
        """
        
        score = 50  # Base score
        factors = {}
        
        # Budget factor
        budget_amount = analysis_result.get("budget_amount") or 0
        if budget_amount > 0:
            factors["budget"] = 25
            score += 25
        
        # Authority factor
        authority = analysis_result.get("authority_level", "")
        if authority in ["ceo_cfo", "vp_director"]:
            factors["authority"] = 20
            score += 20
        elif authority == "manager":
            factors["authority"] = 10
            score += 10
        
        # Need factor
        need = analysis_result.get("need", "")
        if need and len(need) > 5:
            factors["need"] = 20
            score += 20
        
        # Timeline factor
        timeline = analysis_result.get("timeline_urgency", "")
        if timeline in ["immediate", "short_term"]:
            factors["timeline"] = 15
            score += 15
        elif timeline == "medium_term":
            factors["timeline"] = 10
            score += 10
        
        # Intent factor
        intent = analysis_result.get("intent", "")
        if intent in ["purchase", "demo", "renewal"]:
            factors["intent"] = 15
            score += 15
        elif intent in ["pricing", "negotiation"]:
            factors["intent"] = 10
            score += 10
        
        # Buying signals
        buying_signals_count = len(analysis_result.get("buying_signals", []))
        if buying_signals_count > 0:
            factors["buying_signals"] = min(buying_signals_count * 5, 20)
            score += factors["buying_signals"]
        
        # ICP Score
        icp_score = analysis_result.get("icp_score", 0)
        if icp_score > 70:
            factors["icp"] = 15
            score += 15
        elif icp_score > 50:
            factors["icp"] = 8
            score += 8
        
        # Objections penalty
        objections = analysis_result.get("objections", [])
        if objections:
            for obj in objections:
                if obj.get("type") == "price":
                    factors["price_objection"] = -5
                    score -= 5
                elif obj.get("type") in ["competing_solution", "already_using"]:
                    factors["competition_objection"] = -8
                    score -= 8
        
        # Emotion factor
        emotion = analysis_result.get("emotion", "")
        emotion_confidence = analysis_result.get("emotion_confidence", 0)
        
        if emotion in ["interested", "excited", "confident"] and emotion_confidence > 0.6:
            factors["positive_emotion"] = 10
            score += 10
        elif emotion in ["hesitant", "frustrated"] and emotion_confidence > 0.6:
            factors["negative_emotion"] = -8
            score -= 8
        
        # Normalize score to 0-100
        score = max(0, min(100, score))
        factors["final_score"] = score
        
        return score, factors


class LeadScorer:
    """Production Lead Scorer"""
    
    def __init__(self):
        self.rules = LeadScoringRules()
        self.models = {}  # Placeholder for ML models
        self.scoring_history = []
    
    def score(self, analysis_result: Dict[str, Any]) -> LeadScore:
        """
        Score a lead based on analysis results
        
        Returns:
            LeadScore object with score, qualification, and reasoning
        """
        try:
            # Calculate score using rules
            score, factors = self.rules.calculate_lead_score(analysis_result)
            
            # Determine qualification tier
            if score >= 75:
                qualification = QualificationTier.HOT.value
                confidence = min(100, score)
            elif score >= 50:
                qualification = QualificationTier.WARM.value
                confidence = min(100, score)
            else:
                qualification = QualificationTier.COLD.value
                confidence = 100 - score
            
            # Generate reasoning
            reasoning = self._generate_reasoning(analysis_result, score, factors)
            
            # Create result
            result = LeadScore(
                score=score,
                qualification=qualification,
                confidence=confidence,
                reasoning=reasoning,
                factors=factors,
                timestamp=datetime.now().isoformat()
            )
            
            # Store history
            self.scoring_history.append(result)
            
            return result
        
        except Exception as e:
            logger.error(f"Scoring error: {e}")
            # Return neutral score on error
            return LeadScore(
                score=50,
                qualification=QualificationTier.WARM.value,
                confidence=30,
                reasoning=["Error in scoring calculation"],
                factors={},
                timestamp=datetime.now().isoformat()
            )
    
    def _generate_reasoning(self, 
                           analysis_result: Dict[str, Any],
                           score: float,
                           factors: Dict[str, float]) -> List[str]:
        """Generate human-readable reasoning for score"""
        
        reasoning = []
        
        # Key positive factors
        if factors.get("budget", 0) > 0:
            budget_amount = analysis_result.get("budget_amount", 0)
            reasoning.append(f"✓ High budget identified: {budget_amount}")
        
        if factors.get("authority", 0) > 0:
            authority = analysis_result.get("authority", "Unknown")
            reasoning.append(f"✓ Decision maker present: {authority}")
        
        if factors.get("intent", 0) > 0:
            intent = analysis_result.get("intent", "")
            reasoning.append(f"✓ Clear intent: {intent}")
        
        if factors.get("buying_signals", 0) > 0:
            signals_count = len(analysis_result.get("buying_signals", []))
            reasoning.append(f"✓ {signals_count} buying signals detected")
        
        if factors.get("icp", 0) > 0:
            icp_score = analysis_result.get("icp_score", 0)
            reasoning.append(f"✓ Strong ICP match: {icp_score:.0f}%")
        
        # Key negative factors
        if factors.get("price_objection", 0) < 0:
            reasoning.append("✗ Price objection raised")
        
        if factors.get("negative_emotion", 0) < 0:
            emotion = analysis_result.get("emotion", "")
            reasoning.append(f"✗ Negative emotion detected: {emotion}")
        
        if not reasoning:
            reasoning.append("Standard evaluation criteria applied")
        
        return reasoning
    
    def get_report(self) -> Dict[str, Any]:
        """Get scoring statistics"""
        if not self.scoring_history:
            return {}
        
        scores = [r.score for r in self.scoring_history]
        qualifications = [r.qualification for r in self.scoring_history]
        
        return {
            "total_leads_scored": len(self.scoring_history),
            "average_score": np.mean(scores),
            "hot_count": qualifications.count(QualificationTier.HOT.value),
            "warm_count": qualifications.count(QualificationTier.WARM.value),
            "cold_count": qualifications.count(QualificationTier.COLD.value),
            "score_distribution": {
                "min": float(np.min(scores)),
                "max": float(np.max(scores)),
                "median": float(np.median(scores))
            }
        }


# ============================================================================
# ADVANCED LEAD SCORING WITH ML (Future Enhancement)
# ============================================================================

class MLLeadScorer:
    """
    Machine Learning Based Lead Scorer
    Placeholder for Random Forest + XGBoost models
    """
    
    def __init__(self):
        self.rf_model = None
        self.xgb_model = None
        self.feature_scaler = None
    
    def extract_features(self, analysis_result: Dict[str, Any]) -> np.ndarray:
        """
        Extract ML features from analysis result
        
        Features:
        - Emotion confidence (0-1)
        - Budget amount (normalized)
        - Authority level (0-3)
        - Need clarity (0-1)
        - Timeline urgency (0-3)
        - Intent strength (0-1)
        - Buying signals count
        - Objections count
        - ICP score (0-100)
        """
        
        features = [
            analysis_result.get("emotion_confidence", 0),
            min(analysis_result.get("budget_amount", 0) / 1000000, 1),  # Normalize
            self._encode_authority(analysis_result.get("authority_level")),
            1.0 if analysis_result.get("need") else 0,
            self._encode_timeline(analysis_result.get("timeline_urgency")),
            analysis_result.get("intent_confidence", 0),
            len(analysis_result.get("buying_signals", [])),
            len(analysis_result.get("objections", [])),
            analysis_result.get("icp_score", 0) / 100
        ]
        
        return np.array(features).reshape(1, -1)
    
    def _encode_authority(self, authority: str) -> float:
        """Encode authority level"""
        mapping = {
            "ceo_cfo": 3,
            "vp_director": 2,
            "manager": 1,
            "individual_contributor": 0.5
        }
        return mapping.get(authority, 0)
    
    def _encode_timeline(self, timeline: str) -> float:
        """Encode timeline urgency"""
        mapping = {
            "immediate": 3,
            "short_term": 2,
            "medium_term": 1,
            "long_term": 0.5
        }
        return mapping.get(timeline, 0)
    
    def predict(self, analysis_result: Dict[str, Any]) -> float:
        """Predict lead score using ML models"""
        # Placeholder - implement with actual trained models
        return 0.5  # Return neutral score
