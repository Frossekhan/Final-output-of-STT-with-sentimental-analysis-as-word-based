"""
LLM Service for Enterprise AI Sales Conversation Intelligence
Uses Qwen 2.5 or Llama 3.1 for advanced conversation understanding
"""
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BANTExtraction:
    """BANT information extracted by LLM"""
    budget: Optional[str]
    budget_amount: Optional[float]
    budget_currency: str
    authority: Optional[str]
    authority_level: str
    need: Optional[str]
    need_category: str
    timeline: Optional[str]
    timeline_urgency: str
    confidence: float
    raw_evidence: List[str]


@dataclass
class IntentClassification:
    """Intent classification by LLM"""
    intent: str
    confidence: float
    all_intents: Dict[str, float]
    context: str
    reasoning: str


@dataclass
class BuyingSignalDetection:
    """Buying signal detection by LLM"""
    signals: List[Dict[str, Any]]
    overall_readiness: str
    readiness_score: float
    reasoning: str


@dataclass
class ObjectionDetection:
    """Objection detection by LLM"""
    objections: List[Dict[str, Any]]
    severity: str
    handling_priority: List[str]
    reasoning: str


@dataclass
class ConversationSummary:
    """Conversation summary by LLM"""
    summary: str
    key_points: List[str]
    customer_concerns: List[str]
    next_actions: List[str]
    risk_factors: List[str]
    opportunity_score: float


class LLMService:
    """
    LLM-powered conversation intelligence service
    
    Uses Qwen 2.5 or Llama 3.1 for:
    - BANT extraction
    - Intent detection
    - Buying signal recognition
    - Objection classification
    - Summary generation
    """
    
    def __init__(self, model_name: str = "qwen2.5:7b", use_local: bool = True):
        """
        Initialize LLM service
        
        Args:
            model_name: Model to use (qwen2.5:7b, llama3.1:8b, etc.)
            use_local: Use local Ollama instance or API
        """
        self.model_name = model_name
        self.use_local = use_local
        self.conversation_history: List[Dict] = []
        self.max_history = 20  # Keep last 20 exchanges
        
        # Try to import ollama
        try:
            import ollama
            self.ollama = ollama
            self.ollama_available = True
            logger.info(f"Ollama initialized with model: {model_name}")
        except ImportError:
            self.ollama_available = False
            logger.warning("Ollama not available. Install with: pip install ollama")
        
        # Conversation memory
        self.customer_profile: Dict = {}
        self.conversation_context: List[str] = []
    
    async def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """
        Call LLM with prompt
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            
        Returns:
            LLM response text
        """
        if not self.ollama_available:
            return json.dumps({"error": "LLM not available"})
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add conversation history for context
            for msg in self.conversation_history[-10:]:  # Last 10 exchanges
                messages.append(msg)
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Call Ollama
            response = await asyncio.to_thread(
                self.ollama.chat,
                model=self.model_name,
                messages=messages,
                stream=False
            )
            
            return response['message']['content']
        
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return json.dumps({"error": str(e)})
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        try:
            # Try to find JSON in the response
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
            
            return {"error": "No JSON found in response"}
        
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in response", "raw": text}
    
    async def extract_bant(self, transcript: str) -> BANTExtraction:
        """
        Extract BANT information using LLM
        
        Args:
            transcript: Conversation transcript
            
        Returns:
            BANTExtraction with all BANT fields
        """
        system_prompt = """You are a sales intelligence expert. Extract BANT (Budget, Authority, Need, Timeline) information from the conversation.
        
Return JSON with this exact structure:
{
    "budget": "budget information or null",
    "budget_amount": numeric_amount_or_null,
    "budget_currency": "INR/USD/etc",
    "authority": "decision maker role or null",
    "authority_level": "decision_maker/influencer/reporter/unknown",
    "need": "customer need description or null",
    "need_category": "crm/erp/analytics/etc",
    "timeline": "timeline information or null",
    "timeline_urgency": "immediate/short_term/medium_term/long_term/not_mentioned",
    "confidence": 0.0-1.0,
    "raw_evidence": ["list of quotes from transcript"]
}

Be precise and only extract information explicitly mentioned or strongly implied."""

        prompt = f"""Extract BANT information from this sales conversation:

{transcript}

Return only valid JSON, no other text."""

        response = await self._call_llm(prompt, system_prompt)
        result = self._extract_json(response)
        
        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Trim history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
        
        return BANTExtraction(
            budget=result.get("budget"),
            budget_amount=result.get("budget_amount"),
            budget_currency=result.get("budget_currency", "INR"),
            authority=result.get("authority"),
            authority_level=result.get("authority_level", "unknown"),
            need=result.get("need"),
            need_category=result.get("need_category", "general"),
            timeline=result.get("timeline"),
            timeline_urgency=result.get("timeline_urgency", "not_mentioned"),
            confidence=result.get("confidence", 0.0),
            raw_evidence=result.get("raw_evidence", [])
        )
    
    async def detect_intent(self, transcript: str, context: str = "") -> IntentClassification:
        """
        Detect customer intent using LLM
        
        Args:
            transcript: Current conversation text
            context: Previous conversation context
            
        Returns:
            IntentClassification with intent and confidence
        """
        system_prompt = """You are a sales conversation analyst. Classify the customer's intent from the conversation.

Possible intents:
- pricing: Customer is asking about price, cost, or pricing models
- demo: Customer wants to see a demonstration or trial
- purchase: Customer is ready to buy or proceed
- negotiation: Customer wants to negotiate terms or pricing
- support: Customer needs help or has issues
- cancellation: Customer wants to cancel or terminate
- renewal: Customer wants to renew subscription
- information: Customer is gathering information
- objection: Customer has concerns or objections
- competitor: Customer is comparing with competitors

Return JSON:
{
    "intent": "primary_intent",
    "confidence": 0.0-1.0,
    "all_intents": {"intent1": 0.8, "intent2": 0.3, ...},
    "reasoning": "explanation of why this intent was detected"
}"""

        prompt = f"""Context: {context}

Current conversation:
{transcript}

Classify the customer's intent. Return only valid JSON."""

        response = await self._call_llm(prompt, system_prompt)
        result = self._extract_json(response)
        
        return IntentClassification(
            intent=result.get("intent", "information"),
            confidence=result.get("confidence", 0.0),
            all_intents=result.get("all_intents", {}),
            context=context,
            reasoning=result.get("reasoning", "")
        )
    
    async def detect_buying_signals(self, transcript: str) -> BuyingSignalDetection:
        """
        Detect buying signals using LLM
        
        Args:
            transcript: Conversation transcript
            
        Returns:
            BuyingSignalDetection with signals and readiness
        """
        system_prompt = """You are a sales expert. Identify buying signals in the conversation.

Buying signals indicate purchase intent:
- request_quotation: Asking for quote/proposal
- request_demo: Wanting to see demo
- discuss_contract: Discussing contract terms
- discuss_payment: Talking about payment
- discuss_timeline: Discussing implementation timeline
- request_meeting: Scheduling meetings
- request_reference: Asking for references/case studies
- discuss_features: Deep feature discussions
- commitment_language: Expressing commitment
- urgency_indicators: Showing urgency
- budget_confirmation: Confirming budget availability
- decision_maker_engagement: Decision maker involvement

Return JSON:
{
    "signals": [
        {
            "type": "signal_type",
            "strength": 0.0-1.0,
            "evidence": "quote from transcript",
            "recommendation": "what to do next"
        }
    ],
    "overall_readiness": "READY_TO_BUY/HIGH_INTENT/MEDIUM_INTENT/LOW_INTENT/NOT_READY",
    "readiness_score": 0.0-1.0,
    "reasoning": "explanation"
}"""

        prompt = f"""Identify buying signals in this conversation:

{transcript}

Return only valid JSON."""

        response = await self._call_llm(prompt, system_prompt)
        result = self._extract_json(response)
        
        return BuyingSignalDetection(
            signals=result.get("signals", []),
            overall_readiness=result.get("overall_readiness", "NOT_READY"),
            readiness_score=result.get("readiness_score", 0.0),
            reasoning=result.get("reasoning", "")
        )
    
    async def detect_objections(self, transcript: str) -> ObjectionDetection:
        """
        Detect objections using LLM
        
        Args:
            transcript: Conversation transcript
            
        Returns:
            ObjectionDetection with objections and handling priority
        """
        system_prompt = """You are a sales expert. Identify objections in the conversation.

Objection types:
- price: Concern about cost/price
- budget: Budget constraints
- authority: Decision-making authority issues
- need: Don't see the need
- timing: Bad timing
- competitor: Comparing with competitors
- trust: Trust/reliability concerns
- features: Missing features or limitations
- support: Support/service concerns
- implementation: Implementation concerns
- risk: Risk/uncertainty concerns
- generic: Other concerns

Return JSON:
{
    "objections": [
        {
            "type": "objection_type",
            "severity": "critical/high/medium/low",
            "confidence": 0.0-1.0,
            "evidence": "quote from transcript",
            "suggested_response": "how to handle this objection"
        }
    ],
    "severity": "overall severity",
    "handling_priority": ["priority actions"],
    "reasoning": "explanation"
}"""

        prompt = f"""Identify objections in this conversation:

{transcript}

Return only valid JSON."""

        response = await self._call_llm(prompt, system_prompt)
        result = self._extract_json(response)
        
        return ObjectionDetection(
            objections=result.get("objections", []),
            severity=result.get("severity", "low"),
            handling_priority=result.get("handling_priority", []),
            reasoning=result.get("reasoning", "")
        )
    
    async def generate_summary(self, transcript: str, analysis: Dict) -> ConversationSummary:
        """
        Generate conversation summary using LLM
        
        Args:
            transcript: Full conversation transcript
            analysis: Complete analysis (BANT, intent, signals, objections)
            
        Returns:
            ConversationSummary with insights
        """
        system_prompt = """You are a sales intelligence analyst. Generate a comprehensive summary of the sales conversation.

Return JSON:
{
    "summary": "2-3 sentence summary of the conversation",
    "key_points": ["important point 1", "important point 2", ...],
    "customer_concerns": ["concern 1", "concern 2", ...],
    "next_actions": ["action 1", "action 2", ...],
    "risk_factors": ["risk 1", "risk 2", ...],
    "opportunity_score": 0.0-1.0
}"""

        prompt = f"""Generate a summary for this sales conversation:

Transcript:
{transcript}

Analysis:
{json.dumps(analysis, indent=2)}

Return only valid JSON."""

        response = await self._call_llm(prompt, system_prompt)
        result = self._extract_json(response)
        
        return ConversationSummary(
            summary=result.get("summary", ""),
            key_points=result.get("key_points", []),
            customer_concerns=result.get("customer_concerns", []),
            next_actions=result.get("next_actions", []),
            risk_factors=result.get("risk_factors", []),
            opportunity_score=result.get("opportunity_score", 0.0)
        )
    
    async def analyze_conversation_complete(self, transcript: str) -> Dict[str, Any]:
        """
        Complete conversation analysis using LLM
        
        Args:
            transcript: Conversation transcript
            
        Returns:
            Complete analysis dictionary
        """
        # Run all analyses in parallel
        bant_task = self.extract_bant(transcript)
        intent_task = self.detect_intent(transcript, " ".join(self.conversation_context))
        signals_task = self.detect_buying_signals(transcript)
        objections_task = self.detect_objections(transcript)
        
        # Wait for all to complete
        bant, intent, signals, objections = await asyncio.gather(
            bant_task, intent_task, signals_task, objections_task
        )
        
        # Add to context
        self.conversation_context.append(transcript)
        if len(self.conversation_context) > 10:
            self.conversation_context = self.conversation_context[-10:]
        
        # Compile analysis
        analysis = {
            "bant": {
                "budget": bant.budget,
                "budget_amount": bant.budget_amount,
                "budget_currency": bant.budget_currency,
                "authority": bant.authority,
                "authority_level": bant.authority_level,
                "need": bant.need,
                "need_category": bant.need_category,
                "timeline": bant.timeline,
                "timeline_urgency": bant.timeline_urgency,
                "confidence": bant.confidence,
                "evidence": bant.raw_evidence
            },
            "intent": {
                "intent": intent.intent,
                "confidence": intent.confidence,
                "all_intents": intent.all_intents,
                "reasoning": intent.reasoning
            },
            "buying_signals": {
                "signals": signals.signals,
                "readiness": signals.overall_readiness,
                "readiness_score": signals.readiness_score,
                "reasoning": signals.reasoning
            },
            "objections": {
                "objections": objections.objections,
                "severity": objections.severity,
                "handling_priority": objections.handling_priority,
                "reasoning": objections.reasoning
            },
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Generate summary
        summary = await self.generate_summary(transcript, analysis)
        analysis["summary"] = {
            "summary": summary.summary,
            "key_points": summary.key_points,
            "customer_concerns": summary.customer_concerns,
            "next_actions": summary.next_actions,
            "risk_factors": summary.risk_factors,
            "opportunity_score": summary.opportunity_score
        }
        
        return analysis
    
    def reset(self):
        """Reset conversation history and context"""
        self.conversation_history = []
        self.conversation_context = []
        self.customer_profile = {}


class LLMServiceFactory:
    """Factory for creating LLM service instances"""
    
    @staticmethod
    def create(model_name: str = "qwen2.5:7b", **kwargs) -> LLMService:
        """
        Create LLM service instance
        
        Args:
            model_name: Model to use
            **kwargs: Additional arguments
            
        Returns:
            LLMService instance
        """
        return LLMService(model_name=model_name, **kwargs)
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Get list of available models"""
        return [
            "qwen2.5:7b",      # Qwen 2.5 7B (recommended)
            "qwen2.5:14b",     # Qwen 2.5 14B (better quality)
            "llama3.1:8b",     # Llama 3.1 8B
            "llama3.1:70b",    # Llama 3.1 70B (best quality)
            "mistral:7b",      # Mistral 7B
            "gemma2:9b"        # Gemma 2 9B
        ]