from dataclasses import dataclass
from typing import List, Dict


@dataclass
class AnalysisResult:
    duration_seconds: float
    bpm: int
    key: str
    confidence: float
    segment_bars: int


@dataclass
class ArrangementResult:
    key: str
    bpm: int
    progression: List[str]
    ukulele_voicings: Dict[str, str]
    plucking_pattern: List[str]
    strumming_pattern: List[str]


@dataclass
class LessonPlan:
    level: str
    title: str
    steps: List[str]
