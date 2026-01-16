"""main.py

Entry-point della pipeline.

Perché serve:
- rende il progetto usabile da terminale ("reale")
- documenta chiaramente l'ordine dei passi

Comandi tipici:

1) Genera dati sintetici + scoring + report per uno studente:
   python -m src.main --generate-data --score --report --student-id student_0001

2) Solo scoring (se hai già i CSV raw):
   python -m src.main --score

3) Solo report (se hai già i CSV processed):
   python -m src.main --report --student-id student_0001
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import config
from .data_generation import generate_and_save_synthetic_dataset
from .report_builder import build_student_report
from .scoring import run_scoring_pipeline


def _pick_default_student_id() -> str:
    """Se l'utente non passa --student-id, prendiamo il primo dal dataset."""
    if config.STUDENT_ANSWERS_CSV.exists():
        df = pd.read_csv(config.STUDENT_ANSWERS_CSV, usecols=["student_id"])
        return str(df.iloc[0]["student_id"])
    return "student_0001"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="student-performance-ai pipeline")
    p.add_argument("--generate-data", action="store_true", help="Genera dataset sintetico in data/raw")
    p.add_argument("--score", action="store_true", help="Calcola metriche e salva in data/processed")
    p.add_argument("--report", action="store_true", help="Genera report HTML in reports/")
    p.add_argument("--student-id", type=str, default=None, help="ID studente (es. student_0001)")
    p.add_argument("--out-name", type=str, default=None, help="Nome file HTML (opzionale)")
    p.add_argument("--out-dir", type=str, default=str(config.REPORTS_DIR), help="Cartella output report")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Se l'utente non specifica nulla, facciamo tutto (esperienza "one command")
    if not (args.generate_data or args.score or args.report):
        args.generate_data = True
        args.score = True
        args.report = True

    if args.generate_data:
        generate_and_save_synthetic_dataset()
        print(f"[OK] Dataset generato: {config.RAW_DATA_DIR}")

    if args.score:
        outs = run_scoring_pipeline()
        print("[OK] Scoring completato:")
        print(f" - {outs.student_topic_scores_csv}")
        print(f" - {outs.student_overall_summary_csv}")
        print(f" - {outs.student_topic_error_csv}")

    if args.report:
        student_id = args.student_id or _pick_default_student_id()

        # Se non esistono i processed, proviamo a calcolarli automaticamente
        if not (config.STUDENT_TOPIC_SCORES_CSV.exists() and config.STUDENT_OVERALL_SUMMARY_CSV.exists() and config.STUDENT_TOPIC_ERROR_CSV.exists()):
            run_scoring_pipeline()

        out_dir = Path(args.out_dir)
        out_path = build_student_report(student_id=student_id, out_dir=out_dir, out_name=args.out_name)
        print(f"[OK] Report creato: {out_path}")


if __name__ == "__main__":
    main()
