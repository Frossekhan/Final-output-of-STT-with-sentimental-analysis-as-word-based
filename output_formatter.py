"""
Unified Output Formatter
Displays complete analysis results in professional format
"""
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


class OutputFormatter:
    """Format analysis results for display"""
    
    @staticmethod
    def format_analysis_output(analysis: Dict[str, Any]) -> str:
        """
        Format complete analysis output
        
        Returns the beautiful format requested:
        ╔══════════════════════════════════════════════════════════════╗
        │ REAL-TIME SALES INTELLIGENCE ANALYSIS                       │
        ╚══════════════════════════════════════════════════════════════╝
        """
        
        lines = []
        
        # Header
        lines.append("╔" + "═" * 62 + "╗")
        lines.append("║" + " REAL-TIME SALES INTELLIGENCE ANALYSIS ".center(62) + "║")
        lines.append("╠" + "═" * 62 + "╣")
        
        # Transcript
        lines.append("║ 🎤 TRANSCRIPT " + " " * 48 + "║")
        lines.append("║" + "─" * 62 + "║")
        
        transcript = analysis.get("transcript", "")
        if transcript:
            # Wrap transcript text
            for line in OutputFormatter._wrap_text(transcript, 58):
                lines.append(f"║ {line:<60} ║")
        else:
            lines.append("║ [Listening...]" + " " * 46 + "║")
        
        lines.append("║" + " " * 62 + "║")
        
        # Emotion
        lines.append("║ 😊 SPEECH EMOTION " + " " * 44 + "║")
        lines.append("║" + "─" * 62 + "║")
        
        emotion = analysis.get("emotion", {})
        emotion_text = f"{emotion.get('type', 'Unknown')} ({emotion.get('confidence', 0):.0f}%)"
        lines.append(f"║ {emotion_text:<60} ║")
        
        # Emotion details
        scores = emotion.get("scores", {})
        if scores:
            for emotion_type, confidence in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]:
                lines.append(f"║   • {emotion_type}: {confidence:.0f}%" + " " * (40 - len(emotion_type)) + "║")
        
        lines.append("║" + " " * 62 + "║")
        
        # BANT
        lines.append("║ 💼 BANT ANALYSIS " + " " * 45 + "║")
        lines.append("║" + "─" * 62 + "║")
        
        bant = analysis.get("bant", {})
        
        budget_text = f"Budget: {bant.get('budget', 'Not mentioned')}"
        lines.append(f"║ {budget_text:<60} ║")
        
        authority_text = f"Authority: {bant.get('authority', 'Unknown')}"
        lines.append(f"║ {authority_text:<60} ║")
        
        need_text = f"Need: {bant.get('need', 'Not mentioned')[:45]}..."
        if len(bant.get('need', '')) <= 45:
            need_text = f"Need: {bant.get('need', 'Not mentioned')}"
        lines.append(f"║ {need_text:<60} ║")
        
        timeline_text = f"Timeline: {bant.get('timeline', 'Not mentioned')}"
        lines.append(f"║ {timeline_text:<60} ║")
        
        lines.append("║" + " " * 62 + "║")
        
        # Intent
        lines.append("║ 🎯 INTENT DETECTION " + " " * 41 + "║")
        lines.append("║" + "─" * 62 + "║")
        
        intent = analysis.get("intent", {})
        intent_text = f"{intent.get('type', 'Unknown')} ({intent.get('confidence', 0):.0f}% confidence)"
        lines.append(f"║ {intent_text:<60} ║")
        
        lines.append("║" + " " * 62 + "║")
        
        # Buying Signals
        lines.append("║ 🚀 BUYING SIGNALS " + " " * 44 + "║")
        lines.append("║" + "─" * 62 + "║")
        
        buying_signals = analysis.get("buying_signals", [])
        signals_count = len(buying_signals)
        
        if signals_count > 0:
            lines.append(f"║ Signals Detected: {signals_count}" + " " * (27 - len(str(signals_count))) + "║")
            for signal in buying_signals[:3]:
                signal_text = f"   • {signal.get('signal', 'Unknown')} ({signal.get('confidence', 0):.0f}%)"
                lines.append(f"║ {signal_text:<60} ║")
        else:
            lines.append("║ No buying signals detected" + " " * 35 + "║")
        
        lines.append("║" + " " * 62 + "║")
        
        # Objections
        lines.append("║ ⚠️  OBJECTIONS " + " " * 48 + "║")
        lines.append("║" + "─" * 62 + "║")
        
        objections = analysis.get("objections", [])
        
        if objections:
            lines.append(f"║ Found {len(objections)} objection(s):" + " " * (35 - len(str(len(objections)))) + "║")
            for obj in objections[:3]:
                obj_text = f"   • {obj.get('type', 'Unknown')}: {obj.get('description', '')}"
                lines.append(f"║ {obj_text[:58]:<60} ║")
        else:
            lines.append("║ No objections detected" + " " * 39 + "║")
        
        lines.append("║" + " " * 62 + "║")
        
        # ICP Scoring
        lines.append("║ 👥 ICP MATCHING " + " " * 47 + "║")
        lines.append("║" + "─" * 62 + "║")
        
        icp_score = analysis.get("icp_score", 0)
        icp_bar = OutputFormatter._create_progress_bar(icp_score, 25)
        lines.append(f"║ Match Score: {icp_score:.0f}%  {icp_bar:<33} ║")
        
        icp_details = analysis.get("icp_details", {})
        if icp_details:
            for criterion, match in list(icp_details.items())[:3]:
                match_text = f"   • {criterion}: {'✓' if match else '✗'}"
                lines.append(f"║ {match_text:<60} ║")
        
        lines.append("║" + " " * 62 + "║")
        
        # Lead Scoring
        lines.append("║ ⭐ LEAD QUALIFICATION " + " " * 40 + "║")
        lines.append("║" + "─" * 62 + "║")
        
        lead_score = analysis.get("lead_score", {})
        score = lead_score.get("score", 0)
        qualification = lead_score.get("qualification", "UNKNOWN")
        confidence = lead_score.get("confidence", 0)
        
        score_bar = OutputFormatter._create_progress_bar(score, 20)
        lines.append(f"║ Lead Score: {score:.0f}/100  {score_bar:<28} ║")
        lines.append(f"║" + " " * 62 + "║")
        lines.append(f"║ Status: {qualification:<51} ║")
        lines.append(f"║ Confidence: {confidence:.0f}%" + " " * (47 - len(str(int(confidence)))) + "║")
        
        # Reasoning
        if lead_score.get("reasoning"):
            lines.append("║" + " " * 62 + "║")
            lines.append("║ Key Factors:" + " " * 50 + "║")
            for reason in lead_score.get("reasoning", [])[:3]:
                lines.append(f"║   {reason[:55]:<60} ║")
        
        lines.append("║" + " " * 62 + "║")
        
        # Footer
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append("║" + "─" * 62 + "║")
        lines.append(f"║ Generated: {timestamp:<49} ║")
        lines.append("╚" + "═" * 62 + "╝")
        
        return "\n".join(lines)
    
    @staticmethod
    def _wrap_text(text: str, width: int) -> list:
        """Wrap text to specified width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            if len(" ".join(current_line + [word])) <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines
    
    @staticmethod
    def _create_progress_bar(value: float, width: int = 20) -> str:
        """Create ASCII progress bar"""
        filled = int(width * value / 100)
        bar = "█" * filled + "░" * (width - filled)
        return bar


# Example usage and test
def example_analysis():
    """Generate example analysis output"""
    
    example_data = {
        "transcript": "Hello, I'm the CEO of a technology company. We need a CRM solution with a budget of 25 lakhs and want to implement it in 3 months. Can you send us a quote?",
        "emotion": {
            "type": "Interested",
            "confidence": 89,
            "scores": {
                "interested": 89,
                "confident": 65,
                "professional": 75
            }
        },
        "bant": {
            "budget": "₹25 Lakhs",
            "authority": "CEO",
            "need": "CRM Solution",
            "timeline": "3 Months"
        },
        "intent": {
            "type": "Purchase",
            "confidence": 92
        },
        "buying_signals": [
            {"signal": "Budget mentioned", "confidence": 95},
            {"signal": "Implementation timeline specified", "confidence": 88}
        ],
        "objections": [],
        "icp_score": 85,
        "icp_details": {
            "Technology Industry": True,
            "Company Size (Large)": True,
            "Decision Maker Present": True
        },
        "lead_score": {
            "score": 92,
            "qualification": "🟢 HOT",
            "confidence": 94,
            "reasoning": [
                "✓ High budget identified: ₹25 Lakhs",
                "✓ Decision maker present: CEO",
                "✓ Clear intent: Purchase",
                "✓ Strong ICP match: 85%"
            ]
        }
    }
    
    output = OutputFormatter.format_analysis_output(example_data)
    return output


if __name__ == "__main__":
    print(example_analysis())
