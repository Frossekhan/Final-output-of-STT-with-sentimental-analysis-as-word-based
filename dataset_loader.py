"""
Dataset Loader for Sales Conversations
Loads and prepares the goendalf666/sales-conversations dataset
"""
import logging
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Single conversation turn"""
    speaker: str
    text: str
    turn_number: int


@dataclass
class SalesConversation:
    """Sales conversation from dataset"""
    conversation_id: str
    turns: List[ConversationTurn]
    scenario: str
    customer_profile: Dict
    salesperson_profile: Dict
    outcome: Optional[str] = None
    metadata: Dict = None
    
    def get_full_transcript(self) -> str:
        """Get full transcript as string"""
        return "\n".join([f"{turn.speaker}: {turn.text}" for turn in self.turns])
    
    def get_customer_text(self) -> str:
        """Get all customer utterances"""
        return " ".join([turn.text for turn in self.turns if turn.speaker.lower() in ["customer", "buyer"]])
    
    def get_salesperson_text(self) -> str:
        """Get all salesperson utterances"""
        return " ".join([turn.text for turn in self.turns if turn.speaker.lower() in ["salesperson", "seller", "agent"]])
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "conversation_id": self.conversation_id,
            "transcript": self.get_full_transcript(),
            "customer_text": self.get_customer_text(),
            "salesperson_text": self.get_salesperson_text(),
            "scenario": self.scenario,
            "customer_profile": self.customer_profile,
            "salesperson_profile": self.salesperson_profile,
            "outcome": self.outcome,
            "num_turns": len(self.turns),
            "metadata": self.metadata
        }


class SalesDatasetLoader:
    """
    Load and prepare sales conversation dataset
    """
    
    def __init__(self, dataset_name: str = "goendalf666/sales-conversations"):
        """
        Initialize dataset loader
        
        Args:
            dataset_name: HuggingFace dataset name
        """
        self.dataset_name = dataset_name
        self.conversations: List[SalesConversation] = []
        
    def load_from_huggingface(self, split: str = "train", max_samples: Optional[int] = None) -> List[SalesConversation]:
        """
        Load dataset from Hugging Face
        
        Args:
            split: Dataset split (train/test/validation)
            max_samples: Maximum number of samples to load (None for all)
            
        Returns:
            List of SalesConversation objects
        """
        try:
            from datasets import load_dataset
            
            print(f"📥 Loading dataset: {self.dataset_name}")
            print(f"   Split: {split}")
            
            # Load dataset
            dataset = load_dataset(self.dataset_name, split=split)
            
            print(f"✅ Loaded {len(dataset)} conversations")
            
            # Limit samples if specified
            if max_samples:
                dataset = dataset.select(range(min(max_samples, len(dataset))))
                print(f"   Limited to {len(dataset)} samples")
            
            # Convert to SalesConversation objects
            self.conversations = []
            for idx, item in enumerate(dataset):
                try:
                    conversation = self._parse_conversation(item, idx)
                    self.conversations.append(conversation)
                except Exception as e:
                    logger.warning(f"Failed to parse conversation {idx}: {e}")
                    continue
            
            print(f"✅ Parsed {len(self.conversations)} conversations")
            return self.conversations
            
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            print(f"❌ Error: {e}")
            print("\n💡 Try installing datasets library:")
            print("   pip install datasets")
            return []
    
    def _parse_conversation(self, item: Dict, idx: int) -> SalesConversation:
        """
        Parse a single conversation from dataset
        
        Args:
            item: Dataset item
            idx: Index for ID
            
        Returns:
            SalesConversation object
        """
        # Extract conversation ID
        conversation_id = item.get("id", f"conv_{idx}")
        
        # Extract turns
        turns = []
        turn_number = 0
        
        # Try different possible field names for conversation
        conversation_text = item.get("conversation", item.get("dialogue", item.get("transcript", "")))
        
        if isinstance(conversation_text, str):
            # Parse text format
            turns = self._parse_conversation_text(conversation_text)
        elif isinstance(conversation_text, list):
            # Parse list format
            for turn in conversation_text:
                if isinstance(turn, dict):
                    speaker = turn.get("speaker", turn.get("role", "unknown"))
                    text = turn.get("text", turn.get("utterance", ""))
                    turns.append(ConversationTurn(
                        speaker=speaker,
                        text=text,
                        turn_number=turn_number
                    ))
                    turn_number += 1
        
        # Extract profiles
        customer_profile = item.get("customer_profile", item.get("buyer_profile", {}))
        salesperson_profile = item.get("salesperson_profile", item.get("seller_profile", {}))
        
        # Extract scenario
        scenario = item.get("scenario", item.get("context", "unknown"))
        
        # Extract outcome
        outcome = item.get("outcome", item.get("result", None))
        
        return SalesConversation(
            conversation_id=str(conversation_id),
            turns=turns,
            scenario=scenario,
            customer_profile=customer_profile,
            salesperson_profile=salesperson_profile,
            outcome=outcome,
            metadata=item
        )
    
    def _parse_conversation_text(self, text: str) -> List[ConversationTurn]:
        """
        Parse conversation text into turns
        
        Args:
            text: Conversation text
            
        Returns:
            List of ConversationTurn objects
        """
        turns = []
        lines = text.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to parse "Speaker: Text" format
            if ":" in line:
                parts = line.split(":", 1)
                speaker = parts[0].strip()
                text = parts[1].strip()
                
                turns.append(ConversationTurn(
                    speaker=speaker,
                    text=text,
                    turn_number=len(turns)
                ))
        
        return turns
    
    def get_statistics(self) -> Dict:
        """
        Get dataset statistics
        
        Returns:
            Statistics dictionary
        """
        if not self.conversations:
            return {"error": "No conversations loaded"}
        
        total_turns = sum(len(conv.turns) for conv in self.conversations)
        avg_turns = total_turns / len(self.conversations)
        
        # Count outcomes
        outcomes = {}
        for conv in self.conversations:
            if conv.outcome:
                outcomes[conv.outcome] = outcomes.get(conv.outcome, 0) + 1
        
        # Count scenarios
        scenarios = {}
        for conv in self.conversations:
            scenario = conv.scenario
            scenarios[scenario] = scenarios.get(scenario, 0) + 1
        
        return {
            "total_conversations": len(self.conversations),
            "total_turns": total_turns,
            "avg_turns_per_conversation": round(avg_turns, 2),
            "outcomes": outcomes,
            "scenarios": scenarios,
            "sample_conversation": self.conversations[0].to_dict() if self.conversations else None
        }
    
    def prepare_for_training(self) -> List[Dict]:
        """
        Prepare conversations for training ML models
        
        Returns:
            List of training examples
        """
        training_data = []
        
        for conv in self.conversations:
            # Create training example
            example = {
                "conversation_id": conv.conversation_id,
                "transcript": conv.get_full_transcript(),
                "customer_text": conv.get_customer_text(),
                "salesperson_text": conv.get_salesperson_text(),
                "scenario": conv.scenario,
                "outcome": conv.outcome,
                "num_turns": len(conv.turns),
                # Add more features as needed
            }
            
            training_data.append(example)
        
        return training_data
    
    def save_to_json(self, filepath: str):
        """
        Save conversations to JSON file
        
        Args:
            filepath: Output file path
        """
        data = [conv.to_dict() for conv in self.conversations]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(data)} conversations to {filepath}")
    
    def load_from_json(self, filepath: str) -> List[SalesConversation]:
        """
        Load conversations from JSON file
        
        Args:
            filepath: Input file path
            
        Returns:
            List of SalesConversation objects
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.conversations = []
        for item in data:
            conv = SalesConversation(
                conversation_id=item["conversation_id"],
                turns=[ConversationTurn(**turn) for turn in item.get("turns", [])],
                scenario=item.get("scenario", "unknown"),
                customer_profile=item.get("customer_profile", {}),
                salesperson_profile=item.get("salesperson_profile", {}),
                outcome=item.get("outcome"),
                metadata=item.get("metadata")
            )
            self.conversations.append(conv)
        
        print(f"✅ Loaded {len(self.conversations)} conversations from {filepath}")
        return self.conversations


def main():
    """Test dataset loader"""
    print("=" * 80)
    print("📊 SALES CONVERSATION DATASET LOADER")
    print("=" * 80)
    
    # Initialize loader
    loader = SalesDatasetLoader()
    
    # Load dataset (limit to 10 samples for testing)
    conversations = loader.load_from_huggingface(split="train", max_samples=10)
    
    if not conversations:
        print("\n❌ Failed to load dataset")
        print("\n💡 Make sure you have installed the datasets library:")
        print("   pip install datasets")
        return
    
    # Show statistics
    print("\n" + "=" * 80)
    print("📈 DATASET STATISTICS")
    print("=" * 80)
    
    stats = loader.get_statistics()
    print(f"Total Conversations: {stats['total_conversations']}")
    print(f"Total Turns: {stats['total_turns']}")
    print(f"Avg Turns/Conversation: {stats['avg_turns_per_conversation']}")
    
    if stats.get('scenarios'):
        print(f"\nScenarios:")
        for scenario, count in stats['scenarios'].items():
            print(f"  - {scenario}: {count}")
    
    if stats.get('outcomes'):
        print(f"\nOutcomes:")
        for outcome, count in stats['outcomes'].items():
            print(f"  - {outcome}: {count}")
    
    # Show sample conversation
    if stats.get('sample_conversation'):
        print("\n" + "=" * 80)
        print("📝 SAMPLE CONVERSATION")
        print("=" * 80)
        sample = stats['sample_conversation']
        print(f"ID: {sample['conversation_id']}")
        print(f"Scenario: {sample['scenario']}")
        print(f"Outcome: {sample.get('outcome', 'N/A')}")
        print(f"\nTranscript (first 500 chars):")
        print(sample['transcript'][:500])
    
    # Save to file
    output_file = "sales_conversations.json"
    loader.save_to_json(output_file)
    
    # Prepare for training
    training_data = loader.prepare_for_training()
    print(f"\n✅ Prepared {len(training_data)} training examples")
    
    print("\n" + "=" * 80)
    print("✅ DATASET LOADED SUCCESSFULLY")
    print("=" * 80)
    print(f"\nNext steps:")
    print(f"1. Dataset saved to: {output_file}")
    print(f"2. Use training_data for ML model training")
    print(f"3. Annotate with BANT, intent, signals, objections")
    print(f"4. Train Random Forest + XGBoost models")


if __name__ == "__main__":
    main()