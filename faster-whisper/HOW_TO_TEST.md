# How to Test Sentiment Analysis

## The Problem
You said "still i didnt get output as sentimental analysis too"

This means the server is probably still running the OLD code. You need to:

## Step 1: Stop the Current Server
1. Go to the terminal/command prompt where the server is running
2. Press `Ctrl+C` to stop it
3. Or close that terminal window

## Step 2: Start the Server with NEW Code
**Option A: Use the batch file (Easiest)**
```bash
cd faster-whisper
start_server.bat
```

**Option B: Manual start**
```bash
cd faster-whisper
python app.py
```

You should see these messages:
```
INFO:     Loading faster-whisper model base on cpu (int8)
INFO:     Model loaded successfully
INFO:     Loading sentiment model...
INFO:     Sentiment model loaded successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 3: Test the API

### Method 1: Using Swagger UI (Recommended)
1. Open browser: http://localhost:8000/docs
2. Find the `/transcribe` endpoint
3. Click **"Try it out"**
4. Upload an audio file (WAV, MP3, etc.)
5. Click **"Execute"**
6. Look at the response - you should see:
   ```json
   {
     "text": "I am very happy today",
     "language": "en",
     "language_probability": 0.997,
     "duration": 2.5,
     "duration_after_vad": 2.3,
     "sentiment": "POSITIVE",        <-- THIS IS NEW!
     "sentiment_score": 0.9987,      <-- THIS IS NEW!
     "segments": [...]
   }
   ```

### Method 2: Using the Test HTML Page
1. Open in browser: `faster-whisper/test_api.html`
2. Click "Test Root Endpoint" to verify server is running
3. Follow the instructions to test with audio

### Method 3: Using curl/Postman
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@your_audio_file.wav" \
  -F "language=en"
```

## What Changed in the Code

### 1. Added Import
```python
from transformers import pipeline
```

### 2. Added Sentiment Model Variable
```python
sentiment_model = None
```

### 3. Updated Startup to Load Sentiment Model
```python
@app.on_event("startup")
async def startup_event():
    global model, sentiment_model  # <-- Added sentiment_model
    
    # Load whisper model (existing code)
    if model is None:
        model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    
    # Load sentiment model (NEW!)
    if sentiment_model is None:
        sentiment_model = pipeline("sentiment-analysis")
```

### 4. Updated Response Model
```python
class TranscriptionResponse(BaseModel):
    text: str
    language: str
    language_probability: float
    duration: float
    duration_after_vad: float
    
    sentiment: str = Field(...)           # <-- NEW!
    sentiment_score: float = Field(...)   # <-- NEW!
    
    segments: List[Segment]
```

### 5. Added Sentiment Analysis in Transcribe Endpoint
```python
# After getting transcribed text
text = " ".join([segment.text for segment in segments]).strip()

# NEW: Perform sentiment analysis
sentiment_result = sentiment_model(text)
sentiment_label = sentiment_result[0]["label"]
sentiment_score = round(sentiment_result[0]["score"], 4)

# Return with sentiment data
return TranscriptionResponse(
    text=text,
    sentiment=sentiment_label,        # <-- NEW!
    sentiment_score=sentiment_score,  # <-- NEW!
    # ... other fields
)
```

## Example Response

**Before (without sentiment):**
```json
{
  "text": "I love this product",
  "language": "en",
  "language_probability": 0.99,
  "duration": 3.2,
  "segments": [...]
}
```

**After (with sentiment):**
```json
{
  "text": "I love this product",
  "language": "en",
  "language_probability": 0.99,
  "duration": 3.2,
  "sentiment": "POSITIVE",      <-- ADDED
  "sentiment_score": 0.9998,    <-- ADDED
  "segments": [...]
}
```

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'transformers'"
**Solution:**
```bash
pip install transformers torch
```

### Problem: Server won't start / crashes on startup
**Solution:**
1. Check if port 8000 is already in use
2. Stop all Python processes and try again
3. Check the error message in the terminal

### Problem: Sentiment fields not in response
**Solution:**
1. Make sure you stopped the OLD server (Ctrl+C)
2. Start a NEW server with the updated code
3. The old server won't have sentiment analysis!

### Problem: "sentiment_model is not defined"
**Solution:**
This means the server is running old code. Restart it!

## Quick Test

After starting the server, run this in a new terminal:
```bash
cd faster-whisper
python verify_sentiment.py
```

This will test the sentiment model directly and show you it's working.

## Summary

**The sentiment analysis IS implemented in the code.** You just need to:
1. Stop the old server
2. Start a new server with the updated code
3. Test using http://localhost:8000/docs

The response will now include:
- `sentiment`: "POSITIVE" or "NEGATIVE"
- `sentiment_score`: Confidence score (0.0 to 1.0)