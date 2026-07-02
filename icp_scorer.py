"""
ICP (Ideal Customer Profile) Scoring Module
Matches customer against ideal profile criteria
"""

import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class ICPScorer:
    """
    Scores customers against ideal customer profile
    5 criteria: Industry, Company Size, Revenue, Region, Role
    """
    
    # Industry matching
    INDUSTRIES = {
        'technology': [
            r'\b(?:technology|tech|software|it|information\s+technology|saas)\b',
            r'\b(?:startup|fintech|edtech|healthtech)\b',
        ],
        'finance': [
            r'\b(?:finance|banking|financial\s+services|insurance|investment)\b',
            r'\b(?:fintech|crypto|securities|trading)\b',
        ],
        'healthcare': [
            r'\b(?:healthcare|health|medical|hospital|clinic|pharmaceutical)\b',
            r'\b(?:biotech|life\s+sciences|wellness)\b',
        ],
        'retail': [
            r'\b(?:retail|e-commerce|ecommerce|store|shopping|mall)\b',
            r'\b(?:fashion|luxury|grocery)\b',
        ],
        'manufacturing': [
            r'\b(?:manufacturing|factory|industrial|production|supply\s+chain)\b',
            r'\b(?:automotive|logistics|warehouse)\b',
        ],
        'education': [
            r'\b(?:education|university|school|college|academy|edtech)\b',
            r'\b(?:learning|training|course)\b',
        ],
        'real_estate': [
            r'\b(?:real\s+estate|property|realty|construction|building)\b',
            r'\b(?:real\s+estate|property\s+management)\b',
        ],
        'hospitality': [
            r'\b(?:hospitality|hotel|restaurant|travel|tourism)\b',
            r'\b(?:food\s+service|catering)\b',
        ],
    }
    
    # Company size matching
    SIZES = {
        'enterprise': [
            r'\b(?:enterprise|large|big\s+company|multinational)\b',
            r'\b(?:500\+|global|worldwide)\b',
        ],
        'medium': [
            r'\b(?:medium|mid-size|medium\s+sized)\b',
            r'\b(?:50-500|sme|mid-market)\b',
        ],
        'small': [
            r'\b(?:small|startup|smb)\b',
            r'\b(?:10-50|small\s+business|growing)\b',
        ],
    }
    
    # Revenue ranges
    REVENUES = {
        'large': [
            r'\b(?:billion|100\s*million|revenue\s+over\s+100m)\b',
        ],
        'medium': [
            r'\b(?:million|10\s*million|revenue.*\d+\s*m)\b',
        ],
        'small': [
            r'\b(?:startup|bootstrapped|early\s+stage)\b',
        ],
    }
    
    # Regions
    REGIONS = {
        'asia': [
            r'\b(?:india|bangalore|delhi|mumbai|hyderabad|asia)\b',
            r'\b(?:singapore|hong\s+kong|tokyo|shanghai)\b',
        ],
        'north_america': [
            r'\b(?:usa|us|america|canada|toronto|new\s+york)\b',
            r'\b(?:california|silicon\s+valley)\b',
        ],
        'europe': [
            r'\b(?:europe|uk|london|berlin|paris|switzerland)\b',
            r'\b(?:netherlands|scandinavia)\b',
        ],
    }
    
    # Roles
    ROLES = {
        'c_level': [
            r'\b(?:ceo|cfo|cto|coo|president|executive)\b',
            r'\b(?:c-level|chief)\b',
        ],
        'director': [
            r'\b(?:director|vp|vice\s+president)\b',
            r'\b(?:head\s+of|chief\s+technology|chief\s+marketing)\b',
        ],
        'manager': [
            r'\b(?:manager|team\s+lead|supervisor)\b',
            r'\b(?:project\s+manager|product\s+manager)\b',
        ],
    }
    
    # Ideal customer profile (what to score for)
    IDEAL_PROFILE = {
        'industry': {
            'preferred': ['technology', 'finance', 'healthcare'],
            'acceptable': ['retail', 'education'],
            'weight': 0.25
        },
        'size': {
            'preferred': ['medium', 'enterprise'],
            'acceptable': ['small'],
            'weight': 0.20
        },
        'revenue': {
            'preferred': ['large', 'medium'],
            'acceptable': ['small'],
            'weight': 0.25
        },
        'region': {
            'preferred': ['asia', 'north_america'],
            'acceptable': ['europe'],
            'weight': 0.15
        },
        'role': {
            'preferred': ['c_level', 'director'],
            'acceptable': ['manager'],
            'weight': 0.15
        }
    }
    
    def __init__(self):
        """Initialize ICP scorer"""
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict:
        """Compile regex patterns"""
        compiled = {}
        
        for category in ['industries', 'sizes', 'revenues', 'regions', 'roles']:
            if category == 'industries':
                patterns_dict = self.INDUSTRIES
            elif category == 'sizes':
                patterns_dict = self.SIZES
            elif category == 'revenues':
                patterns_dict = self.REVENUES
            elif category == 'regions':
                patterns_dict = self.REGIONS
            else:  # roles
                patterns_dict = self.ROLES
            
            compiled[category] = {}
            for key, patterns in patterns_dict.items():
                compiled[category][key] = [re.compile(p, re.IGNORECASE) for p in patterns]
        
        return compiled
    
    def extract_attributes(self, text: str) -> Dict[str, any]:
        """
        Extract customer attributes from text
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with extracted attributes
        """
        text_lower = text.lower()
        
        attributes = {
            'industry': None,
            'size': None,
            'revenue': None,
            'region': None,
            'role': None,
            'raw_matches': {}
        }
        
        # Extract industry
        for industry, patterns in self.compiled_patterns['industries'].items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    attributes['industry'] = industry
                    break
            if attributes['industry']:
                break
        
        # Extract size
        for size, patterns in self.compiled_patterns['sizes'].items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    attributes['size'] = size
                    break
            if attributes['size']:
                break
        
        # Extract revenue
        for revenue, patterns in self.compiled_patterns['revenues'].items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    attributes['revenue'] = revenue
                    break
            if attributes['revenue']:
                break
        
        # Extract region
        for region, patterns in self.compiled_patterns['regions'].items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    attributes['region'] = region
                    break
            if attributes['region']:
                break
        
        # Extract role
        for role, patterns in self.compiled_patterns['roles'].items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    attributes['role'] = role
                    break
            if attributes['role']:
                break
        
        return attributes
    
    def score_icp(self, attributes: Dict[str, any]) -> Dict[str, any]:
        """
        Score customer against ideal profile
        
        Args:
            attributes: Extracted customer attributes
        
        Returns:
            ICP score and tier
        """
        total_score = 0
        criteria_scores = {}
        criteria_details = {}
        
        ideal_profile = self.IDEAL_PROFILE
        
        # Score each criterion
        for criterion, config in ideal_profile.items():
            attribute_value = attributes.get(criterion)
            weight = config['weight']
            preferred = config['preferred']
            acceptable = config['acceptable']
            
            if attribute_value is None:
                # Not found - no points
                criterion_score = 0
                detail = 'Not detected'
            elif attribute_value in preferred:
                # Preferred match - full points
                criterion_score = 1.0
                detail = f'Ideal match: {attribute_value}'
            elif attribute_value in acceptable:
                # Acceptable match - partial points
                criterion_score = 0.6
                detail = f'Acceptable: {attribute_value}'
            else:
                # Not a fit
                criterion_score = 0.2
                detail = f'Not ideal: {attribute_value}'
            
            criteria_scores[criterion] = criterion_score
            criteria_details[criterion] = detail
            total_score += criterion_score * weight
        
        # Convert to percentage
        icp_score = total_score * 100
        
        # Determine tier
        if icp_score >= 90:
            tier = 'A+'
        elif icp_score >= 80:
            tier = 'A'
        elif icp_score >= 70:
            tier = 'B'
        elif icp_score >= 60:
            tier = 'C'
        else:
            tier = 'D'
        
        return {
            'score': icp_score,
            'tier': tier,
            'criteria_scores': criteria_scores,
            'criteria_details': criteria_details,
            'attributes': attributes,
            'recommendation': self._get_recommendation(tier, icp_score)
        }
    
    def _get_recommendation(self, tier: str, score: float) -> str:
        """Get recommendation based on tier"""
        recommendations = {
            'A+': 'Excellent fit. This is a highly qualified ideal customer.',
            'A': 'Great fit. Strong alignment with ideal customer profile.',
            'B': 'Good fit. Acceptable match with some ideal characteristics.',
            'C': 'Moderate fit. Some alignment but notable gaps.',
            'D': 'Poor fit. Significant misalignment with ideal profile.'
        }
        
        return recommendations.get(tier, 'Unknown tier')
    
    def format_icp_summary(self, icp_data: Dict[str, any]) -> Dict[str, any]:
        """
        Format ICP data for display
        
        Args:
            icp_data: ICP scoring result
        
        Returns:
            Formatted summary
        """
        return {
            'score': f"{icp_data['score']:.0f}%",
            'tier': icp_data['tier'],
            'criteria': [
                {
                    'name': criterion.replace('_', ' ').title(),
                    'match': icp_data['attributes'].get(criterion, 'Not detected').replace('_', ' ').title(),
                    'detail': icp_data['criteria_details'].get(criterion, 'Not evaluated')
                }
                for criterion in ['industry', 'size', 'revenue', 'region', 'role']
            ],
            'recommendation': icp_data['recommendation']
        }
