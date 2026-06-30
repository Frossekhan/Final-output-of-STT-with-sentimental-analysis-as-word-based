#!/usr/bin/env python3
"""
Test the /transcribe endpoint to see if sentiment analysis works
"""
import requests
import json
import sys

print("="*70)
print("TESTING /TRANSCRIBE ENDPOINT WITH SENTIMENT ANALYSIS")
print("="*70)

# Create a simple test audio file (silent WAV)
# This is a minimal valid WAV file header
wav_header = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x00\x04\x00\x00\x00\x04\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00'

print("\n1. Testing /transcribe endpoint with sample audio...")
print("-"*70)

try:
    # Prepare the request
    url = "http://localhost:8000/transcribe"
    
    # Create a file-like object with the WAV header
    files = {
        'audio': ('test.wav', wav_header, 'audio/wav')
    }
    data = {
        'language': 'en',
        'task': 'transcribe'
    }
    
    print("   Sending request to /transcribe...")
    response = requests.post(url, files=files, data=data, timeout=30)
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n   ✅ Request successful!")
        print("\n   Response:")
        print(json.dumps(result, indent=4))
        
        # Check for sentiment fields
        print("\n" + "-"*70)
        print("CHECKING FOR SENTIMENT ANALYSIS:")
        print("-"*70)
        
        if "sentiment" in result:
            print(f"✅ 'sentiment' field found: {result['sentiment']}")
        else:
            print("❌ 'sentiment' field NOT found in response")
            print("   → Server is running OLD code without sentiment analysis")
        
        if "sentiment_score" in result:
            print(f"✅ 'sentiment_score' field found: {result['sentiment_score']}")
        else:
            print("❌ 'sentiment_score' field NOT found in response")
            print("   → Server is running OLD code without sentiment analysis")
            
    else:
        print(f"\n   ❌ Request failed with status {response.status_code}")
        print(f"   Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("   ❌ ERROR: Cannot connect to server!")
    print("\n   Please start the server first:")
    print("   cd faster-whisper")
    print("   python app.py")
    sys.exit(1)
    
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)