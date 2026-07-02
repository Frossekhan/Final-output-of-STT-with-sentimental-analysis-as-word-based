"""
Objection Detection Module
Identifies customer objections and concerns
"""

import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ObjectionDetector:
    """
    Detects customer objections from text
    12 objection types with severity levels
    """
    
    # Objection patterns with severity
    OBJECTIONS = {
        'price': {
            'severity': 'critical',
            'patterns': [
                r'\b(?:too\s+)?(?:expensive|costly|dear|pricey)\b',
                r'\b(?:price|cost)\s+(?:is\s+)?too\s+(?:high|much)\b',
                r'\b(?:reduce|lower|discount)\s+(?:the\s+)?(?:price|cost)\b',
                r'\b(?:can\'?t\s+afford|budget\s+is\s+low)\b',
            ],
            'description': 'Customer concerned about price'
        },
        'budget': {
            'severity': 'high',
            'patterns': [
                r'\b(?:no\s+)?budget(?:\s+(?:available|approved|allocated))?\b',
                r'\b(?:budget\s+)?(?:constraint|limited|shortage)\b',
                r'\b(?:can\'?t\s+afford|not\s+in\s+budget)\b',
                r'\b(?:financial\s+constraints?|tight\s+budget)\b',
            ],
            'description': 'Customer has budget constraints'
        },
        'authority': {
            'severity': 'high',
            'patterns': [
                r'\b(?:need\s+(?:to\s+)?(?:check\s+with|get\s+approval\s+from))\b',
                r'\b(?:can\'?t\s+decide|not\s+my\s+call|need\s+approval)\b',
                r'\b(?:have\s+to\s+discuss\s+with|need\s+to\s+consult)\b',
                r'\b(?:decision\s+maker|boss|team|committee)\s+(?:needs\s+to|will\s+decide)\b',
            ],
            'description': 'Customer lacks decision-making authority'
        },
        'need': {
            'severity': 'medium',
            'patterns': [
                r'\b(?:don\'?t\s+)?(?:need|require|necessity)\s+(?:this|it)\b',
                r'\b(?:not\s+(?:needed|necessary|applicable))\b',
                r'\b(?:don\'?t\s+see\s+the|don\'?t\s+understand\s+the)\s+(?:need|value|benefit)\b',
                r'\b(?:already\s+(?:have|using|developed))\b',
            ],
            'description': 'Customer questions need for solution'
        },
        'timing': {
            'severity': 'medium',
            'patterns': [
                r'\b(?:not\s+now|timing\s+not\s+right|too\s+soon)\b',
                r'\b(?:later|next\s+(?:year|quarter|month))\b',
                r'\b(?:postpone|defer|wait)\b',
                r'\b(?:currently\s+evaluating|exploring\s+options)\b',
            ],
            'description': 'Customer wants to delay decision'
        },
        'competitor': {
            'severity': 'high',
            'patterns': [
                r'\b(?:considering|looking\s+at|evaluating|comparing)\s+(?:other|alternatives)\b',
                r'\b(?:competitor\'?s|competitor|alternative)\s+(?:solution|product)\b',
                r'\b(?:what\s+(?:makes|sets)\s+you\s+apart|vs\.|versus)\b',
                r'\b(?:salesforce|hubspot|microsoft|oracle|sap)\b',
            ],
            'description': 'Customer considering competitors'
        },
        'trust': {
            'severity': 'medium',
            'patterns': [
                r'\b(?:don\'?t\s+)?(?:trust|confident)\b',
                r'\b(?:unknown|unproven|risky|uncertain)\b',
                r'\b(?:what\s+(?:is|guarantees)|reliability|stability)\b',
                r'\b(?:established|proven|track\s+record)\b',
            ],
            'description': 'Customer trust or credibility concern'
        },
        'features': {
            'severity': 'medium',
            'patterns': [
                r'\b(?:missing|doesn\'?t\s+have|lacks?|don\'?t\s+support)\s+(?:feature|capability)\b',
                r'\b(?:can\'?t\s+do|doesn\'?t\s+support|won\'?t\s+work\s+for)\b',
                r'\b(?:limitation|limitation|shortcoming)\b',
                r'\b(?:what\s+about|how\s+do\s+you)\s+(?:handle|support)\b',
            ],
            'description': 'Customer concerned about missing features'
        },
        'integration': {
            'severity': 'medium',
            'patterns': [
                r'\b(?:integrate|integration|connect|sync)\s+with\b',
                r'\b(?:won\'?t\s+work|compatibility|incompatible)\b',
                r'\b(?:existing\s+(?:system|tool|platform))\b',
                r'\b(?:api|third-party|data\s+sync)\b',
            ],
            'description': 'Customer concerned about integration'
        },
        'security': {
            'severity': 'high',
            'patterns': [
                r'\b(?:security|privacy|compliance|data\s+protection)\s+(?:concern|issue)\b',
                r'\b(?:secure|encrypted|compliant|gdpr|hipaa|soc\s+2)\b',
                r'\b(?:worried\s+about|concerned\s+with)\s+(?:security|privacy)\b',
                r'\b(?:data|information)\s+(?:security|privacy|protection)\b',
            ],
            'description': 'Customer has security/compliance concerns'
        },
        'support': {
            'severity': 'low',
            'patterns': [
                r'\b(?:support|customer\s+service|help)\s+(?:concern|issue|worried)\b',
                r'\b(?:what\'?s\s+the|how\'?s\s+the)\s+(?:support|customer\s+service)\b',
                r'\b(?:24/7|response\s+time|availability)\b',
                r'\b(?:training|documentation|help)\b',
            ],
            'description': 'Customer concerned about support quality'
        },
        'implementation': {
            'severity': 'medium',
            'patterns': [
                r'\b(?:implementation|rollout|deployment)\s+(?:complex|difficult|challenging)\b',
                r'\b(?:too\s+)?complex(?:\s+to\s+implement)?\b',
                r'\b(?:resource|effort|time)\s+(?:required|needed)\b',
                r'\b(?:learning\s+curve|difficult\s+to\s+set\s+up)\b',
            ],
            'description': 'Customer concerned about implementation complexity'
        }
    }
    
    def __init__(self):
        """Initialize objection detector"""
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List]:
        """Compile regex patterns"""
        compiled = {}
        for objection, info in self.OBJECTIONS.items():
            compiled[objection] = [re.compile(p, re.IGNORECASE) for p in info['patterns']]
        return compiled
    
    def detect_objections(self, text: str) -> Dict[str, any]:
        """
        Detect objections from text
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with detected objections
        """
        text_lower = text.lower()
        
        detected_objections = []
        
        # Check each objection type
        for objection_name, patterns in self.compiled_patterns.items():
            objection_info = self.OBJECTIONS[objection_name]
            severity = objection_info['severity']
            
            # Check if any pattern matches
            for pattern in patterns:
                if pattern.search(text_lower):
                    detected_objections.append({
                        'objection': objection_name,
                        'severity': severity,
                        'description': objection_info['description'],
                        'confidence': 0.80
                    })
                    break  # Count each objection once
        
        # Sort by severity (critical > high > medium > low)
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        detected_objections.sort(key=lambda x: (severity_order.get(x['severity'], 4), -x['confidence']))
        
        return {
            'objections': detected_objections,
            'objection_count': len(detected_objections),
            'has_critical': any(o['severity'] == 'critical' for o in detected_objections),
            'has_high': any(o['severity'] == 'high' for o in detected_objections),
            'detected': len(detected_objections) > 0
        }
    
    def get_objection_priority(self, objections_data: Dict[str, any]) -> Dict[str, any]:
        """
        Determine priority for addressing objections
        
        Args:
            objections_data: Result from detect_objections
        
        Returns:
            Priority analysis for objections
        """
        objections = objections_data.get('objections', [])
        
        if not objections:
            return {
                'priority_level': 'LOW',
                'recommendation': 'No objections detected. Focus on closing.',
                'immediate_action': None
            }
        
        # Get most critical objection
        most_critical = objections[0]
        
        priority_recommendations = {
            'critical': {
                'priority_level': 'CRITICAL',
                'recommendation': f'Address {most_critical["objection"].replace("_", " ")} immediately before proceeding.',
                'immediate_action': f'Handle {most_critical["objection"]} objection first'
            },
            'high': {
                'priority_level': 'HIGH',
                'recommendation': f'Resolve {most_critical["objection"].replace("_", " ")} before moving to contract.',
                'immediate_action': f'Provide solution to {most_critical["objection"]} concern'
            },
            'medium': {
                'priority_level': 'MEDIUM',
                'recommendation': f'Address {most_critical["objection"].replace("_", " ")} during follow-up.',
                'immediate_action': f'Plan follow-up to address {most_critical["objection"]}'
            },
            'low': {
                'priority_level': 'LOW',
                'recommendation': f'Minor objection detected. Continue with proposal.',
                'immediate_action': f'Briefly address {most_critical["objection"]} if asked'
            }
        }
        
        return {
            **priority_recommendations.get(most_critical['severity'], {}),
            'primary_objection': most_critical['objection'],
            'objections_count': len(objections),
            'all_objections': [o['objection'] for o in objections[:3]]
        }
    
    def format_objections_summary(self, objections_data: Dict[str, any]) -> Dict[str, any]:
        """
        Format objections for display
        
        Args:
            objections_data: Detected objections
        
        Returns:
            Formatted summary
        """
        objections = objections_data.get('objections', [])
        
        formatted = {
            'count': objections_data.get('objection_count', 0),
            'objections': [
                {
                    'type': o['objection'].replace('_', ' ').title(),
                    'severity': o['severity'].upper(),
                    'description': o['description']
                }
                for o in objections[:5]
            ]
        }
        
        return formatted
    
    def get_handling_strategy(self, objection_type: str) -> Dict[str, str]:
        """
        Get handling strategy for specific objection
        
        Args:
            objection_type: Type of objection
        
        Returns:
            Handling strategy
        """
        strategies = {
            'price': 'Emphasize value and ROI. Discuss payment options and custom pricing.',
            'budget': 'Explore phased implementation. Discuss budget availability timeline.',
            'authority': 'Request meeting with decision maker. Provide case studies for justification.',
            'need': 'Reconnect with initial pain points. Present specific use cases.',
            'timing': 'Create urgency. Discuss future costs of delay.',
            'competitor': 'Differentiate features and support. Request direct comparison opportunity.',
            'trust': 'Share customer testimonials and case studies. Discuss track record.',
            'features': 'Provide detailed product demo. Discuss custom configurations.',
            'integration': 'Provide technical documentation. Schedule integration discussion.',
            'security': 'Share compliance certifications. Discuss security measures.',
            'support': 'Outline support options and SLAs. Provide training availability.',
            'implementation': 'Show implementation timeline. Discuss dedicated support.'
        }
        
        return {
            'objection': objection_type,
            'strategy': strategies.get(objection_type, 'Address specific concern and provide solution.'),
            'next_step': 'Schedule follow-up to discuss concerns in detail'
        }
