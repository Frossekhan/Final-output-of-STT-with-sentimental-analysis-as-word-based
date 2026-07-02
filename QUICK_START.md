# ⚡ Quick Start Guide

Get the Sales Intelligence Platform running in 5 minutes.

## Step 1: Install Dependencies (2 minutes)

```bash
pip install fastapi uvicorn websockets sounddevice numpy scipy librosa faster-whisper scikit-learn xgboost pydantic python-dotenv aiofiles
```

Or use requirements file:
```bash
pip install -r requirements.txt
```

## Step 2: Start Server (Terminal 1)

```bash
python server.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**That's it! Server is running.**

## Step 3: Start Client (Terminal 2)

```bash
python client.py
```

You should see:
```
INFO - Recording started. Listening to microphone...
```

**Now you can speak naturally and watch real-time analysis!**

---

## 🎤 Try It Out

Say something like:

> "Hello, I'm the CEO of a technology company. We need a CRM solution with a budget of 20 lakhs and want to implement it in 3 months. Can you send us a quote?"

Watch the real-time output:
- ✅ Transcription
- ✅ Lead Score (HOT/WARM/COLD)
- ✅ BANT Analysis
- ✅ Buying Signals
- ✅ ICP Match
- ✅ Recommendations

---

## 📊 Understanding the Output

### Lead Score
- 🔴 **HOT** (75%+): Ready to buy - start closing
- 🟡 **WARM** (50-74%): Interested - nurture and follow up
- 🔵 **COLD** (<50%): Early stage - focus on education

### Key Metrics
| Component | What it measures |
|-----------|-----------------|
| Emotion | Tone, enthusiasm, confidence |
| BANT | Budget, Authority, Need, Timeline |
| Intent | Customer's intention (pricing, demo, buy, etc.) |
| Buying Signals | Indicators of purchase readiness |
| Objections | Concerns that need addressing |
| ICP | How well customer fits ideal profile |

---

## 🚀 Common Conversation Examples

### Example 1: Strong Lead
```
"Hi, I'm the decision maker. We have $50k budget and need this by end of month. 
Send us a proposal ASAP."
```
**Expected Result**: HOT (85%+) - Immediate action needed

### Example 2: Warm Lead
```
"We're interested in your solution. Can you explain the features? 
Also, how much does it cost?"
```
**Expected Result**: WARM (65-75%) - Schedule follow-up

### Example 3: Cold Lead
```
"I'm just exploring options right now. We don't have budget yet."
```
**Expected Result**: COLD (30-40%) - Focus on education

---

## 🔧 Customization (Optional)

### Use Different Whisper Model

Edit `streaming_stream_processor.py`, line ~25:

```python
self.model = WhisperModel("base")  # Change to: tiny, small, medium, large
```

**Speed vs Accuracy:**
- `tiny`: Fast (2-3s/chunk) - Lower accuracy
- `base`: Balanced (3-6s/chunk) - Good accuracy (default)
- `small`: Slower (8-12s/chunk) - Better accuracy
- `medium`/`large`: Very slow but best accuracy

### Use GPU for Speed

Same file, line ~25:

```python
device="auto"  # Automatically uses GPU if available
# Or explicitly:
device="cuda"  # NVIDIA GPU
device="cpu"   # CPU only
```

### Change Server Port

Edit `server.py`, line ~300:

```python
uvicorn.run(
    "server:app",
    port=8000  # Change to your desired port
)
```

---

## ❓ FAQ

**Q: Microphone not detected?**
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```
Then update device ID if needed.

**Q: Too slow?**
- Use GPU: Add CUDA_VISIBLE_DEVICES
- Use smaller model: Change to "tiny"
- Reduce chunk_duration to 1.0 second

**Q: Connection refused error?**
- Make sure server is running in Terminal 1
- Check firewall settings

**Q: How accurate is it?**
- Emotion: ~80%
- Transcription: ~90%+
- Intent: ~80%
- Overall: Depends on audio quality and conversation

---

## 📈 Next Steps

1. ✅ **Test with sample conversations** - Try different scenarios
2. 🔌 **Integrate with your CRM** - Connect to Salesforce/HubSpot
3. 📊 **Set up dashboard** - Create web UI for visualization
4. 🚀 **Deploy to cloud** - AWS/GCP/Azure
5. 📚 **Fine-tune models** - Train on your data

---

## 🆘 Getting Help

1. Check server logs:
```bash
tail -f server.log
```

2. Test microphone:
```bash
python -c "
import sounddevice as sd
recording = sd.rec(int(2 * 16000), samplerate=16000, channels=1, dtype='float32')
sd.wait()
print('Microphone works!')
"
```

3. Test connection:
```bash
python -c "
import asyncio
import websockets
async def test():
    async with websockets.connect('ws://localhost:8000/ws/test') as ws:
        print('Connection successful!')
asyncio.run(test())
"
```

---

## 💡 Pro Tips

1. **Clear audio works best** - Minimize background noise
2. **Natural speech** - Avoid reading scripts
3. **Complete sentences** - Better analysis with full context
4. **Multiple conversations** - Each session gets independent analysis
5. **Monitor trends** - Track lead scores across similar conversations

---

**You're all set! 🎉 Start analyzing sales conversations with AI.**

Need more info? See `README.md` for detailed documentation.
