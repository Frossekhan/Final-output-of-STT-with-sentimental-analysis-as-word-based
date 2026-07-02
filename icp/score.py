"""
ICP (Ideal Customer Profile) scoring engine
Scores how well a customer matches the ideal customer profile
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IndustryType(Enum):
    """Industry categories"""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    CONSULTING = "consulting"
    MEDIA = "media"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    OTHER = "other"


class CompanySize(Enum):
    """Company size categories"""
    STARTUP = "startup"  # 1-10 employees
    SMALL = "small"  # 11-50 employees
    MEDIUM = "medium"  # 51-200 employees
    LARGE = "large"  # 201-1000 employees
    ENTERPRISE = "enterprise"  # 1000+ employees


class RevenueRange(Enum):
    """Annual revenue ranges (INR)"""
    UNDER_1CR = "under_1_crore"
    RANGE_1CR_10CR = "1cr_to_10cr"
    RANGE_10CR_50CR = "10cr_to_50cr"
    RANGE_50CR_200CR = "50cr_to_200cr"
    OVER_200CR = "over_200cr"


@dataclass
class ICPProfile:
    """Ideal Customer Profile definition"""
    target_industries: List[IndustryType]
    target_company_sizes: List[CompanySize]
    target_revenue_ranges: List[RevenueRange]
    target_regions: List[str]
    target_roles: List[str]
    min_score_threshold: float
    weights: Dict[str, float]


@dataclass
class ICPResult:
    """ICP scoring result"""
    overall_score: float
    industry_score: float
    company_size_score: float
    revenue_score: float
    region_score: float
    role_score: float
    matched_criteria: List[str]
    missing_criteria: List[str]
    recommendations: List[str]
    details: Dict


class ICPScorer:
    """
    ICP (Ideal Customer Profile) scoring engine
    
    Scores how well a customer matches the ideal customer profile
    based on industry, company size, revenue, region, and role.
    """
    
    # Default ICP profile (customizable)
    DEFAULT_ICP = ICPProfile(
        target_industries=[
            IndustryType.TECHNOLOGY,
            IndustryType.SAAS,
            IndustryType.FINANCE,
            IndustryType.ECOMMERCE
        ],
        target_company_sizes=[
            CompanySize.MEDIUM,
            CompanySize.LARGE,
            CompanySize.ENTERPRISE
        ],
        target_revenue_ranges=[
            RevenueRange.RANGE_10CR_50CR,
            RevenueRange.RANGE_50CR_200CR,
            RevenueRange.OVER_200CR
        ],
        target_regions=["india", "usa", "uk", "singapore", "uae"],
        target_roles=[
            "ceo", "cto", "cfo", "coo", "vp", "director",
            "head of", "manager", "founder", "owner"
        ],
        min_score_threshold=0.6,
        weights={
            "industry": 0.25,
            "company_size": 0.20,
            "revenue": 0.25,
            "region": 0.15,
            "role": 0.15
        }
    )
    
    # Industry keywords mapping
    INDUSTRY_KEYWORDS = {
        IndustryType.TECHNOLOGY: [
            'tech', 'software', 'it', 'information technology', 'digital',
            'computer', 'internet', 'cloud', 'data', 'ai', 'ml', 'artificial intelligence',
            'machine learning', 'automation', 'saas', 'paas', 'iaas'
        ],
        IndustryType.FINANCE: [
            'finance', 'banking', 'insurance', 'fintech', 'investment',
            'financial', 'bank', 'insurance', 'payment', 'lending', 'nbfc'
        ],
        IndustryType.HEALTHCARE: [
            'healthcare', 'hospital', 'medical', 'pharma', 'pharmaceutical',
            'health', 'clinic', 'doctor', 'patient', 'medicine', 'biotech'
        ],
        IndustryType.RETAIL: [
            'retail', 'store', 'shop', 'mall', 'supermarket', 'hypermarket',
            'fashion', 'apparel', 'consumer goods', 'fmcg', 'distribution'
        ],
        IndustryType.MANUFACTURING: [
            'manufacturing', 'factory', 'production', 'industrial', 'machinery',
            'automotive', 'chemical', 'textile', 'steel', 'engineering'
        ],
        IndustryType.EDUCATION: [
            'education', 'school', 'college', 'university', 'edtech',
            'learning', 'training', 'institute', 'academy', 'e-learning'
        ],
        IndustryType.REAL_ESTATE: [
            'real estate', 'property', 'construction', 'builder', 'developer',
            'housing', 'commercial', 'residential', 'realty'
        ],
        IndustryType.CONSULTING: [
            'consulting', 'consultancy', 'advisory', 'professional services',
            'management consulting', 'strategy', 'advisory services'
        ],
        IndustryType.MEDIA: [
            'media', 'entertainment', 'advertising', 'marketing', 'agency',
            'television', 'film', 'music', 'gaming', 'content'
        ],
        IndustryType.ECOMMERCE: [
            'ecommerce', 'e-commerce', 'online store', 'marketplace',
            'shopping', 'retail tech', 'd2c', 'direct to consumer'
        ],
        IndustryType.SAAS: [
            'saas', 'software as a service', 'cloud software', 'subscription',
            'b2b software', 'enterprise software', 'product'
        ]
    }
    
    # Company size indicators
    COMPANY_SIZE_INDICATORS = {
        CompanySize.STARTUP: [
            'startup', 'early stage', 'seed', 'pre-seed', 'bootstrapped',
            'small team', 'just started', 'founded recently'
        ],
        CompanySize.SMALL: [
            'small business', 'small company', '10-50', 'less than 50',
            'growing', 'emerging', 'emerging business'
        ],
        CompanySize.MEDIUM: [
            'medium', 'mid-size', 'mid market', '50-200', '100-200',
            'growing company', 'established'
        ],
        CompanySize.LARGE: [
            'large', '200-1000', '500-1000', 'corporate', 'enterprise-level',
            'mid-large', 'established company'
        ],
        CompanySize.ENTERPRISE: [
            'enterprise', 'large enterprise', '1000+', 'fortune', 'mnc',
            'multinational', 'conglomerate', 'big corporation'
        ]
    }
    
    # Revenue indicators (INR)
    REVENUE_INDICATORS = {
        RevenueRange.UNDER_1CR: [
            'under 1 crore', 'less than 1 cr', 'startup revenue',
            'early revenue', 'pre-revenue'
        ],
        RevenueRange.RANGE_1CR_10CR: [
            '1 crore', '2 crore', '5 crore', '10 crore', 'cr turnover',
            'small revenue', 'growing revenue'
        ],
        RevenueRange.RANGE_10CR_50CR: [
            '10 crore', '20 crore', '30 crore', '40 crore', '50 crore',
            '10-50 cr', 'mid-revenue', 'established revenue'
        ],
        RevenueRange.RANGE_50CR_200CR: [
            '50 crore', '100 crore', '150 crore', '200 crore',
            '50-200 cr', 'high revenue', 'significant revenue'
        ],
        RevenueRange.OVER_200CR: [
            '200 crore', '500 crore', '1000 crore', '200+ cr',
            'large revenue', 'major player', 'industry leader'
        ]
    }
    
    def __init__(self, icp_profile: Optional[ICPProfile] = None):
        """Initialize ICP scorer with custom or default profile"""
        self.icp_profile = icp_profile or self.DEFAULT_ICP
        
    def score_customer(
        self,
        text: str,
        industry: Optional[str] = None,
        company_size: Optional[str] = None,
        revenue: Optional[str] = None,
        region: Optional[str] = None,
        role: Optional[str] = None
    ) -> ICPResult:
        """
        Score customer against ICP
        
        Args:
            text: Conversation text for extraction
            industry: Industry type (optional, will extract from text if not provided)
            company_size: Company size (optional)
            revenue: Revenue range (optional)
            region: Region/country (optional)
            role: Decision maker role (optional)
            
        Returns:
            ICPResult with scores and analysis
        """
        text_lower = text.lower()
        
        # Extract information if not provided
        if not industry:
            industry = self._extract_industry(text_lower)
        if not company_size:
            company_size = self._extract_company_size(text_lower)
        if not revenue:
            revenue = self._extract_revenue(text_lower)
        if not region:
            region = self._extract_region(text_lower)
        if not role:
            role = self._extract_role(text_lower)
        
        # Calculate individual scores
        industry_score = self._score_industry(industry)
        company_size_score = self._score_company_size(company_size)
        revenue_score = self._score_revenue(revenue)
        region_score = self._score_region(region)
        role_score = self._score_role(role)
        
        # Calculate weighted overall score
        weights = self.icp_profile.weights
        overall_score = (
            industry_score * weights["industry"] +
            company_size_score * weights["company_size"] +
            revenue_score * weights["revenue"] +
            region_score * weights["region"] +
            role_score * weights["role"]
        )
        
        # Identify matched and missing criteria
        matched_criteria, missing_criteria = self._identify_criteria(
            industry, company_size, revenue, region, role
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_score, matched_criteria, missing_criteria
        )
        
        # Create details
        details = {
            "industry": industry,
            "company_size": company_size,
            "revenue": revenue,
            "region": region,
            "role": role,
            "scores": {
                "industry": round(industry_score, 2),
                "company_size": round(company_size_score, 2),
                "revenue": round(revenue_score, 2),
                "region": round(region_score, 2),
                "role": round(role_score, 2)
            }
        }
        
        return ICPResult(
            overall_score=round(overall_score, 2),
            industry_score=round(industry_score, 2),
            company_size_score=round(company_size_score, 2),
            revenue_score=round(revenue_score, 2),
            region_score=round(region_score, 2),
            role_score=round(role_score, 2),
            matched_criteria=matched_criteria,
            missing_criteria=missing_criteria,
            recommendations=recommendations,
            details=details
        )
    
    def _extract_industry(self, text: str) -> Optional[str]:
        """Extract industry from text"""
        for industry, keywords in self.INDUSTRY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return industry.value
        return None
    
    def _extract_company_size(self, text: str) -> Optional[str]:
        """Extract company size from text"""
        for size, indicators in self.COMPANY_SIZE_INDICATORS.items():
            for indicator in indicators:
                if indicator in text:
                    return size.value
        return None
    
    def _extract_revenue(self, text: str) -> Optional[str]:
        """Extract revenue from text"""
        for revenue, indicators in self.REVENUE_INDICATORS.items():
            for indicator in indicators:
                if indicator in text:
                    return revenue.value
        return None
    
    def _extract_region(self, text: str) -> Optional[str]:
        """Extract region from text"""
        regions = {
            "india": ["india", "indian", "mumbai", "delhi", "bangalore", "chennai", "hyderabad"],
            "usa": ["usa", "united states", "america", "us ", "new york", "california", "texas"],
            "uk": ["uk", "united kingdom", "britain", "london", "england"],
            "singapore": ["singapore"],
            "uae": ["uae", "dubai", "abu dhabi", "united arab emirates"]
        }
        
        for region, keywords in regions.items():
            for keyword in keywords:
                if keyword in text:
                    return region
        return None
    
    def _extract_role(self, text: str) -> Optional[str]:
        """Extract decision maker role from text"""
        roles = [
            'ceo', 'cto', 'cfo', 'coo', 'cio', 'cmo',
            'vp', 'vice president',
            'director', 'head of',
            'founder', 'co-founder', 'owner', 'partner',
            'manager', 'lead', 'supervisor'
        ]
        
        for role in roles:
            if role in text:
                return role
        return None
    
    def _score_industry(self, industry: Optional[str]) -> float:
        """Score industry match"""
        if not industry:
            return 0.0
        
        try:
            industry_enum = IndustryType(industry)
            if industry_enum in self.icp_profile.target_industries:
                return 1.0
            else:
                return 0.3  # Partial match
        except ValueError:
            return 0.5
    
    def _score_company_size(self, company_size: Optional[str]) -> float:
        """Score company size match"""
        if not company_size:
            return 0.0
        
        try:
            size_enum = CompanySize(company_size)
            if size_enum in self.icp_profile.target_company_sizes:
                return 1.0
            else:
                return 0.4  # Partial match
        except ValueError:
            return 0.5
    
    def _score_revenue(self, revenue: Optional[str]) -> float:
        """Score revenue match"""
        if not revenue:
            return 0.0
        
        try:
            revenue_enum = RevenueRange(revenue)
            if revenue_enum in self.icp_profile.target_revenue_ranges:
                return 1.0
            else:
                return 0.3  # Partial match
        except ValueError:
            return 0.5
    
    def _score_region(self, region: Optional[str]) -> float:
        """Score region match"""
        if not region:
            return 0.0
        
        if region in self.icp_profile.target_regions:
            return 1.0
        else:
            return 0.2  # Low match for non-target regions
    
    def _score_role(self, role: Optional[str]) -> float:
        """Score decision maker role match"""
        if not role:
            return 0.0
        
        if any(target_role in role for target_role in self.icp_profile.target_roles):
            return 1.0
        else:
            return 0.5  # Partial match
    
    def _identify_criteria(
        self,
        industry: Optional[str],
        company_size: Optional[str],
        revenue: Optional[str],
        region: Optional[str],
        role: Optional[str]
    ) -> Tuple[List[str], List[str]]:
        """Identify matched and missing criteria"""
        matched = []
        missing = []
        
        # Industry
        if industry and self._score_industry(industry) >= 0.8:
            matched.append(f"Target industry: {industry}")
        else:
            missing.append(f"Industry: {industry or 'not detected'}")
        
        # Company size
        if company_size and self._score_company_size(company_size) >= 0.8:
            matched.append(f"Target company size: {company_size}")
        else:
            missing.append(f"Company size: {company_size or 'not detected'}")
        
        # Revenue
        if revenue and self._score_revenue(revenue) >= 0.8:
            matched.append(f"Target revenue range: {revenue}")
        else:
            missing.append(f"Revenue: {revenue or 'not detected'}")
        
        # Region
        if region and self._score_region(region) >= 0.8:
            matched.append(f"Target region: {region}")
        else:
            missing.append(f"Region: {region or 'not detected'}")
        
        # Role
        if role and self._score_role(role) >= 0.8:
            matched.append(f"Target role: {role}")
        else:
            missing.append(f"Role: {role or 'not detected'}")
        
        return matched, missing
    
    def _generate_recommendations(
        self,
        overall_score: float,
        matched_criteria: List[str],
        missing_criteria: List[str]
    ) -> List[str]:
        """Generate recommendations based on ICP score"""
        recommendations = []
        
        if overall_score >= 0.8:
            recommendations.append("EXCELLENT FIT: Strong match with ICP. Prioritize this lead.")
            recommendations.append("Assign to senior sales representative for immediate follow-up.")
        elif overall_score >= 0.6:
            recommendations.append("GOOD FIT: Meets ICP criteria. Proceed with standard sales process.")
            recommendations.append("Focus on addressing missing criteria to improve conversion.")
        elif overall_score >= 0.4:
            recommendations.append("MODERATE FIT: Partial ICP match. Consider for nurturing campaign.")
            recommendations.append("Gather additional information to better qualify.")
        else:
            recommendations.append("LOW FIT: Does not meet ICP criteria. Consider disqualifying or low-priority nurturing.")
            recommendations.append("Focus resources on higher-scoring leads.")
        
        # Specific recommendations for missing criteria
        if missing_criteria:
            recommendations.append(f"Missing criteria to address: {', '.join(missing_criteria[:3])}")
        
        return recommendations
    
    def get_icp_tier(self, score: float) -> str:
        """Get ICP tier from score"""
        if score >= 0.8:
            return "A+ (Excellent)"
        elif score >= 0.7:
            return "A (Very Good)"
        elif score >= 0.6:
            return "B+ (Good)"
        elif score >= 0.5:
            return "B (Average)"
        elif score >= 0.4:
            return "C (Below Average)"
        else:
            return "D (Poor)"
    
    def update_icp_profile(self, new_profile: ICPProfile):
        """Update ICP profile"""
        self.icp_profile = new_profile
    
    def get_icp_profile(self) -> Dict:
        """Get current ICP profile"""
        return {
            "target_industries": [i.value for i in self.icp_profile.target_industries],
            "target_company_sizes": [s.value for s in self.icp_profile.target_company_sizes],
            "target_revenue_ranges": [r.value for r in self.icp_profile.target_revenue_ranges],
            "target_regions": self.icp_profile.target_regions,
            "target_roles": self.icp_profile.target_roles,
            "min_score_threshold": self.icp_profile.min_score_threshold,
            "weights": self.icp_profile.weights
        }


class ICPAnalyzer:
    """Advanced ICP analysis and insights"""
    
    def __init__(self, icp_profile: Optional[ICPProfile] = None):
        self.scorer = ICPScorer(icp_profile)
        self.score_history: List[ICPResult] = []
        
    def analyze_customer(self, customer_data: Dict) -> ICPResult:
        """
        Analyze customer against ICP
        
        Args:
            customer_data: Dictionary with customer information
            
        Returns:
            ICPResult with scoring
        """
        result = self.scorer.score_customer(
            text=customer_data.get('text', ''),
            industry=customer_data.get('industry'),
            company_size=customer_data.get('company_size'),
            revenue=customer_data.get('revenue'),
            region=customer_data.get('region'),
            role=customer_data.get('role')
        )
        
        self.score_history.append(result)
        return result
    
    def analyze_batch(self, customers: List[Dict]) -> List[ICPResult]:
        """
        Analyze multiple customers
        
        Args:
            customers: List of customer data dictionaries
            
        Returns:
            List of ICPResult
        """
        results = []
        for customer in customers:
            result = self.analyze_customer(customer)
            results.append(result)
        return results
    
    def get_icp_distribution(self) -> Dict:
        """Get distribution of ICP scores"""
        if not self.score_history:
            return {}
        
        scores = [r.overall_score for r in self.score_history]
        
        # Count by tier
        tiers = {
            "A+ (Excellent)": 0,
            "A (Very Good)": 0,
            "B+ (Good)": 0,
            "B (Average)": 0,
            "C (Below Average)": 0,
            "D (Poor)": 0
        }
        
        for score in scores:
            tier = self.scorer.get_icp_tier(score)
            if tier in tiers:
                tiers[tier] += 1
        
        # Calculate statistics
        return {
            "total_analyzed": len(scores),
            "average_score": round(sum(scores) / len(scores), 2),
            "above_threshold": sum(1 for s in scores if s >= self.scorer.icp_profile.min_score_threshold),
            "below_threshold": sum(1 for s in scores if s < self.scorer.icp_profile.min_score_threshold),
            "tier_distribution": tiers,
            "score_range": {
                "min": round(min(scores), 2),
                "max": round(max(scores), 2),
                "median": round(sorted(scores)[len(scores) // 2], 2)
            }
        }
    
    def get_top_icp_matches(self, n: int = 10) -> List[Dict]:
        """Get top N ICP matches"""
        sorted_results = sorted(
            self.score_history,
            key=lambda x: x.overall_score,
            reverse=True
        )
        
        return [
            {
                "rank": i + 1,
                "score": result.overall_score,
                "tier": self.scorer.get_icp_tier(result.overall_score),
                "industry": result.details.get('industry'),
                "company_size": result.details.get('company_size'),
                "revenue": result.details.get('revenue'),
                "matched_criteria": result.matched_criteria[:3]
            }
            for i, result in enumerate(sorted_results[:n])
        ]
    
    def get_icp_insights(self) -> Dict:
        """Get insights from ICP analysis"""
        if not self.score_history:
            return {"message": "No data available"}
        
        # Analyze patterns
        high_scoring = [r for r in self.score_history if r.overall_score >= 0.7]
        low_scoring = [r for r in self.score_history if r.overall_score < 0.5]
        
        insights = {
            "total_analyzed": len(self.score_history),
            "high_quality_leads": len(high_scoring),
            "low_quality_leads": len(low_scoring),
            "conversion_potential": round(len(high_scoring) / len(self.score_history), 2) if self.score_history else 0
        }
        
        # Common characteristics of high-scoring leads
        if high_scoring:
            common_industries = {}
            for result in high_scoring:
                industry = result.details.get('industry')
                if industry:
                    common_industries[industry] = common_industries.get(industry, 0) + 1
            
            if common_industries:
                top_industry = max(common_industries, key=common_industries.get)
                insights["top_industry"] = top_industry
                insights["industry_breakdown"] = common_industries
        
        return insights
    
    def reset(self):
        """Reset score history"""
        self.score_history = []