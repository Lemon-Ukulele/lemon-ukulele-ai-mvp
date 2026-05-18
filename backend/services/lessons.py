from .types import ArrangementResult, LessonPlan


def build_lessons(arrangement: ArrangementResult, level: str = "beginner") -> LessonPlan:
    chords = " - ".join(arrangement.progression)
    if level == "medium":
        steps = [
            f"Warmup: play chord set slowly ({chords}).",
            "Transition drill: 2 bars per chord with metronome at 70% BPM.",
            "Pattern drill: alternate plucking and strumming every 4 bars.",
            "Performance run: full progression x6 loops at target BPM.",
        ]
        title = "Teach Me Mode - Medium"
    else:
        steps = [
            f"Learn chords only: {chords} (one minute each).",
            "Switch practice: change chord every 4 beats using down-strum.",
            "Rhythm starter: D-D-U pattern with slow metronome.",
            "Play-along: full progression x4 loops with backing track.",
        ]
        title = "Teach Me Mode - Beginner"

    return LessonPlan(level=level, title=title, steps=steps)
