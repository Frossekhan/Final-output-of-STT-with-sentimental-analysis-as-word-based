import io
import logging
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from faster_whisper import WhisperModel

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
MODEL_SIZE = "base"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"


class Segment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    
    class Config:
        schema_extra = {
            "example": {"id": 0, "start": 0.0, "end": 4.4, "text": "Hello world."}
        }


class TranscriptionResponse(BaseModel):
    text: str = Field(...)
    language: str = Field(...)
    language_probability: float = Field(...)
    duration: float = Field(...)
    duration_after_vad: float = Field(...)
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


@app.on_event("startup")
async def startup_event():
    global model
    if model is None:
        logger.info("Loading faster-whisper model %s on %s (%s)", MODEL_SIZE, DEVICE, COMPUTE_TYPE)
        model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
        logger.info("Model loaded successfully")


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

        return TranscriptionResponse(
            text=text,
            language=info.language,
            language_probability=info.language_probability,
            duration=info.duration,
            duration_after_vad=info.duration_after_vad,
            segments=[
                {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                }
                for segment in segments
            ],
        )
    except Exception as exc:
        logger.exception("Transcription failed")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
