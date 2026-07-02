"""
Enterprise Model Training Script
Uses goendalf666/sales-conversations dataset to train ML models
"""
import asyncio
import json
import logging
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnterpriseModelTrainer:
    """
    Train enterprise AI models on sales conversations
    """
    
    def __init__(self, use_llm_for_annotation: bool = True):
        """
        Initialize trainer
        
        Args:
            use_llm_for_annotation: Use LLM to annotate dataset (requires Ollama)
        """
        self.use_llm = use_llm_for_annotation
        self.llm_service = None
        self.ml_scorer = None
        
    async def initialize(self):
        """Initialize components"""
        # Initialize LLM for annotation
        if self.use_llm:
            try:
                from llm.service import LLMServiceFactory
                self.llm_service = LLMServiceFactory.create(model_name="qwen2.5:7b")
                print("✅ LLM Service initialized for annotation")
            except Exception as e:
                print(f"⚠️  LLM not available: {e}")
                print("   Will use rule-based annotation instead")
                self.use_llm = False
        
        # Initialize ML scorer
        try:
            from ml.lead_scorer import MLLeadScorerFactory
            self.ml_scorer = MLLeadScorerFactory.create()
            print("✅ ML Lead Scorer initialized")
        except Exception as e:
            print(f"❌ Failed to initialize ML scorer: {e}")
            raise
    
    async def load_and_annotate_dataset(self, num_samples: int = 50) -> List[Dict]:
        """
        Load dataset and annotate with LLM
        
        Args:
            num_samples: Number of conversations to process
            
        Returns:
            List of annotated conversations
        """
        from dataset_loader import SalesDatasetLoader
        
        print(f"\n📥 Loading dataset...")
        loader = SalesDatasetLoader()
        conversations = loader.load_from_huggingface(split="train", max_samples=num_samples)
        
        if not conversations:
            print("❌ Failed to load dataset")
            return []
        
        print(f"✅ Loaded {len(conversations)} conversations")
        
        # Annotate conversations
        print(f"\n🏷️  Annotating conversations...")
        if self.use_llm and self.llm_service:
            annotated_data = await self._annotate_with_llm(conversations)
        else:
            annotated_data = self._annotate_with_rules(conversations)
        
        print(f"✅ Annotated {len(annotated_data)} conversations")
        
        # Save annotated dataset
        output_file = "annotated_sales_conversations.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(annotated_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved to {output_file}")
        
        return annotated_data
    
    async def _annotate_with_llm(self, conversations: List) -> List[Dict]:
        """
        Annotate conversations using LLM
        
        Args:
            conversations: List of SalesConversation objects
            
        Returns:
            List of annotated dictionaries
        """
        annotated_data = []
        
        for idx, conv in enumerate(conversations):
            print(f"   Processing {idx + 1}/{len(conversations)}: {conv.conversation_id}")
            
            try:
                # Get full transcript
                transcript = conv.get_full_transcript()
                customer_text = conv.get_customer_text()
                
                # Run LLM analysis
                analysis = await self.llm_service.analyze_conversation_complete(transcript)
                
                # Create annotated example
                annotated = {
                    "conversation_id": conv.conversation_id,
                    "transcript": transcript,
                    "customer_text": customer_text,
                    "scenario": conv.scenario,
                    "outcome": conv.outcome,
                    "num_turns": len(conv.turns),
                    # LLM annotations
                    "bant": analysis.get("bant", {}),
                    "intent": analysis.get("intent", {}),
                    "buying_signals": analysis.get("buying_signals", {}),
                    "objections": analysis.get("objections", {}),
                    "emotion": analysis.get("emotion", {}),
                    "summary": analysis.get("summary", {}),
                    # Metadata
                    "annotated_at": "2024-01-01T00:00:00",
                    "annotation_method": "llm"
                }
                
                annotated_data.append(annotated)
                
            except Exception as e:
                logger.warning(f"Failed to annotate {conv.conversation_id}: {e}")
                continue
        
        return annotated_data
    
    def _annotate_with_rules(self, conversations: List) -> List[Dict]:
        """
        Annotate conversations using rule-based methods (fallback)
        
        Args:
            conversations: List of SalesConversation objects
            
        Returns:
            List of annotated dictionaries
        """
        annotated_data = []
        
        for conv in conversations:
            transcript = conv.get_full_transcript()
            customer_text = conv.get_customer_text()
            
            # Simple rule-based annotation
            annotated = {
                "conversation_id": conv.conversation_id,
                "transcript": transcript,
                "customer_text": customer_text,
                "scenario": conv.scenario,
                "outcome": conv.outcome,
                "num_turns": len(conv.turns),
                # Rule-based annotations
                "bant": self._extract_bant_rules(transcript),
                "intent": self._extract_intent_rules(transcript),
                "buying_signals": self._extract_signals_rules(transcript),
                "objections": self._extract_objections_rules(transcript),
                "emotion": {"emotion": "neutral", "confidence": 0.5},
                "summary": {"summary": "", "key_points": []},
                "annotated_at": "2024-01-01T00:00:00",
                "annotation_method": "rules"
            }
            
            annotated_data.append(annotated)
        
        return annotated_data
    
    def _extract_bant_rules(self, text: str) -> Dict:
        """Simple rule-based BANT extraction"""
        text_lower = text.lower()
        
        # Budget
        budget = None
        budget_amount = None
        if "budget" in text_lower or "₹" in text or "lakh" in text_lower or "crore" in text_lower:
            budget = "Budget discussed"
            # Try to extract amount
            import re
            amounts = re.findall(r'(\d+)\s*(lakh|crore|k|thousand)', text_lower)
            if amounts:
                budget_amount = float(amounts[0][0])
        
        # Authority
        authority = None
        authority_level = "unknown"
        roles = ["ceo", "cto", "cfo", "director", "vp", "vice president", "manager", "founder"]
        for role in roles:
            if role in text_lower:
                authority = role.upper()
                authority_level = "decision_maker" if role in ["ceo", "cto", "cfo", "founder"] else "manager"
                break
        
        # Need
        need = None
        need_category = "general"
        if "need" in text_lower or "looking for" in text_lower or "require" in text_lower:
            need = "Customer has a need"
        
        # Timeline
        timeline = None
        timeline_urgency = "not_mentioned"
        if "urgent" in text_lower or "asap" in text_lower or "immediately" in text_lower:
            timeline = "Urgent"
            timeline_urgency = "immediate"
        elif "month" in text_lower or "quarter" in text_lower:
            timeline = "Timeline discussed"
            timeline_urgency = "medium_term"
        
        return {
            "budget": budget,
            "budget_amount": budget_amount,
            "budget_currency": "INR",
            "authority": authority,
            "authority_level": authority_level,
            "need": need,
            "need_category": need_category,
            "timeline": timeline,
            "timeline_urgency": timeline_urgency,
            "confidence": 0.6,
            "evidence": []
        }
    
    def _extract_intent_rules(self, text: str) -> Dict:
        """Simple rule-based intent extraction"""
        text_lower = text.lower()
        
        intents = {
            "purchase": ["buy", "purchase", "order", "proceed", "sign"],
            "pricing": ["price", "cost", "budget", "expensive", "cheap"],
            "demo": ["demo", "demonstration", "trial", "try"],
            "negotiation": ["negotiate", "discount", "offer", "deal"],
            "information": ["information", "details", "learn", "understand"]
        }
        
        intent_scores = {}
        for intent, keywords in intents.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                intent_scores[intent] = min(1.0, score / 3.0)
        
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[primary_intent]
        else:
            primary_intent = "information"
            confidence = 0.5
        
        return {
            "intent": primary_intent,
            "confidence": confidence,
            "all_intents": intent_scores,
            "reasoning": "Rule-based detection"
        }
    
    def _extract_signals_rules(self, text: str) -> Dict:
        """Simple rule-based buying signal extraction"""
        text_lower = text.lower()
        
        signals = []
        
        signal_keywords = {
            "budget_confirmation": ["budget", "approved", "allocated"],
            "request_quotation": ["quote", "proposal", "pricing"],
            "request_demo": ["demo", "demonstration", "trial"],
            "decision_maker_engagement": ["i'm the", "i am the", "my decision"],
            "urgency_indicators": ["urgent", "asap", "immediately", "soon"]
        }
        
        for signal_type, keywords in signal_keywords.items():
            if any(kw in text_lower for kw in keywords):
                signals.append({
                    "type": signal_type,
                    "strength": 0.7,
                    "evidence": f"Keyword match: {keywords}",
                    "recommendation": "Follow up on this signal"
                })
        
        readiness_score = min(1.0, len(signals) * 0.2)
        
        return {
            "signals": signals,
            "overall_readiness": "MEDIUM_INTENT" if signals else "NOT_READY",
            "readiness_score": readiness_score,
            "reasoning": "Rule-based detection"
        }
    
    def _extract_objections_rules(self, text: str) -> Dict:
        """Simple rule-based objection extraction"""
        text_lower = text.lower()
        
        objections = []
        
        objection_keywords = {
            "price": ["expensive", "cost", "price", "budget"],
            "timing": ["not now", "later", "bad time"],
            "competitor": ["competitor", "alternative", "other option"],
            "trust": ["trust", "reliable", "proven"]
        }
        
        for objection_type, keywords in objection_keywords.items():
            if any(kw in text_lower for kw in keywords):
                objections.append({
                    "type": objection_type,
                    "severity": "medium",
                    "confidence": 0.6,
                    "evidence": f"Keyword match: {keywords}",
                    "suggested_response": f"Address {objection_type} concerns"
                })
        
        severity = "high" if len(objections) >= 3 else "medium" if objections else "low"
        
        return {
            "objections": objections,
            "severity": severity,
            "handling_priority": [o["type"] for o in objections],
            "reasoning": "Rule-based detection"
        }
    
    def prepare_ml_training_data(self, annotated_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for ML model training
        
        Args:
            annotated_data: List of annotated conversations
            
        Returns:
            X (features) and y (labels) arrays
        """
        from ml.lead_scorer import LeadFeatures
        
        print(f"\n🔧 Preparing ML training data...")
        
        X = []
        y = []
        
        for item in annotated_data:
            try:
                # Extract features using ML scorer
                lead_score = self.ml_scorer.predict(item)
                
                # Create feature vector
                features = self.ml_scorer.extract_features(item)
                feature_array = self.ml_scorer._features_to_array(features)[0]
                
                X.append(feature_array)
                
                # Label: 1 if HOT, 0 otherwise
                label = 1 if lead_score.qualification == "HOT" else 0
                y.append(label)
                
            except Exception as e:
                logger.warning(f"Failed to process {item['conversation_id']}: {e}")
                continue
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"✅ Prepared {len(X)} training examples")
        print(f"   Features: {X.shape[1]}")
        print(f"   Positive samples (HOT): {sum(y)}")
        print(f"   Negative samples (WARM/COLD): {len(y) - sum(y)}")
        
        return X, y
    
    def train_models(self, X: np.ndarray, y: np.ndarray, test_split: float = 0.2):
        """
        Train Random Forest and XGBoost models
        
        Args:
            X: Feature matrix
            y: Labels
            test_split: Fraction of data to use for testing
        """
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        print(f"\n🤖 Training ML models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_split, random_state=42
        )
        
        print(f"   Training set: {len(X_train)} samples")
        print(f"   Test set: {len(X_test)} samples")
        
        # Train Random Forest
        print(f"\n   Training Random Forest...")
        from sklearn.ensemble import RandomForestClassifier
        
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        rf_model.fit(X_train, y_train)
        
        # Evaluate Random Forest
        rf_pred = rf_model.predict(X_test)
        rf_accuracy = accuracy_score(y_test, rf_pred)
        rf_precision = precision_score(y_test, rf_pred, zero_division=0)
        rf_recall = recall_score(y_test, rf_pred, zero_division=0)
        rf_f1 = f1_score(y_test, rf_pred, zero_division=0)
        
        print(f"   ✅ Random Forest trained")
        print(f"      Accuracy: {rf_accuracy:.2%}")
        print(f"      Precision: {rf_precision:.2%}")
        print(f"      Recall: {rf_recall:.2%}")
        print(f"      F1 Score: {rf_f1:.2%}")
        
        # Train XGBoost
        print(f"\n   Training XGBoost...")
        try:
            from xgboost import XGBClassifier
            
            xgb_model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            xgb_model.fit(X_train, y_train)
            
            # Evaluate XGBoost
            xgb_pred = xgb_model.predict(X_test)
            xgb_accuracy = accuracy_score(y_test, xgb_pred)
            xgb_precision = precision_score(y_test, xgb_pred, zero_division=0)
            xgb_recall = recall_score(y_test, xgb_pred, zero_division=0)
            xgb_f1 = f1_score(y_test, xgb_pred, zero_division=0)
            
            print(f"   ✅ XGBoost trained")
            print(f"      Accuracy: {xgb_accuracy:.2%}")
            print(f"      Precision: {xgb_precision:.2%}")
            print(f"      Recall: {xgb_recall:.2%}")
            print(f"      F1 Score: {xgb_f1:.2%}")
            
            # Save models
            self._save_models(rf_model, xgb_model)
            
        except ImportError:
            print("   ⚠️  XGBoost not available. Install with: pip install xgboost")
            xgb_model = None
        
        return rf_model, xgb_model
    
    def _save_models(self, rf_model, xgb_model):
        """Save trained models"""
        import joblib
        import os
        
        os.makedirs("models", exist_ok=True)
        
        joblib.dump(rf_model, "models/rf_model.pkl")
        print(f"   ✅ Saved Random Forest model to models/rf_model.pkl")
        
        if xgb_model:
            joblib.dump(xgb_model, "models/xgb_model.pkl")
            print(f"   ✅ Saved XGBoost model to models/xgb_model.pkl")
    
    async def run_complete_training(self, num_samples: int = 50):
        """
        Run complete training pipeline
        
        Args:
            num_samples: Number of conversations to use
        """
        print("=" * 80)
        print("🏆 ENTERPRISE AI MODEL TRAINING")
        print("=" * 80)
        
        # Initialize
        await self.initialize()
        
        # Load and annotate dataset
        annotated_data = await self.load_and_annotate_dataset(num_samples)
        
        if not annotated_data:
            print("❌ No annotated data available")
            return
        
        # Prepare ML training data
        X, y = self.prepare_ml_training_data(annotated_data)
        
        if len(X) == 0:
            print("❌ No training data prepared")
            return
        
        # Train models
        rf_model, xgb_model = self.train_models(X, y)
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ TRAINING COMPLETE")
        print("=" * 80)
        print(f"\nModels saved to: models/")
        print(f"Annotated dataset: annotated_sales_conversations.json")
        print(f"\nNext steps:")
        print(f"1. Review annotated data")
        print(f"2. Test models with test_enterprise_integration.py")
        print(f"3. Fine-tune based on results")
        print(f"4. Deploy with server_enterprise.py")


async def main():
    """Main training function"""
    trainer = EnterpriseModelTrainer(use_llm_for_annotation=True)
    await trainer.run_complete_training(num_samples=20)  # Start with 20 samples


if __name__ == "__main__":
    asyncio.run(main())