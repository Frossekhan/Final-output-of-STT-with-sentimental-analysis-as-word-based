"""
Conversation Intelligence Engine
Orchestrates all 7 modules for comprehensive conversation analysis
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
from collections import deque

from emotion.speech_emotion import SpeechEmotionRecognizer
from bant.parser import BANTEngine
from intent.predict import IntentDetector
from buying_signal.detect import BuyingSignalDetector
from objection.detect import ObjectionDetector
from icp.score import ICPScorer

logger = logging.getLogger(__name__)

class ConversationEngine:
    """
    Orchestrates all conversation intelligence modules
    """
    
    def __init__(self):
        """Initialize conversation engine with all modules"""
        self.emotion_recognizer = SpeechEmotionRecognizer()
        self.bant_extractor = BANTEngine()
        self.intent_detector = IntentDetector()
        self.buying_signal_detector = BuyingSignalDetector()
        self.objection_detector = ObjectionDetector()
        self.icp_scorer = ICPScorer()
        
        # Conversation history
        self.transcript_segments = deque(maxlen=20)
        self.audio_history = deque(maxlen=10)
        
        # Analysis results
        self.latest_analysis = {}
        self.conversation_summary = {
            "start_time": datetime.now(),
            "segments_processed": 0,
            "total_duration": 0.0
        }
        
        # Lead score tracking
        self.lead_scores = []
        self.component_scores = {
            "emotion": [],
            "bant": [],
            "intent": [],
            "buying_signals": [],
            "objections": [],
            "icp": [],
            "quality": []
        }
        
        logger.info("Conversation Engine initialized")
    
    def analyze_segment(self, text: str, audio: np.ndarray) -> Dict[str, any]:
        """
        Analyze a conversation segment (text + audio)
        
        Args:
            text: Transcribed text
            audio: Audio samples
        
        Returns:
            Complete analysis of the segment
        """
        try:
            # Store in history
            self.transcript_segments.append(text)
            self.audio_history.append(audio)
            
            # Run all 7 analyses
            analyses = {}
            
            # 1. Speech Emotion Recognition
            analyses['emotion'] = self._analyze_emotion(audio)
            
            # 2. BANT Extraction
            analyses['bant'] = self._analyze_bant(text)
            
            # 3. Intent Detection
            analyses['intent'] = self._analyze_intent(text)
            
            # 4. Buying Signals
            analyses['buying_signals'] = self._analyze_buying_signals(text)
            
            # 5. Objection Detection
            analyses['objections'] = self._analyze_objections(text)
            
            # 6. ICP Scoring
            analyses['icp'] = self._analyze_icp(text)
            
            # 7. Conversation Quality
            analyses['quality'] = self._analyze_conversation_quality(text, audio)
            
            # Update latest analysis
            self.latest_analysis = analyses
            
            # Calculate lead score
            lead_score_result = self._calculate_lead_score(analyses)
            
            # Build comprehensive response
            response = {
                "transcript": text,
                "timestamp": datetime.now().isoformat(),
                "lead_qualification": {
                    "score": lead_score_result["score"],
                    "qualification": lead_score_result["qualification"],
                    "confidence": lead_score_result["confidence"]
                },
                "emotion": self._format_emotion(analyses['emotion']),
                "bant_summary": self._format_bant(analyses['bant']),
                "intent": self._format_intent(analyses['intent']),
                "buying_readiness": self._format_buying_signals(analyses['buying_signals']),
                "objections": self._format_objections(analyses['objections']),
                "icp_match": self._format_icp(analyses['icp']),
                "key_insights": self._generate_insights(analyses),
                "recommendations": self._generate_recommendations(analyses, lead_score_result)
            }
            
            # Update stats
            self.conversation_summary["segments_processed"] += 1
            
            return response
        
        except Exception as e:
            logger.error(f"Error in analyze_segment: {e}")
            raise
    
    # ========================================================================
    # INDIVIDUAL MODULE ANALYSES
    # ========================================================================
    
    def _analyze_emotion(self, audio: np.ndarray) -> Dict[str, any]:
        """Analyze speech emotion"""
        emotion, confidence = self.emotion_recognizer.recognize_emotion(audio)
        self.component_scores["emotion"].append(confidence)
        return {"emotion": emotion, "confidence": confidence}
    
    def _analyze_bant(self, text: str) -> Dict[str, any]:
        """Extract BANT"""
        bant = self.bant_extractor.extract_bant(text)
        completeness = bant.get("completeness", 0)
        self.component_scores["bant"].append(completeness)
        return bant
    
    def _analyze_intent(self, text: str) -> Dict[str, any]:
        """Detect intent"""
        intent = self.intent_detector.detect_intent(text)
        self.component_scores["intent"].append(intent.get("confidence", 0))
        return intent
    
    def _analyze_buying_signals(self, text: str) -> Dict[str, any]:
        """Detect buying signals"""
        signals = self.buying_signal_detector.detect_signals(text)
        readiness = self.buying_signal_detector.calculate_buying_readiness(signals)
        self.component_scores["buying_signals"].append(readiness.get("score", 0))
        return {"signals": signals, "readiness": readiness}
    
    def _analyze_objections(self, text: str) -> Dict[str, any]:
        """Detect objections"""
        objections = self.objection_detector.detect_objections(text)
        # Lower score for objections (negative indicator)
        objection_score = 1.0 - min(0.5, len(objections.get("objections", [])) * 0.15)
        self.component_scores["objections"].append(objection_score)
        return objections
    
    def _analyze_icp(self, text: str) -> Dict[str, any]:
        """Score ICP match"""
        attributes = self.icp_scorer.extract_attributes(text)
        icp_score = self.icp_scorer.score_icp(attributes)
        normalized_score = icp_score["score"] / 100.0
        self.component_scores["icp"].append(normalized_score)
        return icp_score
    
    def _analyze_conversation_quality(self, text: str, audio: np.ndarray) -> Dict[str, any]:
        """Analyze conversation quality"""
        # Text length and clarity
        word_count = len(text.split())
        sentences = len(text.split('.'))
        
        # Audio quality
        rms_energy = np.sqrt(np.mean(audio ** 2))
        
        # Quality score
        quality_score = 0.5
        if word_count > 10:
            quality_score += 0.2
        if sentences > 1:
            quality_score += 0.15
        if rms_energy > 0.05:
            quality_score += 0.15
        
        quality_score = min(0.99, quality_score)
        self.component_scores["quality"].append(quality_score)
        
        return {
            "word_count": word_count,
            "sentence_count": sentences,
            "audio_energy": float(rms_energy),
            "quality_score": quality_score
        }
    
    # ========================================================================
    # LEAD SCORING
    # ========================================================================
    
    def _calculate_lead_score(self, analyses: Dict[str, any]) -> Dict[str, any]:
        """
        Calculate overall lead score using weighted ensemble
        
        Weights:
        - Emotion: 15%
        - BANT: 20%
        - Intent: 15%
        - Buying Signals: 25%
        - ICP: 15%
        - Quality: 10%
        """
        
        # Extract scores from analyses
        emotion_score = analyses.get('emotion', {}).get('confidence', 0.5)
        bant_score = analyses.get('bant', {}).get('completeness', 0.0)
        intent_score = analyses.get('intent', {}).get('confidence', 0.0)
        buying_score = analyses.get('buying_signals', {}).get('readiness', {}).get('score', 0.0)
        icp_score = analyses.get('icp', {}).get('score', 0.0) / 100.0
        quality_score = analyses.get('quality', {}).get('quality_score', 0.5)
        
        # Weighted calculation
        weights = {
            'emotion': 0.15,
            'bant': 0.20,
            'intent': 0.15,
            'buying': 0.25,
            'icp': 0.15,
            'quality': 0.10
        }
        
        weighted_score = (
            emotion_score * weights['emotion'] +
            bant_score * weights['bant'] +
            intent_score * weights['intent'] +
            buying_score * weights['buying'] +
            icp_score * weights['icp'] +
            quality_score * weights['quality']
        )
        
        # Convert to 0-100 scale
        lead_score = weighted_score * 100
        
        # Classify
        if lead_score >= 75:
            qualification = "HOT"
            confidence = 0.85
        elif lead_score >= 50:
            qualification = "WARM"
            confidence = 0.75
        else:
            qualification = "COLD"
            confidence = 0.70
        
        # Store for trend analysis
        self.lead_scores.append(lead_score)
        
        return {
            "score": float(lead_score),
            "qualification": qualification,
            "confidence": float(confidence),
            "component_scores": {
                "emotion": float(emotion_score),
                "bant": float(bant_score),
                "intent": float(intent_score),
                "buying_signals": float(buying_score),
                "icp": float(icp_score),
                "quality": float(quality_score)
            }
        }
    
    def get_lead_score(self) -> Dict[str, any]:
        """Get current lead score"""
        if not self.lead_scores:
            return {
                "score": 0.0,
                "qualification": "COLD",
                "confidence": 0.5
            }
        
        # Average of all scores (with recent ones weighted higher)
        if len(self.lead_scores) == 1:
            current_score = self.lead_scores[0]
        else:
            # Exponential weighted average (recent scores matter more)
            weights = np.array([0.5 ** (len(self.lead_scores) - i - 1) for i in range(len(self.lead_scores))])
            weights /= weights.sum()
            current_score = np.average(self.lead_scores, weights=weights)
        
        if current_score >= 75:
            qualification = "HOT"
            confidence = 0.85
        elif current_score >= 50:
            qualification = "WARM"
            confidence = 0.75
        else:
            qualification = "COLD"
            confidence = 0.70
        
        return {
            "score": float(current_score),
            "qualification": qualification,
            "confidence": float(confidence),
            "trend": self._calculate_trend()
        }
    
    def _calculate_trend(self) -> str:
        """Calculate lead score trend"""
        if len(self.lead_scores) < 2:
            return "neutral"
        
        recent = self.lead_scores[-3:]
        if len(recent) < 2:
            return "neutral"
        
        change = recent[-1] - recent[0]
        if change > 5:
            return "improving"
        elif change < -5:
            return "declining"
        else:
            return "neutral"
    
    # ========================================================================
    # FORMATTING & DISPLAY
    # ========================================================================
    
    def _format_emotion(self, emotion_data: Dict) -> Dict[str, str]:
        """Format emotion for display"""
        emotion_emoji = {
            "interested": "👂",
            "excited": "🤩",
            "confident": "💪",
            "curious": "🤔",
            "neutral": "😐",
            "hesitant": "😕",
            "frustrated": "😤",
            "anxious": "😰",
            "angry": "😠",
            "skeptical": "🤨"
        }
        
        emotion = emotion_data.get('emotion', 'neutral')
        emoji = emotion_emoji.get(emotion, '😐')
        confidence = emotion_data.get('confidence', 0)
        
        return {
            "emotion": emotion,
            "emoji": emoji,
            "confidence": f"{confidence * 100:.0f}%"
        }
    
    def _format_bant(self, bant_data: Dict) -> Dict:
        """Format BANT for display"""
        return self.bant_extractor.format_bant_summary(bant_data)
    
    def _format_intent(self, intent_data: Dict) -> Dict:
        """Format intent for display"""
        return self.intent_detector.format_intent_summary(intent_data)
    
    def _format_buying_signals(self, signal_data: Dict) -> Dict:
        """Format buying signals for display"""
        return self.buying_signal_detector.calculate_buying_readiness(signal_data['signals'])
    
    def _format_objections(self, objection_data: Dict) -> Dict:
        """Format objections for display"""
        return self.objection_detector.format_objections_summary(objection_data)
    
    def _format_icp(self, icp_data: Dict) -> Dict:
        """Format ICP for display"""
        return self.icp_scorer.format_icp_summary(icp_data)
    
    # ========================================================================
    # INSIGHTS & RECOMMENDATIONS
    # ========================================================================
    
    def _generate_insights(self, analyses: Dict[str, any]) -> List[str]:
        """Generate key insights from analysis"""
        insights = []
        
        # Emotion insight
        emotion = analyses['emotion'].get('emotion', 'neutral')
        if emotion in ['excited', 'interested', 'confident']:
            insights.append(f"Customer shows {emotion} tone - positive engagement signal")
        elif emotion in ['hesitant', 'anxious']:
            insights.append(f"Customer appears {emotion} - may need reassurance")
        
        # BANT insight
        bant = analyses['bant']
        bant_complete = sum([
            bant['budget']['amount'] is not None,
            bant['authority']['level'] is not None,
            bant['need']['primary_need'] is not None,
            bant['timeline']['urgency'] is not None
        ])
        if bant_complete == 4:
            insights.append("Complete BANT information gathered - strong qualification signal")
        elif bant_complete >= 2:
            insights.append("Partial BANT gathered - probe for missing information")
        
        # Buying signals insight
        signal_count = analyses['buying_signals']['signals']['signal_count']
        if signal_count >= 3:
            insights.append(f"Multiple buying signals detected ({signal_count}) - high purchase intent")
        elif signal_count >= 1:
            insights.append(f"Some buying signals present - explore further")
        
        # Objections insight
        objection_count = analyses['objections']['objection_count']
        if objection_count > 0:
            objection = analyses['objections']['objections'][0]
            insights.append(f"Key objection detected: {objection['objection']} - needs addressing")
        
        # ICP insight
        icp_tier = analyses['icp']['tier']
        if icp_tier in ['A+', 'A']:
            insights.append(f"Strong ICP match (Tier {icp_tier}) - ideal customer profile")
        
        return insights
    
    def _generate_recommendations(self, analyses: Dict[str, any], lead_score: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        qualification = lead_score['qualification']
        
        if qualification == "HOT":
            recommendations.append("URGENT: Lead is highly qualified. Initiate closing sequence immediately.")
            recommendations.append("Schedule final presentation/demo with decision makers.")
            recommendations.append("Prepare and send proposal/quotation.")
            recommendations.append("Discuss contract terms and timeline.")
        
        elif qualification == "WARM":
            recommendations.append("Lead shows strong potential. Provide additional information.")
            recommendations.append("Schedule discovery call to understand needs better.")
            recommendations.append("Send case studies and success stories.")
            recommendations.append("Address any objections identified.")
        
        else:  # COLD
            recommendations.append("Lead needs more nurturing. Focus on education.")
            recommendations.append("Identify and address main concerns.")
            recommendations.append("Provide value-focused content.")
            recommendations.append("Plan follow-up for future opportunity.")
        
        # Specific recommendations based on analysis
        objections = analyses['objections']
        if objections['objection_count'] > 0:
            obj_type = objections['objections'][0]['objection']
            strategy = self.objection_detector.get_handling_strategy(obj_type)
            recommendations.append(f"Handle objection: {strategy['strategy']}")
        
        return recommendations
