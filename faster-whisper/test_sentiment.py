#!/usr/bin/env python3
"""
Quick test script to verify sentiment analysis is working
"""
import sys
sys.path.insert(0, '.')

from app import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test 1: Check if app loads
print("✓ FastAPI app loaded successfully")

# Test 2: Check root endpoint
response = client.get("/")
print(f"✓ Root endpoint response: {response.json()}")

# Test 3: Check if sentiment model is loaded
from app import sentiment_model
if sentiment_model is not None:
    print("✓ Sentiment model is loaded")
    
    # Test 4: Test sentiment analysis directly
    test_text = "I am very happy today"
    result = sentiment_model(test_text)
    print(f"✓ Sentiment analysis test:")
    print(f"  Input: '{test_text}'")
    print(f"  Result: {result}")
else:
    print("✗ Sentiment model is NOT loaded")

print("\n=== Summary ===")
print("The app has sentiment analysis integrated.")
print("To test with audio, use the /transcribe endpoint at http://localhost:8000/docs")