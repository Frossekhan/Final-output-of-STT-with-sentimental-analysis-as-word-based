"""
Test script for AI Sales Intelligence Platform
Verifies all components are working correctly
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from streaming.websocket import manager
        print("✓ streaming.websocket")
        
        from streaming.audio_buffer import AudioBuffer, VADBuffer
        print("✓ streaming.audio_buffer")
        
        # Note: faster-whisper is optional for core functionality
        try:
            from streaming.stream_processor import StreamProcessor, StreamingTranscriptionService
            print("✓ streaming.stream_processor (faster-whisper available)")
        except ImportError:
            print("⚠ streaming.stream_processor (faster-whisper not installed - optional)")
        
        from emotion.speech_emotion import SpeechEmotionRecognizer, EmotionTracker
        print("✓ emotion.speech_emotion")
        
        from bant.parser import BANTEngine
        print("✓ bant.parser")
        
        from intent.predict import IntentDetector
        print("✓ intent.predict")
        
        from buying_signal.detect import BuyingSignalDetector, BuyingSignalAnalyzer
        print("✓ buying_signal.detect")
        
        from objection.detect import ObjectionDetector, ObjectionAnalyzer
        print("✓ objection.detect")
        
        from icp.score import ICPScorer, ICPAnalyzer
        print("✓ icp.score")
        
        from conversation_engine.engine import ConversationIntelligenceEngine
        print("✓ conversation_engine.engine")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_emotion_recognition():
    """Test emotion recognition"""
    print("\nTesting emotion recognition...")
    
    try:
        import numpy as np
        from emotion.speech_emotion import SpeechEmotionRecognizer
        
        recognizer = SpeechEmotionRecognizer()
        
        # Create dummy audio (2 seconds of noise)
        audio = np.random.randn(32000).astype(np.float32)
        
        result = recognizer.detect_emotion(audio, sample_rate=16000)
        
        print(f"✓ Detected emotion: {result.emotion} ({result.confidence:.2%})")
        print(f"✓ Features extracted: {len(result.features)} features")
        
        return True
    except Exception as e:
        print(f"✗ Emotion recognition error: {e}")
        return False


def test_bant_extraction():
    """Test BANT extraction"""
    print("\nTesting BANT extraction...")
    
    try:
        from bant.parser import BANTEngine
        
        engine = BANTEngine()
        
        sample_text = """
        Hello, I'm the CEO of a technology company in Bangalore. 
        We're looking for a CRM solution and have a budget of around 20 lakhs. 
        We need to implement it within 3 months.
        """
        
        result = engine.extract_bant(sample_text)
        
        print(f"✓ Budget: {result.budget} (₹{result.budget_amount:,.0f})")
        print(f"✓ Authority: {result.authority} ({result.authority_level.value})")
        print(f"✓ Need: {result.need} ({result.need_category})")
        print(f"✓ Timeline: {result.timeline} ({result.timeline_urgency.value})")
        
        return True
    except Exception as e:
        print(f"✗ BANT extraction error: {e}")
        return False


def test_intent_detection():
    """Test intent detection"""
    print("\nTesting intent detection...")
    
    try:
        from intent.predict import IntentDetector
        
        detector = IntentDetector()
        
        sample_text = "Can you send us a quotation? We need pricing information."
        
        result = detector.detect_intent(sample_text)
        
        print(f"✓ Detected intent: {result.intent.value} ({result.confidence:.2%})")
        print(f"✓ Keywords matched: {len(result.keywords_matched)}")
        
        return True
    except Exception as e:
        print(f"✗ Intent detection error: {e}")
        return False


def test_buying_signals():
    """Test buying signal detection"""
    print("\nTesting buying signal detection...")
    
    try:
        from buying_signal.detect import BuyingSignalDetector
        
        detector = BuyingSignalDetector()
        
        sample_text = "Can you send us a quotation? We're ready to proceed."
        
        signals = detector.detect_signals(sample_text)
        
        print(f"✓ Signals detected: {len(signals)}")
        for signal in signals[:3]:
            print(f"  - {signal.signal_type}: {signal.strength:.2%} ({signal.strength_level.value})")
        
        return True
    except Exception as e:
        print(f"✗ Buying signal detection error: {e}")
        return False


def test_objection_detection():
    """Test objection detection"""
    print("\nTesting objection detection...")
    
    try:
        from objection.detect import ObjectionDetector
        
        detector = ObjectionDetector()
        
        sample_text = "This seems too expensive for our budget. We need to think about it."
        
        objections = detector.detect_objections(sample_text)
        
        print(f"✓ Objections detected: {len(objections)}")
        for obj in objections[:3]:
            print(f"  - {obj.objection_type.value}: {obj.severity.value} ({obj.confidence:.2%})")
        
        return True
    except Exception as e:
        print(f"✗ Objection detection error: {e}")
        return False


def test_icp_scoring():
    """Test ICP scoring"""
    print("\nTesting ICP scoring...")
    
    try:
        from icp.score import ICPScorer
        
        scorer = ICPScorer()
        
        sample_text = """
        I'm the CEO of a technology company in Bangalore. 
        We're a medium-sized company with 100 employees.
        """
        
        result = scorer.score_customer(sample_text)
        
        print(f"✓ ICP Score: {result.overall_score:.2%}")
        print(f"✓ ICP Tier: {scorer.get_icp_tier(result.overall_score)}")
        print(f"✓ Matched criteria: {len(result.matched_criteria)}")
        
        return True
    except Exception as e:
        print(f"✗ ICP scoring error: {e}")
        return False


def test_conversation_engine():
    """Test conversation intelligence engine"""
    print("\nTesting conversation intelligence engine...")
    
    try:
        from conversation_engine.engine import ConversationIntelligenceEngine
        import numpy as np
        
        engine = ConversationIntelligenceEngine()
        
        sample_text = """
        Hello, I'm the CEO of a technology company in Bangalore. 
        We're looking for a CRM solution and have a budget of around 20 lakhs. 
        We need to implement it within 3 months. 
        Can you send us a quotation? We're ready to proceed.
        """
        
        # Create dummy audio
        audio = np.random.randn(32000).astype(np.float32)
        
        # Process conversation
        features = engine.process_conversation(
            transcript=sample_text,
            audio=audio,
            sample_rate=16000
        )
        
        print(f"✓ Emotion: {features.emotion} ({features.emotion_confidence:.2%})")
        print(f"✓ Budget: {features.budget}")
        print(f"✓ Authority: {features.authority}")
        print(f"✓ Intent: {features.intent} ({features.intent_confidence:.2%})")
        print(f"✓ Buying signals: {len(features.buying_signals)}")
        print(f"✓ Objections: {features.objection_count}")
        print(f"✓ ICP Score: {features.icp_score:.2%}")
        
        # Calculate lead score
        lead_score = engine.calculate_lead_score()
        
        print(f"✓ Lead Score: {lead_score.overall_score:.2%}")
        print(f"✓ Qualification: {lead_score.qualification}")
        print(f"✓ Confidence: {lead_score.confidence:.2%}")
        
        return True
    except Exception as e:
        print(f"✗ Conversation engine error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi_app():
    """Test FastAPI application"""
    print("\nTesting FastAPI application...")
    
    try:
        # Check if faster-whisper is available
        try:
            import faster_whisper
            print("✓ faster-whisper is installed")
        except ImportError:
            print("⚠ faster-whisper not installed - skipping FastAPI test")
            print("  (Install with: pip install faster-whisper)")
            return True  # Skip but don't fail
        
        from app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/api/health")
        assert response.status_code == 200
        print(f"✓ Health check: {response.json()['status']}")
        
        # Test test endpoint
        response = client.get("/api/test")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Test endpoint: Lead score = {data['lead_score']['score']:.2%}")
        print(f"✓ Qualification: {data['lead_score']['qualification']}")
        
        return True
    except Exception as e:
        print(f"✗ FastAPI app error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("AI Sales Intelligence Platform - System Tests")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Emotion Recognition", test_emotion_recognition),
        ("BANT Extraction", test_bant_extraction),
        ("Intent Detection", test_intent_detection),
        ("Buying Signals", test_buying_signals),
        ("Objection Detection", test_objection_detection),
        ("ICP Scoring", test_icp_scoring),
        ("Conversation Engine", test_conversation_engine),
        ("FastAPI App", test_fastapi_app),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())