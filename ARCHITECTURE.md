# AI Sales Intelligence Platform - Complete Architecture Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Data Flow](#data-flow)
3. [Component Details](#component-details)
4. [Processing Pipeline](#processing-pipeline)
5. [Real-Time Operation](#real-time-operation)
6. [Lead Scoring Algorithm](#lead-scoring-algorithm)
7. [Example Walkthrough](#example-walkthrough)

---

## System Overview

The AI Sales Intelligence Platform is a **real-time conversation intelligence system** that transforms sales calls into actionable insights. It combines multiple AI/ML techniques to analyze speech, extract business intelligence, and score leads automatically.

### Key Differentiators
- **Voice-based emotion detection** (not word-based sentiment)
- **Real-time processing** via WebSockets
- **Comprehensive BANT extraction** (Budget, Authority, Need, Timeline)
- **Multi-layer analysis** (emotion + intent + signals + objections + ICP)
- **Automated lead scoring** (HOT/WARM/COLD)

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CUSTOMER VOICE                               │
│                    (Microphone/Audio File)                           │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FRONTEND LAYER                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Browser (HTML/JavaScript)                                   │  │
│  │  - MediaRecorder API (microphone capture)                    │  │
│  │  - WebSocket client (real-time communication)                │  │
│  │  - Dashboard UI (visualization)                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ WebSocket (audio chunks)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BACKEND LAYER (FastAPI)                                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  WebSocket Endpoint (/ws)                                    │  │
│  │  - Receives base64-encoded audio chunks                      │  │
│  │  - Routes to streaming processor                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STREAMING LAYER                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Audio Buffer (2-second chunks with 0.5s overlap)            │  │
│  │  - Buffers incoming audio                                    │  │
│  │  - Voice Activity Detection (VAD)                            │  │
│  │  - Extracts speech segments                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Stream Processor (faster-whisper)                           │  │
│  │  - Real-time transcription                                   │  │
│  │  - Language detection                                        │  │
│  │  - Segment extraction with timestamps                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ Transcript + Audio
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CONVERSATION INTELLIGENCE ENGINE (Central Orchestrator)            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  1. Speech Emotion Recognition                               │  │
│  │     - Extracts audio features (energy, pitch, pace, etc.)    │  │
│  │     - Classifies into 10 emotion categories                  │  │
│  │     - Tracks emotion trajectory                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  2. BANT Extraction                                          │  │
│  │     - Budget: ₹20 Lakhs, $50K, etc.                         │  │
│  │     - Authority: CEO, Manager, etc.                          │  │
│  │     - Need: CRM, ERP, etc.                                   │  │
│  │     - Timeline: 3 months, ASAP, etc.                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  3. Intent Detection                                         │  │
│  │     - pricing, demo, purchase, negotiation, etc.             │  │
│  │     - Confidence scoring                                     │  │
│  │     - Intent progression tracking                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  4. Buying Signal Detection                                  │  │
│  │     - request_quotation, request_demo, etc.                  │  │
│  │     - Signal strength (0-100%)                               │  │
│  │     - Buying readiness score                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  5. Objection Detection                                      │  │
│  │     - price, budget, authority, need, timing, etc.           │  │
│  │     - Severity: critical, high, medium, low                  │  │
│  │     - Suggested responses                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  6. ICP Scoring                                              │  │
│  │     - Industry match                                         │  │
│  │     - Company size match                                     │  │
│  │     - Revenue match                                          │  │
│  │     - Region match                                           │  │
│  │     - Role match                                             │  │
│  │     - Overall ICP tier (A+ to D)                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LEAD SCORING ENGINE                                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Weighted Score Calculation:                                 │  │
│  │  - Emotion: 15%                                             │  │
│  │  - BANT: 20%                                                │  │
│  │  - Intent: 15%                                              │  │
│  │  - Buying Signals: 25%                                      │  │
│  │  - ICP: 15%                                                 │  │
│  │  - Conversation Quality: 10%                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Qualification:                                              │  │
│  │  - HOT: score >= 0.75                                       │  │
│  │  - WARM: 0.50 <= score < 0.75                               │  │
│  │  - COLD: score < 0.50                                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OUTPUT LAYER                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Real-time Dashboard (HTML/JavaScript)                       │  │
│  │  - Lead Score: 85/100 (HOT)                                 │  │
│  │  - Emotion: Interested (85%)                                 │  │
│  │  - BANT: Budget ₹20L, Authority CEO, Need CRM, Timeline 3M  │  │
│  │  - Intent: Pricing (72%)                                     │  │
│  │  - Buying Signals: Request Quotation (95%)                   │  │
│  │  - Objections: None                                          │  │
│  │  - ICP: A+ (Excellent)                                       │  │
│  │  - Recommendations: [actionable items]                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Streaming Layer

#### `streaming/websocket.py`
**Purpose**: Manages WebSocket connections for real-time audio streaming

**Key Features**:
- Connection management (connect/disconnect)
- Audio buffer management per client
- Message broadcasting
- Error handling

**Data Flow**:
```
Client → WebSocket → Manager → Buffer → Processor
```

#### `streaming/audio_buffer.py`
**Purpose**: Buffers audio chunks and performs Voice Activity Detection

**Key Components**:
- **AudioBuffer**: Collects 2-second audio chunks with 0.5s overlap
- **VADBuffer**: Detects speech vs silence using energy thresholds

**Processing**:
```
Raw Audio (16-bit PCM, 16kHz)
    ↓
Normalize to float32
    ↓
Buffer until 2 seconds
    ↓
VAD: Detect speech segments
    ↓
Output: Speech segment (numpy array)
```

#### `streaming/stream_processor.py`
**Purpose**: Real-time speech-to-text using faster-whisper

**Key Features**:
- Streaming transcription (chunk-by-chunk)
- Language detection
- Timestamp extraction
- Session management

**Processing**:
```
Audio Chunk (2s)
    ↓
faster-whisper model
    ↓
Segments with timestamps
    ↓
Text + Metadata
```

### 2. Emotion Recognition Layer

#### `emotion/speech_emotion.py`
**Purpose**: Detects emotions from voice characteristics (NOT words)

**Key Innovation**: Unlike traditional sentiment analysis that analyzes text, this analyzes **how** something is said.

**Features Extracted**:
1. **Energy**: RMS amplitude (loudness)
2. **Pitch Variation**: Zero-crossing rate (prosody)
3. **Speaking Rate**: Energy envelope analysis
4. **Stability**: Variance of energy (voice steadiness)
5. **Pause Frequency**: Silence detection
6. **Pace**: Syllable estimation
7. **Clarity**: Zero-crossing rate
8. **Tension**: High-frequency energy ratio
9. **Emphasis**: Dynamic range
10. **Consistency**: Energy variation

**Emotion Categories**:
- **Positive**: interested, excited, confident, curious
- **Negative**: frustrated, angry, anxious, hesitant
- **Neutral**: neutral, skeptical

**Scoring**:
```
For each emotion:
  score = Σ(feature_value × weight)
  
Normalize scores to sum to 1.0
Top emotion = detected emotion
Confidence = score of top emotion
```

### 3. BANT Analysis Layer

#### `bant/parser.py`
**Purpose**: Extracts sales qualification information

**Budget Extraction**:
```
Patterns:
  - "20 lakhs" → ₹20,00,000
  - "₹50 lakhs" → ₹50,00,000
  - "$10,000" → ₹8,30,000 (converted)
  - "1 crore" → ₹1,00,00,000

Categories:
  - Under 1L
  - 1L-5L
  - 5L-10L
  - 10L-50L
  - 50L+
```

**Authority Extraction**:
```
Levels:
  - CEO/CFO: "I'm the CEO", "Founder"
  - VP/Director: "VP of Sales", "Director"
  - Manager: "Team Lead", "Manager"
  - IC: "Engineer", "Analyst"
```

**Need Extraction**:
```
Categories:
  - CRM, ERP, HRMS, Marketing, E-commerce
  - Analytics, Communication, Security
  - Cloud, Mobile, Website, Support
```

**Timeline Extraction**:
```
Urgency Levels:
  - Immediate: "ASAP", "urgent", "immediately"
  - Short-term: "this week", "within a month"
  - Medium-term: "this quarter", "2-3 months"
  - Long-term: "next year", "future"
```

### 4. Intent Detection Layer

#### `intent/predict.py`
**Purpose**: Classifies customer intent

**Intent Classes**:
1. **Pricing**: "How much?", "Send quote", "Pricing"
2. **Demo**: "Show me", "Demo", "Trial"
3. **Purchase**: "Buy", "Proceed", "Ready to sign"
4. **Negotiation**: "Negotiate", "Flexible", "Terms"
5. **Support**: "Help", "Issue", "Problem"
6. **Cancellation**: "Cancel", "Refund", "End"
7. **Renewal**: "Renew", "Extend", "Continue"
8. **Information**: "Tell me", "What is", "How does"
9. **Objection**: "But", "Concern", "Worried"
10. **Competitor**: "Alternative", "Compare", "Other"

**Scoring**:
```
For each intent:
  keyword_matches = count of keywords found
  phrase_matches = count of phrases found × 2
  
  score = (keyword_matches + phrase_matches) / max_possible
  
  confidence = min(1.0, score × 3)
```

### 5. Buying Signal Detection Layer

#### `buying_signal/detect.py`
**Purpose**: Identifies strong purchase intent signals

**Signal Types** (12 total):
1. **request_quotation** (weight: 0.95)
2. **request_demo** (weight: 0.85)
3. **discuss_contract** (weight: 0.90)
4. **discuss_payment** (weight: 0.88)
5. **discuss_timeline** (weight: 0.80)
6. **request_meeting** (weight: 0.75)
7. **request_reference** (weight: 0.82)
8. **discuss_features** (weight: 0.70)
9. **discuss_pricing** (weight: 0.78)
10. **commitment_language** (weight: 0.85)
11. **urgency_indicators** (weight: 0.72)
12. **budget_confirmation** (weight: 0.87)

**Buying Readiness Score**:
```
Weighted average of recent signals
(More recent signals have higher weight)

Levels:
  - READY_TO_BUY: >= 0.8
  - HIGH_INTENT: >= 0.6
  - MEDIUM_INTENT: >= 0.4
  - LOW_INTENT: >= 0.2
  - NOT_READY: < 0.2
```

### 6. Objection Detection Layer

#### `objection/detect.py`
**Purpose**: Detects and classifies customer objections

**Objection Types** (12 total):
1. **PRICE**: "Too expensive", "Can't afford"
2. **BUDGET**: "No budget", "Budget exhausted"
3. **AUTHORITY**: "Not my decision", "Need approval"
4. **NEED**: "Don't need", "Already have solution"
5. **TIMING**: "Not right now", "Later"
6. **COMPETITOR**: "Using competitor", "Comparing options"
7. **TRUST**: "Don't trust", "Not sure about"
8. **FEATURES**: "Missing feature", "Doesn't support"
9. **SUPPORT**: "Support?", "Response time?"
10. **IMPLEMENTATION**: "Complex", "Time-consuming"
11. **RISK**: "Risky", "What if it fails?"
12. **GENERIC**: "But", "However", "Concern"

**Severity Levels**:
- **CRITICAL**: Deal-breaker (e.g., "Don't need")
- **HIGH**: Major concern (e.g., "Too expensive")
- **MEDIUM**: Moderate concern (e.g., "Support?")
- **LOW**: Minor concern (e.g., "But...")

### 7. ICP Scoring Layer

#### `icp/score.py`
**Purpose**: Scores how well a customer matches the ideal profile

**Scoring Criteria**:
1. **Industry** (weight: 25%)
   - Target: Technology, SaaS, Finance, E-commerce
   - Score: 1.0 (match), 0.3 (partial), 0.0 (no match)

2. **Company Size** (weight: 20%)
   - Target: Medium (50-200), Large (200-1000), Enterprise (1000+)
   - Score: 1.0 (match), 0.4 (partial), 0.0 (no match)

3. **Revenue** (weight: 25%)
   - Target: 10Cr-50Cr, 50Cr-200Cr, 200Cr+
   - Score: 1.0 (match), 0.3 (partial), 0.0 (no match)

4. **Region** (weight: 15%)
   - Target: India, USA, UK, Singapore, UAE
   - Score: 1.0 (match), 0.2 (no match)

5. **Role** (weight: 15%)
   - Target: CEO, CTO, CFO, Director, VP, Manager
   - Score: 1.0 (match), 0.5 (partial), 0.0 (no match)

**ICP Tiers**:
- A+ (Excellent): >= 0.8
- A (Very Good): >= 0.7
- B+ (Good): >= 0.6
- B (Average): >= 0.5
- C (Below Average): >= 0.4
- D (Poor): < 0.4

### 8. Conversation Intelligence Engine

#### `conversation_engine/engine.py`
**Purpose**: Central orchestrator that combines all analysis modules

**Processing Flow**:
```
Input: Transcript + Audio + Segments
    ↓
1. Analyze Emotion (from audio)
2. Extract BANT (from transcript)
3. Detect Intent (from transcript)
4. Detect Buying Signals (from transcript)
5. Detect Objections (from transcript)
6. Score ICP (from transcript)
7. Calculate Conversation Metrics
    ↓
Output: ConversationFeatures (all analysis results)
```

**ConversationFeatures** includes:
- Transcript and segments
- Emotion data (emotion, confidence, scores, trajectory)
- BANT data (budget, authority, need, timeline)
- Intent data (intent, confidence, progression)
- Buying signals (list with strengths)
- Objections (list with severity)
- ICP data (score, tier, matched criteria)
- Conversation metrics (duration, WPM, interruptions)

### 9. Lead Scoring Engine

**Component Scores**:

1. **Emotion Score** (15%)
   - Positive emotions (interested, excited, confident): 0.8-1.0
   - Negative emotions (frustrated, angry, anxious): 0.3-0.5
   - Neutral: 0.5

2. **BANT Score** (20%)
   - Directly uses BANT qualification score
   - Higher when all BANT elements present

3. **Intent Score** (15%)
   - Positive intents (purchase, demo, pricing): 0.7-1.0
   - Neutral intents (information, support): 0.5-0.7
   - Negative intents (cancellation, objection): 0.2-0.4

4. **Buying Signal Score** (25%)
   - Directly uses buying readiness score
   - Most heavily weighted component

5. **ICP Score** (15%)
   - Directly uses ICP overall score

6. **Conversation Quality Score** (10%)
   - Good speaking rate (120-180 WPM): +0.2
   - Low interruptions (≤2): +0.15
   - Good turn taking (≥5): +0.15
   - Base: 0.5

**Overall Score**:
```
overall_score = Σ(component_score × weight)

Qualification:
  - HOT: >= 0.75
  - WARM: >= 0.50
  - COLD: < 0.50
```

---

## Processing Pipeline

### Real-Time Streaming Pipeline

```
Time 0s:    [Audio Chunk 1] → Transcribe → "Hello"
Time 2s:    [Audio Chunk 2] → Transcribe → "Hello I'm"
Time 4s:    [Audio Chunk 3] → Transcribe → "Hello I'm the"
Time 6s:    [Audio Chunk 4] → Transcribe → "Hello I'm the CEO"
...
Time 20s:   [Complete thought] → Full Analysis → Lead Score: HOT
```

### Batch Processing Pipeline

```
Audio File
    ↓
Transcribe (full audio)
    ↓
Extract segments
    ↓
Process with Conversation Engine
    ↓
Calculate Lead Score
    ↓
Return complete analysis
```

---

## Real-Time Operation

### WebSocket Message Flow

```
Client                              Server
  │                                    │
  │──── session_start ────────────────►│
  │                                    │ Initialize session
  │◄─── session_started ──────────────│
  │                                    │
  │──── audio (chunk 1) ──────────────►│
  │                                    │ Buffer audio
  │                                    │ Transcribe
  │                                    │ Analyze
  │◄─── transcription + analysis ─────│
  │                                    │
  │──── audio (chunk 2) ──────────────►│
  │                                    │ Buffer + Transcribe
  │◄─── transcription + analysis ─────│
  │                                    │
  │──── session_stop ─────────────────►│
  │                                    │ Cleanup
  │◄─── session_stopped ──────────────│
```

### Audio Chunk Format

**Client → Server**:
```json
{
  "type": "audio",
  "audio_data": "base64_encoded_audio_bytes",
  "session_id": "unique_session_id"
}
```

**Server → Client**:
```json
{
  "type": "transcription",
  "text": "Hello I'm the CEO",
  "start": 0.0,
  "end": 2.5,
  "analysis": {
    "lead_qualification": {
      "score": 0.75,
      "qualification": "HOT",
      "confidence": 0.85
    },
    "key_insights": {
      "emotion": "interested (85%)",
      "intent": "pricing (72%)",
      "buying_readiness": "READY_TO_BUY (80%)",
      "icp_tier": "A+ (Excellent)"
    },
    "bant_summary": {
      "budget": "₹20 Lakhs",
      "authority": "CEO",
      "need": "CRM System",
      "timeline": "3 Months"
    }
  },
  "lead_score": {
    "score": 0.75,
    "qualification": "HOT",
    "confidence": 0.85
  }
}
```

---

## Lead Scoring Algorithm

### Step-by-Step Calculation

```
Input: ConversationFeatures
    ↓
Step 1: Calculate Component Scores
    ↓
    emotion_score = 0.85 (interested, 85% confidence)
    bant_score = 0.90 (all BANT elements present)
    intent_score = 0.78 (pricing intent, 72% confidence)
    buying_signal_score = 0.80 (READY_TO_BUY)
    icp_score = 0.90 (A+ tier)
    conv_quality_score = 0.75 (good metrics)
    ↓
Step 2: Apply Weights
    ↓
    overall = (0.85 × 0.15)  // emotion
           + (0.90 × 0.20)  // bant
           + (0.78 × 0.15)  // intent
           + (0.80 × 0.25)  // buying signals
           + (0.90 × 0.15)  // icp
           + (0.75 × 0.10)  // conv quality
           = 0.8475
    ↓
Step 3: Determine Qualification
    ↓
    score = 0.8475 → HOT (>= 0.75)
    ↓
Step 4: Calculate Confidence
    ↓
    confidence = 0.5 (base)
               + 0.2 (all BANT present)
               + 0.15 (strong buying signals)
               + 0.1 (clear intent)
               + 0.05 (good ICP match)
               = 0.90
    ↓
Step 5: Identify Strengths & Weaknesses
    ↓
    strengths = [
      "Strong Buying Signals (80%)",
      "Strong ICP Match (90%)",
      "Strong BANT (90%)"
    ]
    weaknesses = []
    ↓
Step 6: Generate Recommendations
    ↓
    recommendations = [
      "URGENT: Lead is highly qualified. Initiate closing sequence immediately.",
      "Schedule final presentation with decision makers."
    ]
    ↓
Step 7: Generate Next Actions
    ↓
    next_actions = [
      "Send proposal/quote",
      "Schedule contract review meeting",
      "Connect with decision makers",
      "Prepare detailed pricing proposal"
    ]
    ↓
Output: LeadScore
```

---

## Example Walkthrough

### Sample Conversation

**Customer**: "Hello, I'm the CEO of a technology company in Bangalore. We're looking for a CRM solution and have a budget of around 20 lakhs. We need to implement it within 3 months. Can you send us a quotation? We're ready to proceed if the pricing works for us."

### Analysis Steps

#### Step 1: Speech Emotion Recognition
```
Audio Features:
  - Energy: 0.65 (moderate-high)
  - Pitch Variation: 0.72 (varied)
  - Speaking Rate: 0.68 (moderate)
  - Stability: 0.75 (stable)
  - Clarity: 0.80 (clear)

Emotion Scores:
  - interested: 0.35
  - confident: 0.28
  - excited: 0.15
  - neutral: 0.10
  - curious: 0.08
  - others: < 0.05

Detected Emotion: interested (35% confidence)
```

#### Step 2: BANT Extraction
```
Budget:
  - Pattern matched: "20 lakhs"
  - Amount: ₹20,00,000
  - Category: 10L-50L
  - Confidence: 0.9

Authority:
  - Keyword matched: "CEO"
  - Level: CEO/CFO
  - Confidence: 0.8

Need:
  - Category: CRM
  - Description: "looking for a CRM solution"
  - Confidence: 0.85

Timeline:
  - Pattern matched: "3 months"
  - Urgency: SHORT_TERM
  - Confidence: 0.75
```

#### Step 3: Intent Detection
```
Intent Scores:
  - pricing: 0.72 (keywords: "budget", "quotation", "pricing")
  - purchase: 0.45 (keywords: "ready to proceed")
  - information: 0.30

Detected Intent: pricing (72% confidence)
```

#### Step 4: Buying Signal Detection
```
Signals Detected:
  1. request_quotation: 0.95 (VERY_HIGH)
     - "send us a quotation"
     - Recommendation: "Immediate follow-up required"
  
  2. budget_confirmation: 0.87 (HIGH)
     - "budget of around 20 lakhs"
     - Recommendation: "Budget confirmed. Move to proposal stage."
  
  3. commitment_language: 0.85 (HIGH)
     - "ready to proceed"
     - Recommendation: "Strong commitment. Prepare for closing."

Buying Readiness Score: 0.89 (READY_TO_BUY)
```

#### Step 5: Objection Detection
```
Objections Detected: None
  - No objection keywords or phrases found
  - Customer sentiment is positive
```

#### Step 6: ICP Scoring
```
Extracted Information:
  - Industry: technology
  - Company Size: medium (implied)
  - Revenue: not mentioned
  - Region: india
  - Role: ceo

Scores:
  - Industry: 1.0 (technology is target)
  - Company Size: 1.0 (medium is target)
  - Revenue: 0.0 (not detected)
  - Region: 1.0 (india is target)
  - Role: 1.0 (CEO is target)

Overall ICP Score: 0.80 (A+ - Excellent)
```

#### Step 7: Lead Scoring
```
Component Scores:
  - Emotion: 0.85 (interested)
  - BANT: 0.90 (all elements present)
  - Intent: 0.78 (pricing)
  - Buying Signals: 0.89 (READY_TO_BUY)
  - ICP: 0.80 (A+)
  - Conversation Quality: 0.75

Weighted Calculation:
  = (0.85 × 0.15) + (0.90 × 0.20) + (0.78 × 0.15)
    + (0.89 × 0.25) + (0.80 × 0.15) + (0.75 × 0.10)
  = 0.1275 + 0.1800 + 0.1170 + 0.2225 + 0.1200 + 0.0750
  = 0.8420

Qualification: HOT (>= 0.75)

Confidence: 0.90
  - All BANT present: +0.2
  - Strong buying signals: +0.15
  - Clear intent: +0.1
  - Good ICP match: +0.05
  - Base: 0.5
```

### Final Output

```json
{
  "lead_qualification": {
    "score": 84,
    "qualification": "HOT",
    "confidence": 90
  },
  "key_insights": {
    "emotion": "interested (85%)",
    "intent": "pricing (72%)",
    "buying_readiness": "READY_TO_BUY (89%)",
    "icp_tier": "A+ (Excellent)"
  },
  "bant_summary": {
    "budget": "₹20 Lakhs",
    "authority": "CEO",
    "need": "CRM System",
    "timeline": "3 Months"
  },
  "top_buying_signals": [
    {
      "type": "request_quotation",
      "strength": 95,
      "recommendation": "Immediate follow-up required"
    }
  ],
  "critical_objections": [],
  "recommendations": [
    "URGENT: Lead is highly qualified. Initiate closing sequence immediately.",
    "Schedule final presentation with decision makers.",
    "Send proposal/quote",
    "Schedule contract review meeting"
  ],
  "next_actions": [
    "Send proposal/quote",
    "Schedule contract review meeting",
    "Connect with decision makers",
    "Prepare detailed pricing proposal"
  ]
}
```

---

## Summary

The AI Sales Intelligence Platform provides:

1. **Real-time transcription** with faster-whisper
2. **Voice-based emotion detection** (not text-based)
3. **Comprehensive BANT extraction** for sales qualification
4. **Intent classification** to understand customer goals
5. **Buying signal detection** to identify purchase intent
6. **Objection detection** to address concerns
7. **ICP scoring** to prioritize high-value leads
8. **Automated lead scoring** (HOT/WARM/COLD)
9. **Actionable recommendations** for sales teams
10. **Real-time dashboard** for live visualization

The system processes audio in real-time, extracting maximum intelligence from every conversation to help sales teams prioritize leads and close deals faster.