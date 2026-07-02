"""
ML-Based Lead Scoring
Random Forest + XGBoost for accurate lead qualification
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LeadFeatures:
    """Features for lead scoring"""
    # BANT features
    bant_completeness: float = 0.0
    budget_amount: float = 0.0
    authority_level: float = 0.0
    need_clarity: float = 0.0
    timeline_urgency: float = 0.0
    
    # Intent features
    intent_strength: float = 0.0
    purchase_intent: float = 0.0
    demo_intent: float = 0.0
    pricing_intent: float = 0.0
    
    # Buying signals
    buying_signal_count: int = 0
    buying_signal_strength: float = 0.0
    readiness_score: float = 0.0
    
    # Objections
    objection_count: int = 0
    critical_objections: int = 0
    objection_severity: float = 0.0
    
    # Emotion
    emotion_positive_ratio: float = 0.0
    emotion_negative_ratio: float = 0.0
    emotion_confidence: float = 0.0
    
    # Conversation metrics
    conversation_duration: float = 0.0
    speaker_turns: int = 0
    question_count: int = 0
    words_per_minute: float = 0.0
    
    # ICP
    icp_score: float = 0.0
    
    # Summary
    opportunity_score: float = 0.0


@dataclass
class LeadScoreResult:
    """Lead scoring result"""
    score: float
    qualification: str  # HOT, WARM, COLD
    confidence: float
    probability: float  # Probability of conversion
    feature_importance: Dict[str, float]
    model_predictions: Dict[str, float]
    recommendations: List[str]


class MLLeadScorer:
    """
    ML-based lead scoring using Random Forest and XGBoost
    
    Trains on historical conversation data to predict lead quality
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize ML lead scorer
        
        Args:
            model_path: Path to saved model (optional)
        """
        self.model_path = model_path
        self.rf_model = None
        self.xgb_model = None
        self.feature_names = [
            'bant_completeness', 'budget_amount', 'authority_level', 'need_clarity', 'timeline_urgency',
            'intent_strength', 'purchase_intent', 'demo_intent', 'pricing_intent',
            'buying_signal_count', 'buying_signal_strength', 'readiness_score',
            'objection_count', 'critical_objections', 'objection_severity',
            'emotion_positive_ratio', 'emotion_negative_ratio', 'emotion_confidence',
            'conversation_duration', 'speaker_turns', 'question_count', 'words_per_minute',
            'icp_score', 'opportunity_score'
        ]
        
        # Try to load models
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models"""
        try:
            import joblib
            import os
            
            if self.model_path and os.path.exists(f"{self.model_path}/rf_model.pkl"):
                self.rf_model = joblib.load(f"{self.model_path}/rf_model.pkl")
                logger.info("Loaded Random Forest model")
            
            if self.model_path and os.path.exists(f"{self.model_path}/xgb_model.pkl"):
                self.xgb_model = joblib.load(f"{self.model_path}/xgb_model.pkl")
                logger.info("Loaded XGBoost model")
        
        except Exception as e:
            logger.warning(f"Failed to load models: {e}")
            self.rf_model = None
            self.xgb_model = None
    
    def _save_models(self):
        """Save trained models"""
        try:
            import joblib
            import os
            
            if self.model_path:
                os.makedirs(self.model_path, exist_ok=True)
                
                if self.rf_model:
                    joblib.dump(self.rf_model, f"{self.model_path}/rf_model.pkl")
                
                if self.xgb_model:
                    joblib.dump(self.xgb_model, f"{self.model_path}/xgb_model.pkl")
                
                logger.info("Models saved successfully")
        
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def extract_features(self, analysis: Dict) -> LeadFeatures:
        """
        Extract features from conversation analysis
        
        Args:
            analysis: Complete analysis dictionary from LLM engine
            
        Returns:
            LeadFeatures object
        """
        # BANT features
        bant = analysis.get("bant", {})
        bant_fields = sum([1 for f in ["budget", "authority", "need", "timeline"] if bant.get(f)])
        bant_completeness = bant_fields / 4.0
        
        # Budget amount (normalize)
        budget_amount = 0.0
        if bant.get("budget_amount"):
            try:
                budget_amount = min(1.0, float(bant["budget_amount"]) / 10000000)  # Normalize to 1 crore
            except:
                budget_amount = 0.0
        
        # Authority level
        authority_level = 0.0
        if bant.get("authority_level") in ["decision_maker", "ceo_cfo"]:
            authority_level = 1.0
        elif bant.get("authority_level") in ["vp_director", "manager"]:
            authority_level = 0.7
        elif bant.get("authority_level"):
            authority_level = 0.4
        
        # Need clarity
        need_clarity = 0.0
        if bant.get("need") and bant.get("need_category") != "general":
            need_clarity = 0.8
        elif bant.get("need"):
            need_clarity = 0.5
        
        # Timeline urgency
        timeline_urgency = 0.0
        if bant.get("timeline_urgency") == "immediate":
            timeline_urgency = 1.0
        elif bant.get("timeline_urgency") == "short_term":
            timeline_urgency = 0.8
        elif bant.get("timeline_urgency") == "medium_term":
            timeline_urgency = 0.5
        elif bant.get("timeline_urgency") == "long_term":
            timeline_urgency = 0.3
        
        # Intent features
        intent = analysis.get("intent", {})
        intent_strength = intent.get("confidence", 0.0)
        
        all_intents = intent.get("all_intents", {})
        purchase_intent = all_intents.get("purchase", 0.0)
        demo_intent = all_intents.get("demo", 0.0)
        pricing_intent = all_intents.get("pricing", 0.0)
        
        # Buying signals
        buying_signals = analysis.get("buying_signals", {})
        signals = buying_signals.get("signals", [])
        buying_signal_count = len(signals)
        buying_signal_strength = np.mean([s.get("strength", 0.0) for s in signals]) if signals else 0.0
        readiness_score = buying_signals.get("readiness_score", 0.0)
        
        # Objections
        objections = analysis.get("objections", {})
        objection_list = objections.get("objections", [])
        objection_count = len(objection_list)
        critical_objections = sum(1 for o in objection_list if o.get("severity") == "critical")
        objection_severity = 1.0 if critical_objections > 0 else (0.5 if objection_count > 0 else 0.0)
        
        # Emotion
        emotion = analysis.get("emotion", {})
        emotion_scores = emotion.get("all_scores", {})
        positive_emotions = ["interested", "excited", "confident", "happy"]
        negative_emotions = ["frustrated", "angry", "anxious", "hesitant"]
        
        emotion_positive_ratio = sum(emotion_scores.get(e, 0.0) for e in positive_emotions)
        emotion_negative_ratio = sum(emotion_scores.get(e, 0.0) for e in negative_emotions)
        emotion_confidence = emotion.get("confidence", 0.0)
        
        # Conversation metrics
        conv_metrics = analysis.get("conversation_metrics", {})
        conversation_duration = conv_metrics.get("speaking_duration", 0.0)
        speaker_turns = conv_metrics.get("turn_taking_count", 0)
        question_count = conv_metrics.get("question_count", 0)
        words_per_minute = conv_metrics.get("words_per_minute", 0.0)
        
        # ICP
        icp_score = analysis.get("icp_score", 0.0)
        
        # Summary
        summary = analysis.get("summary", {})
        opportunity_score = summary.get("opportunity_score", 0.0)
        
        return LeadFeatures(
            bant_completeness=bant_completeness,
            budget_amount=budget_amount,
            authority_level=authority_level,
            need_clarity=need_clarity,
            timeline_urgency=timeline_urgency,
            intent_strength=intent_strength,
            purchase_intent=purchase_intent,
            demo_intent=demo_intent,
            pricing_intent=pricing_intent,
            buying_signal_count=buying_signal_count,
            buying_signal_strength=buying_signal_strength,
            readiness_score=readiness_score,
            objection_count=objection_count,
            critical_objections=critical_objections,
            objection_severity=objection_severity,
            emotion_positive_ratio=emotion_positive_ratio,
            emotion_negative_ratio=emotion_negative_ratio,
            emotion_confidence=emotion_confidence,
            conversation_duration=conversation_duration,
            speaker_turns=speaker_turns,
            question_count=question_count,
            words_per_minute=words_per_minute,
            icp_score=icp_score,
            opportunity_score=opportunity_score
        )
    
    def _features_to_array(self, features: LeadFeatures) -> np.ndarray:
        """Convert features to numpy array"""
        return np.array([
            features.bant_completeness,
            features.budget_amount,
            features.authority_level,
            features.need_clarity,
            features.timeline_urgency,
            features.intent_strength,
            features.purchase_intent,
            features.demo_intent,
            features.pricing_intent,
            features.buying_signal_count,
            features.buying_signal_strength,
            features.readiness_score,
            features.objection_count,
            features.critical_objections,
            features.objection_severity,
            features.emotion_positive_ratio,
            features.emotion_negative_ratio,
            features.emotion_confidence,
            features.conversation_duration,
            features.speaker_turns,
            features.question_count,
            features.words_per_minute,
            features.icp_score,
            features.opportunity_score
        ]).reshape(1, -1)
    
    def predict(self, analysis: Dict) -> LeadScoreResult:
        """
        Predict lead score using ML models
        
        Args:
            analysis: Complete analysis dictionary
            
        Returns:
            LeadScoreResult with prediction
        """
        # Extract features
        features = self.extract_features(analysis)
        feature_array = self._features_to_array(features)
        
        # If no models loaded, use rule-based scoring
        if self.rf_model is None and self.xgb_model is None:
            return self._rule_based_score(features, analysis)
        
        # Get predictions from both models
        predictions = {}
        
        if self.rf_model is not None:
            rf_pred = self.rf_model.predict_proba(feature_array)[0]
            predictions["random_forest"] = rf_pred[1] if len(rf_pred) > 1 else rf_pred[0]
        
        if self.xgb_model is not None:
            xgb_pred = self.xgb_model.predict_proba(feature_array)[0]
            predictions["xgboost"] = xgb_pred[1] if len(xgb_pred) > 1 else xgb_pred[0]
        
        # Ensemble prediction (average)
        if predictions:
            avg_score = np.mean(list(predictions.values()))
        else:
            avg_score = 0.5
        
        # Get feature importance
        feature_importance = self._get_feature_importance()
        
        # Determine qualification
        qualification = self._get_qualification(avg_score)
        
        # Calculate confidence
        confidence = self._calculate_confidence(predictions)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(qualification, features)
        
        return LeadScoreResult(
            score=round(avg_score, 2),
            qualification=qualification,
            confidence=round(confidence, 2),
            probability=round(avg_score, 2),
            feature_importance=feature_importance,
            model_predictions=predictions,
            recommendations=recommendations
        )
    
    def _rule_based_score(self, features: LeadFeatures, analysis: Dict) -> LeadScoreResult:
        """
        Fallback rule-based scoring when ML models not available
        
        Args:
            features: Lead features
            analysis: Complete analysis
            
        Returns:
            LeadScoreResult
        """
        # Calculate weighted score
        score = (
            features.bant_completeness * 0.20 +
            features.readiness_score * 0.25 +
            features.intent_strength * 0.15 +
            (1.0 - features.objection_severity) * 0.10 +
            features.emotion_positive_ratio * 0.15 +
            features.icp_score * 0.15
        )
        
        # Determine qualification
        qualification = self._get_qualification(score)
        
        # Feature importance (simplified)
        feature_importance = {
            "bant_completeness": 0.20,
            "buying_readiness": 0.25,
            "intent_strength": 0.15,
            "objection_severity": 0.10,
            "emotion": 0.15,
            "icp_score": 0.15
        }
        
        # Recommendations
        recommendations = self._generate_recommendations(qualification, features)
        
        return LeadScoreResult(
            score=round(score, 2),
            qualification=qualification,
            confidence=0.7,  # Lower confidence for rule-based
            probability=round(score, 2),
            feature_importance=feature_importance,
            model_predictions={},
            recommendations=recommendations
        )
    
    def _get_qualification(self, score: float) -> str:
        """Get qualification from score"""
        if score >= 0.75:
            return "HOT"
        elif score >= 0.5:
            return "WARM"
        else:
            return "COLD"
    
    def _calculate_confidence(self, predictions: Dict[str, float]) -> float:
        """Calculate confidence in prediction"""
        if not predictions:
            return 0.7  # Rule-based confidence
        
        # Higher confidence when both models agree
        if len(predictions) == 2:
            diff = abs(predictions["random_forest"] - predictions["xgboost"])
            confidence = 1.0 - (diff * 0.5)
        else:
            confidence = 0.8
        
        return min(1.0, max(0.5, confidence))
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from models"""
        importance = {}
        
        if self.rf_model is not None and hasattr(self.rf_model, 'feature_importances_'):
            rf_importance = self.rf_model.feature_importances_
            for i, name in enumerate(self.feature_names):
                importance[name] = round(float(rf_importance[i]), 3)
        
        elif self.xgb_model is not None and hasattr(self.xgb_model, 'feature_importances_'):
            xgb_importance = self.xgb_model.feature_importances_
            for i, name in enumerate(self.feature_names):
                importance[name] = round(float(xgb_importance[i]), 3)
        
        else:
            # Default importance
            importance = {
                "bant_completeness": 0.20,
                "buying_readiness": 0.25,
                "intent_strength": 0.15,
                "objection_severity": 0.10,
                "emotion": 0.15,
                "icp_score": 0.15
            }
        
        return importance
    
    def _generate_recommendations(self, qualification: str, features: LeadFeatures) -> List[str]:
        """Generate recommendations based on features"""
        recommendations = []
        
        if qualification == "HOT":
            recommendations.append("URGENT: Lead is highly qualified. Initiate closing sequence immediately.")
            recommendations.append("Schedule final presentation with decision makers.")
        elif qualification == "WARM":
            recommendations.append("Lead shows promise. Continue nurturing and addressing gaps.")
        else:
            recommendations.append("Lead needs more qualification. Continue discovery process.")
        
        # Specific recommendations based on features
        if features.bant_completeness < 0.5:
            recommendations.append("Gather missing BANT information.")
        
        if features.objection_count > 0:
            recommendations.append(f"Address {features.objection_count} objection(s).")
        
        if features.readiness_score >= 0.7:
            recommendations.append("Strong buying signals. Accelerate sales process.")
        
        if features.emotion_positive_ratio < 0.3:
            recommendations.append("Customer engagement is low. Improve conversation quality.")
        
        return recommendations[:5]
    
    def train(self, training_data: List[Tuple[LeadFeatures, int, float]]):
        """
        Train ML models on historical data
        
        Args:
            training_data: List of (features, converted, lead_score) tuples
        """
        if not training_data:
            logger.warning("No training data provided")
            return
        
        try:
            from sklearn.ensemble import RandomForestClassifier
            from xgboost import XGBClassifier
            
            # Prepare data
            X = np.array([self._features_to_array(f)[0] for f, _, _ in training_data])
            y = np.array([conv for _, conv, _ in training_data])
            
            # Train Random Forest
            logger.info("Training Random Forest model...")
            self.rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42
            )
            self.rf_model.fit(X, y)
            
            # Train XGBoost
            logger.info("Training XGBoost model...")
            self.xgb_model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.xgb_model.fit(X, y)
            
            # Save models
            self._save_models()
            
            logger.info("Models trained successfully")
        
        except Exception as e:
            logger.error(f"Training failed: {e}")
    
    def evaluate(self, test_data: List[Tuple[LeadFeatures, int]]) -> Dict:
        """
        Evaluate model performance
        
        Args:
            test_data: List of (features, converted) tuples
            
        Returns:
            Evaluation metrics
        """
        if not test_data or (self.rf_model is None and self.xgb_model is None):
            return {"error": "No models or test data"}
        
        try:
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            X = np.array([self._features_to_array(f)[0] for f, _ in test_data])
            y_true = np.array([conv for _, conv in test_data])
            
            results = {}
            
            if self.rf_model is not None:
                y_pred = self.rf_model.predict(X)
                results["random_forest"] = {
                    "accuracy": round(accuracy_score(y_true, y_pred), 3),
                    "precision": round(precision_score(y_true, y_pred, zero_division=0), 3),
                    "recall": round(recall_score(y_true, y_pred, zero_division=0), 3),
                    "f1": round(f1_score(y_true, y_pred, zero_division=0), 3)
                }
            
            if self.xgb_model is not None:
                y_pred = self.xgb_model.predict(X)
                results["xgboost"] = {
                    "accuracy": round(accuracy_score(y_true, y_pred), 3),
                    "precision": round(precision_score(y_true, y_pred, zero_division=0), 3),
                    "recall": round(recall_score(y_true, y_pred, zero_division=0), 3),
                    "f1": round(f1_score(y_true, y_pred, zero_division=0), 3)
                }
            
            return results
        
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"error": str(e)}


class MLLeadScorerFactory:
    """Factory for creating ML lead scorer instances"""
    
    @staticmethod
    def create(model_path: Optional[str] = None) -> MLLeadScorer:
        """
        Create ML lead scorer
        
        Args:
            model_path: Path to saved models
            
        Returns:
            MLLeadScorer instance
        """
        return MLLeadScorer(model_path=model_path)