"""
Buying Signal Detection Module
Identifies signals indicating purchase readiness
"""

import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class BuyingSignalDetector:
    """
    Detects buying signals from conversation text
    12 signal types with weighted importance
    """
    
    # Signal patterns with weights
    SIGNALS = {
        'request_quotation': {
            'weight': 0.95,
            'patterns': [
                r'\b(?:send|give|provide)\s+(?:us|me)\s+(?:a\s+)?(?:quote|quotation|proposal)\b',
                r'\b(?:request|ask\s+for)\s+(?:a\s+)?(?:quote|proposal|pricing)\b',
                r'\b(?:quotation|quote)\s+(?:please|now|asap)\b',
                r'\bsend\s+(?:us|me)\s+(?:details|proposal)\b',
            ],
            'description': 'Customer directly requesting a quotation'
        },
        'discuss_contract': {
            'weight': 0.90,
            'patterns': [
                r'\b(?:discuss|talk\s+about)\s+(?:contract|terms|agreement)\b',
                r'\b(?:contract|agreement)\s+(?:details|terms|conditions)\b',
                r'\b(?:what\s+are|let\'?s\s+discuss)\s+(?:the\s+)?(?:terms|conditions)\b',
                r'\b(?:ready\s+to|let\'?s)\s+(?:sign|finalize)\b',
            ],
            'description': 'Customer ready to discuss contract terms'
        },
        'budget_confirmation': {
            'weight': 0.87,
            'patterns': [
                r'\b(?:budget|budget)\s+(?:is\s+)?(?:approved|confirmed|allocated)\b',
                r'\b(?:we\s+have|we\'?ve\s+got)\s+(?:the\s+)?budget\b',
                r'\b(?:budget\s+is)\s+not\s+(?:a\s+)?issue\b',
                r'\b(?:can\s+allocate|have\s+allocated)\s+(?:funds|budget)\b',
            ],
            'description': 'Customer has confirmed budget availability'
        },
        'commitment_language': {
            'weight': 0.85,
            'patterns': [
                r'\b(?:we|let\'?s)\s+(?:are\s+)?(?:ready|prepared|committed)\s+to\b',
                r'\b(?:we\'?re\s+)?interested\s+in\s+(?:moving|proceeding)\s+(?:forward|ahead)\b',
                r'\b(?:let\'?s\s+)?(?:move|proceed|go)\s+(?:forward|ahead)\b',
                r'\b(?:committed\s+to|determined\s+to)\s+(?:implement|deploy)\b',
            ],
            'description': 'Customer expressing commitment to move forward'
        },
        'request_demo': {
            'weight': 0.85,
            'patterns': [
                r'\b(?:schedule|book|set\s+up)\s+(?:a\s+)?(?:demo|call|presentation)\b',
                r'\b(?:demo|trial|poc)\s+(?:when|start|available)\b',
                r'\b(?:want|need)\s+(?:to\s+)?(?:see|try|test)\b',
                r'\b(?:show|demonstrate)\s+(?:us|me)\s+how\b',
            ],
            'description': 'Customer requesting a product demo'
        },
        'request_reference': {
            'weight': 0.82,
            'patterns': [
                r'\b(?:case\s+studies?|references?|testimonials?)\b',
                r'\b(?:show|share)\s+(?:success|case\s+studies?)\b',
                r'\b(?:who|which)\s+(?:customers|clients)\s+(?:use|have)\b',
                r'\b(?:success\s+stories?|examples?)\b',
            ],
            'description': 'Customer asking for references or case studies'
        },
        'decision_maker_engagement': {
            'weight': 0.80,
            'patterns': [
                r'\b(?:i\s+)?(?:am|i\'?m)\s+(?:the\s+)?(?:ceo|cfo|decision\s+maker)\b',
                r'\b(?:i\s+)?(?:am|i\'?m)\s+(?:in\s+charge|responsible)\b',
                r'\b(?:can\s+decide|can\s+approve|make\s+decisions)\b',
                r'\b(?:authorized|authorized|empowered)\s+to\b',
            ],
            'description': 'Decision maker is directly engaged'
        },
        'discuss_timeline': {
            'weight': 0.80,
            'patterns': [
                r'\b(?:when|timeline)\s+(?:can\s+we|should\s+we|can\s+you)\s+(?:start|implement|deploy)\b',
                r'\b(?:implementation|rollout|deployment)\s+(?:timeline|schedule)\b',
                r'\b(?:how\s+long|when)\s+(?:would|can|does|will)\s+(?:it\s+take|this\s+take)\b',
                r'\b(?:urgent|asap|soon)\s+(?:implementation|deployment|start)\b',
            ],
            'description': 'Customer discussing implementation timeline'
        },
        'urgency_indicators': {
            'weight': 0.72,
            'patterns': [
                r'\b(?:urgent|urgent|asap|immediately|right\s+now)\b',
                r'\b(?:critical|critical|emergency|crisis)\b',
                r'\b(?:need\s+)?(?:it|this)\s+(?:urgently|asap|now)\b',
                r'\b(?:cannot\s+wait|no\s+time|hurry)\b',
            ],
            'description': 'Customer expressing urgency'
        },
        'discuss_pricing': {
            'weight': 0.78,
            'patterns': [
                r'\b(?:pricing|cost|price)\s+(?:details|breakdown|structure)\b',
                r'\b(?:what\'?s\s+)?(?:included|not\s+included)\b',
                r'\b(?:pricing|payment)\s+(?:options|plans)\b',
                r'\b(?:license|subscription)\s+(?:model|type)\b',
            ],
            'description': 'Customer discussing pricing details'
        },
        'discuss_features': {
            'weight': 0.70,
            'patterns': [
                r'\b(?:can\s+(?:it|this)|does\s+(?:it|this))\s+(?:have|support|do)\b',
                r'\b(?:can\s+it|does|will)\s+(?:integrate|work\s+with|support)\b',
                r'\b(?:features?|capabilities|functionality)\s+(?:that|we|you)\s+need\b',
                r'\b(?:what\s+(?:about|if)|need)\s+(?:support\s+for|ability\s+to)\b',
            ],
            'description': 'Customer asking about specific features'
        },
        'request_meeting': {
            'weight': 0.75,
            'patterns': [
                r'\b(?:schedule|book|set\s+up|arrange)\s+(?:a\s+)?(?:call|meeting|discussion)\b',
                r'\b(?:let\'?s\s+)?(?:discuss|talk|meet)\s+(?:this\s+)?(?:week|soon|further)\b',
                r'\b(?:when\s+can\s+we|can\s+we)\s+(?:talk|meet|discuss)\b',
                r'\b(?:meeting|call)\s+(?:schedule|available|when)\b',
            ],
            'description': 'Customer requesting a meeting'
        }
    }
    
    def __init__(self):
        """Initialize buying signal detector"""
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List]:
        """Compile regex patterns"""
        compiled = {}
        for signal, info in self.SIGNALS.items():
            compiled[signal] = [re.compile(p, re.IGNORECASE) for p in info['patterns']]
        return compiled
    
    def detect_signals(self, text: str) -> Dict[str, any]:
        """
        Detect buying signals from text
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with detected signals
        """
        text_lower = text.lower()
        
        detected_signals = []
        total_strength = 0
        
        # Check each signal type
        for signal_name, patterns in self.compiled_patterns.items():
            signal_info = self.SIGNALS[signal_name]
            weight = signal_info['weight']
            
            # Check if any pattern matches
            for pattern in patterns:
                if pattern.search(text_lower):
                    detected_signals.append({
                        'signal': signal_name,
                        'weight': weight,
                        'description': signal_info['description'],
                        'strength': weight
                    })
                    total_strength += weight
                    break  # Count each signal once
        
        # Sort by strength (weight)
        detected_signals.sort(key=lambda x: x['strength'], reverse=True)
        
        return {
            'signals': detected_signals,
            'signal_count': len(detected_signals),
            'total_strength': total_strength,
            'average_strength': total_strength / len(detected_signals) if detected_signals else 0.0,
            'detected': len(detected_signals) > 0
        }
    
    def calculate_buying_readiness(self, signals_data: Dict[str, any]) -> Dict[str, any]:
        """
        Calculate overall buying readiness from signals
        
        Args:
            signals_data: Result from detect_signals
        
        Returns:
            Buying readiness score (0-1.0)
        """
        signals = signals_data.get('signals', [])
        
        if not signals:
            return {
                'readiness': 'NOT_READY',
                'score': 0.0,
                'confidence': 0.5,
                'recommendation': 'No buying signals detected'
            }
        
        # Calculate score based on signals
        # Most important signals have higher weight
        top_signals = signals[:5]  # Top 5 signals
        
        if len(top_signals) >= 3:
            # Multiple strong signals
            readiness_score = min(1.0, sum(s['strength'] for s in top_signals) / 5.0)
            readiness = 'READY_TO_BUY'
            confidence = 0.85
        elif len(top_signals) >= 2:
            # Some signals
            readiness_score = sum(s['strength'] for s in top_signals) / 3.0
            readiness = 'LIKELY_TO_BUY'
            confidence = 0.70
        else:
            # Single signal
            readiness_score = top_signals[0]['strength'] / 3.0
            readiness = 'CONSIDERING'
            confidence = 0.60
        
        return {
            'readiness': readiness,
            'score': float(readiness_score),
            'confidence': float(confidence),
            'top_signals': [s['signal'] for s in top_signals[:3]],
            'recommendation': self._get_recommendation(readiness, top_signals)
        }
    
    def _get_recommendation(self, readiness: str, top_signals: List[Dict]) -> str:
        """Get recommendation based on readiness level"""
        if readiness == 'READY_TO_BUY':
            return 'URGENT: Lead is highly qualified. Initiate closing sequence.'
        elif readiness == 'LIKELY_TO_BUY':
            return 'Lead shows strong interest. Prepare proposal and follow up soon.'
        elif readiness == 'CONSIDERING':
            return 'Lead is considering. Provide more information and case studies.'
        else:
            return 'Continue nurturing. Focus on education and value demonstration.'
    
    def format_signals_summary(self, signals_data: Dict[str, any]) -> Dict[str, any]:
        """
        Format signals for display
        
        Args:
            signals_data: Detected signals
        
        Returns:
            Formatted summary
        """
        top_signals = signals_data.get('signals', [])[:5]
        
        formatted = {
            'detected_count': signals_data.get('signal_count', 0),
            'top_signals': [
                {
                    'signal': s['signal'].replace('_', ' ').title(),
                    'strength': f"{s['strength'] * 100:.0f}%",
                    'description': s['description']
                }
                for s in top_signals
            ],
            'average_strength': f"{signals_data.get('average_strength', 0.0) * 100:.0f}%"
        }
        
        return formatted
