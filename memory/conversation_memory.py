"""
Conversation Memory System
Maintains context, customer profile, and conversation history
"""
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class CustomerProfile:
    """Customer profile information"""
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    revenue_range: Optional[str] = None
    region: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # BANT information
    budget: Optional[str] = None
    budget_amount: Optional[float] = None
    authority_level: Optional[str] = None
    need_category: Optional[str] = None
    timeline: Optional[str] = None
    
    # Preferences and history
    preferred_contact_method: Optional[str] = None
    previous_interactions: int = 0
    last_interaction: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "company": self.company,
            "role": self.role,
            "industry": self.industry,
            "company_size": self.company_size,
            "revenue_range": self.revenue_range,
            "region": self.region,
            "email": self.email,
            "phone": self.phone,
            "budget": self.budget,
            "budget_amount": self.budget_amount,
            "authority_level": self.authority_level,
            "need_category": self.need_category,
            "timeline": self.timeline,
            "preferred_contact_method": self.preferred_contact_method,
            "previous_interactions": self.previous_interactions,
            "last_interaction": self.last_interaction
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CustomerProfile':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ConversationTurn:
    """Single conversation turn"""
    speaker: str  # "customer" or "salesperson"
    text: str
    timestamp: str
    emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None
    intent: Optional[str] = None
    buying_signals: List[str] = field(default_factory=list)
    objections: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "speaker": self.speaker,
            "text": self.text,
            "timestamp": self.timestamp,
            "emotion": self.emotion,
            "emotion_confidence": self.emotion_confidence,
            "intent": self.intent,
            "buying_signals": self.buying_signals,
            "objections": self.objections
        }


@dataclass
class ConversationSession:
    """Complete conversation session"""
    session_id: str
    started_at: str
    ended_at: Optional[str] = None
    turns: List[ConversationTurn] = field(default_factory=list)
    summary: Optional[str] = None
    lead_score: Optional[float] = None
    qualification: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "turns": [turn.to_dict() for turn in self.turns],
            "summary": self.summary,
            "lead_score": self.lead_score,
            "qualification": self.qualification
        }


class ConversationMemory:
    """
    Conversation memory system
    
    Maintains:
    - Customer profile (persistent across sessions)
    - Conversation history (current session)
    - Context for LLM analysis
    - Key insights and preferences
    """
    
    def __init__(self, max_history: int = 100):
        """
        Initialize conversation memory
        
        Args:
            max_history: Maximum number of conversation turns to keep
        """
        self.max_history = max_history
        
        # Customer profiles (persistent)
        self.customer_profiles: Dict[str, CustomerProfile] = {}
        
        # Active conversation sessions
        self.active_sessions: Dict[str, ConversationSession] = {}
        
        # Conversation history per customer
        self.customer_history: Dict[str, deque] = {}
        
        # Key insights extracted from conversations
        self.key_insights: Dict[str, List[str]] = {}
        
        # Objection history
        self.objection_history: Dict[str, List[Dict]] = {}
        
        # Buying signal history
        self.buying_signal_history: Dict[str, List[Dict]] = {}
    
    def start_session(self, session_id: str, customer_id: Optional[str] = None) -> ConversationSession:
        """
        Start a new conversation session
        
        Args:
            session_id: Unique session identifier
            customer_id: Customer identifier (optional)
            
        Returns:
            ConversationSession object
        """
        session = ConversationSession(
            session_id=session_id,
            started_at=datetime.now().isoformat()
        )
        
        self.active_sessions[session_id] = session
        
        # Initialize customer history if needed
        if customer_id and customer_id not in self.customer_history:
            self.customer_history[customer_id] = deque(maxlen=self.max_history)
            self.key_insights[customer_id] = []
            self.objection_history[customer_id] = []
            self.buying_signal_history[customer_id] = []
        
        logger.info(f"Started session: {session_id} for customer: {customer_id}")
        return session
    
    def end_session(self, session_id: str):
        """
        End a conversation session
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.ended_at = datetime.now().isoformat()
            logger.info(f"Ended session: {session_id}")
    
    def add_turn(
        self,
        session_id: str,
        speaker: str,
        text: str,
        customer_id: Optional[str] = None,
        **kwargs
    ):
        """
        Add a conversation turn
        
        Args:
            session_id: Session identifier
            speaker: "customer" or "salesperson"
            text: Conversation text
            customer_id: Customer identifier (optional)
            **kwargs: Additional metadata (emotion, intent, etc.)
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return
        
        turn = ConversationTurn(
            speaker=speaker,
            text=text,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )
        
        session = self.active_sessions[session_id]
        session.turns.append(turn)
        
        # Add to customer history
        if customer_id:
            if customer_id not in self.customer_history:
                self.customer_history[customer_id] = deque(maxlen=self.max_history)
            
            self.customer_history[customer_id].append(turn)
            
            # Update customer profile
            self._update_customer_profile(customer_id, turn)
    
    def _update_customer_profile(self, customer_id: str, turn: ConversationTurn):
        """
        Update customer profile from conversation turn
        
        Args:
            customer_id: Customer identifier
            turn: Conversation turn
        """
        if customer_id not in self.customer_profiles:
            self.customer_profiles[customer_id] = CustomerProfile()
        
        profile = self.customer_profiles[customer_id]
        
        # Extract information from text (simple keyword matching)
        text_lower = turn.text.lower()
        
        # Extract role
        roles = ['ceo', 'cto', 'cfo', 'director', 'vp', 'manager', 'founder', 'owner']
        for role in roles:
            if role in text_lower and not profile.role:
                profile.role = role
                break
        
        # Extract company indicators
        if 'company' in text_lower or 'organization' in text_lower or 'firm' in text_lower:
            # Simple extraction - can be enhanced with LLM
            words = text_lower.split()
            for i, word in enumerate(words):
                if word in ['company', 'organization', 'firm'] and i > 0:
                    profile.company = words[i-1]
                    break
        
        # Update last interaction
        profile.last_interaction = turn.timestamp
        profile.previous_interactions += 1
    
    def get_customer_profile(self, customer_id: str) -> Optional[CustomerProfile]:
        """
        Get customer profile
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            CustomerProfile or None
        """
        return self.customer_profiles.get(customer_id)
    
    def update_customer_profile(self, customer_id: str, **kwargs):
        """
        Update customer profile
        
        Args:
            customer_id: Customer identifier
            **kwargs: Fields to update
        """
        if customer_id not in self.customer_profiles:
            self.customer_profiles[customer_id] = CustomerProfile()
        
        profile = self.customer_profiles[customer_id]
        
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
    
    def get_conversation_context(self, customer_id: str, n_turns: int = 10) -> str:
        """
        Get recent conversation context for LLM
        
        Args:
            customer_id: Customer identifier
            n_turns: Number of recent turns to include
            
        Returns:
            Formatted conversation context string
        """
        if customer_id not in self.customer_history:
            return ""
        
        history = list(self.customer_history[customer_id])[-n_turns:]
        
        context_parts = []
        for turn in history:
            speaker_name = "Customer" if turn.speaker == "customer" else "Salesperson"
            context_parts.append(f"{speaker_name}: {turn.text}")
        
        return "\n".join(context_parts)
    
    def get_full_context(self, session_id: str) -> str:
        """
        Get full conversation context for current session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Formatted conversation context
        """
        if session_id not in self.active_sessions:
            return ""
        
        session = self.active_sessions[session_id]
        context_parts = []
        
        for turn in session.turns:
            speaker_name = "Customer" if turn.speaker == "customer" else "Salesperson"
            context_parts.append(f"{speaker_name}: {turn.text}")
        
        return "\n".join(context_parts)
    
    def add_key_insight(self, customer_id: str, insight: str):
        """
        Add key insight for customer
        
        Args:
            customer_id: Customer identifier
            insight: Insight text
        """
        if customer_id not in self.key_insights:
            self.key_insights[customer_id] = []
        
        self.key_insights[customer_id].append(insight)
        
        # Keep only recent insights
        if len(self.key_insights[customer_id]) > 20:
            self.key_insights[customer_id] = self.key_insights[customer_id][-20:]
    
    def get_key_insights(self, customer_id: str, n: int = 10) -> List[str]:
        """
        Get recent key insights
        
        Args:
            customer_id: Customer identifier
            n: Number of insights to return
            
        Returns:
            List of insights
        """
        if customer_id not in self.key_insights:
            return []
        
        return self.key_insights[customer_id][-n:]
    
    def add_objection(self, customer_id: str, objection: Dict):
        """
        Add objection to history
        
        Args:
            customer_id: Customer identifier
            objection: Objection dictionary
        """
        if customer_id not in self.objection_history:
            self.objection_history[customer_id] = []
        
        objection["timestamp"] = datetime.now().isoformat()
        self.objection_history[customer_id].append(objection)
    
    def get_objection_history(self, customer_id: str) -> List[Dict]:
        """
        Get objection history for customer
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of objections
        """
        return self.objection_history.get(customer_id, [])
    
    def add_buying_signal(self, customer_id: str, signal: Dict):
        """
        Add buying signal to history
        
        Args:
            customer_id: Customer identifier
            signal: Signal dictionary
        """
        if customer_id not in self.buying_signal_history:
            self.buying_signal_history[customer_id] = []
        
        signal["timestamp"] = datetime.now().isoformat()
        self.buying_signal_history[customer_id].append(signal)
    
    def get_buying_signal_history(self, customer_id: str) -> List[Dict]:
        """
        Get buying signal history for customer
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of buying signals
        """
        return self.buying_signal_history.get(customer_id, [])
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """
        Get session summary
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session summary dictionary
        """
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        # Calculate metrics
        customer_turns = sum(1 for t in session.turns if t.speaker == "customer")
        salesperson_turns = sum(1 for t in session.turns if t.speaker == "salesperson")
        
        return {
            "session_id": session_id,
            "duration": self._calculate_duration(session.started_at, session.ended_at),
            "total_turns": len(session.turns),
            "customer_turns": customer_turns,
            "salesperson_turns": salesperson_turns,
            "summary": session.summary,
            "lead_score": session.lead_score,
            "qualification": session.qualification
        }
    
    def _calculate_duration(self, start: str, end: Optional[str]) -> str:
        """Calculate duration between timestamps"""
        try:
            start_time = datetime.fromisoformat(start)
            end_time = datetime.fromisoformat(end) if end else datetime.now()
            duration = end_time - start_time
            
            minutes = int(duration.total_seconds() / 60)
            seconds = int(duration.total_seconds() % 60)
            
            return f"{minutes}m {seconds}s"
        except:
            return "unknown"
    
    def get_customer_journey(self, customer_id: str) -> Dict:
        """
        Get complete customer journey
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Customer journey dictionary
        """
        profile = self.get_customer_profile(customer_id)
        history = list(self.customer_history.get(customer_id, []))
        insights = self.get_key_insights(customer_id)
        objections = self.get_objection_history(customer_id)
        signals = self.get_buying_signal_history(customer_id)
        
        return {
            "profile": profile.to_dict() if profile else None,
            "total_interactions": len(history),
            "recent_insights": insights,
            "total_objections": len(objections),
            "critical_objections": sum(1 for o in objections if o.get("severity") == "critical"),
            "total_buying_signals": len(signals),
            "strong_signals": sum(1 for s in signals if s.get("strength", 0) >= 0.7),
            "conversation_history": [turn.to_dict() for turn in history[-20:]]
        }
    
    def reset_session(self, session_id: str):
        """
        Reset a session
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Reset session: {session_id}")
    
    def reset_customer(self, customer_id: str):
        """
        Reset all data for a customer
        
        Args:
            customer_id: Customer identifier
        """
        if customer_id in self.customer_profiles:
            del self.customer_profiles[customer_id]
        if customer_id in self.customer_history:
            del self.customer_history[customer_id]
        if customer_id in self.key_insights:
            del self.key_insights[customer_id]
        if customer_id in self.objection_history:
            del self.objection_history[customer_id]
        if customer_id in self.buying_signal_history:
            del self.buying_signal_history[customer_id]
        
        logger.info(f"Reset customer: {customer_id}")
    
    def export_to_dict(self) -> Dict:
        """
        Export all memory data to dictionary
        
        Returns:
            Dictionary with all memory data
        """
        return {
            "customer_profiles": {
                cid: profile.to_dict() 
                for cid, profile in self.customer_profiles.items()
            },
            "active_sessions": {
                sid: session.to_dict() 
                for sid, session in self.active_sessions.items()
            },
            "key_insights": dict(self.key_insights),
            "exported_at": datetime.now().isoformat()
        }
    
    def import_from_dict(self, data: Dict):
        """
        Import memory data from dictionary
        
        Args:
            data: Dictionary with memory data
        """
        # Import customer profiles
        if "customer_profiles" in data:
            for cid, profile_data in data["customer_profiles"].items():
                self.customer_profiles[cid] = CustomerProfile.from_dict(profile_data)
        
        # Import key insights
        if "key_insights" in data:
            self.key_insights = data["key_insights"]
        
        logger.info(f"Imported {len(self.customer_profiles)} customer profiles")


class ConversationMemoryFactory:
    """Factory for creating conversation memory instances"""
    
    @staticmethod
    def create(max_history: int = 100) -> ConversationMemory:
        """
        Create conversation memory instance
        
        Args:
            max_history: Maximum history size
            
        Returns:
            ConversationMemory instance
        """
        return ConversationMemory(max_history=max_history)