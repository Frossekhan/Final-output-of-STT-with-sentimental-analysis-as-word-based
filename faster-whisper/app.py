import io
import logging
import re
from collections import Counter
from typing import Dict, List, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from faster_whisper import WhisperModel
from transformers import pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("faster-whisper-api")

app = FastAPI(
    title="Faster Whisper Audio-to-Text API",
    description="Upload audio and transcribe speech using faster-whisper. Swagger UI is available at /docs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model: Optional[WhisperModel] = None
sentiment_model = None

MODEL_SIZE = "base"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"


class Segment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    tone: Optional[str] = None
    tone_score: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {"id": 0, "start": 0.0, "end": 4.4, "text": "Hello world."}
        }


class ToneAnalytics(BaseModel):
    primary_tone: str = Field(...)
    tone_score: float = Field(...)
    emotional_intensity: float = Field(...)
    urgency_score: float = Field(...)
    politeness_score: float = Field(...)
    confidence_score: float = Field(...)
    tone_distribution: Dict[str, float] = Field(...)
    indicators: List[str] = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "primary_tone": "confident",
                "tone_score": 0.76,
                "emotional_intensity": 0.42,
                "urgency_score": 0.18,
                "politeness_score": 0.64,
                "confidence_score": 0.81,
                "tone_distribution": {
                    "confident": 0.76,
                    "positive": 0.58,
                    "neutral": 0.22,
                },
                "indicators": ["clear commitment language", "positive sentiment"],
            }
        }


class TranscriptionResponse(BaseModel):
    text: str = Field(...)
    language: str = Field(...)
    language_probability: float = Field(...)
    duration: float = Field(...)
    duration_after_vad: float = Field(...)

    sentiment: str = Field(...)
    sentiment_score: float = Field(...)
    tone_analytics: ToneAnalytics = Field(...)


    segments: List[Segment] = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "text": "Hello world. This is a test.",
                "language": "en",
                "language_probability": 0.997,
                "duration": 10.5,
                "duration_after_vad": 9.8,
                "segments": [
                    {"id": 0, "start": 0.0, "end": 4.4, "text": "Hello world."},
                    {"id": 1, "start": 4.5, "end": 8.1, "text": "This is a test."},
                ],
            }
        }


TONE_KEYWORDS = {
    "positive": {
        "happy", "great", "good", "excellent", "awesome", "love", "like", "thanks",
        "thank", "perfect", "nice", "glad", "amazing", "wonderful", "best",
    },
    "negative": {
        "bad", "wrong", "problem", "issue", "hate", "poor", "worst", "fail",
        "failed", "failure", "sorry", "sad", "upset", "disappointed", "angry",
    },
    "urgent": {
        "urgent", "immediately", "now", "asap", "quick", "quickly", "fast",
        "emergency", "important", "deadline", "today", "soon", "must",
    },
    "polite": {
        "please", "kindly", "thanks", "thank", "appreciate", "sorry", "excuse",
        "request", "could", "would",
    },
    "confident": {
        "sure", "definitely", "clearly", "confirm", "confirmed", "will", "can",
        "done", "ready", "exactly", "certainly", "guarantee",
    },
    "uncertain": {
        "maybe", "might", "probably", "possibly", "think", "guess", "unsure",
        "confused", "doubt", "perhaps", "not sure",
    },
    "frustrated": {
        "again", "still", "never", "can't", "cannot", "why", "stuck", "error",
        "broken", "not working", "doesn't", "dont", "don't",
    },
}


def _normalize_words(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def _keyword_hits(text: str, words: List[str], tone: str) -> int:
    lowered = text.lower()
    hits = 0
    word_counts = Counter(words)
    for keyword in TONE_KEYWORDS[tone]:
        if " " in keyword:
            hits += lowered.count(keyword)
        else:
            hits += word_counts[keyword]
    return hits


def analyze_human_tone(text: str, sentiment_label: str, sentiment_score: float) -> ToneAnalytics:
    words = _normalize_words(text)
    word_count = max(len(words), 1)
    exclamation_count = text.count("!")
    question_count = text.count("?")
    uppercase_words = [word for word in re.findall(r"\b[A-Z]{2,}\b", text) if len(word) > 2]

    raw_scores = {}
    for tone in TONE_KEYWORDS:
        hits = _keyword_hits(text, words, tone)
        raw_scores[tone] = min(1.0, hits / max(word_count / 8, 1))

    sentiment_label = sentiment_label.upper()
    if sentiment_label == "POSITIVE":
        raw_scores["positive"] = max(raw_scores["positive"], sentiment_score * 0.8)
    elif sentiment_label == "NEGATIVE":
        raw_scores["negative"] = max(raw_scores["negative"], sentiment_score * 0.8)

    raw_scores["urgent"] = min(1.0, raw_scores["urgent"] + exclamation_count * 0.12)
    raw_scores["frustrated"] = min(
        1.0,
        raw_scores["frustrated"] + len(uppercase_words) * 0.08 + exclamation_count * 0.08,
    )
    raw_scores["uncertain"] = min(1.0, raw_scores["uncertain"] + question_count * 0.08)

    confidence_score = max(0.0, min(1.0, raw_scores["confident"] - raw_scores["uncertain"] * 0.35))
    politeness_score = raw_scores["polite"]
    urgency_score = raw_scores["urgent"]
    emotional_intensity = max(
        raw_scores["positive"],
        raw_scores["negative"],
        raw_scores["frustrated"],
        urgency_score,
        min(1.0, (exclamation_count + len(uppercase_words)) * 0.12),
    )

    tone_distribution = {
        "positive": round(raw_scores["positive"], 4),
        "negative": round(raw_scores["negative"], 4),
        "urgent": round(urgency_score, 4),
        "polite": round(politeness_score, 4),
        "confident": round(confidence_score, 4),
        "uncertain": round(raw_scores["uncertain"], 4),
        "frustrated": round(raw_scores["frustrated"], 4),
    }

    primary_tone = max(tone_distribution, key=tone_distribution.get)
    tone_score = tone_distribution[primary_tone]
    if tone_score < 0.18:
        primary_tone = "neutral"
        tone_score = 1.0 - emotional_intensity
        tone_distribution["neutral"] = round(tone_score, 4)

    indicators = []
    if sentiment_label in {"POSITIVE", "NEGATIVE"}:
        indicators.append(f"{sentiment_label.lower()} sentiment")
    if exclamation_count:
        indicators.append("exclamation emphasis")
    if question_count:
        indicators.append("questioning tone")
    if uppercase_words:
        indicators.append("uppercase emphasis")
    for tone, score in tone_distribution.items():
        if tone != "neutral" and score >= 0.35:
            indicators.append(f"{tone} language")

    return ToneAnalytics(
        primary_tone=primary_tone,
        tone_score=round(tone_score, 4),
        emotional_intensity=round(emotional_intensity, 4),
        urgency_score=round(urgency_score, 4),
        politeness_score=round(politeness_score, 4),
        confidence_score=round(confidence_score, 4),
        tone_distribution=tone_distribution,
        indicators=indicators[:6],
    )


def analyze_sentiment(text: str):
    if not text.strip():
        return "NEUTRAL", 0.0
    result = sentiment_model(text[:3000])
    return result[0]["label"], round(result[0]["score"], 4)


@app.on_event("startup")
async def startup_event():
    global model, sentiment_model
    if model is None:
        logger.info("Loading faster-whisper model %s on %s (%s)", MODEL_SIZE, DEVICE, COMPUTE_TYPE)
        model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
        logger.info("Model loaded successfully")

    if sentiment_model is None:
        logger.info("Loading sentiment model...")
        sentiment_model = pipeline("sentiment-analysis")
        logger.info("Sentiment model loaded successfully")


@app.get("/")
async def root():
    return {
        "message": "Faster Whisper Swagger UI available at /docs. Use /transcribe to upload audio."
    }


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form(None, description="Language code, e.g. en"),
    task: str = Form("transcribe", description="Task to run: transcribe or translate"),
):
    if not audio.content_type.startswith("audio") and audio.content_type != "application/octet-stream":
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload an audio file.")

    try:
        audio_bytes = await audio.read()
        audio_stream = io.BytesIO(audio_bytes)

        segments, info = model.transcribe(
            audio_stream,
            language=language,
            task=task,
            vad_filter=False,
            word_timestamps=False,
        )

        segments = list(segments)
        text = " ".join([segment.text for segment in segments]).strip()
        
        # Overall sentiment (ML model - one call only)
        sentiment_label, sentiment_score = analyze_sentiment(text)
        tone_analytics = analyze_human_tone(text, sentiment_label, sentiment_score)
        
        # Segment-level tone (rule-based only - no ML calls, fast!)
        segment_payload = []
        for segment in segments:
            # Use rule-based tone analysis only (no ML model call)
            segment_tone = analyze_human_tone(segment.text, sentiment_label, sentiment_score)
            segment_payload.append(
                {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "sentiment": sentiment_label,  # Use overall sentiment
                    "sentiment_score": sentiment_score,
                    "tone": segment_tone.primary_tone,
                    "tone_score": segment_tone.tone_score,
                }
            )

        return TranscriptionResponse(
            text=text,
            language=info.language,
            language_probability=info.language_probability,
            duration=info.duration,
            duration_after_vad=info.duration_after_vad,
            sentiment=sentiment_label,
            sentiment_score=sentiment_score,
            tone_analytics=tone_analytics,
            segments=segment_payload,
        )
    except Exception as exc:
        logger.exception("Transcription failed")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
