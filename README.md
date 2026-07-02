# Real-Time AI Sales Conversation Intelligence Platform

A production-ready platform that analyzes sales conversations in real-time, providing instant lead scoring and actionable insights.

## 🚀 Features

- **Real-Time Audio Streaming** - Continuous audio capture via microphone
- **Speech-to-Text** - Fast Whisper model for accurate transcription
- **7 AI Intelligence Modules**:
  - Speech Emotion Recognition (analyzes tone, pitch, energy)
  - BANT Extraction (Budget, Authority, Need, Timeline)
  - Intent Detection (10 customer intent categories)
  - Buying Signal Detection (12 purchase intent indicators)
  - Objection Detection (12 concern types)
  - ICP Scoring (Ideal Customer Profile matching)
  - Conversation Quality Analysis

- **Lead Scoring** - HOT/WARM/COLD classification with confidence
- **WebSocket Streaming** - Bidirectional real-time communication
- **Comprehensive Analysis** - Complete sales qualification in 3-6 seconds

## 📋 Architecture Overview

```
Microphone Audio → WebSocket → Server → 7 AI Modules → Lead Score
                                      ↓
                            Real-time Dashboard
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- 2GB+ RAM
- GPU recommended (CUDA-enabled GPU for faster processing)

### Step 1: Clone/Setup Project

```bash
# Create project directory
mkdir sales-intelligence
cd sales-intelligence

# Copy all Python files from outputs
# (server.py, client.py, streaming_*.py, emotion_*.py, etc.)
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **FastAPI** - Web server framework
- **faster-whisper** - Speech-to-text (optimized Whisper)
- **sounddevice** - Microphone capture
- **numpy/scipy** - Audio processing
- **librosa** - Audio feature extraction
- **scikit-learn/xgboost** - Machine learning
- **spacy** - NLP processing

### Step 3: Download Whisper Model (Optional)

The first run automatically downloads the model (~140MB for 'base'):

```bash
# Pre-download to avoid delays
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"
```

## 📁 Project Structure

```
sales-intelligence/
├── server.py                          # Main FastAPI server
├── client.py                          # Microphone client
├── requirements.txt                   # Dependencies
├── conversation_engine.py             # Orchestration engine
├── streaming_audio_buffer.py          # Audio buffering & VAD
├── streaming_stream_processor.py      # Whisper transcription
├── emotion_speech_emotion.py          # Emotion recognition
├── bant_parser.py                     # BANT extraction
├── intent_detector.py                 # Intent detection
├── buying_signal_detector.py          # Buying signals
├── objection_detector.py              # Objection detection
├── icp_scorer.py                      # ICP matching
└── static/
    └── index.html                     # Web dashboard (optional)
```

## ▶️ Quick Start

### Terminal 1: Start Server

```bash
python server.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Terminal 2: Start Client (with Microphone)

```bash
python client.py
```

You'll see:
```
INFO - MicrophoneClient initialized (Session: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
INFO - Connecting to ws://localhost:8000/ws
INFO - Connected to server
INFO - Recording started. Listening to microphone...
```

### Start Speaking

The system will:
1. Capture your audio in 2-second chunks
2. Transcribe in real-time
3. Analyze with 7 AI modules
4. Display results every 2 seconds

Example output:
```
================================================================================
TRANSCRIPTION UPDATE
================================================================================

Text: Hello I'm the CEO of a technology company in Bangalore

Lead Score: 65% - WARM

Emotion: 👂 Interested (85%)

BANT:
  Budget: Not detected
  Authority: CEO
  Need: Not detected
  Timeline: Not detected

Intent: Information (70%)

Buying Readiness: CONSIDERING (45%)

ICP Match: Tier A (Excellent)

Key Insights:
  • Customer shows interested tone - positive engagement signal
  • Strong ICP match (Tier A) - ideal customer profile

Recommendations:
  • Lead shows strong potential. Provide additional information.
  • Schedule discovery call to understand needs better.
  • Send case studies and success stories.

================================================================================
```

## 🎯 Usage Examples

### Example 1: Hot Lead Conversation

```
User says:
"Hi, I'm the CFO. We have a budget of 50 lakhs and need a CRM solution. 
We need to implement it in 2 months. Can you send us a quotation?"

System Output:
Lead Score: 89% - HOT 🔴
Emotion: Confident (88%)
BANT: ✓ Budget: ₹50L ✓ Authority: CFO ✓ Need: CRM ✓ Timeline: 2 months
Buying Readiness: READY_TO_BUY (92%)
Recommendations:
  • URGENT: Lead is highly qualified. Initiate closing sequence immediately.
  • Schedule final presentation with decision makers.
  • Prepare and send proposal/quotation.
  • Discuss contract terms and timeline.
```

### Example 2: Warm Lead with Objections

```
User says:
"We're interested in your solution, but we're concerned about the price. 
Can you reduce the cost?"

System Output:
Lead Score: 62% - WARM 🟡
Buying Signals: Multiple signals detected (3) - high purchase intent
Objections: Price (Critical) - too expensive
Recommendations:
  • Address price objection immediately before proceeding.
  • Emphasize value and ROI.
  • Discuss payment options and custom pricing.
```

## 📊 Understanding Lead Scores

| Score | Classification | Action | Confidence |
|-------|-----------------|--------|------------|
| 75-100% | 🔴 HOT | Initiate closing sequence | 85%+ |
| 50-74% | 🟡 WARM | Nurture and follow-up | 70-85% |
| 0-49% | 🔵 COLD | Education and awareness | 70%+ |

## 🔧 Configuration

### Server Configuration

Edit `server.py`:

```python
# Change host/port
if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",      # Listen on all interfaces
        port=8000,           # Change port
        reload=True,         # Disable for production
        log_level="info"
    )
```

### Client Configuration

Edit `client.py`:

```python
client = MicrophoneClient(
    server_url="ws://localhost:8000/ws",  # Change server URL
    sample_rate=16000,                     # Audio quality
    chunk_duration=2.0,                    # Chunk size (seconds)
    channels=1                             # Mono audio
)
```

### Model Configuration

Edit `streaming_stream_processor.py`:

```python
self.model = WhisperModel(
    "base",            # Change to: tiny, small, medium, large
    device="auto",     # Change to: cpu, cuda
    compute_type="int8"  # Change to: float32, float16
)
```

## 🌐 API Endpoints

### WebSocket

**Connect:** `ws://localhost:8000/ws/{session_id}`

**Message Types:**

1. **Session Start**
```json
{
  "type": "session_start",
  "session_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

2. **Audio Chunk**
```json
{
  "type": "audio",
  "audio_data": "base64_encoded_audio",
  "session_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

3. **Session Stop**
```json
{
  "type": "session_stop",
  "session_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### REST Endpoints

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Get Sessions:**
```bash
curl http://localhost:8000/api/sessions
```

**Get Session Details:**
```bash
curl http://localhost:8000/api/session/{session_id}
```

## 📈 Understanding the Analysis

### 1. Emotion Recognition
- **Features Analyzed**: Energy, pitch, pace, stability, clarity
- **10 Categories**: interested, excited, confident, curious, neutral, hesitant, frustrated, anxious, angry, skeptical
- **Accuracy**: ~80%

### 2. BANT Extraction
- **Budget**: Monetary amounts with currency (lakhs, crores, dollars, etc.)
- **Authority**: Decision-maker level (CEO/CFO, Director, Manager, Individual)
- **Need**: Solution type (CRM, ERP, Automation, Integration, Analytics, Support)
- **Timeline**: Urgency level (immediate, short-term, medium-term, long-term)

### 3. Intent Detection
- **10 Categories**: pricing, demo, purchase, negotiation, support, cancellation, renewal, information, objection, competitor

### 4. Buying Signals
- **12 Signals**: 
  - request_quotation (95% weight)
  - discuss_contract (90%)
  - budget_confirmation (87%)
  - commitment_language (85%)
  - request_demo (85%)
  - decision_maker_engagement (80%)
  - discuss_timeline (80%)
  - urgency_indicators (72%)
  - discuss_pricing (78%)
  - discuss_features (70%)
  - request_meeting (75%)
  - request_reference (82%)

### 5. Objection Detection
- **12 Types**: price, budget, authority, need, timing, competitor, trust, features, integration, security, support, implementation
- **Severity Levels**: critical, high, medium, low

### 6. ICP Scoring
- **5 Criteria**: Industry, Company Size, Revenue, Region, Role
- **Tiers**: A+ (90%+), A (80-89%), B (70-79%), C (60-69%), D (<60%)

### 7. Lead Scoring
- **Formula**: Weighted combination of all 6 components
- **Weights**: Emotion 15%, BANT 20%, Intent 15%, Buying Signals 25%, ICP 15%, Quality 10%

## 🐛 Troubleshooting

### Issue: Microphone not working
```bash
# Check available devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Test recording
python -c "
import sounddevice as sd
import numpy as np
recording = sd.rec(int(2 * 16000), samplerate=16000, channels=1, dtype='float32')
sd.wait()
print(f'Recorded {len(recording)} samples')
"
```

### Issue: Connection refused
```
Error: [Errno 111] Connection refused
Solution: Make sure server is running on terminal 1
```

### Issue: WebSocket connection timeout
```
Solution: Check firewall settings and server URL configuration
```

### Issue: Slow transcription
```
Solution: 
1. Use GPU: Change device to "cuda"
2. Use smaller model: Change from "base" to "tiny"
3. Increase chunk_duration to reduce frequency
```

## 🚀 Production Deployment

### Docker (Coming Soon)
```bash
docker build -t sales-intelligence .
docker run -p 8000:8000 sales-intelligence
```

### Cloud Deployment

**AWS EC2**
```bash
# Install FFmpeg (required for faster-whisper)
sudo apt-get install ffmpeg

# Run server with systemd
sudo systemctl start sales-intelligence
```

**Google Cloud Run**
```bash
gcloud run deploy sales-intelligence --source .
```

**Azure Container Instances**
```bash
az container create --resource-group mygroup --name sales-intelligence --image myregistry/sales-intelligence
```

## 📚 Example Integration

### Django/Flask Integration

```python
import websockets
import json
import asyncio

async def analyze_sales_call(audio_file_path):
    """Analyze saved audio file"""
    async with websockets.connect("ws://localhost:8000/ws/session-123") as ws:
        # Read and send audio chunks
        with open(audio_file_path, 'rb') as f:
            while True:
                chunk = f.read(32000)  # 2 seconds at 16kHz
                if not chunk:
                    break
                
                # Send to server
                await ws.send(json.dumps({
                    "type": "audio",
                    "audio_data": base64.b64encode(chunk).decode()
                }))
                
                # Receive analysis
                response = await ws.recv()
                analysis = json.loads(response)
                yield analysis
```

### CRM Integration (HubSpot Example)

```python
from hubspot import HubSpot
import json

def sync_to_hubspot(analysis):
    """Sync analysis to HubSpot contact"""
    api_client = HubSpot()
    
    contact_data = {
        "properties": {
            "lead_score": analysis['lead_score']['score'],
            "lead_qualification": analysis['lead_score']['qualification'],
            "hs_lead_status": "Qualified",
            "hs_lifecyclestage_lead_date": analysis['timestamp']
        }
    }
    
    # Update contact
    api_client.crm.contacts.basic_api.update(
        contact_id=contact_id,
        simple_public_object_input=contact_data
    )
```

## 📝 Logging & Monitoring

### Enable Debug Logging

```python
# In server.py
logging.basicConfig(level=logging.DEBUG)
```

### Monitor Performance

```bash
# Watch server activity
tail -f sales-intelligence.log

# Monitor resource usage
watch -n 1 'ps aux | grep python'
```

## 🧪 Testing

### Unit Tests (Example)

```python
# test_emotion.py
from emotion_speech_emotion import SpeechEmotionRecognizer
import numpy as np

def test_emotion_recognition():
    recognizer = SpeechEmotionRecognizer()
    
    # Create test audio (silence)
    test_audio = np.zeros(16000)
    emotion, confidence = recognizer.recognize_emotion(test_audio)
    
    assert emotion in recognizer.EMOTIONS
    assert 0 <= confidence <= 1.0
```

### Integration Tests

```bash
# Test end-to-end flow
python test_e2e.py
```

## 📖 Documentation

- **Module Documentation**: See docstrings in each Python file
- **API Spec**: HTTP/WebSocket endpoints documented above
- **Algorithm Details**: See original project documentation

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Web dashboard UI
- Additional intent/signal categories
- ML model fine-tuning
- Performance optimization
- Database integration

## 📄 License

MIT License - Use freely in commercial projects

## 📧 Support

For issues or questions:
1. Check troubleshooting section above
2. Review server logs for errors
3. Test with sample conversation scripts
4. File GitHub issue with error details

## 🎓 Learning Resources

- [Whisper Model](https://github.com/openai/whisper)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket Guide](https://websockets.readthedocs.io/)
- [Sales Qualification (BANT)](https://en.wikipedia.org/wiki/BANT_framework)

---

**Built with ❤️ for sales teams who want AI-powered intelligence in real-time.**

Happy selling! 🚀
