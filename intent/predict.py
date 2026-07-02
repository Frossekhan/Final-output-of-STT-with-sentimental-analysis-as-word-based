"""
Intent detection for sales conversations
Classifies customer intent from conversation text
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Sales conversation intent types"""
    PRICING = "pricing"
    DEMO = "demo"
    PURCHASE = "purchase"
    NEGOTIATION = "negotiation"
    SUPPORT = "support"
    CANCELLATION = "cancellation"
    RENEWAL = "renewal"
    INFORMATION = "information"
    OBJECTION = "objection"
    COMPETITOR = "competitor"


@dataclass
class IntentResult:
    """Intent detection result"""
    intent: IntentType
    confidence: float
    all_scores: Dict[str, float]
    keywords_matched: List[str]
    context: str


class IntentDetector:
    """
    Intent detection using rule-based keyword matching
    Can be extended with ML models for better accuracy
    """
    
    # Intent keywords and patterns
    INTENT_PATTERNS = {
        IntentType.PRICING: {
            'keywords': [
                'price', 'cost', 'pricing', 'how much', 'quote', 'quotation',
                'rate', 'fee', 'charge', 'payment', 'budget', 'afford',
                'expensive', 'cheap', 'discount', 'offer', 'deal'
            ],
            'phrases': [
                r'what\s+(?:is|are)\s+(?:the\s+)?(?:price|cost|pricing)',
                r'how\s+much\s+(?:does\s+it|will\s+it|is\s+it)',
                r'can\s+you\s+(?:send\s+)?(?:me\s+)?(?:a\s+)?(?:quote|quotation)',
                r'what\s+(?:is|are)\s+your\s+(?:rates?|fees?)',
                r'(?:looking\s+for|need)\s+(?:a\s+)?(?:better\s+)?(?:price|deal|offer)'
            ]
        },
        IntentType.DEMO: {
            'keywords': [
                'demo', 'demonstration', 'show', 'presentation', 'trial',
                'try', 'test', 'preview', 'see', 'watch', 'experience',
                'walkthrough', 'tour', 'showcase'
            ],
            'phrases': [
                r'can\s+(?:i|we)\s+(?:see|get|have)\s+(?:a\s+)?demo',
                r'show\s+(?:me|us)\s+(?:how\s+)?it\s+(?:works?|functions?)',
                r'(?:can\s+you|please)\s+(?:give|show)\s+(?:me|us)\s+(?:a\s+)?(?:tour|walkthrough)',
                r'(?:i|we)\s+(?:want|would\s+like)\s+(?:to\s+)?(?:see|try|test)',
                r'is\s+(?:there\s+)?(?:a\s+)?(?:free\s+)?trial'
            ]
        },
        IntentType.PURCHASE: {
            'keywords': [
                'buy', 'purchase', 'order', 'checkout', 'cart', 'payment',
                'subscribe', 'sign up', 'register', 'enroll', 'proceed',
                'confirm', 'finalize', 'complete', 'accept', 'agree'
            ],
            'phrases': [
                r'(?:i|we)\s+(?:want\s+to|would\s+like\s+to|will)\s+(?:buy|purchase)',
                r'let\s+(?:me|us)\s+(?:proceed|move\s+forward|go\s+ahead)',
                r'(?:i|we)\s+(?:am|are)\s+(?:ready|willing)\s+to\s+(?:buy|purchase|sign)',
                r'how\s+(?:do\s+)?(?:i|we)\s+(?:buy|purchase|order|subscribe)',
                r'(?:ready|let\s+us)\s+to\s+(?:move\s+forward|proceed|close)'
            ]
        },
        IntentType.NEGOTIATION: {
            'keywords': [
                'negotiate', 'negotiation', 'bargain', 'compromise', 'adjust',
                'modify', 'customize', 'tailor', 'flexible', 'deal', 'terms',
                'conditions', 'contract', 'agreement', 'counter'
            ],
            'phrases': [
                r'(?:can|could|would)\s+you\s+(?:negotiate|adjust|modify|flexible)',
                r'(?:i|we)\s+(?:want|need)\s+(?:better|different|custom)\s+(?:terms?|pricing|deal)',
                r'(?:is|are)\s+(?:there\s+)?(?:any\s+)?(?:room|flexibility|option)',
                r'can\s+we\s+(?:work\s+out|find|discuss)\s+(?:a\s+)?(?:deal|compromise)',
                r'(?:i|we)\s+(?:have|want)\s+(?:a\s+)?(?:counter|counteroffer)'
            ]
        },
        IntentType.SUPPORT: {
            'keywords': [
                'help', 'support', 'assist', 'issue', 'problem', 'error',
                'bug', 'fix', 'broken', 'not working', 'troubleshoot',
                'resolve', 'solution', 'answer', 'question'
            ],
            'phrases': [
                r'(?:i|we)\s+(?:need|want|require)\s+(?:help|support|assistance)',
                r'(?:there\s+is|having|facing)\s+(?:an?\s+)?(?:issue|problem|error)',
                r'(?:can|could)\s+you\s+(?:help|assist|support)',
                r'(?:something|it|this)\s+(?:is|seems?)\s+(?:not\s+)?working',
                r'(?:how\s+to|how\s+do\s+i|what\s+is\s+the\s+way\s+to)'
            ]
        },
        IntentType.CANCELLATION: {
            'keywords': [
                'cancel', 'cancellation', 'refund', 'money back', 'terminate',
                'end', 'stop', 'discontinue', 'close', 'unsubscribe',
                'dissatisfied', 'unhappy', 'disappointed'
            ],
            'phrases': [
                r'(?:i|we)\s+(?:want|would\s+like|need)\s+to\s+(?:cancel|terminate|end)',
                r'(?:can|could)\s+you\s+(?:cancel|refund|terminate)',
                r'(?:not\s+)?(?:satisfied|happy|happy)\s+with',
                r'(?:want|need)\s+(?:a\s+)?(?:refund|money\s+back)',
                r'(?:i|we)\s+(?:am|are)\s+(?:leaving|switching|moving)'
            ]
        },
        IntentType.RENEWAL: {
            'keywords': [
                'renew', 'renewal', 'extend', 'continue', 'subscription',
                'expiring', 'expire', 'renewal', 'upcoming', r'next\s+cycle'
            ],
            'phrases': [
                r'(?:i|we)\s+(?:want|would\s+like|need)\s+to\s+(?:renew|extend|continue)',
                r'(?:our|my)\s+(?:subscription|contract|plan)\s+(?:is|will\s+be)\s+(?:expiring|ending)',
                r'(?:when|how)\s+(?:is|do\s+we)\s+(?:renew|extend|continue)',
                r'(?:looking\s+to|want\s+to)\s+(?:renew|extend|renewal)',
                r'(?:upcoming|next)\s+(?:renewal|cycle|billing)'
            ]
        },
        IntentType.INFORMATION: {
            'keywords': [
                'information', 'details', 'specs', 'specifications', 'features',
                'benefits', 'advantages', 'overview', 'summary', 'learn',
                'understand', 'know', 'tell', 'explain', 'describe'
            ],
            'phrases': [
                r'(?:can|could|please)\s+(?:you\s+)?(?:tell|provide|share|give)',
                r'(?:i|we)\s+(?:want|would\s+like|need)\s+(?:to\s+)?(?:know|learn|understand)',
                r'what\s+(?:are|is|does|do|can|will)',
                r'(?:how\s+does|how\s+do|how\s+is|how\s+are)',
                r'(?:tell|explain|describe)\s+(?:me|us)\s+(?:more|about|how)'
            ]
        },
        IntentType.OBJECTION: {
            'keywords': [
                'but', 'however', 'concern', 'worry', 'issue', 'problem',
                'however', 'although', 'though', 'still', 'yet', 'hesitate',
                'doubt', 'skeptical', 'unsure', 'confused'
            ],
            'phrases': [
                r'(?:but|however|although)\s+(?:i|we)',
                r'(?:i|we)\s+(?:am|are)\s+(?:not\s+)?(?:sure|convinced|convinced)',
                r'(?:my|our)\s+(?:concern|worry|issue|problem)\s+(?:is|are)',
                r'(?:i|we)\s+(?:have|had)\s+(?:a\s+)?(?:bad|poor)\s+(?:experience|issue)',
                r'(?:not\s+)?(?:convinced|sure|sold)\s+(?:yet|still|completely)'
            ]
        },
        IntentType.COMPETITOR: {
            'keywords': [
                'competitor', 'competition', 'alternative', 'other', 'vendor',
                'provider', 'option', 'comparison', 'compare', 'versus', 'vs',
                'better', 'worse', 'difference', 'similar'
            ],
            'phrases': [
                r'(?:how\s+)?(?:are\s+you|do\s+you)\s+(?:compare|differ|stack\s+up)',
                r'(?:what\s+)?(?:makes\s+you|your\s+(?:product|service|solution))',
                r'(?:i|we)\s+(?:are\s+)?(?:also\s+)?(?:looking\s+at|considering|evaluating)',
                r'(?:using|tried|tried)\s+(?:a\s+)?(?:different|other|competitor)',
                r'(?:why\s+)?(?:should\s+)?(?:i|we)\s+(?:choose|pick|go\s+with)\s+you'
            ]
        }
    }
    
    def __init__(self):
        self.intent_history: List[IntentResult] = []
        
    def detect_intent(self, text: str, context: str = "") -> IntentResult:
        """
        Detect intent from text
        
        Args:
            text: Input text
            context: Additional context (previous conversation)
            
        Returns:
            IntentResult with detected intent and confidence
        """
        text_lower = text.lower()
        
        # Calculate scores for each intent
        intent_scores = {}
        keywords_matched = {}
        
        for intent_type, patterns in self.INTENT_PATTERNS.items():
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
            
            # Normalize score
            max_possible = len(patterns['keywords']) + len(patterns['phrases']) * 2
            if max_possible > 0:
                normalized_score = min(1.0, score / max_possible * 3)
            else:
                normalized_score = 0.0
            
            intent_scores[intent_type.value] = normalized_score
            keywords_matched[intent_type.value] = matched_keywords
        
        # Get top intent
        if intent_scores:
            top_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[top_intent]
        else:
            top_intent = IntentType.INFORMATION.value
            confidence = 0.0
        
        result = IntentResult(
            intent=IntentType(top_intent),
            confidence=confidence,
            all_scores=intent_scores,
            keywords_matched=keywords_matched.get(top_intent, []),
            context=context
        )
        
        # Add to history
        self.intent_history.append(result)
        
        return result
    
    def detect_intent_sequence(self, texts: List[str]) -> List[IntentResult]:
        """
        Detect intent from sequence of texts
        
        Args:
            texts: List of text segments
            
        Returns:
            List of IntentResult for each text
        """
        results = []
        context = ""
        
        for text in texts:
            result = self.detect_intent(text, context)
            results.append(result)
            context += " " + text
        
        return results
    
    def get_intent_transitions(self) -> List[Tuple[str, str]]:
        """Get intent transitions over time"""
        if len(self.intent_history) < 2:
            return []
        
        transitions = []
        for i in range(1, len(self.intent_history)):
            prev_intent = self.intent_history[i-1].intent.value
            curr_intent = self.intent_history[i].intent.value
            if prev_intent != curr_intent:
                transitions.append((prev_intent, curr_intent))
        
        return transitions
    
    def get_dominant_intent(self, window_size: int = 5) -> Tuple[str, float]:
        """Get dominant intent from recent history"""
        if not self.intent_history:
            return IntentType.INFORMATION.value, 0.0
        
        # Get recent history
        recent = self.intent_history[-window_size:]
        
        # Count intents
        intent_counts = {}
        for result in recent:
            intent = result.intent.value
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Get most common
        dominant = max(intent_counts, key=intent_counts.get)
        frequency = intent_counts[dominant] / len(recent)
        
        return dominant, frequency
    
    def get_intent_progression(self) -> Dict[str, List[float]]:
        """Get intent progression over time"""
        progression = {}
        
        for result in self.intent_history:
            intent = result.intent.value
            if intent not in progression:
                progression[intent] = []
            progression[intent].append(result.confidence)
        
        return progression
    
    def reset(self):
        """Reset intent history"""
        self.intent_history = []


class IntentClassifier:
    """
    ML-based intent classifier (placeholder for future implementation)
    Can be extended with transformers or other ML models
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        
    async def load_model(self):
        """Load ML model for intent classification"""
        # Placeholder for loading a trained model
        # Can use transformers library with a model like:
        # - BERT fine-tuned on sales intent data
        # - DistilBERT for faster inference
        # - Custom trained model
        pass
    
    async def classify(self, text: str) -> IntentResult:
        """Classify intent using ML model"""
        # Placeholder for ML-based classification
        # This would use the loaded model to predict intent
        pass
    
    async def train(self, training_data: List[Tuple[str, IntentType]]):
        """Train the intent classifier"""
        # Placeholder for training logic
        pass