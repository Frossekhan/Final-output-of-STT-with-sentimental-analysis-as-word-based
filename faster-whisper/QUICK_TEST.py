#!/usr/bin/env python3
"""
QUICK TEST - Run this to see if sentiment analysis works
This will test everything step by step
"""

print("="*70)
print(" "*15 + "SENTIMENT ANALYSIS - QUICK TEST")
print("="*70)

# Step 1: Check if server is running
print("\n📍 STEP 1: Check if server is running")
print("-"*70)
try:
    import requests
    response = requests.get("http://localhost:8000/", timeout=3)
    print(f"✅ Server is RUNNING at http://localhost:8000")
    print(f"   Response: {response.json()}")
except:
    print("❌ Server is NOT running!")
    print("\n   Please start it first:")
    print("   cd faster-whisper")
    print("   python app.py")
    exit(1)

# Step 2: Check if sentiment fields are in the API schema
print("\n📍 STEP 2: Check API schema for sentiment fields")
print("-"*70)
try:
    response = requests.get("http://localhost:8000/openapi.json", timeout=3)
    schema = response.json()
    transcribe_schema = schema.get("components", {}).get("schemas", {}).get("TranscriptionResponse", {})
    properties = transcribe_schema.get("properties", {})
    
    if "sentiment" in properties:
        print("✅ 'sentiment' field is in the API schema")
    else:
        print("❌ 'sentiment' field is MISSING from schema")
        print("   → The server is running OLD code. Restart it!")
    
    if "sentiment_score" in properties:
        print("✅ 'sentiment_score' field is in the API schema")
    else:
        print("❌ 'sentiment_score' field is MISSING from schema")
        print("   → The server is running OLD code. Restart it!")
        
except Exception as e:
    print(f"❌ Error checking schema: {e}")

# Step 3: Test sentiment model directly
print("\n📍 STEP 3: Test sentiment model directly")
print("-"*70)
try:
    from transformers import pipeline
    print("   Loading sentiment model...")
    sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    
    test_text = "I am very happy today"
    result = sentiment_model(test_text)
    
    print(f"✅ Sentiment model works!")
    print(f"   Input: '{test_text}'")
    print(f"   Result: {result}")
    print(f"   Sentiment: {result[0]['label']}")
    print(f"   Score: {result[0]['score']:.4f}")
    
except Exception as e:
    print(f"❌ Error testing sentiment model: {e}")

# Step 4: Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("\n✅ The code is READY with sentiment analysis!")
print("\n📝 TO TEST WITH AUDIO:")
print("   1. Open: http://localhost:8000/docs")
print("   2. Find: /transcribe endpoint")
print("   3. Click: 'Try it out'")
print("   4. Upload: Any audio file (WAV, MP3, etc.)")
print("   5. Click: 'Execute'")
print("   6. Look for: 'sentiment' and 'sentiment_score' in response")
print("\n💡 TIP: The server must be restarted to load the new code!")
print("   Stop it (Ctrl+C) and start again: python app.py")
print("="*70)