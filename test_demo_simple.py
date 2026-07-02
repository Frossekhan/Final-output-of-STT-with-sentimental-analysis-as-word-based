"""
Simple test to show formatted output
No emojis to avoid Windows encoding issues
"""
import sys
from conversation_engine.engine import ConversationIntelligenceEngine
from lead_scoring import LeadScorer
from output_formatter import OutputFormatter

# Test transcript
test_transcript = "Hello, I'm the CEO of a technology company. We need a CRM solution with a budget of 25 lakhs and want to implement it in 3 months. Can you send us a quote?"

print("\nSales Intelligence Platform - Analysis Demo")
print("=" * 66)
print("\nAnalyzing conversation...")

try:
    # Initialize components
    engine = ConversationIntelligenceEngine()
    lead_scorer = LeadScorer()
    
    # Process conversation
    features = engine.process_conversation(test_transcript)
    
    # Score the lead
    lead_score_result = lead_scorer.score({
        "transcript": features.transcript,
        "emotion": features.emotion,
        "emotion_confidence": features.emotion_confidence,
        "emotion_scores": features.emotion_scores,
        "budget_amount": features.budget_amount,
        "authority_level": features.authority_level,
        "need": features.need,
        "need_category": features.need_category,
        "timeline_urgency": features.timeline_urgency,
        "intent": features.intent,
        "intent_confidence": features.intent_confidence,
        "buying_signals": features.buying_signals,
        "objections": features.objections,
        "icp_score": features.icp_score
    })
    
    # Format output
    analysis_output = {
        "transcript": features.transcript,
        "emotion": {
            "type": features.emotion,
            "confidence": features.emotion_confidence * 100,
            "scores": {k: v*100 for k, v in features.emotion_scores.items()}
        },
        "bant": {
            "budget": f"₹{features.budget_amount:,.0f}" if features.budget_amount else "Not mentioned",
            "authority": features.authority,
            "need": features.need,
            "timeline": features.timeline
        },
        "intent": {
            "type": features.intent,
            "confidence": features.intent_confidence * 100
        },
        "buying_signals": features.buying_signals,
        "objections": features.objections,
        "icp_score": features.icp_score * 100,
        "icp_details": {f"Criteria {i+1}": True for i in range(min(3, len(features.icp_matched_criteria)))},
        "lead_score": {
            "score": lead_score_result.score,
            "qualification": lead_score_result.qualification,
            "confidence": lead_score_result.confidence,
            "reasoning": lead_score_result.reasoning
        }
    }
    
    # Display formatted output
    formatted = OutputFormatter.format_analysis_output(analysis_output)
    print(formatted)
    
    print("\n" + "=" * 66)
    print("SUCCESS: All systems working correctly!")
    print("=" * 66 + "\n")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
