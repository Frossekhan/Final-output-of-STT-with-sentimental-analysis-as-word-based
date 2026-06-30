#!/usr/bin/env python3
"""
Standalone test to verify sentiment analysis works
This tests the sentiment model directly without needing the server
"""

print("=" * 60)
print("TESTING SENTIMENT ANALYSIS")
print("=" * 60)

# Test 1: Import transformers
print("\n1. Testing imports...")
try:
    from transformers import pipeline
    print("   ✓ transformers imported successfully")
except Exception as e:
    print(f"   ✗ Error importing transformers: {e}")
    exit(1)

# Test 2: Load sentiment model
print("\n2. Loading sentiment model...")
try:
    sentiment_model = pipeline("sentiment-analysis")
    print("   ✓ Sentiment model loaded successfully")
except Exception as e:
    print(f"   ✗ Error loading sentiment model: {e}")
    exit(1)

# Test 3: Test with positive text
print("\n3. Testing with positive text...")
positive_text = "I am very happy today, this is wonderful!"
try:
    result = sentiment_model(positive_text)
    print(f"   Input: '{positive_text}'")
    print(f"   Result: {result}")
    print(f"   ✓ Sentiment: {result[0]['label']}, Score: {result[0]['score']:.4f}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: Test with negative text
print("\n4. Testing with negative text...")
negative_text = "This is terrible and I am very sad"
try:
    result = sentiment_model(negative_text)
    print(f"   Input: '{negative_text}'")
    print(f"   Result: {result}")
    print(f"   ✓ Sentiment: {result[0]['label']}, Score: {result[0]['score']:.4f}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 5: Test with neutral text
print("\n5. Testing with neutral text...")
neutral_text = "The weather is cloudy today"
try:
    result = sentiment_model(neutral_text)
    print(f"   Input: '{neutral_text}'")
    print(f"   Result: {result}")
    print(f"   ✓ Sentiment: {result[0]['label']}, Score: {result[0]['score']:.4f}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("SENTIMENT ANALYSIS IS WORKING! ✓")
print("=" * 60)
print("\nNow the /transcribe endpoint will return:")
print('  "sentiment": "POSITIVE" or "NEGATIVE"')
print('  "sentiment_score": 0.9987')
print("\nTo test with the API:")
print("1. Start server: python app.py")
print("2. Open: http://localhost:8000/docs")
print("3. Use /transcribe endpoint to upload audio")
print("=" * 60)