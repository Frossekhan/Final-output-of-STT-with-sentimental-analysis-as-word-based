"""
Enterprise Platform Integration Test
Tests the complete pipeline end-to-end
"""
import asyncio
import logging
import numpy as np
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_complete_pipeline():
    """Test the complete enterprise pipeline"""
    print("=" * 80)
    print("🏆 ENTERPRISE AI SALES INTELLIGENCE - INTEGRATION TEST")
    print("=" * 80)
    
    # Test 1: LLM Service
    print("\n[1/6] Testing LLM Service...")
    try:
        from llm.service import LLMServiceFactory
        
        llm = LLMServiceFactory.create(model_name="qwen2.5:7b")
        print("✅ LLM Service initialized")
        
        # Test BANT extraction
        test_transcript = "Hi, I'm the CFO. We have a budget of 50 lakhs for a CRM solution."
        bant = await llm.extract_bant(test_transcript)
        print(f"   Budget: {bant.budget}")
        print(f"   Authority: {bant.authority}")
        print(f"   Need: {bant.need}")
        print("✅ BANT extraction working")
    except Exception as e:
        print(f"❌ LLM Service failed: {e}")
        return False
    
    # Test 2: Conversation Memory
    print("\n[2/6] Testing Conversation Memory...")
    try:
        from memory.conversation_memory import ConversationMemoryFactory
        
        memory = ConversationMemoryFactory.create(max_history=100)
        session = memory.start_session("test-session-1", customer_id="customer-1")
        print(f"✅ Session started: {session.session_id}")
        
        # Add conversation turns
        memory.add_turn("test-session-1", "customer", "We need a CRM solution", customer_id="customer-1")
        memory.add_turn("test-session-1", "salesperson", "Great! What's your budget?", customer_id="customer-1")
        memory.add_turn("test-session-1", "customer", "Around 50 lakhs", customer_id="customer-1")
        
        # Get context
        context = memory.get_conversation_context("customer-1", n_turns=3)
        print(f"✅ Context retrieved ({len(context)} chars)")
        print(f"   Context preview: {context[:100]}...")
        
    except Exception as e:
        print(f"❌ Conversation Memory failed: {e}")
        return False
    
    # Test 3: Speaker Diarization
    print("\n[3/6] Testing Speaker Diarization...")
    try:
        from speaker.diarization import SpeakerDiarizerFactory
        
        diarizer = SpeakerDiarizerFactory.create()
        
        # Create test audio (sine wave)
        duration = 5  # seconds
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        test_audio = np.sin(2 * np.pi * 440 * t) * 0.5
        
        result = diarizer.diarize(test_audio, sample_rate)
        print(f"✅ Diarization complete")
        print(f"   Segments: {len(result.segments)}")
        print(f"   Speakers: {len(result.speaker_labels)}")
        print(f"   Turn-taking: {result.turn_taking_count}")
        
    except Exception as e:
        print(f"❌ Speaker Diarization failed: {e}")
        return False
    
    # Test 4: Emotion Recognition
    print("\n[4/6] Testing Emotion Recognition...")
    try:
        from emotion.speech_emotion import SpeechEmotionRecognizer
        
        emotion_recognizer = SpeechEmotionRecognizer()
        emotion_result = emotion_recognizer.detect_emotion(test_audio, sample_rate)
        print(f"✅ Emotion detected: {emotion_result.emotion}")
        print(f"   Confidence: {emotion_result.confidence:.2%}")
        
    except Exception as e:
        print(f"❌ Emotion Recognition failed: {e}")
        return False
    
    # Test 5: ML Lead Scoring
    print("\n[5/6] Testing ML Lead Scoring...")
    try:
        from ml.lead_scorer import MLLeadScorerFactory
        
        scorer = MLLeadScorerFactory.create()
        
        # Create test analysis
        test_analysis = {
            "bant": {
                "budget": "50 lakhs",
                "budget_amount": 5000000,
                "authority": "CFO",
                "authority_level": "decision_maker",
                "need": "CRM solution",
                "need_category": "crm",
                "timeline": "Q1 next year",
                "timeline_urgency": "short_term"
            },
            "intent": {
                "intent": "purchase",
                "confidence": 0.9,
                "all_intents": {"purchase": 0.9, "pricing": 0.3}
            },
            "buying_signals": {
                "signals": [
                    {"type": "budget_confirmation", "strength": 0.95},
                    {"type": "decision_maker_engagement", "strength": 0.9}
                ],
                "readiness_score": 0.88,
                "readiness": "READY_TO_BUY"
            },
            "objections": {
                "objections": [],
                "severity": "low"
            },
            "emotion": {
                "emotion": "confident",
                "confidence": 0.85,
                "all_scores": {
                    "confident": 0.85,
                    "interested": 0.10,
                    "neutral": 0.05
                }
            },
            "summary": {
                "opportunity_score": 0.8
            },
            "conversation_metrics": {
                "speaking_duration": 300,
                "turn_taking_count": 6,
                "question_count": 3,
                "words_per_minute": 120
            },
            "icp_score": 0.85
        }
        
        lead_score = scorer.predict(test_analysis)
        print(f"✅ Lead Score: {lead_score.score:.2%} - {lead_score.qualification}")
        print(f"   Confidence: {lead_score.confidence:.2%}")
        print(f"   Probability: {lead_score.probability:.2%}")
        
    except Exception as e:
        print(f"❌ ML Lead Scoring failed: {e}")
        return False
    
    # Test 6: Confidence Engine
    print("\n[6/6] Testing Confidence Engine...")
    try:
        from confidence.confidence_engine import ConfidenceEngineFactory
        
        conf_engine = ConfidenceEngineFactory.create()
        confidences = conf_engine.calculate_all_confidences(test_analysis)
        
        print(f"✅ Confidence scores calculated")
        print(f"   BANT: {confidences['bant']['overall']:.2%} ({confidences['bant']['level']})")
        print(f"   Intent: {confidences['intent']['primary_confidence']:.2%} ({confidences['intent']['level']})")
        print(f"   Lead Score: {confidences['lead_score']['overall_confidence']:.2%} ({confidences['lead_score']['level']})")
        
    except Exception as e:
        print(f"❌ Confidence Engine failed: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - ENTERPRISE PLATFORM READY")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Install Ollama: https://ollama.ai")
    print("2. Pull model: ollama pull qwen2.5:7b")
    print("3. Start server: python server_enterprise.py")
    print("4. Start client: python client.py")
    print("\nFor production:")
    print("- Install PostgreSQL")
    print("- Train ML models on real data")
    print("- Add CRM integration")
    print("- Deploy with Docker")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_complete_pipeline())
    exit(0 if success else 1)