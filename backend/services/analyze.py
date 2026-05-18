import io
import math
import os
import tempfile
import wave
from statistics import median
from typing import List, Optional, Tuple

from .types import AnalysisResult

# Fallback key wheel for deterministic no-cost prototype behavior.
KEYS = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]

try:
    from basic_pitch import ICASSP_2022_MODEL_PATH
    from basic_pitch.inference import predict

    HAS_BASIC_PITCH = True
except Exception:
    HAS_BASIC_PITCH = False

try:
    import librosa

    HAS_LIBROSA = True
except Exception:
    HAS_LIBROSA = False

# Krumhansl-Schmuckler major key profile (normalized-ish shape).
MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

PITCH_CLASS_NAMES = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def _safe_note_event(event: tuple) -> Optional[Tuple[float, float, int]]:
    """
    Normalizes note event tuple from basic-pitch.
    Supports common layouts like:
    (start, end, pitch, amp, ...)
    """
    if len(event) < 3:
        return None
    try:
        start = float(event[0])
        end = float(event[1])
        pitch = int(round(float(event[2])))
    except (TypeError, ValueError):
        return None
    if end <= start:
        return None
    return start, end, pitch


def _estimate_bpm_from_notes(notes: List[Tuple[float, float, int]]) -> int:
    onsets = sorted([n[0] for n in notes])
    if len(onsets) < 4:
        return 96
    deltas = [b - a for a, b in zip(onsets[:-1], onsets[1:]) if 0.08 <= (b - a) <= 2.0]
    if len(deltas) < 3:
        return 96
    beat_sec = median(deltas)
    if beat_sec <= 0:
        return 96
    bpm = int(round(60.0 / beat_sec))
    # Keep in musically practical range for MVP.
    return max(60, min(180, bpm))


def _estimate_key_from_notes(notes: List[Tuple[float, float, int]]) -> str:
    if not notes:
        return "C"
    pitch_class_energy = [0.0] * 12
    for start, end, midi_pitch in notes:
        dur = max(0.05, end - start)
        pc = midi_pitch % 12
        pitch_class_energy[pc] += dur

    best_key_idx = 0
    best_score = float("-inf")
    for key_idx in range(12):
        score = 0.0
        for i in range(12):
            score += pitch_class_energy[i] * MAJOR_PROFILE[(i - key_idx) % 12]
        if score > best_score:
            best_score = score
            best_key_idx = key_idx
    return PITCH_CLASS_NAMES[best_key_idx]


def _estimate_key_from_chroma(chroma_mean: List[float]) -> str:
    if not chroma_mean or len(chroma_mean) != 12:
        return "C"

    best_key_idx = 0
    best_score = float("-inf")
    for key_idx in range(12):
        maj = 0.0
        min_score = 0.0
        for i in range(12):
            maj += chroma_mean[i] * MAJOR_PROFILE[(i - key_idx) % 12]
            min_score += chroma_mean[i] * MINOR_PROFILE[(i - key_idx) % 12]
        score = max(maj, min_score)
        if score > best_score:
            best_score = score
            best_key_idx = key_idx
    return PITCH_CLASS_NAMES[best_key_idx]


def _audio_features_from_file(path: str) -> Tuple[Optional[float], Optional[int], Optional[str]]:
    """
    Extracts duration/bpm/key from waveform features.
    Uses librosa when available.
    """
    if not HAS_LIBROSA:
        return None, None, None
    try:
        y, sr = librosa.load(path, sr=22050, mono=True)
        if y is None or len(y) == 0:
            return None, None, None

        duration = float(librosa.get_duration(y=y, sr=sr))

        # Percussive separation helps strum/onset-driven tempo extraction.
        _, y_perc = librosa.effects.hpss(y)
        onset_env = librosa.onset.onset_strength(y=y_perc, sr=sr)

        tempo_bt, _ = librosa.beat.beat_track(y=y_perc, sr=sr, hop_length=512)
        bpm_bt = float(tempo_bt) if tempo_bt else 0.0

        # Onset interval tempo estimate as backup.
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=512)
        bpm_onset = 0.0
        if len(onset_frames) > 4:
            onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)
            deltas = [b - a for a, b in zip(onset_times[:-1], onset_times[1:]) if 0.10 <= (b - a) <= 1.5]
            if deltas:
                beat_sec = median(deltas)
                if beat_sec > 0:
                    bpm_onset = 60.0 / beat_sec

        bpm_candidates = [b for b in [bpm_bt, bpm_onset] if b > 0]
        bpm = int(round(sum(bpm_candidates) / len(bpm_candidates))) if bpm_candidates else None
        if bpm is not None:
            # Correct common half/double tempo ambiguities.
            while bpm < 78:
                bpm *= 2
            while bpm > 168:
                bpm = int(round(bpm / 2))
            bpm = max(60, min(180, bpm))

        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1).tolist() if chroma is not None else None
        key = _estimate_key_from_chroma(chroma_mean) if chroma_mean else None
        return duration, bpm, key
    except Exception:
        return None, None, None


def _duration_from_wav(raw: bytes) -> Optional[float]:
    try:
        with wave.open(io.BytesIO(raw), "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate()
            if rate <= 0:
                return None
            return float(frames) / float(rate)
    except wave.Error:
        return None


def _analyze_with_basic_pitch(raw: bytes, filename: str) -> Optional[AnalysisResult]:
    if not HAS_BASIC_PITCH:
        return None

    suffix = os.path.splitext(filename)[1].lower() or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(raw)
        tmp.flush()

        try:
            _, _, note_events = predict(tmp.name, model_or_model_path=ICASSP_2022_MODEL_PATH)
        except Exception:
            return None
        feat_duration, feat_bpm, feat_key = _audio_features_from_file(tmp.name)

    notes: List[Tuple[float, float, int]] = []
    for e in note_events:
        parsed = _safe_note_event(e)
        if parsed:
            notes.append(parsed)

    if not notes:
        return None

    note_duration = max([end for _, end, _ in notes] + [0.0])
    duration = feat_duration if (feat_duration and feat_duration > 0.1) else note_duration
    bpm = feat_bpm if feat_bpm is not None else _estimate_bpm_from_notes(notes)
    key = feat_key if feat_key else _estimate_key_from_notes(notes)

    # Confidence proxy from note density and coverage.
    density = len(notes) / max(duration, 1.0)
    confidence = max(0.5, min(0.95, 0.55 + min(density, 8.0) * 0.05))

    beats = max(4.0, duration * (bpm / 60.0))
    bars = int(max(4, round(beats / 4.0)))

    return AnalysisResult(
        duration_seconds=round(duration, 2),
        bpm=int(bpm),
        key=key,
        confidence=round(confidence, 2),
        segment_bars=bars,
    )


def _fallback_heuristic(raw: bytes, filename: str) -> AnalysisResult:
    """
    No-cost deterministic fallback.
    """
    duration = _duration_from_wav(raw)
    if duration is None:
        duration = 90.0

    seed = max(1, len(raw) + len(filename))
    bpm = 72 + (seed % 70)
    key = KEYS[seed % len(KEYS)]

    confidence = max(0.45, min(0.92, 0.45 + math.log10(max(duration, 1.0)) * 0.18))
    beats = max(4.0, duration * (bpm / 60.0))
    bars = int(max(4, round(beats / 4.0)))

    return AnalysisResult(
        duration_seconds=round(duration, 2),
        bpm=int(bpm),
        key=key,
        confidence=round(confidence, 2),
        segment_bars=bars,
    )


def analyze_audio(raw: bytes, filename: str) -> AnalysisResult:
    """
    Stage-1 analyzer:
    - Uses basic-pitch when available for real note extraction.
    - Falls back to deterministic heuristic when unavailable/failing.
    """
    bp = _analyze_with_basic_pitch(raw, filename)
    if bp is not None:
        return bp
    return _fallback_heuristic(raw, filename)
