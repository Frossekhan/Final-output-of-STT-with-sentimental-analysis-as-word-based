"""
Objection detection for sales conversations
Identifies and classifies customer objections during sales calls
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ObjectionType(Enum):
    """Types of sales objections"""
    PRICE = "price"
    BUDGET = "budget"
    AUTHORITY = "authority"
    NEED = "need"
    TIMING = "timing"
    COMPETITOR = "competitor"
    TRUST = "trust"
    FEATURES = "features"
    SUPPORT = "support"
    IMPLEMENTATION = "implementation"
    RISK = "risk"
    GENERIC = "generic"


class ObjectionSeverity(Enum):
    """Severity levels of objections"""
    CRITICAL = "critical"  # Deal-breaker if not addressed
    HIGH = "high"  # Major concern, needs immediate attention
    MEDIUM = "medium"  # Moderate concern, should be addressed
    LOW = "low"  # Minor concern, can be addressed later


@dataclass
class Objection:
    """Objection detection result"""
    objection_type: ObjectionType
    severity: ObjectionSeverity
    confidence: float
    text: str
    keywords_matched: List[str]
    context: str
    suggested_response: str


class ObjectionDetector:
    """
    Detects and classifies customer objections in sales conversations
    
    Objections are concerns or hesitations that need to be addressed
    to move the sales process forward.
    """
    
    # Objection patterns by type
    OBJECTION_PATTERNS = {
        ObjectionType.PRICE: {
            "severity": ObjectionSeverity.HIGH,
            "keywords": [
                'too expensive', 'too costly', 'overpriced', 'not worth',
                'can\'t afford', 'budget constraints', 'price is high',
                'cheaper alternative', 'lower price', 'discount needed'
            ],
            "phrases": [
                r'(?:it|this|your)\s+(?:is|seems?)\s+(?:too\s+)?(?:expensive|costly|pricey)',
                r'(?:i|we)\s+(?:can\'t|cannot|do\s+not\s+want\s+to)\s+(?:pay|afford)',
                r'(?:the|your)\s+price\s+(?:is|seems?)\s+(?:too\s+)?high',
                r'(?:looking\s+for|need|want)\s+(?:a\s+)?(?:cheaper|lower|better)\s+(?:price|option|alternative)',
                r'(?:can|could)\s+you\s+(?:reduce|lower|bring\s+down)\s+(?:the\s+)?price'
            ],
            "suggested_response": "Acknowledge the concern, emphasize value proposition, and explore flexible pricing options or ROI justification."
        },
        ObjectionType.BUDGET: {
            "severity": ObjectionSeverity.HIGH,
            "keywords": [
                'no budget', 'budget exhausted', 'budget limitations',
                'funds not available', 'financial constraints', 'budget cut',
                'next fiscal year', 'next quarter budget', 'waiting for budget'
            ],
            "phrases": [
                r'(?:we|i)\s+(?:don\'t|do\s+not|have\s+no)\s+(?:have\s+)?budget',
                r'(?:our|the)\s+budget\s+(?:is|has\s+been)\s+(?:exhausted|cut|limited|constraint)',
                r'(?:no|not\s+enough)\s+(?:funds?|money|budget)\s+(?:available|allocated)',
                r'(?:have|need)\s+to\s+(?:wait|postpone)\s+(?:until|for)\s+(?:next\s+)?(?:quarter|year|fiscal)',
                r'(?:budget|funds?)\s+(?:will\s+be|is\s+going\s+to\s+be)\s+(?:available|approved)'
            ],
            "suggested_response": "Understand budget cycle, offer phased implementation or payment plans, and demonstrate long-term ROI."
        },
        ObjectionType.AUTHORITY: {
            "severity": ObjectionSeverity.MEDIUM,
            "keywords": [
                'not my decision', 'need approval', 'check with boss',
                'higher authority', 'decision maker', 'management approval',
                'board approval', 'need to consult', 'not in my hands'
            ],
            "phrases": [
                r'(?:i|we)\s+(?:don\'t|do\s+not|cannot)\s+(?:have\s+)?(?:the\s+)?authority',
                r'(?:need|have)\s+to\s+(?:check|consult|discuss|get\s+approval)',
                r'(?:not|isn\'t)\s+(?:my|our)\s+(?:decision|call|choice)',
                r'(?:i|we)\s+(?:report|answer)\s+to',
                r'(?:need|requires?)\s+(?:higher|senior|executive)\s+(?:approval|sign-off)'
            ],
            "suggested_response": "Identify the true decision maker, offer to present to stakeholders, and provide materials for internal advocacy."
        },
        ObjectionType.NEED: {
            "severity": ObjectionSeverity.CRITICAL,
            "keywords": [
                'don\'t need', 'no need', 'not necessary', 'not required',
                'already have', 'existing solution', 'current system works',
                'not a priority', 'not urgent', 'can manage without'
            ],
            "phrases": [
                r'(?:we|i)\s+(?:don\'t|do\s+not)\s+(?:really\s+)?need',
                r'(?:already|currently)\s+(?:have|using|using)\s+(?:a\s+)?(?:solution|system|tool)',
                r'(?:our|the)\s+(?:current|existing)\s+(?:system|solution|process)\s+(?:works?|is\s+fine)',
                r'(?:not|isn\'t)\s+(?:really\s+)?(?:a\s+)?(?:priority|necessity|urgent)',
                r'(?:we|i)\s+can\s+(?:manage|do|handle)\s+(?:without|fine\s+without)'
            ],
            "suggested_response": "Uncover hidden pain points, demonstrate consequences of inaction, and create urgency through business case."
        },
        ObjectionType.TIMING: {
            "severity": ObjectionSeverity.MEDIUM,
            "keywords": [
                'not right now', 'bad timing', 'wrong time', 'later',
                'next year', 'future', 'postpone', 'delay', 'hold off',
                'not the right time', 'too busy', 'other priorities'
            ],
            "phrases": [
                r'(?:not|isn\'t)\s+(?:the\s+)?(?:right|good)\s+time',
                r'(?:we|i)\s+(?:are|am)\s+(?:too\s+)?busy',
                r'(?:can|could)\s+we\s+(?:postpone|delay|put\s+this\s+on\s+hold)',
                r'(?:let\'s|we\s+should)\s+(?:revisit|discuss|look\s+at)\s+(?:this\s+)?(?:later|next\s+year)',
                r'(?:have|got)\s+(?:other|more)\s+(?:priorities|things|projects)'
            ],
            "suggested_response": "Create urgency by highlighting costs of delay, offer pilot program, or schedule follow-up for appropriate timing."
        },
        ObjectionType.COMPETITOR: {
            "severity": ObjectionSeverity.HIGH,
            "keywords": [
                'using competitor', 'switching from', 'already using',
                'competitor product', 'alternative', 'other vendor',
                'comparing with', 'evaluating options', 'shortlisted'
            ],
            "phrases": [
                r'(?:already|currently)\s+(?:using|with|on)\s+(?:a\s+)?(?:competitor|alternative|other)',
                r'(?:comparing|evaluating|looking\s+at)\s+(?:multiple|other|different)\s+(?:options|solutions?|vendors?)',
                r'(?:have|got)\s+(?:a\s+)?(?:shortlist|list|few)\s+(?:of\s+)?(?:options|alternatives)',
                r'(?:why\s+)?(?:should\s+)?(?:we|i)\s+(?:choose|pick|go\s+with)\s+you\s+(?:over|instead\s+of)',
                r'(?:what\s+)?(?:makes\s+you|your\s+(?:product|service))\s+(?:different|better|unique)'
            ],
            "suggested_response": "Differentiate from competitors, highlight unique value proposition, and provide comparison matrix or case studies."
        },
        ObjectionType.TRUST: {
            "severity": ObjectionSeverity.HIGH,
            "keywords": [
                'not sure about', 'don\'t trust', 'reliable', 'reputation',
                'references', 'track record', 'experience', 'proven',
                'security', 'data privacy', 'compliance', 'certification'
            ],
            "phrases": [
                r'(?:not|isn\'t)\s+(?:sure|convinced|confident)\s+(?:about|with|in)',
                r'(?:don\'t|do\s+not)\s+(?:know|trust|believe)',
                r'(?:what\s+)?(?:about\s+)?(?:your\s+)?(?:reputation|track\s+record|experience)',
                r'(?:need|want|require)\s+(?:references|proof|evidence|guarantee)',
                r'(?:concerned|worried)\s+(?:about|with)\s+(?:security|privacy|compliance|data)'
            ],
            "suggested_response": "Build credibility with testimonials, case studies, security certifications, and trial period with money-back guarantee."
        },
        ObjectionType.FEATURES: {
            "severity": ObjectionSeverity.MEDIUM,
            "keywords": [
                'missing feature', 'doesn\'t have', 'lack of', 'not available',
                'doesn\'t support', 'can\'t do', 'unable to', 'limitation',
                'doesn\'t work', 'not compatible', 'integration issues'
            ],
            "phrases": [
                r'(?:it|this|your)\s+(?:doesn\'t|does\s+not|doesn\'t)\s+(?:have|support|offer|provide)',
                r'(?:missing|lacks?|no)\s+(?:feature|functionality|capability)',
                r'(?:can\'t|cannot|unable\s+to)\s+(?:do|handle|support|integrate)',
                r'(?:not|isn\'t)\s+(?:compatible|supported|available|working)',
                r'(?:have|got)\s+(?:an?\s+)?(?:issue|problem|limitation)\s+(?:with|in)'
            ],
            "suggested_response": "Address feature gaps, provide roadmap, offer workarounds, or demonstrate how existing features meet the need."
        },
        ObjectionType.SUPPORT: {
            "severity": ObjectionSeverity.MEDIUM,
            "keywords": [
                'support', 'helpdesk', 'customer service', 'response time',
                'uptime', 'sla', 'service level', 'maintenance', 'updates',
                'training', 'documentation', 'onboarding'
            ],
            "phrases": [
                r'(?:what|how)\s+(?:about|is|are)\s+(?:the\s+)?(?:support|help|assistance)',
                r'(?:what|how)\s+(?:is|are)\s+(?:the\s+)?(?:sla|uptime|response\s+time)',
                r'(?:need|require|want)\s+(?:training|documentation|onboarding|support)',
                r'(?:how|what)\s+(?:do\s+you|you\s+do)\s+(?:for|about)\s+(?:maintenance|updates|issues?)',
                r'(?:concerned|worried)\s+(?:about|with)\s+(?:support|service|assistance)'
            ],
            "suggested_response": "Detail support offerings, SLAs, response times, training programs, and dedicated account management."
        },
        ObjectionType.IMPLEMENTATION: {
            "severity": ObjectionSeverity.MEDIUM,
            "keywords": [
                'implementation', 'deployment', 'setup', 'installation',
                'migration', 'data transfer', 'complex', 'difficult',
                'time-consuming', 'disruption', 'downtime', 'training'
            ],
            "phrases": [
                r'(?:how|what)\s+(?:long|much\s+time)\s+(?:does|will|is)\s+(?:implementation|deployment|setup)',
                r'(?:is|will\s+it\s+be)\s+(?:complex|difficult|time-consuming|disruptive)',
                r'(?:concerned|worried)\s+(?:about|with)\s+(?:migration|data\s+transfer|downtime)',
                r'(?:how|what)\s+(?:do\s+you|you\s+do)\s+(?:for|about)\s+(?:training|onboarding|support)',
                r'(?:need|require|want)\s+(?:help|assistance|support)\s+(?:with|for)\s+(?:implementation|setup)'
            ],
            "suggested_response": "Provide implementation plan, timeline, dedicated support team, and phased rollout approach to minimize disruption."
        },
        ObjectionType.RISK: {
            "severity": ObjectionSeverity.HIGH,
            "keywords": [
                'risk', 'risky', 'uncertainty', 'uncertain', 'worry',
                'concern', 'afraid', 'hesitant', 'doubt', 'skeptical',
                'not convinced', 'not sure', 'what if', 'failure'
            ],
            "phrases": [
                r'(?:i|we)\s+(?:am|are)\s+(?:worried|concerned|afraid|hesitant)',
                r'(?:what\s+)?(?:if|what\s+if)\s+(?:it|this|something)\s+(?:goes?\s+)?wrong',
                r'(?:too\s+)?(?:risky|uncertain|unproven|untested)',
                r'(?:not|isn\'t)\s+(?:convinced|sure|confident|sold)',
                r'(?:have|got)\s+(?:doubts?|reservations?|concerns?)'
            ],
            "suggested_response": "Address concerns with data, provide risk mitigation strategies, offer trial period, and share success stories."
        },
        ObjectionType.GENERIC: {
            "severity": ObjectionSeverity.LOW,
            "keywords": [
                'but', 'however', 'although', 'though', 'still',
                'yet', 'concern', 'worry', 'issue', 'problem'
            ],
            "phrases": [
                r'(?:but|however|although|though)\s+(?:i|we)',
                r'(?:i|we)\s+(?:am|are)\s+(?:not\s+)?(?:sure|convinced|confident)',
                r'(?:my|our)\s+(?:concern|worry|issue|problem)\s+(?:is|are)',
                r'(?:i|we)\s+(?:have|had)\s+(?:a\s+)?(?:bad|poor)\s+(?:experience|issue)',
                r'(?:not\s+)?(?:convinced|sure|sold)\s+(?:yet|still|completely)'
            ],
            "suggested_response": "Explore the specific concern, ask clarifying questions, and address the root issue empathetically."
        }
    }
    
    def __init__(self):
        self.objection_history: List[Objection] = []
        
    def detect_objections(self, text: str) -> List[Objection]:
        """
        Detect all objections in text
        
        Args:
            text: Input text
            
        Returns:
            List of Objection detected
        """
        text_lower = text.lower()
        objections = []
        
        for objection_type, patterns in self.OBJECTION_PATTERNS.items():
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
                normalized_score = min(1.0, score / max_possible)
                confidence = min(1.0, score / max_possible)
                
                objection = Objection(
                    objection_type=objection_type,
                    severity=patterns['severity'],
                    confidence=confidence,
                    text=text,
                    keywords_matched=matched_keywords,
                    context=text,
                    suggested_response=patterns['suggested_response']
                )
                
                objections.append(objection)
                self.objection_history.append(objection)
        
        # Sort by severity and confidence
        objections.sort(
            key=lambda x: (x.severity.value, x.confidence),
            reverse=True
        )
        
        return objections
    
    def get_critical_objections(self) -> List[Objection]:
        """Get critical objections that need immediate attention"""
        return [
            o for o in self.objection_history
            if o.severity == ObjectionSeverity.CRITICAL
        ]
    
    def get_objections_by_type(self, objection_type: ObjectionType) -> List[Objection]:
        """Get objections of a specific type"""
        return [
            o for o in self.objection_history
            if o.objection_type == objection_type
        ]
    
    def get_objection_summary(self) -> Dict:
        """Get summary of objections"""
        if not self.objection_history:
            return {
                "total_objections": 0,
                "critical_objections": 0,
                "high_objections": 0,
                "medium_objections": 0,
                "low_objections": 0,
                "by_type": {},
                "top_objections": [],
                "recommendations": []
            }
        
        # Count by severity
        critical = sum(1 for o in self.objection_history if o.severity == ObjectionSeverity.CRITICAL)
        high = sum(1 for o in self.objection_history if o.severity == ObjectionSeverity.HIGH)
        medium = sum(1 for o in self.objection_history if o.severity == ObjectionSeverity.MEDIUM)
        low = sum(1 for o in self.objection_history if o.severity == ObjectionSeverity.LOW)
        
        # Count by type
        by_type = {}
        for objection in self.objection_history:
            type_name = objection.objection_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
        
        # Get top objections (by severity and confidence)
        top_objections = sorted(
            self.objection_history,
            key=lambda x: (x.severity.value, x.confidence),
            reverse=True
        )[:5]
        
        # Get recommendations
        recommendations = list(set(
            o.suggested_response for o in self.objection_history
            if o.severity in [ObjectionSeverity.CRITICAL, ObjectionSeverity.HIGH]
        ))
        
        return {
            "total_objections": len(self.objection_history),
            "critical_objections": critical,
            "high_objections": high,
            "medium_objections": medium,
            "low_objections": low,
            "by_type": by_type,
            "top_objections": [
                {
                    "type": o.objection_type.value,
                    "severity": o.severity.value,
                    "confidence": round(o.confidence, 2),
                    "text": o.text[:100],
                    "suggested_response": o.suggested_response
                }
                for o in top_objections
            ],
            "recommendations": recommendations
        }
    
    def get_objection_handling_priority(self) -> List[Dict]:
        """
        Get prioritized list of objections to handle
        
        Returns:
            List of objections sorted by priority
        """
        if not self.objection_history:
            return []
        
        # Remove duplicates (same type)
        seen_types = set()
        unique_objections = []
        
        for objection in sorted(
            self.objection_history,
            key=lambda x: (x.severity.value, x.confidence),
            reverse=True
        ):
            if objection.objection_type not in seen_types:
                seen_types.add(objection.objection_type)
                unique_objections.append(objection)
        
        # Create priority list
        priority_list = []
        for i, objection in enumerate(unique_objections[:10], 1):
            priority_list.append({
                "priority": i,
                "type": objection.objection_type.value,
                "severity": objection.severity.value,
                "confidence": round(objection.confidence, 2),
                "suggested_response": objection.suggested_response,
                "action_required": "IMMEDIATE" if objection.severity == ObjectionSeverity.CRITICAL else "HIGH" if objection.severity == ObjectionSeverity.HIGH else "MEDIUM"
            })
        
        return priority_list
    
    def detect_objection_patterns(self) -> Dict:
        """
        Detect patterns in objections over time
        
        Returns:
            Pattern analysis
        """
        if len(self.objection_history) < 2:
            return {"patterns": [], "trends": {}}
        
        # Group objections by type
        objection_types = {}
        for objection in self.objection_history:
            type_name = objection.objection_type.value
            if type_name not in objection_types:
                objection_types[type_name] = []
            objection_types[type_name].append(objection)
        
        # Analyze patterns
        patterns = []
        for objection_type, objections in objection_types.items():
            if len(objections) >= 2:
                # Check if recurring
                patterns.append({
                    "type": objection_type,
                    "frequency": len(objections),
                    "pattern": "recurring" if len(objections) >= 3 else "occasional",
                    "avg_confidence": round(
                        sum(o.confidence for o in objections) / len(objections),
                        2
                    ),
                    "severity": objections[0].severity.value
                })
        
        # Sort by frequency
        patterns.sort(key=lambda x: x['frequency'], reverse=True)
        
        return {
            "patterns": patterns,
            "most_common": patterns[0]['type'] if patterns else None,
            "total_unique_types": len(objection_types)
        }
    
    def get_objection_resolution_status(self) -> Dict:
        """
        Get status of objection resolution
        
        Note: This is a placeholder for integration with CRM or
        conversation tracking to determine if objections were resolved.
        """
        return {
            "total_objections": len(self.objection_history),
            "resolved": 0,  # Placeholder - would need CRM integration
            "unresolved": len(self.objection_history),
            "resolution_rate": 0.0,
            "pending_actions": len(self.objection_history)
        }
    
    def reset(self):
        """Reset objection history"""
        self.objection_history = []


class ObjectionAnalyzer:
    """Advanced objection analysis and handling strategies"""
    
    def __init__(self):
        self.detector = ObjectionDetector()
        
    def analyze_objections(self, texts: List[str]) -> Dict:
        """
        Analyze objections across a conversation
        
        Args:
            texts: List of conversation texts
            
        Returns:
            Comprehensive objection analysis
        """
        all_objections = []
        
        for text in texts:
            objections = self.detector.detect_objections(text)
            all_objections.extend(objections)
        
        # Get summary
        summary = self.detector.get_objection_summary()
        
        # Get priority list
        priority_list = self.detector.get_objection_handling_priority()
        
        # Get patterns
        patterns = self.detector.detect_objection_patterns()
        
        # Generate action plan
        action_plan = self._generate_action_plan(summary, priority_list)
        
        return {
            "summary": summary,
            "priority_list": priority_list,
            "patterns": patterns,
            "action_plan": action_plan,
            "total_objections_detected": len(all_objections),
            "objection_density": round(len(all_objections) / max(len(texts), 1), 2)
        }
    
    def _generate_action_plan(self, summary: Dict, priority_list: List[Dict]) -> List[Dict]:
        """Generate action plan for handling objections"""
        action_plan = []
        
        for item in priority_list[:5]:
            action_plan.append({
                "priority": item['priority'],
                "objection_type": item['type'],
                "severity": item['severity'],
                "action": item['suggested_response'],
                "action_required": item['action_required'],
                "status": "pending"
            })
        
        return action_plan
    
    def get_handling_strategy(self, objection_type: ObjectionType) -> Dict:
        """
        Get handling strategy for specific objection type
        
        Args:
            objection_type: Type of objection
            
        Returns:
            Handling strategy
        """
        strategies = {
            ObjectionType.PRICE: {
                "strategy": "Value-Based Response",
                "steps": [
                    "Acknowledge the price concern",
                    "Reframe to value and ROI",
                    "Break down cost per benefit",
                    "Offer flexible payment options",
                    "Provide comparison with alternatives"
                ],
                "key_points": [
                    "Total cost of ownership",
                    "ROI calculation",
                    "Competitive pricing",
                    "Value proposition"
                ]
            },
            ObjectionType.BUDGET: {
                "strategy": "Budget Alignment",
                "steps": [
                    "Understand budget cycle",
                    "Offer phased implementation",
                    "Provide ROI justification",
                    "Explore payment plans",
                    "Schedule for next budget cycle"
                ],
                "key_points": [
                    "Budget timing",
                    "Phased approach",
                    "Cost savings",
                    "Long-term value"
                ]
            },
            ObjectionType.NEED: {
                "strategy": "Needs Discovery",
                "steps": [
                    "Uncover pain points",
                    "Quantify the problem",
                    "Show consequences of inaction",
                    "Demonstrate solution fit",
                    "Create urgency"
                ],
                "key_points": [
                    "Pain point identification",
                    "Business impact",
                    "Cost of delay",
                    "Solution benefits"
                ]
            },
            ObjectionType.TIMING: {
                "strategy": "Urgency Creation",
                "steps": [
                    "Understand timing concerns",
                    "Highlight costs of delay",
                    "Offer pilot program",
                    "Provide quick wins",
                    "Schedule follow-up"
                ],
                "key_points": [
                    "Time-sensitive benefits",
                    "Opportunity cost",
                    "Quick implementation",
                    "Pilot program"
                ]
            },
            ObjectionType.COMPETITOR: {
                "strategy": "Differentiation",
                "steps": [
                    "Acknowledge competition",
                    "Highlight unique value",
                    "Provide comparison matrix",
                    "Share success stories",
                    "Offer trial/POC"
                ],
                "key_points": [
                    "Unique features",
                    "Better value",
                    "Success stories",
                    "Trial offer"
                ]
            },
            ObjectionType.TRUST: {
                "strategy": "Credibility Building",
                "steps": [
                    "Address concerns directly",
                    "Share testimonials",
                    "Provide references",
                    "Offer trial period",
                    "Show certifications"
                ],
                "key_points": [
                    "Social proof",
                    "Security credentials",
                    "Money-back guarantee",
                    "Trial period"
                ]
            }
        }
        
        return strategies.get(objection_type, {
            "strategy": "General Handling",
            "steps": [
                "Listen actively",
                "Empathize with concern",
                "Ask clarifying questions",
                "Address the root issue",
                "Confirm resolution"
            ],
            "key_points": [
                "Active listening",
                "Empathy",
                "Clear communication",
                "Solution-focused"
            ]
        })