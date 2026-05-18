from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.analyze import analyze_audio
from services.arrange import build_arrangement
from services.lessons import build_lessons

app = FastAPI(title="Lemon Ukulele AI MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "stage": "stage1+stage2"}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)) -> dict:
    raw = await file.read()
    analysis = analyze_audio(raw, file.filename or "upload")
    return {
        "duration_seconds": analysis.duration_seconds,
        "bpm": analysis.bpm,
        "key": analysis.key,
        "confidence": analysis.confidence,
        "segment_bars": analysis.segment_bars,
    }


@app.post("/api/arrange")
async def arrange(
    file: UploadFile = File(...),
    level: str = Form("beginner"),
) -> dict:
    raw = await file.read()
    analysis = analyze_audio(raw, file.filename or "upload")
    arrangement = build_arrangement(analysis, mode=level)

    return {
        "analysis": {
            "duration_seconds": analysis.duration_seconds,
            "bpm": analysis.bpm,
            "key": analysis.key,
            "confidence": analysis.confidence,
            "segment_bars": analysis.segment_bars,
        },
        "arrangement": {
            "progression": arrangement.progression,
            "ukulele_voicings": arrangement.ukulele_voicings,
            "plucking_pattern": arrangement.plucking_pattern,
            "strumming_pattern": arrangement.strumming_pattern,
        },
    }


@app.post("/api/lesson-plan")
async def lesson_plan(
    file: UploadFile = File(...),
    level: str = Form("beginner"),
) -> dict:
    raw = await file.read()
    analysis = analyze_audio(raw, file.filename or "upload")
    arrangement = build_arrangement(analysis, mode=level)
    lesson = build_lessons(arrangement, level=level)

    return {
        "level": lesson.level,
        "title": lesson.title,
        "steps": lesson.steps,
        "bpm": arrangement.bpm,
        "key": arrangement.key,
        "progression": arrangement.progression,
    }
