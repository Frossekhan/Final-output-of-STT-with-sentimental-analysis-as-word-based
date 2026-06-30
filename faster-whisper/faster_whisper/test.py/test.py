from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")

segments, info = model.transcribe("sample.mp3")

for segment in segments:
    print(segment.text)