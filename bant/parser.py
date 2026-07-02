"""
BANT (Budget, Authority, Need, Timeline) extraction engine
Extracts key sales qualification information from conversation text
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class BudgetCategory(Enum):
    """Budget range categories"""
    UNDER_1L = "under_1_lakh"
    RANGE_1L_5L = "1L_to_5L"
    RANGE_5L_10L = "5L_to_10L"
    RANGE_10L_50L = "10L_to_50L"
    OVER_50L = "over_50L"
    NOT_MENTIONED = "not_mentioned"


class AuthorityLevel(Enum):
    """Decision-making authority levels"""
    CEO_CFO = "ceo_cfo"
    VP_DIRECTOR = "vp_director"
    MANAGER = "manager"
    INDIVIDUAL_CONTRIBUTOR = "individual_contributor"
    UNKNOWN = "unknown"


class TimelineUrgency(Enum):
    """Timeline urgency levels"""
    IMMEDIATE = "immediate"  # < 1 month
    SHORT_TERM = "short_term"  # 1-3 months
    MEDIUM_TERM = "medium_term"  # 3-6 months
    LONG_TERM = "long_term"  # > 6 months
    NOT_MENTIONED = "not_mentioned"


@dataclass
class BANTResult:
    """BANT extraction result"""
    budget: Optional[str]
    budget_amount: Optional[float]
    budget_currency: str
    authority: Optional[str]
    authority_level: AuthorityLevel
    need: Optional[str]
    need_category: str
    timeline: Optional[str]
    timeline_urgency: TimelineUrgency
    confidence_scores: Dict[str, float]
    raw_mentions: Dict[str, List[str]]


class BudgetExtractor:
    """Extract budget information from text"""
    
    # Indian currency patterns
    INR_PATTERNS = [
        r'(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?|l)',
        r'(\d+(?:\.\d+)?)\s*(?:crores?|cr)',
        r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'inr\s*(\d+(?:,\d+)*(?:\.\d+)?)',
    ]
    
    # USD patterns
    USD_PATTERNS = [
        r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:usd|dollars?)',
    ]
    
    # Generic patterns
    GENERIC_PATTERNS = [
        r'budget\s+(?:is|of|around|about|approximately)?\s*(?:rs\.?|₹|inr)?\s*(\d+(?:\.\d+)?)',
        r'(?:around|about|approximately|roughly)\s+(?:rs\.?|₹|inr)?\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*(?:thousand|k)',
    ]
    
    def extract(self, text: str) -> Tuple[Optional[str], Optional[float], str]:
        """
        Extract budget from text
        
        Returns:
            Tuple of (budget_string, amount_in_inr, currency)
        """
        text_lower = text.lower()
        
        # Try INR patterns
        for pattern in self.INR_PATTERNS:
            matches = re.findall(pattern, text_lower)
            if matches:
                amount_str = matches[0]
                amount = self._parse_amount(amount_str, text_lower)
                if amount:
                    return f"₹{amount_str}", amount, "INR"
        
        # Try USD patterns
        for pattern in self.USD_PATTERNS:
            matches = re.findall(pattern, text_lower)
            if matches:
                amount_str = matches[0].replace(',', '')
                try:
                    amount_usd = float(amount_str)
                    amount_inr = amount_usd * 83  # Approximate conversion
                    return f"${amount_str}", amount_inr, "USD"
                except:
                    pass
        
        # Try generic patterns
        for pattern in self.GENERIC_PATTERNS:
            matches = re.findall(pattern, text_lower)
            if matches:
                amount_str = matches[0]
                amount = self._parse_amount(amount_str, text_lower)
                if amount:
                    return f"₹{amount_str}", amount, "INR"
        
        return None, None, "INR"
    
    def _parse_amount(self, amount_str: str, context: str) -> Optional[float]:
        """Parse amount string to numeric value in INR"""
        try:
            amount = float(amount_str.replace(',', ''))
            
            # Convert to INR based on context
            if 'lakh' in context or 'lac' in context:
                return amount * 100000
            elif 'crore' in context or 'cr' in context:
                return amount * 10000000
            elif 'thousand' in context or 'k ' in context:
                return amount * 1000
            else:
                return amount
        except:
            return None
    
    def categorize_budget(self, amount_inr: Optional[float]) -> BudgetCategory:
        """Categorize budget into ranges"""
        if amount_inr is None:
            return BudgetCategory.NOT_MENTIONED
        
        if amount_inr < 100000:
            return BudgetCategory.UNDER_1L
        elif amount_inr < 500000:
            return BudgetCategory.RANGE_1L_5L
        elif amount_inr < 1000000:
            return BudgetCategory.RANGE_5L_10L
        elif amount_inr < 5000000:
            return BudgetCategory.RANGE_10L_50L
        else:
            return BudgetCategory.OVER_50L


class AuthorityExtractor:
    """Extract decision-making authority information"""
    
    # Authority level keywords
    AUTHORITY_KEYWORDS = {
        AuthorityLevel.CEO_CFO: {
            'ceo', 'chief executive', 'cfo', 'chief financial', 'founder', 
            'owner', 'proprietor', 'partner', 'managing director'
        },
        AuthorityLevel.VP_DIRECTOR: {
            'vp', 'vice president', 'director', 'head of', 'president',
            'senior manager', 'associate director'
        },
        AuthorityLevel.MANAGER: {
            'manager', 'team lead', 'lead', 'supervisor', 'coordinator',
            'assistant manager', 'deputy manager'
        },
        AuthorityLevel.INDIVIDUAL_CONTRIBUTOR: {
            'engineer', 'developer', 'analyst', 'executive', 'associate',
            'assistant', 'trainee', 'intern'
        }
    }
    
    # Decision-making phrases
    DECISION_PHRASES = [
        r'(?:i|we)\s+(?:will|can|need to|have to|must|should)\s+(?:decide|approve|sign|confirm)',
        r'(?:i|we)\s+have\s+(?:the\s+)?authority',
        r'(?:i|we)\s+(?:report|answer)\s+to',
        r'(?:my|our)\s+(?:boss|manager|superior)',
        r'need\s+(?:to\s+)?(?:check|consult|discuss)\s+with',
        r'(?:i|we)\s+(?:don\'t|do\s+not)\s+have\s+(?:the\s+)?authority',
        r'final\s+(?:decision|approval)',
    ]
    
    def extract(self, text: str) -> Tuple[Optional[str], AuthorityLevel]:
        """
        Extract authority information from text
        
        Returns:
            Tuple of (authority_role, authority_level)
        """
        text_lower = text.lower()
        
        # Check for authority keywords
        for level, keywords in self.AUTHORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Extract the role
                    role = self._extract_role(text, keyword)
                    return role, level
        
        # Check for decision-making phrases
        for phrase in self.DECISION_PHRASES:
            if re.search(phrase, text_lower):
                return self._infer_authority(text), AuthorityLevel.UNKNOWN
        
        return None, AuthorityLevel.UNKNOWN
    
    def _extract_role(self, text: str, keyword: str) -> str:
        """Extract the role from context"""
        # Find the keyword and extract surrounding context
        pattern = rf'\b\w*\s*{keyword}\s*\w*\b'
        matches = re.findall(pattern, text.lower())
        if matches:
            return matches[0].strip()
        return keyword
    
    def _infer_authority(self, text: str) -> str:
        """Infer authority from context"""
        text_lower = text.lower()
        
        if 'final' in text_lower or 'ultimate' in text_lower:
            return "Decision Maker"
        elif 'check' in text_lower or 'consult' in text_lower:
            return "Influencer"
        elif 'report' in text_lower:
            return "Report to Higher Authority"
        
        return "Unknown Authority"


class NeedExtractor:
    """Extract customer needs and requirements"""
    
    # Need categories
    NEED_CATEGORIES = {
        'crm': ['crm', 'customer relationship management', 'sales automation', 'lead management'],
        'erp': ['erp', 'enterprise resource planning', 'inventory management', 'accounting'],
        'hrms': ['hrms', 'human resource', 'payroll', 'attendance', 'leave management'],
        'marketing': ['marketing automation', 'email marketing', 'campaign management', 'seo'],
        'ecommerce': ['ecommerce', 'online store', 'shopping cart', 'payment gateway'],
        'analytics': ['analytics', 'reporting', 'dashboard', 'bi', 'business intelligence'],
        'communication': ['communication', 'chat', 'video conferencing', 'collaboration'],
        'security': ['security', 'cybersecurity', 'firewall', 'vpn', 'data protection'],
        'cloud': ['cloud', 'aws', 'azure', 'gcp', 'hosting', 'saas'],
        'mobile': ['mobile app', 'android', 'ios', 'app development'],
        'website': ['website', 'web development', 'web app', 'portal'],
        'support': ['support', 'helpdesk', 'ticket', 'customer service'],
    }
    
    # Need indicators
    NEED_INDICATORS = [
        r'(?:we\s+)?(?:need|require|looking\s+for|want|searching\s+for)',
        r'(?:our|the)\s+(?:current|existing)\s+(?:system|solution|software)\s+(?:is|has)',
        r'(?:we\s+are\s+)?(?:facing|having|experiencing)\s+(?:issues?|problems?|challenges?)',
        r'(?:help|improve|optimize|streamline|automate)',
        r'(?:pain\s+point|challenge|issue|problem)',
    ]
    
    def extract(self, text: str) -> Tuple[Optional[str], str]:
        """
        Extract need from text
        
        Returns:
            Tuple of (need_description, need_category)
        """
        text_lower = text.lower()
        
        # Check for need indicators
        has_need = any(re.search(pattern, text_lower) for pattern in self.NEED_INDICATORS)
        
        if not has_need:
            return None, "unknown"
        
        # Extract need category
        category = self._categorize_need(text_lower)
        
        # Extract need description
        description = self._extract_description(text)
        
        return description, category
    
    def _categorize_need(self, text: str) -> str:
        """Categorize the need"""
        for category, keywords in self.NEED_CATEGORIES.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return "general"
    
    def _extract_description(self, text: str) -> str:
        """Extract need description from text"""
        # Find the sentence containing need indicators
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(re.search(pattern, sentence_lower) for pattern in self.NEED_INDICATORS):
                return sentence.strip()
        
        return text[:200]  # Fallback to first 200 chars


class TimelineExtractor:
    """Extract timeline and urgency information"""
    
    # Timeline patterns
    TIMELINE_PATTERNS = [
        (r'(?:within|in)\s+(\d+)\s+(?:days?|weeks?|months?)', 'relative'),
        (r'(?:by|before|until)\s+(\w+\s+\d+)', 'date'),
        (r'(?:next|this)\s+(?:week|month|quarter|year)', 'relative'),
        (r'(?:asap|immediately|urgent|right\s+now)', 'immediate'),
        (r'(\d+)\s+(?:days?|weeks?|months?)\s+(?:from\s+now|remaining|left)', 'relative'),
        (r'q[1-4]\s+\d{4}', 'quarter'),
        (r'(?:end\s+of|before\s+end\s+of)\s+(?:this\s+)?(?:month|quarter|year)', 'relative'),
    ]
    
    # Urgency keywords
    URGENCY_KEYWORDS = {
        TimelineUrgency.IMMEDIATE: ['asap', 'immediately', 'urgent', 'right now', 'critical', 'emergency'],
        TimelineUrgency.SHORT_TERM: ['soon', 'quickly', 'fast', 'this week', 'next week', 'within a month'],
        TimelineUrgency.MEDIUM_TERM: ['this quarter', 'next quarter', 'few months', '2-3 months'],
        TimelineUrgency.LONG_TERM: ['later', 'future', 'next year', 'long term', 'eventually'],
    }
    
    def extract(self, text: str) -> Tuple[Optional[str], TimelineUrgency]:
        """
        Extract timeline from text
        
        Returns:
            Tuple of (timeline_string, urgency_level)
        """
        text_lower = text.lower()
        
        # Check for urgency keywords first
        urgency = self._detect_urgency(text_lower)
        
        # Extract timeline
        timeline = self._extract_timeline(text_lower)
        
        return timeline, urgency
    
    def _detect_urgency(self, text: str) -> TimelineUrgency:
        """Detect urgency level from text"""
        for urgency, keywords in self.URGENCY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return urgency
        
        return TimelineUrgency.NOT_MENTIONED
    
    def _extract_timeline(self, text: str) -> Optional[str]:
        """Extract timeline string from text"""
        for pattern, pattern_type in self.TIMELINE_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                if pattern_type == 'relative':
                    return f"In {matches[0]}"
                elif pattern_type == 'date':
                    return f"By {matches[0]}"
                elif pattern_type == 'immediate':
                    return "Immediately"
                elif pattern_type == 'quarter':
                    return f"Q{matches[0]}"
        
        return None


class BANTEngine:
    """Main BANT extraction engine"""
    
    def __init__(self):
        self.budget_extractor = BudgetExtractor()
        self.authority_extractor = AuthorityExtractor()
        self.need_extractor = NeedExtractor()
        self.timeline_extractor = TimelineExtractor()
    
    def extract_bant(self, text: str) -> BANTResult:
        """
        Extract all BANT information from text
        
        Args:
            text: Conversation text
            
        Returns:
            BANTResult with all extracted information
        """
        # Extract each component
        budget_str, budget_amount, currency = self.budget_extractor.extract(text)
        budget_category = self.budget_extractor.categorize_budget(budget_amount)
        
        authority_role, authority_level = self.authority_extractor.extract(text)
        
        need_desc, need_category = self.need_extractor.extract(text)
        
        timeline_str, timeline_urgency = self.timeline_extractor.extract(text)
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence(
            budget_str, authority_role, need_desc, timeline_str
        )
        
        # Collect raw mentions
        raw_mentions = self._collect_raw_mentions(text)
        
        return BANTResult(
            budget=budget_str,
            budget_amount=budget_amount,
            budget_currency=currency,
            authority=authority_role,
            authority_level=authority_level,
            need=need_desc,
            need_category=need_category,
            timeline=timeline_str,
            timeline_urgency=timeline_urgency,
            confidence_scores=confidence_scores,
            raw_mentions=raw_mentions
        )
    
    def _calculate_confidence(
        self,
        budget: Optional[str],
        authority: Optional[str],
        need: Optional[str],
        timeline: Optional[str]
    ) -> Dict[str, float]:
        """Calculate confidence scores for each BANT component"""
        return {
            "budget": 0.9 if budget else 0.0,
            "authority": 0.8 if authority else 0.0,
            "need": 0.85 if need else 0.0,
            "timeline": 0.75 if timeline else 0.0,
        }
    
    def _collect_raw_mentions(self, text: str) -> Dict[str, List[str]]:
        """Collect raw mentions of BANT elements"""
        mentions = {
            "budget": [],
            "authority": [],
            "need": [],
            "timeline": []
        }
        
        # Budget mentions
        budget_patterns = [
            r'\d+\s*(?:lakhs?|lacs?|crores?|cr)',
            r'[₹$]\s*\d+',
        ]
        for pattern in budget_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            mentions["budget"].extend(matches)
        
        # Authority mentions
        authority_keywords = [
            'ceo', 'cfo', 'cto', 'director', 'vp', 'manager', 'founder', 'owner'
        ]
        for keyword in authority_keywords:
            if keyword in text.lower():
                mentions["authority"].append(keyword)
        
        # Need mentions
        need_keywords = ['need', 'require', 'looking for', 'want', 'problem', 'issue']
        for keyword in need_keywords:
            if keyword in text.lower():
                mentions["need"].append(keyword)
        
        # Timeline mentions
        timeline_patterns = [
            r'\d+\s*(?:days?|weeks?|months?)',
            r'(?:asap|immediately|urgent)',
        ]
        for pattern in timeline_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            mentions["timeline"].extend(matches)
        
        return mentions
    
    def get_bant_summary(self, result: BANTResult) -> Dict:
        """Get summary of BANT extraction"""
        return {
            "budget": {
                "value": result.budget,
                "amount_inr": result.budget_amount,
                "category": result.budget_category.value if result.budget_category else "unknown",
                "confidence": result.confidence_scores.get("budget", 0.0)
            },
            "authority": {
                "role": result.authority,
                "level": result.authority_level.value if result.authority_level else "unknown",
                "confidence": result.confidence_scores.get("authority", 0.0)
            },
            "need": {
                "description": result.need,
                "category": result.need_category,
                "confidence": result.confidence_scores.get("need", 0.0)
            },
            "timeline": {
                "value": result.timeline,
                "urgency": result.timeline_urgency.value if result.timeline_urgency else "unknown",
                "confidence": result.confidence_scores.get("timeline", 0.0)
            },
            "overall_qualification": self._calculate_qualification_score(result)
        }
    
    def _calculate_qualification_score(self, result: BANTResult) -> float:
        """Calculate overall BANT qualification score"""
        scores = list(result.confidence_scores.values())
        if not scores:
            return 0.0
        
        # Weighted average
        weights = [0.3, 0.2, 0.3, 0.2]  # Budget, Authority, Need, Timeline
        weighted_score = sum(s * w for s, w in zip(scores, weights))
        
        return round(weighted_score, 2)