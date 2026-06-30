#!/usr/bin/env python3
"""
Debug script to check if sentiment analysis is working
Writes output to a file so we can see what's happening
"""

output_file = "sentiment_debug_output.txt"

with open(output_file, "w") as f:
    f.write("=" * 60 + "\n")
    f.write("SENTIMENT ANALYSIS DEBUG\n")
    f.write("=" * 60 + "\n\n")
    
    # Test 1: Import
    f.write("1. Testing imports...\n")
    try:
        from transformers import pipeline
        f.write("   ✓ transformers imported\n")
    except Exception as e:
        f.write(f"   ✗ Error: {e}\n")
        exit(1)
    
    # Test 2: Load model
    f.write("\n2. Loading sentiment model...\n")
    try:
        sentiment_model = pipeline("sentiment-analysis")
        f.write("   ✓ Model loaded\n")
    except Exception as e:
        f.write(f"   ✗ Error: {e}\n")
        exit(1)
    
    # Test 3: Test sentiment
    f.write("\n3. Testing sentiment analysis...\n")
    test_texts = [
        "I am very happy today",
        "This is terrible",
        "The weather is nice"
    ]
    
    for text in test_texts:
        try:
            result = sentiment_model(text)
            f.write(f"   Input: '{text}'\n")
            f.write(f"   Result: {result}\n")
            f.write(f"   ✓ Sentiment: {result[0]['label']}, Score: {result[0]['score']:.4f}\n\n")
        except Exception as e:
            f.write(f"   ✗ Error: {e}\n\n")
    
    f.write("=" * 60 + "\n")
    f.write("DEBUG COMPLETE\n")
    f.write("=" * 60 + "\n")

print(f"Debug output written to: {output_file}")
print("Check the file to see results")