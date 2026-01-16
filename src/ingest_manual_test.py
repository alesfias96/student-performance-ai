"""
src/ingest_manual_test.py

Scopo
-----
Convertire un CSV "semplice" compilato da te (correzione manuale) in un CSV compatibile con la pipeline,
facendo merge con la banca domande (questions_bank.csv).

Input (manual_responses.csv) - minimo:
- question_id
- answer_given
- is_correct   (0/1 oppure True/False)
- error_type   (none, segno, algebra, formula, concetto, distrazione)

Opzionali:
- time_seconds
- confidence

Output:
- data/raw/student_answers.csv (stesso schema del progetto)

Esempio:
python -m src.ingest_manual_test --responses data/raw/manual_responses_student_0001.csv --student-id student_real_001 --test-id test_01
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd

from . import config


ALLOWED_ERROR_TYPES = {"none", "segno", "algebra", "formula", "concetto", "distrazione"}


def _to_bool01(series: pd.Series) -> pd.Series:
    # accetta 0/1, "0"/"1", True/False, "true"/"false"
    if series.dtype == bool:
        return series.astype(int)
    s = series.astype(str).str.strip().str.lower()
    mapping = {"1": 1, "0": 0, "true": 1, "false": 0, "yes": 1, "no": 0}
    if not set(s.unique()).issubset(set(mapping.keys())):
        raise ValueError("La colonna is_correct deve contenere 0/1 oppure True/False.")
    return s.map(mapping).astype(int)


def _validate_manual_df(df: pd.DataFrame) -> pd.DataFrame:
    required = {"question_id", "answer_given", "is_correct", "error_type"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"manual_responses.csv manca colonne: {sorted(missing)}")

    df = df.copy()

    df["question_id"] = df["question_id"].astype(str).str.strip()
    df["error_type"] = df["error_type"].astype(str).str.strip().str.lower()
    df["is_correct"] = _to_bool01(df["is_correct"])

    bad_err = set(df["error_type"].unique()) - ALLOWED_ERROR_TYPES
    if bad_err:
        raise ValueError(f"error_type non valido: {sorted(bad_err)}. Ammessi: {sorted(ALLOWED_ERROR_TYPES)}")

    # regola: se corretto → error_type deve essere 'none'
    mask_correct = df["is_correct"] == 1
    if (df.loc[mask_correct, "error_type"] != "none").any():
        wrong = df.loc[mask_correct & (df["error_type"] != "none"), ["question_id", "error_type"]]
        raise ValueError(
            "Se is_correct=1 allora error_type deve essere 'none'. Problemi su:\n"
            + wrong.to_string(index=False)
        )

    # Se sbagliato e hai messo none → lo forziamo a "distrazione" (più neutro) oppure alziamo errore.
    mask_wrong_none = (df["is_correct"] == 0) & (df["error_type"] == "none")
    if mask_wrong_none.any():
        df.loc[mask_wrong_none, "error_type"] = "distrazione"

    # opzionali: se mancano, li creiamo
    if "time_seconds" not in df.columns:
        df["time_seconds"] = 60.0
    if "confidence" not in df.columns:
        df["confidence"] = 3

    # pulizia tipi
    df["time_seconds"] = pd.to_numeric(df["time_seconds"], errors="coerce").fillna(60.0)
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(3).astype(int).clip(1, 5)

    return df


def build_student_answers(
    manual_responses_csv: Path,
    student_id: str,
    test_id: str,
    question_bank_csv: Path = config.QUESTIONS_BANK_CSV,
) -> pd.DataFrame:
    qb = pd.read_csv(question_bank_csv)
    required_qb = {"question_id", "test_id", "topic", "subskill", "difficulty", "correct_answer"}
    missing_qb = required_qb - set(qb.columns)
    if missing_qb:
        raise ValueError(f"questions_bank.csv manca colonne: {sorted(missing_qb)}")

    manual = pd.read_csv(manual_responses_csv)
    manual = _validate_manual_df(manual)

    merged = manual.merge(qb, on="question_id", how="left", suffixes=("", "_qb"))

    # verifica che tutte le question_id esistano nel question bank
    if merged["topic"].isna().any():
        missing_ids = merged.loc[merged["topic"].isna(), "question_id"].tolist()
        raise ValueError(
            "Alcune question_id non esistono in questions_bank.csv:\n"
            + "\n".join(missing_ids[:50])
        )

    # forza student_id e test_id scelti da CLI (così controlli tu il contesto)
    merged["student_id"] = student_id
    merged["test_id"] = test_id

    # riordina colonne nello schema della pipeline
    out = merged[[
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
    ]].copy()

    return out


def save_student_answers(
    out_df: pd.DataFrame,
    output_csv: Path,
    append: bool = False,
) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if append and output_csv.exists():
        existing = pd.read_csv(output_csv)
        combined = pd.concat([existing, out_df], ignore_index=True)
        combined.to_csv(output_csv, index=False)
    else:
        out_df.to_csv(output_csv, index=False)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest manual test responses -> student_answers.csv compatibile")
    p.add_argument("--responses", type=str, required=True, help="Path al CSV manuale (question_id, answer_given, is_correct, error_type, ...)")
    p.add_argument("--student-id", type=str, required=True, help="ID studente (es. student_real_001)")
    p.add_argument("--test-id", type=str, required=True, help="ID test (es. test_01)")
    p.add_argument("--question-bank", type=str, default=str(config.QUESTIONS_BANK_CSV), help="Path a questions_bank.csv")
    p.add_argument("--output", type=str, default=str(config.STUDENT_ANSWERS_CSV), help="Output student_answers.csv")
    p.add_argument("--append", action="store_true", help="Se attivo, aggiunge allo student_answers.csv esistente invece di sovrascrivere.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    responses_csv = Path(args.responses)
    qb_csv = Path(args.question_bank)
    out_csv = Path(args.output)

    df = build_student_answers(
        manual_responses_csv=responses_csv,
        student_id=args.student_id,
        test_id=args.test_id,
        question_bank_csv=qb_csv,
    )
    save_student_answers(df, out_csv, append=args.append)

    print("[OK] Creato student_answers.csv compatibile.")
    print(f"Output: {out_csv}")
    print(f"Righe scritte: {len(df)}")
    print("Esempio:")
    print(df.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
