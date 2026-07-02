"""
BANT Extraction Module
Extracts Budget, Authority, Need, Timeline from conversation
"""

import re
from typing import Dict, Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

class BANTExtractor:
    """
    Extracts BANT (Budget, Authority, Need, Timeline) from text
    """
    
    # Currency patterns
    CURRENCY_PATTERNS = {
        'lakhs': (r'(\d+(?:[.,]\d+)?)\s*(?:lakh|lac|lakhs|lacs)', 100000),
        'crores': (r'(\d+(?:[.,]\d+)?)\s*(?:crore|crores)', 10000000),
        'thousands': (r'(\d+(?:[.,]\d+)?)\s*(?:thousand|k|K)', 1000),
        'dollars': (r'\$\s*(\d+(?:[.,]\d+)?)', 1),
        'rupees': (r'₹\s*(\d+(?:[.,]\d+)?)', 1),
    }
    
    # Authority patterns
    AUTHORITY_PATTERNS = {
        'ceo_cfo': [
            r'\b(?:i\s+)?(?:am|i\'m)\s+(?:the\s+)?(?:ceo|cfo|chief executive|chief financial)',
            r'\b(?:ceo|cfo)\s+(?:here|speaking)',
            r'\bowner\b.*\bcompany',
            r'\b(?:am|i\'m)\s+(?:in\s+)?(?:charge|control)',
        ],
        'director': [
            r'\bdirector\b',
            r'\bvp\b.*\b(?:operations|sales|engineering)',
            r'\bhead\s+of\b',
        ],
        'manager': [
            r'\bmanager\b',
            r'\bleader\s+of\b',
            r'\bresponsible\s+for\b',
        ],
        'individual': [
            r'\buser\b',
            r'\bteam\s+member\b',
            r'\bemployee\b',
        ]
    }
    
    # Need patterns
    NEED_PATTERNS = {
        'software': [
            r'\b(?:software|application|app|platform|system|solution)\b',
            r'\b(?:need|looking for|require)\s+(?:a\s+)?(?:crm|erp|saas|tool)',
        ],
        'crm': [
            r'\bcrm\b',
            r'\bcustomer\s+relationship\s+management\b',
            r'\b(?:manage|track)\s+(?:customers|leads|sales)',
        ],
        'automation': [
            r'\b(?:automation|automate|streamline|improve)\b',
            r'\b(?:workflow|process|efficiency)\b',
        ],
        'integration': [
            r'\b(?:integrate|integration|connect|sync)\b',
            r'\b(?:api|third-party|integration)\b',
        ],
        'analytics': [
            r'\b(?:analytics|reporting|dashboards|insights|metrics)\b',
            r'\b(?:analyze|track|measure|report)\b',
        ],
        'support': [
            r'\b(?:support|customer service|help desk|ticketing)\b',
            r'\b(?:support\s+team|customer\s+care)\b',
        ],
    }
    
    # Timeline patterns
    TIMELINE_PATTERNS = {
        'immediate': [
            r'\b(?:asap|urgent|right now|immediately|today)\b',
            r'\b(?:urgent|emergency|critical)\b',
            r'\bneed\s+(?:it\s+)?(?:now|today|immediately)\b',
        ],
        'short_term': [
            r'(?:within\s+)?(\d+)\s*(?:days?|weeks?)',
            r'(?:next\s+)?(?:week|month)',
            r'\b(?:soon|quickly)\b',
        ],
        'medium_term': [
            r'(\d+)\s*months?',
            r'(?:quarter|q[1-4])',
            r'(?:3\s+to\s+6\s+months)',
        ],
        'long_term': [
            r'(?:this\s+)?year',
            r'(?:next\s+)?year',
            r'(\d+)\s*years?',
            r'(?:long\s+term|strategic)',
        ]
    }
    
    def __init__(self):
        """Initialize BANT extractor"""
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict:
        """Compile regex patterns"""
        compiled = {
            'authority': {},
            'need': {},
            'timeline': {}
        }
        
        for level, patterns in self.AUTHORITY_PATTERNS.items():
            compiled['authority'][level] = [re.compile(p, re.IGNORECASE) for p in patterns]
        
        for category, patterns in self.NEED_PATTERNS.items():
            compiled['need'][category] = [re.compile(p, re.IGNORECASE) for p in patterns]
        
        for timeline, patterns in self.TIMELINE_PATTERNS.items():
            compiled['timeline'][timeline] = [re.compile(p, re.IGNORECASE) for p in patterns]
        
        return compiled
    
    def extract_budget(self, text: str) -> Dict[str, any]:
        """
        Extract budget from text
        
        Args:
            text: Text to extract from
        
        Returns:
            Dictionary with budget info
        """
        budget_info = {
            "amount": None,
            "currency": None,
            "original_text": None,
            "confidence": 0.0
        }
        
        text_lower = text.lower()
        
        # Search for currency patterns
        for currency, (pattern, multiplier) in self.CURRENCY_PATTERNS.items():
            regex = re.compile(pattern, re.IGNORECASE)
            match = regex.search(text)
            
            if match:
                try:
                    amount_str = match.group(1).replace(',', '').replace('.', '')
                    amount = float(amount_str) * multiplier
                    
                    budget_info["amount"] = amount
                    budget_info["currency"] = currency
                    budget_info["original_text"] = match.group(0)
                    budget_info["confidence"] = 0.90
                    
                    return budget_info
                except (ValueError, IndexError):
                    continue
        
        return budget_info
    
    def extract_authority(self, text: str) -> Dict[str, any]:
        """
        Extract decision maker authority from text
        
        Args:
            text: Text to extract from
        
        Returns:
            Dictionary with authority info
        """
        authority_info = {
            "level": None,
            "original_text": None,
            "confidence": 0.0
        }
        
        text_lower = text.lower()
        
        # Check authority patterns (in order of hierarchy)
        for level in ['ceo_cfo', 'director', 'manager', 'individual']:
            patterns = self.compiled_patterns['authority'].get(level, [])
            
            for pattern in patterns:
                match = pattern.search(text_lower)
                if match:
                    authority_info["level"] = level
                    authority_info["original_text"] = match.group(0)
                    authority_info["confidence"] = 0.85
                    return authority_info
        
        return authority_info
    
    def extract_need(self, text: str) -> Dict[str, any]:
        """
        Extract customer need from text
        
        Args:
            text: Text to extract from
        
        Returns:
            Dictionary with need info
        """
        need_info = {
            "categories": [],
            "primary_need": None,
            "confidence": 0.0
        }
        
        text_lower = text.lower()
        
        # Check need patterns
        matches = {}
        for category, patterns in self.compiled_patterns['need'].items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    matches[category] = 0.88
        
        if matches:
            need_info["categories"] = list(matches.keys())
            need_info["primary_need"] = max(matches.items(), key=lambda x: x[1])[0]
            need_info["confidence"] = max(matches.values())
        
        return need_info
    
    def extract_timeline(self, text: str) -> Dict[str, any]:
        """
        Extract timeline from text
        
        Args:
            text: Text to extract from
        
        Returns:
            Dictionary with timeline info
        """
        timeline_info = {
            "urgency": None,
            "original_text": None,
            "confidence": 0.0
        }
        
        text_lower = text.lower()
        
        # Check timeline patterns (in order of urgency)
        for urgency in ['immediate', 'short_term', 'medium_term', 'long_term']:
            patterns = self.compiled_patterns['timeline'].get(urgency, [])
            
            for pattern in patterns:
                match = pattern.search(text_lower)
                if match:
                    timeline_info["urgency"] = urgency
                    timeline_info["original_text"] = match.group(0)
                    timeline_info["confidence"] = 0.75
                    return timeline_info
        
        return timeline_info
    
    def extract_bant(self, text: str) -> Dict[str, any]:
        """
        Extract complete BANT from text
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with BANT information
        """
        bant = {
            "budget": self.extract_budget(text),
            "authority": self.extract_authority(text),
            "need": self.extract_need(text),
            "timeline": self.extract_timeline(text),
            "completeness": 0.0
        }
        
        # Calculate completeness (0-1.0)
        completeness = 0
        max_score = 4
        
        if bant["budget"]["amount"] is not None:
            completeness += 1
        if bant["authority"]["level"] is not None:
            completeness += 1
        if bant["need"]["primary_need"] is not None:
            completeness += 1
        if bant["timeline"]["urgency"] is not None:
            completeness += 1
        
        bant["completeness"] = completeness / max_score
        
        return bant
    
    def format_bant_summary(self, bant: Dict[str, any]) -> Dict[str, str]:
        """
        Format BANT for display
        
        Args:
            bant: BANT dictionary
        
        Returns:
            Formatted summary
        """
        budget = bant.get("budget", {})
        authority = bant.get("authority", {})
        need = bant.get("need", {})
        timeline = bant.get("timeline", {})
        
        budget_text = "Not detected"
        if budget.get("amount"):
            if budget["currency"] == "lakhs":
                budget_text = f"₹{budget['amount']/100000:.0f} Lakhs"
            elif budget["currency"] == "crores":
                budget_text = f"₹{budget['amount']/10000000:.0f} Crores"
            else:
                budget_text = f"₹{budget['amount']:.0f}"
        
        authority_text = authority.get("level", "Not detected").replace("_", " ").title()
        need_text = need.get("primary_need", "Not detected").replace("_", " ").title()
        timeline_text = timeline.get("urgency", "Not detected").replace("_", " ").title()
        
        return {
            "budget": budget_text,
            "authority": authority_text,
            "need": need_text,
            "timeline": timeline_text
        }
