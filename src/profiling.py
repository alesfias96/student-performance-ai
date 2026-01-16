"""profiling.py

Qui trasformiamo i numeri dello scoring in un profilo umano.

Scoring = "misurazione".
Profiling = "interpretazione":
- livelli (beginner / intermediate / advanced)
- punti forti e lacune

Perché serve:
Un report senza interpretazione è solo una tabella. Questo modulo è
il ponte verso raccomandazioni e report finale.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from . import config


@dataclass
class TopicProfile:
    topic: str
    accuracy: float
    avg_time_seconds: float
    n_questions: int
    level: str
    label: str  # "strength" | "weakness" | "neutral"


@dataclass
class StudentProfile:
    student_id: str
    overall_accuracy: float
    overall_avg_time_seconds: float
    overall_n_questions: int
    overall_level: str
    strengths: List[TopicProfile]
    weaknesses: List[TopicProfile]
    neutrals: List[TopicProfile]


def _accuracy_to_level(acc: float) -> str:
    """Mappa accuracy (0..1) in un livello testuale usando config.LEVEL_BANDS."""
    for level, (lo, hi) in config.LEVEL_BANDS.items():
        if lo <= acc < hi:
            return level
    return "intermediate"


def _label_topic(acc: float) -> str:
    """Etichetta un topic come punto forte / lacuna / intermedio."""
    if acc >= config.STRENGTH_ACCURACY_THRESHOLD:
        return "strength"
    if acc <= config.WEAKNESS_ACCURACY_THRESHOLD:
        return "weakness"
    return "neutral"


def build_student_profile(
    student_id: str,
    student_topic_scores_df: pd.DataFrame,
    student_overall_df: pd.DataFrame,
) -> StudentProfile:
    """Costruisce un profilo completo per un singolo studente."""

    # 1) Riga overall
    row = student_overall_df.loc[student_overall_df["student_id"] == student_id]
    if row.empty:
        raise ValueError(f"Student_id non trovato nei dati overall: {student_id}")

    overall_accuracy = float(row.iloc[0]["overall_accuracy"])
    overall_avg_time = float(row.iloc[0]["overall_avg_time_seconds"])
    overall_nq = int(row.iloc[0]["overall_n_questions"])
    overall_level = _accuracy_to_level(overall_accuracy)

    # 2) Topic profiles
    topic_rows = student_topic_scores_df.loc[student_topic_scores_df["student_id"] == student_id].copy()
    if topic_rows.empty:
        raise ValueError(f"Nessun topic score per student_id: {student_id}")

    topic_profiles: List[TopicProfile] = []
    for _, r in topic_rows.iterrows():
        acc = float(r["topic_accuracy"])
        topic_profiles.append(
            TopicProfile(
                topic=str(r["topic"]),
                accuracy=acc,
                avg_time_seconds=float(r["topic_avg_time_seconds"]),
                n_questions=int(r["topic_n_questions"]),
                level=_accuracy_to_level(acc),
                label=_label_topic(acc),
            )
        )

    strengths = [t for t in topic_profiles if t.label == "strength"]
    weaknesses = [t for t in topic_profiles if t.label == "weakness"]
    neutrals = [t for t in topic_profiles if t.label == "neutral"]

    strengths.sort(key=lambda x: x.accuracy, reverse=True)
    weaknesses.sort(key=lambda x: x.accuracy)
    neutrals.sort(key=lambda x: x.accuracy, reverse=True)

    return StudentProfile(
        student_id=student_id,
        overall_accuracy=overall_accuracy,
        overall_avg_time_seconds=overall_avg_time,
        overall_n_questions=overall_nq,
        overall_level=overall_level,
        strengths=strengths,
        weaknesses=weaknesses,
        neutrals=neutrals,
    )


def summarize_profiles_for_class(
    student_topic_scores_df: pd.DataFrame,
    student_overall_df: pd.DataFrame,
) -> pd.DataFrame:
    """Tabella veloce per vedere livelli e performance della classe."""
    df = student_overall_df.copy()
    df["overall_level"] = df["overall_accuracy"].apply(_accuracy_to_level)
    return df[["student_id", "overall_accuracy", "overall_level", "overall_avg_time_seconds", "overall_n_questions"]]
