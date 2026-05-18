# Lemon Ukulele AI MVP (Stage 1 + Stage 2)

This repo is a working starter for:
- Stage 1: upload song -> analysis -> ukulele arrangement draft
- Stage 2: Teach Me lesson-plan generation

## Tech (free/open)
- FastAPI backend (free/open source)
- Simple static frontend (no framework required)
- Planned swaps in next sprint:
  - Basic Pitch / Basic Pitch TS
  - Essentia.js or aubio
  - Tone.js playback engine

## Project layout
- `backend/` API + arrangement/lesson logic
- `frontend/` interactive UI page
- `frontend/samples/` optional local chord sample pack
- `docs/` architecture and upgrade plan

## Run locally

### 1) Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

### 2) Frontend
In another terminal:
```bash
cd frontend
python3 -m http.server 8080
```
Open: `http://127.0.0.1:8080`

Manual local library page:
- `http://127.0.0.1:8080/explorer.html`

Asset note:
- `frontend/assets/ukulele-cc0.svg` sourced from Wikimedia Commons (public domain / CC0):  
  https://commons.wikimedia.org/wiki/File:Ukulele.svg

## Better sounding preview
Playback now uses your local ukulele library by default with synth fallback for missing files.
It also prefers pre-generated upstroke variants (`up_01.mp3` / `up_play.mp3`) when present.

Preview controls:
- `Chord Progression Override`: e.g. `C G Am F | C G Am F`
- `Strum Pattern`: tokens `D U - | T X`
  - `D` downstroke
  - `U` upstroke
  - `-` rest
  - `|` micro break
  - `T` or `X` percussive thump/chuck
- `Play Uploaded + Ukulele Mix`: plays original uploaded track + your custom ukulele pattern merged in real time.

It reads from:
- `frontend/ukulele_audio` (symlink to `../ukulele_audio`)

You can also manually test files in:
- `frontend/explorer.html`

Generate upstroke variants (one-time batch):
```bash
cd /Users/sachouha/lemon-ukulele-ai-mvp
./scripts/generate_upstroke_samples.sh
```

Optional flags:
- `OVERWRITE=1 ./scripts/generate_upstroke_samples.sh` to regenerate all
- `DRY_RUN=1 ./scripts/generate_upstroke_samples.sh` to preview changes
- `ROOT_FILTER='C,G,A,F,D,E' TYPE_FILTER='maj,min' OVERWRITE=1 ./scripts/generate_upstroke_samples.sh` for targeted regeneration

## APIs
- `POST /api/analyze` -> key/bpm/confidence/bars
- `POST /api/arrange` -> analysis + chord progression + ukulele voicings + patterns
- `POST /api/lesson-plan` -> Teach Me step list

`/api/arrange` form fields:
- `file`
- `level` = `beginner|medium`

## Important
Analyzer now supports two modes:
1. Real extraction mode (recommended): install `basic-pitch`
2. Fallback mode: deterministic heuristic if `basic-pitch` is not installed

To enable real extraction mode:
```bash
cd backend
source .venv/bin/activate
pip install "basic-pitch[onnx]==0.4.0"
```

Next quality upgrades:
- add essentia/aubio for stronger tempo tracking
- add chord confidence per segment
- add manual correction endpoint
