#!/usr/bin/env python3
"""
Test the actual API to see if sentiment analysis is working
"""
import requests
import json

print("="*60)
print("TESTING REAL API WITH SENTIMENT ANALYSIS")
print("="*60)

# Test 1: Check if server is running
print("\n1. Checking if server is running...")
try:
    response = requests.get("http://localhost:8000/", timeout=5)
    if response.status_code == 200:
        print(f"   ✓ Server is running")
        print(f"   Response: {response.json()}")
    else:
        print(f"   ✗ Server returned status {response.status_code}")
        exit(1)
except Exception as e:
    print(f"   ✗ Server is not running: {e}")
    print("\n   Please start the server first:")
    print("   cd faster-whisper")
    print("   python app.py")
    exit(1)

# Test 2: Check the API schema
print("\n2. Checking API schema...")
try:
    response = requests.get("http://localhost:8000/openapi.json", timeout=5)
    schema = response.json()
    
    # Check if sentiment fields are in the schema
    transcribe_schema = schema.get("components", {}).get("schemas", {}).get("TranscriptionResponse", {})
    
    if "sentiment" in transcribe_schema.get("properties", {}):
        print("   ✓ 'sentiment' field found in schema")
    else:
        print("   ✗ 'sentiment' field NOT in schema - server needs restart!")
    
    if "sentiment_score" in transcribe_schema.get("properties", {}):
        print("   ✓ 'sentiment_score' field found in schema")
    else:
        print("   ✗ 'sentiment_score' field NOT in schema - server needs restart!")
        
except Exception as e:
    print(f"   ✗ Error checking schema: {e}")

print("\n" + "="*60)
print("NEXT STEPS:")
print("="*60)
print("1. Make sure server is running (python app.py)")
print("2. Open http://localhost:8000/docs")
print("3. Use /transcribe endpoint with an audio file")
print("4. Check the response for 'sentiment' and 'sentiment_score' fields")
print("="*60)