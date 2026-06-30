#!/usr/bin/env python3
"""
Simple test with timeout to check sentiment analysis
"""
import sys
import signal

def timeout_handler(signum, frame):
    print("TIMEOUT: Script took too long")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout

print("Starting simple sentiment test...")
print(f"Python version: {sys.version}")

try:
    print("\n1. Importing transformers...")
    from transformers import pipeline
    print("   ✓ SUCCESS: transformers imported")
    
    print("\n2. Loading sentiment model (this may take a minute)...")
    sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    print("   ✓ SUCCESS: Model loaded")
    
    print("\n3. Testing sentiment analysis...")
    test_text = "I am very happy today"
    result = sentiment_model(test_text)
    print(f"   Input: '{test_text}'")
    print(f"   Result: {result}")
    print(f"   ✓ Sentiment: {result[0]['label']}, Score: {result[0]['score']:.4f}")
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60)
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

signal.alarm(0)  # Cancel timeout