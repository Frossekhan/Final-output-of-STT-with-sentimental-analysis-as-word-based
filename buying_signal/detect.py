"""
Buying signal detection for sales conversations
Identifies strong purchase intent signals from customer speech
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Buying signal strength levels"""
    VERY_HIGH = "very_high"  # > 0.8
    HIGH = "high"  # 0.6 - 0.8
    MEDIUM = "medium"  # 0.4 - 0.6
    LOW = "low"  # 0.2 - 0.4
    VERY_LOW = "very_low"  # < 0.2


@dataclass
class BuyingSignal:
    """Buying signal detection result"""
    signal_type: str
    strength: float
    strength_level: SignalStrength
    confidence: float
    keywords_matched: List[str]
    context: str
    recommendation: str


class BuyingSignalDetector:
    """
    Detects buying signals in sales conversations
    
    Buying signals indicate customer's willingness to purchase:
    - High intent signals (ready to buy)
    - Information signals (requesting details)
    - Engagement signals (active participation)
    - Commitment signals (time/resource investment)
    """
    
    # Buying signal categories and patterns
    SIGNAL_PATTERNS = {
        "request_quotation": {
            "weight": 0.95,
            "keywords": [
                'send quotation', 'send quote', 'need quotation', 'need quote',
                'share pricing', 'share rates', 'send proposal', 'send estimate'
            ],
            "phrases": [
                r'can\s+you\s+(?:send|share|provide)\s+(?:me\s+)?(?:a\s+)?(?:quotation|quote|proposal)',
                r'(?:i|we)\s+(?:need|want|require)\s+(?:a\s+)?(?:quotation|quote|proposal|estimate)',
                r'(?:please|kindly)\s+(?:send|share)\s+(?:the\s+)?(?:pricing|rates?|quotation)'
            ],
            "recommendation": "Immediate follow-up required. Customer is ready to receive pricing."
        },
        "request_demo": {
            "weight": 0.85,
            "keywords": [
                'schedule demo', 'book demo', 'arrange demo', 'set up demo',
                'show me', 'demonstrate', 'walkthrough', 'presentation'
            ],
            "phrases": [
                r'(?:can|could)\s+you\s+(?:schedule|arrange|set\s+up|book)\s+(?:a\s+)?demo',
                r'(?:i|we)\s+(?:want|would\s+like|need)\s+(?:to\s+)?(?:see|get)\s+(?:a\s+)?demo',
                r'when\s+(?:can|could)\s+we\s+(?:schedule|have|do)\s+(?:a\s+)?demo'
            ],
            "recommendation": "High interest. Schedule demo immediately to maintain momentum."
        },
        "discuss_contract": {
            "weight": 0.9,
            "keywords": [
                'contract', 'agreement', 'terms', 'legal', 'paperwork',
                'documentation', 'sign', 'signature', 'msa', 'sow'
            ],
            "phrases": [
                r'(?:can|could)\s+we\s+(?:discuss|review|go\s+over)\s+(?:the\s+)?(?:contract|agreement|terms)',
                r'(?:i|we)\s+(?:want|need|ready)\s+to\s+(?:sign|review|discuss)',
                r'(?:what|how)\s+(?:are|is)\s+(?:the\s+)?(?:terms?|conditions?|agreement)'
            ],
            "recommendation": "Very strong signal. Prepare contract and initiate legal review."
        },
        "discuss_payment": {
            "weight": 0.88,
            "keywords": [
                'payment terms', 'payment method', 'invoice', 'billing',
                'payment schedule', 'installment', 'upfront', 'advance'
            ],
            "phrases": [
                r'(?:what|how)\s+(?:are|is)\s+(?:the\s+)?(?:payment|billing|invoice)',
                r'(?:can|could)\s+we\s+(?:discuss|arrange|set\s+up)\s+(?:payment|billing)',
                r'(?:i|we)\s+(?:prefer|want|need)\s+(?:to\s+)?(?:pay|payment)'
            ],
            "recommendation": "Strong signal. Discuss payment options and terms."
        },
        "discuss_timeline": {
            "weight": 0.8,
            "keywords": [
                'when can we start', 'implementation timeline', 'onboarding',
                'go-live', 'launch date', 'start date', 'deployment'
            ],
            "phrases": [
                r'(?:when|how\s+soon)\s+(?:can|could)\s+we\s+(?:start|begin|launch|deploy)',
                r'(?:what|how)\s+(?:is|are)\s+(?:the\s+)?(?:timeline|schedule|roadmap)',
                r'(?:i|we)\s+(?:want|need|plan)\s+to\s+(?:start|begin|launch|implement)'
            ],
            "recommendation": "Good engagement. Provide implementation timeline and next steps."
        },
        "request_meeting": {
            "weight": 0.75,
            "keywords": [
                'schedule call', 'book meeting', 'set up meeting', 'arrange call',
                'can we meet', 'let us meet', 'schedule time'
            ],
            "phrases": [
                r'(?:can|could)\s+you\s+(?:schedule|book|arrange)\s+(?:a\s+)?(?:call|meeting|discussion)',
                r'(?:when|how\s+about)\s+(?:can|could)\s+we\s+(?:meet|talk|discuss)',
                r'(?:i|we)\s+(?:want|would\s+like)\s+to\s+(?:schedule|book|have)\s+(?:a\s+)?(?:call|meeting)'
            ],
            "recommendation": "Active interest. Schedule follow-up meeting with decision makers."
        },
        "request_reference": {
            "weight": 0.82,
            "keywords": [
                'reference', 'case study', 'testimonial', 'customer story',
                'similar customer', 'success story', 'client example'
            ],
            "phrases": [
                r'(?:can|could)\s+you\s+(?:share|provide|send)\s+(?:a\s+)?(?:reference|case\s+study|testimonial)',
                r'(?:do\s+you\s+have|can\s+you\s+share)\s+(?:any\s+)?(?:similar|relevant)\s+(?:case|example|story)',
                r'(?:i|we)\s+(?:want|would\s+like|need)\s+to\s+(?:see|read|hear)\s+(?:about|from)\s+(?:other\s+)?(?:customers?|clients?)'
            ],
            "recommendation": "Serious consideration. Provide relevant case studies and references."
        },
        "discuss_features": {
            "weight": 0.7,
            "keywords": [
                'feature', 'functionality', 'capability', 'integration',
                'customization', 'configuration', 'setup', 'technical'
            ],
            "phrases": [
                r'(?:can|could)\s+you\s+(?:explain|describe|show)\s+(?:the\s+)?(?:features?|functionality)',
                r'(?:how|what)\s+(?:does|do|can|will)\s+(?:it|this|the\s+system)\s+(?:support|handle|do)',
                r'(?:i|we)\s+(?:need|want|require)\s+(?:specific|custom|advanced)\s+(?:features?|functionality)'
            ],
            "recommendation": "Evaluating fit. Provide detailed feature documentation and technical specs."
        },
        "discuss_pricing": {
            "weight": 0.78,
            "keywords": [
                'pricing model', 'pricing structure', 'cost breakdown',
                'what\'s included', 'package', 'plan', 'tier'
            ],
            "phrases": [
                r'(?:what|how)\s+(?:is|are)\s+(?:the\s+)?(?:pricing|prices?|costs?)',
                r'(?:can|could)\s+you\s+(?:explain|break\s+down|detail)\s+(?:the\s+)?(?:pricing|cost)',
                r'(?:what|how)\s+(?:does|is)\s+(?:included|covered|included)\s+(?:in|with)\s+(?:the\s+)?(?:price|plan|package)'
            ],
            "recommendation": "Price sensitivity. Present clear pricing breakdown and value proposition."
        },
        "commitment_language": {
            "weight": 0.85,
            "keywords": [
                'we will', 'i will', 'let us proceed', 'ready to move forward',
                'sounds good', 'looks good', 'makes sense', 'agreed'
            ],
            "phrases": [
                r'(?:i|we)\s+(?:will|am\s+ready|are\s+ready)\s+to\s+(?:proceed|move\s+forward|go\s+ahead)',
                r'(?:that|this)\s+(?:sounds?|looks?)\s+(?:good|great|perfect|right)',
                r'(?:i|we)\s+(?:agree|concur|accept)\s+(?:with|that)',
                r'(?:let\s+us|let\'s)\s+(?:proceed|move\s+forward|go\s+ahead|do\s+it)'
            ],
            "recommendation": "Strong commitment. Prepare for closing and next steps."
        },
        "urgency_indicators": {
            "weight": 0.72,
            "keywords": [
                'asap', 'urgent', 'immediately', 'right away', 'soon',
                'quickly', 'fast', 'deadline', 'time-sensitive'
            ],
            "phrases": [
                r'(?:we|i)\s+(?:need|want|require)\s+(?:this|it)\s+(?:asap|urgently|immediately)',
                r'(?:this|it)\s+(?:is|has\s+to\s+be)\s+(?:urgent|asap|immediate)',
                r'(?:we|i)\s+(?:have|face)\s+(?:a\s+)?(?:deadline|time\s+constraint)'
            ],
            "recommendation": "Time pressure. Accelerate sales process and prioritize response."
        },
        "budget_confirmation": {
            "weight": 0.87,
            "keywords": [
                'budget approved', 'budget allocated', 'funds available',
                'budget is ready', 'financial approval', 'budget secured'
            ],
            "phrases": [
                r'(?:our|the|my)\s+budget\s+(?:is|has\s+been)\s+(?:approved|allocated|secured|ready)',
                r'(?:we|i)\s+(?:have|got)\s+(?:the\s+)?(?:budget|funds?|money)\s+(?:approved|ready|allocated)',
                r'(?:budget|funds?|money)\s+(?:is|are)\s+(?:approved|ready|available)'
            ],
            "recommendation": "Budget confirmed. Move to proposal and contract stage."
        },
        "decision_maker_engagement": {
            "weight": 0.8,
            "keywords": [
                'ceo', 'cto', 'cfo', 'director', 'vp', 'founder',
                'decision maker', 'management', 'leadership', 'board'
            ],
            "phrases": [
                r'(?:i|we)\s+(?:am|are)\s+(?:the\s+)?(?:decision\s+maker|ceo|cto|cfo|director|vp)',
                r'(?:i|we)\s+(?:report|answer)\s+to\s+(?:the\s+)?(?:ceo|cto|cfo|director)',
                r'(?:my|our)\s+(?:ceo|cto|cfo|director|management)\s+(?:is|are)\s+(?:also\s+)?(?:involved|interested|engaged)'
            ],
            "recommendation": "Decision maker engaged. Schedule executive-level presentation."
        }
    }
    
    def __init__(self):
        self.signal_history: List[BuyingSignal] = []
        
    def detect_signals(self, text: str) -> List[BuyingSignal]:
        """
        Detect all buying signals in text
        
        Args:
            text: Input text
            
        Returns:
            List of BuyingSignal detected
        """
        text_lower = text.lower()
        signals = []
        
        for signal_type, patterns in self.SIGNAL_PATTERNS.items():
            score = 0.0
            matched_keywords = []
            
            # Check keywords
            for keyword in patterns['keywords']:
                if keyword in text_lower:
                    score += 1.0
                    matched_keywords.append(keyword)
            
            # Check phrases (higher weight)
            for phrase in patterns['phrases']:
                if re.search(phrase, text_lower):
                    score += 2.0
                    matched_keywords.append(phrase)
            
            # Calculate normalized score
            max_possible = len(patterns['keywords']) + len(patterns['phrases']) * 2
            if max_possible > 0 and score > 0:
                normalized_score = min(1.0, (score / max_possible) * patterns['weight'])
                confidence = min(1.0, score / max_possible)
                
                # Determine strength level
                strength_level = self._get_strength_level(normalized_score)
                
                signal = BuyingSignal(
                    signal_type=signal_type,
                    strength=normalized_score,
                    strength_level=strength_level,
                    confidence=confidence,
                    keywords_matched=matched_keywords,
                    context=text,
                    recommendation=patterns['recommendation']
                )
                
                signals.append(signal)
                self.signal_history.append(signal)
        
        # Sort by strength
        signals.sort(key=lambda x: x.strength, reverse=True)
        
        return signals
    
    def _get_strength_level(self, score: float) -> SignalStrength:
        """Get signal strength level from score"""
        if score >= 0.8:
            return SignalStrength.VERY_HIGH
        elif score >= 0.6:
            return SignalStrength.HIGH
        elif score >= 0.4:
            return SignalStrength.MEDIUM
        elif score >= 0.2:
            return SignalStrength.LOW
        else:
            return SignalStrength.VERY_LOW
    
    def get_top_signals(self, n: int = 5) -> List[BuyingSignal]:
        """Get top N buying signals from history"""
        sorted_signals = sorted(
            self.signal_history,
            key=lambda x: x.strength,
            reverse=True
        )
        return sorted_signals[:n]
    
    def get_signals_by_strength(self, min_strength: float = 0.5) -> List[BuyingSignal]:
        """Get signals above a certain strength threshold"""
        return [s for s in self.signal_history if s.strength >= min_strength]
    
    def get_signal_summary(self) -> Dict:
        """Get summary of buying signals"""
        if not self.signal_history:
            return {
                "total_signals": 0,
                "strong_signals": 0,
                "average_strength": 0.0,
                "top_signals": [],
                "recommendations": []
            }
        
        # Count strong signals
        strong_signals = [s for s in self.signal_history if s.strength >= 0.6]
        
        # Calculate average strength
        avg_strength = sum(s.strength for s in self.signal_history) / len(self.signal_history)
        
        # Get top signals
        top_signals = self.get_top_signals(5)
        
        # Get unique recommendations
        recommendations = list(set(
            s.recommendation for s in strong_signals
        ))
        
        return {
            "total_signals": len(self.signal_history),
            "strong_signals": len(strong_signals),
            "average_strength": round(avg_strength, 2),
            "top_signals": [
                {
                    "type": s.signal_type,
                    "strength": round(s.strength, 2),
                    "level": s.strength_level.value,
                    "recommendation": s.recommendation
                }
                for s in top_signals
            ],
            "recommendations": recommendations
        }
    
    def get_buying_readiness_score(self) -> float:
        """
        Calculate overall buying readiness score
        
        Returns:
            Score between 0 and 1
        """
        if not self.signal_history:
            return 0.0
        
        # Weight recent signals more heavily
        recent_signals = self.signal_history[-10:]
        
        # Calculate weighted average
        total_weight = 0
        weighted_sum = 0
        
        for i, signal in enumerate(recent_signals):
            # More recent signals have higher weight
            weight = (i + 1) / len(recent_signals)
            weighted_sum += signal.strength * weight
            total_weight += weight
        
        if total_weight > 0:
            score = weighted_sum / total_weight
        else:
            score = 0.0
        
        return round(score, 2)
    
    def get_signal_timeline(self) -> List[Dict]:
        """Get timeline of buying signals"""
        timeline = []
        
        for signal in self.signal_history:
            timeline.append({
                "signal_type": signal.signal_type,
                "strength": round(signal.strength, 2),
                "level": signal.strength_level.value,
                "timestamp": len(timeline)  # Placeholder for actual timestamp
            })
        
        return timeline
    
    def detect_signal_transitions(self) -> List[Tuple[str, str, float]]:
        """
        Detect transitions between signal types
        
        Returns:
            List of (from_signal, to_signal, strength_change)
        """
        if len(self.signal_history) < 2:
            return []
        
        transitions = []
        for i in range(1, len(self.signal_history)):
            prev_signal = self.signal_history[i-1]
            curr_signal = self.signal_history[i]
            
            if prev_signal.signal_type != curr_signal.signal_type:
                strength_change = curr_signal.strength - prev_signal.strength
                transitions.append((
                    prev_signal.signal_type,
                    curr_signal.signal_type,
                    round(strength_change, 2)
                ))
        
        return transitions
    
    def reset(self):
        """Reset signal history"""
        self.signal_history = []


class BuyingSignalAnalyzer:
    """Advanced buying signal analysis"""
    
    def __init__(self):
        self.detector = BuyingSignalDetector()
        
    def analyze_conversation(self, texts: List[str]) -> Dict:
        """
        Analyze buying signals across a conversation
        
        Args:
            texts: List of conversation texts
            
        Returns:
            Comprehensive analysis of buying signals
        """
        all_signals = []
        
        for text in texts:
            signals = self.detector.detect_signals(text)
            all_signals.extend(signals)
        
        # Get summary
        summary = self.detector.get_signal_summary()
        
        # Get readiness score
        readiness_score = self.detector.get_buying_readiness_score()
        
        # Get signal progression
        signal_progression = self._analyze_progression(all_signals)
        
        # Get recommendations
        recommendations = self._generate_recommendations(summary, readiness_score)
        
        return {
            "summary": summary,
            "buying_readiness_score": readiness_score,
            "readiness_level": self._get_readiness_level(readiness_score),
            "signal_progression": signal_progression,
            "recommendations": recommendations,
            "total_signals_detected": len(all_signals)
        }
    
    def _analyze_progression(self, signals: List[BuyingSignal]) -> Dict:
        """Analyze progression of buying signals"""
        if not signals:
            return {"trend": "no_signals", "progression": []}
        
        # Group by signal type
        signal_types = {}
        for signal in signals:
            if signal.signal_type not in signal_types:
                signal_types[signal.signal_type] = []
            signal_types[signal.signal_type].append(signal.strength)
        
        # Calculate progression for each type
        progression = {}
        for signal_type, strengths in signal_types.items():
            if len(strengths) > 1:
                # Calculate trend
                if strengths[-1] > strengths[0]:
                    trend = "increasing"
                elif strengths[-1] < strengths[0]:
                    trend = "decreasing"
                else:
                    trend = "stable"
                
                progression[signal_type] = {
                    "trend": trend,
                    "first_strength": round(strengths[0], 2),
                    "last_strength": round(strengths[-1], 2),
                    "change": round(strengths[-1] - strengths[0], 2)
                }
        
        return progression
    
    def _generate_recommendations(self, summary: Dict, readiness_score: float) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Based on readiness score
        if readiness_score >= 0.8:
            recommendations.append("URGENT: Customer is highly ready to buy. Initiate closing sequence immediately.")
            recommendations.append("Prepare final proposal and contract for immediate review.")
        elif readiness_score >= 0.6:
            recommendations.append("Customer shows strong buying signals. Accelerate sales process.")
            recommendations.append("Schedule follow-up meeting with decision makers.")
        elif readiness_score >= 0.4:
            recommendations.append("Moderate interest detected. Continue nurturing and addressing concerns.")
            recommendations.append("Provide additional information and case studies.")
        else:
            recommendations.append("Low buying signals. Focus on needs discovery and value proposition.")
        
        # Based on specific signals
        if summary.get("top_signals"):
            for signal in summary["top_signals"][:3]:
                if signal["strength"] >= 0.7:
                    recommendations.append(signal["recommendation"])
        
        return recommendations
    
    def _get_readiness_level(self, score: float) -> str:
        """Get readiness level from score"""
        if score >= 0.8:
            return "READY_TO_BUY"
        elif score >= 0.6:
            return "HIGH_INTENT"
        elif score >= 0.4:
            return "MEDIUM_INTENT"
        elif score >= 0.2:
            return "LOW_INTENT"
        else:
            return "NOT_READY"