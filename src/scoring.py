"""scoring.py

Scopo: trasformare i dati *grezzi* (una riga = un tentativo di risposta)
in dati *aggregati* utili per profiling e report.

Input:
- data/raw/student_answers.csv

Output (data/processed/):
- student_topic_scores.csv
  (per ogni student_id e topic: accuracy, tempo medio, n domande)
- student_overall_summary.csv
  (per ogni student_id: accuracy totale, tempo medio, n domande)
- student_topic_error_matrix.csv
  (formato long: per (student_id, topic, error_type) la quota error_share)

Nota importante:
Qui non "decidiamo" nulla: misuriamo.
La parte "AI" (profilo + consigli) arriva dopo, partendo da queste metriche.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import pandas as pd

from . import config


@dataclass(frozen=True)
class ScoreOutputs:
    """Percorsi dei file prodotti dalla fase di scoring."""

    student_topic_scores_csv: Path
    student_overall_summary_csv: Path
    student_topic_error_csv: Path


def load_raw_answers(answers_csv: Path = config.STUDENT_ANSWERS_CSV) -> pd.DataFrame:
    """Carica il CSV grezzo delle risposte e controlla che ci siano le colonne minime."""

    answers_df = pd.read_csv(answers_csv)

    required = {
        "student_id",
        "test_id",
        "question_id",
        "topic",
        "subskill",
        "difficulty",
        "correct_answer",
        "answer_given",
        "is_correct",
        "error_type",
        "time_seconds",
        "confidence",
    }
    missing = required - set(answers_df.columns)
    if missing:
        raise ValueError(f"student_answers.csv manca colonne: {sorted(missing)}")

    return answers_df


def compute_student_topic_scores(answers_df: pd.DataFrame) -> pd.DataFrame:
    """Metriche per (student_id, topic)."""

    out = answers_df.groupby(["student_id", "topic"], as_index=False).agg(
        topic_n_questions=("question_id", "count"),
        topic_accuracy=("is_correct", "mean"),
        topic_avg_time_seconds=("time_seconds", "mean"),
        topic_avg_confidence=("confidence", "mean"),
    )

    out["topic_accuracy"] = out["topic_accuracy"].round(4)
    out["topic_avg_time_seconds"] = out["topic_avg_time_seconds"].round(2)
    out["topic_avg_confidence"] = out["topic_avg_confidence"].round(2)
    return out


def compute_student_overall_summary(answers_df: pd.DataFrame) -> pd.DataFrame:
    """Metriche overall per student_id."""

    out = answers_df.groupby(["student_id"], as_index=False).agg(
        overall_n_questions=("question_id", "count"),
        overall_accuracy=("is_correct", "mean"),
        overall_avg_time_seconds=("time_seconds", "mean"),
        overall_avg_confidence=("confidence", "mean"),
    )

    out["overall_accuracy"] = out["overall_accuracy"].round(4)
    out["overall_avg_time_seconds"] = out["overall_avg_time_seconds"].round(2)
    out["overall_avg_confidence"] = out["overall_avg_confidence"].round(2)
    return out


def compute_student_topic_error_shares(answers_df: pd.DataFrame) -> pd.DataFrame:
    """Distribuzione errori per (student_id, topic) in formato *long*.

Ritorna:
- student_id
- topic
- error_type
- error_share (0..1)

Nota: include anche "none" (risposte corrette).
"""

    counts = (
        answers_df.groupby(["student_id", "topic", "error_type"], as_index=False)
        .size()
        .rename(columns={"size": "n"})
    )

    totals = counts.groupby(["student_id", "topic"], as_index=False).agg(total_n=("n", "sum"))
    merged = counts.merge(totals, on=["student_id", "topic"], how="left")
    merged["error_share"] = (merged["n"] / merged["total_n"]).round(4)
    return merged[["student_id", "topic", "error_type", "error_share"]]


def run_scoring_pipeline(
    answers_csv: Path = config.STUDENT_ANSWERS_CSV,
    processed_dir: Path = config.PROCESSED_DATA_DIR,
) -> ScoreOutputs:
    """Esegue scoring end-to-end e salva i CSV in data/processed/."""

    processed_dir.mkdir(parents=True, exist_ok=True)

    answers_df = load_raw_answers(answers_csv)

    topic_scores = compute_student_topic_scores(answers_df)
    overall = compute_student_overall_summary(answers_df)
    error_shares = compute_student_topic_error_shares(answers_df)

    topic_scores.to_csv(config.STUDENT_TOPIC_SCORES_CSV, index=False)
    overall.to_csv(config.STUDENT_OVERALL_SUMMARY_CSV, index=False)
    error_shares.to_csv(config.STUDENT_TOPIC_ERROR_CSV, index=False)

    return ScoreOutputs(
        student_topic_scores_csv=config.STUDENT_TOPIC_SCORES_CSV,
        student_overall_summary_csv=config.STUDENT_OVERALL_SUMMARY_CSV,
        student_topic_error_csv=config.STUDENT_TOPIC_ERROR_CSV,
    )


if __name__ == "__main__":
    outs = run_scoring_pipeline()
    print("[OK] Scoring completato.")
    print(f" - {outs.student_topic_scores_csv}")
    print(f" - {outs.student_overall_summary_csv}")
    print(f" - {outs.student_topic_error_csv}")
