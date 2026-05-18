from typing import Dict, List

from .types import AnalysisResult, ArrangementResult

# Beginner-friendly ukulele chord shapes.
UKULELE_VOICINGS: Dict[str, str] = {
    "C": "0003",
    "G": "0232",
    "D": "2220",
    "A": "2100",
    "E": "1402",
    "B": "4322",
    "F": "2010",
    "Am": "2000",
    "Bm": "4222",
    "Cm": "0333",
    "C#m": "1104",
    "Em": "0432",
    "Dm": "2210",
    "F#m": "2120",
    "Gm": "0231",
    "G#m": "1342",
    "Bb": "3211",
    "Eb": "0331",
    "Ab": "5343",
    "Db": "1114",
    "F#": "3121",
}

MAJOR_PROGRESSIONS: List[List[str]] = [
    ["I", "V", "vi", "IV"],
    ["I", "IV", "V", "I"],
    ["vi", "IV", "I", "V"],
]

ROMAN_TO_DEGREE = {
    "I": 0,
    "ii": 1,
    "iii": 2,
    "IV": 3,
    "V": 4,
    "vi": 5,
    "vii": 6,
}

KEY_SCALE = {
    "C": ["C", "D", "E", "F", "G", "A", "B"],
    "G": ["G", "A", "B", "C", "D", "E", "F#"],
    "D": ["D", "E", "F#", "G", "A", "B", "Db"],
    "A": ["A", "B", "Db", "D", "E", "F#", "Ab"],
    "E": ["E", "F#", "Ab", "A", "B", "Db", "Eb"],
    "B": ["B", "Db", "Eb", "E", "F#", "Ab", "Bb"],
    "F#": ["F#", "Ab", "Bb", "B", "Db", "Eb", "F"],
    "Db": ["Db", "Eb", "F", "F#", "Ab", "Bb", "C"],
    "Ab": ["Ab", "Bb", "C", "Db", "Eb", "F", "G"],
    "Eb": ["Eb", "F", "G", "Ab", "Bb", "C", "D"],
    "Bb": ["Bb", "C", "D", "Eb", "F", "G", "A"],
    "F": ["F", "G", "A", "Bb", "C", "D", "E"],
}


def _roman_to_chords(key: str, progression: List[str]) -> List[str]:
    scale = KEY_SCALE.get(key, KEY_SCALE["C"])
    out = []
    for symbol in progression:
        idx = ROMAN_TO_DEGREE[symbol]
        root = scale[idx]
        out.append(f"{root}m" if symbol.islower() else root)
    return out


def build_arrangement(
    analysis: AnalysisResult,
    mode: str = "beginner",
) -> ArrangementResult:
    pattern_seed = analysis.bpm % len(MAJOR_PROGRESSIONS)
    chords = _roman_to_chords(analysis.key, MAJOR_PROGRESSIONS[pattern_seed])

    if mode == "medium":
        plucking = ["G-3", "C-2", "E-1", "A-0", "E-1", "C-2"]
        strumming = ["D", "D-U", "U-D-U", "D-U"]
    else:
        plucking = ["G-3", "C-2", "E-1", "A-0"]
        strumming = ["D", "D-U", "D-U"]

    voicings = {ch: UKULELE_VOICINGS.get(ch, "0000") for ch in chords}
    return ArrangementResult(
        key=analysis.key,
        bpm=analysis.bpm,
        progression=chords,
        ukulele_voicings=voicings,
        plucking_pattern=plucking,
        strumming_pattern=strumming,
    )
