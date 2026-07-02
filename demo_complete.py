"""
Comprehensive System Demo & Integration Test
Demonstrates complete end-to-end analysis pipeline
"""
import logging
import sys
from typing import Dict, Any

# Import all components
from conversation_engine.engine import ConversationIntelligenceEngine
from lead_scoring import LeadScorer
from output_formatter import OutputFormatter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemDemo:
    """Complete system demonstration"""
    
    def __init__(self):
        self.engine = ConversationIntelligenceEngine()
        self.lead_scorer = LeadScorer()
        self.test_conversations = [
            {
                "name": "High-Value Lead",
                "transcript": "Hello, I'm the CEO of a technology company. We need a CRM solution with a budget of 25 lakhs and want to implement it in 3 months. Can you send us a quote?"
            },
            {
                "name": "Warm Lead",
                "transcript": "Hi, we're currently looking at your competitor Salesforce, but we're open to exploring alternatives. Our company has about 50 employees and we're in the fintech space."
            },
            {
                "name": "Cold Lead",
                "transcript": "Yeah, I saw your email. Maybe someday when we have more budget. For now, we're good with our existing system."
            },
            {
                "name": "Complex Deal",
                "transcript": "We need to move forward, but our CFO is concerned about the price. We have a 6-month timeline and it's critical for our Q4 goals. What's the cheapest option?"
            },
            {
                "name": "Enterprise Deal",
                "transcript": "Our VP of Operations and I are both interested. We manage 500+ users and need enterprise support. Budget is 1 crore annually. When can we schedule a demo?"
            }
        ]
    
    def run_demo(self):
        """Run complete system demonstration"""
        print("\n" + "=" * 66)
        print("  SALES INTELLIGENCE PLATFORM - COMPREHENSIVE DEMO".center(66))
        print("=" * 66 + "\n")
        
        for i, conversation in enumerate(self.test_conversations, 1):
            print(f"\n{'─' * 66}")
            print(f"Demo {i}/{len(self.test_conversations)}: {conversation['name']}")
            print(f"{'─' * 66}\n")
            
            # Analyze conversation
            self.analyze_conversation(conversation["transcript"])
            
            # Brief pause between demos
            if i < len(self.test_conversations):
                input("Press Enter to continue to next demo...")
    
    def analyze_conversation(self, transcript: str):
        """Analyze single conversation and display results"""
        try:
            logger.info("🔄 Analyzing conversation...")
            
            # Run complete analysis
            features = self.engine.process_conversation(transcript)
            
            # Score the lead
            lead_score_result = self.lead_scorer.score({
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
            
            # Print lead scorer report
            self._print_lead_scoring_report(lead_score_result)
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            import traceback
            traceback.print_exc()
    
    def _print_lead_scoring_report(self, lead_score):
        """Print detailed lead scoring report"""
        print("\n" + "=" * 66)
        print("LEAD SCORING DETAILS".center(66))
        print("=" * 66)
        
        print(f"\n📊 Score Breakdown:")
        print(f"   Overall Score: {lead_score.score:.0f}/100")
        print(f"   Qualification: {lead_score.qualification}")
        print(f"   Confidence: {lead_score.confidence:.0f}%")
        
        print(f"\n🔍 Factor Analysis:")
        for factor, weight in sorted(lead_score.factors.items(), key=lambda x: abs(x[1]), reverse=True):
            symbol = "+" if weight >= 0 else ""
            print(f"   {factor}: {symbol}{weight:+.0f}")
        
        print(f"\n💡 Reasoning:")
        for i, reason in enumerate(lead_score.reasoning, 1):
            print(f"   {i}. {reason}")
        
        print("\n" + "=" * 66)
    
    def run_quick_test(self):
        """Quick test of single conversation"""
        transcript = "Hello, I'm the CEO. We need a CRM with 25 lakhs budget for 3 months implementation."
        print("Running quick test with sample transcript...")
        self.analyze_conversation(transcript)
    
    def run_batch_scoring(self):
        """Score all test conversations and print report"""
        print("\n" + "=" * 66)
        print("BATCH LEAD SCORING REPORT".center(66))
        print("=" * 66)
        
        for i, conversation in enumerate(self.test_conversations, 1):
            print(f"\n{i}. {conversation['name']}")
            print("   " + "─" * 50)
            
            try:
                analysis_result = self.engine.process_conversation(
                    conversation["transcript"]
                )
                
                lead_score = self.lead_scorer.score({
                    "transcript": conversation["transcript"],
                    "emotion": analysis_result.emotion,
                    "emotion_confidence": analysis_result.emotion_confidence,
                    "emotion_scores": analysis_result.emotion_scores,
                    "budget_amount": analysis_result.budget_amount,
                    "authority_level": analysis_result.authority_level,
                    "need": analysis_result.need,
                    "need_category": analysis_result.need_category,
                    "timeline_urgency": analysis_result.timeline_urgency,
                    "intent": analysis_result.intent,
                    "intent_confidence": analysis_result.intent_confidence,
                    "buying_signals": analysis_result.buying_signals,
                    "objections": analysis_result.objections,
                    "icp_score": analysis_result.icp_score
                })
                
                print(f"   Score: {lead_score.score:.0f}/100 | Tier: {lead_score.qualification} | Confidence: {lead_score.confidence:.0f}%")
                
            except Exception as e:
                print(f"   Error: {e}")
        
        # Print summary
        print("\n" + "─" * 66)
        report = self.lead_scorer.get_report()
        print(f"Total Leads Scored: {report.get('total_leads_scored', 0)}")
        print(f"Average Score: {report.get('average_score', 0):.0f}/100")
        print(f"Distribution: 🟢 {report.get('hot_count', 0)} HOT | 🟡 {report.get('warm_count', 0)} WARM | 🔵 {report.get('cold_count', 0)} COLD")
        print("=" * 66)


def main():
    """Main entry point"""
    demo = SystemDemo()
    
    print("\n🚀 Sales Intelligence Platform - Demo Menu")
    print("=" * 66)
    print("1. Quick Test (single conversation)")
    print("2. Full Interactive Demo (all conversations)")
    print("3. Batch Scoring Report (all leads)")
    print("4. Exit")
    print("=" * 66)
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        demo.run_quick_test()
    elif choice == "2":
        demo.run_demo()
    elif choice == "3":
        demo.run_batch_scoring()
    elif choice == "4":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid option")
        sys.exit(1)


if __name__ == "__main__":
    main()
