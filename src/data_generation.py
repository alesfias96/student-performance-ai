"""data_generation.py

Questo modulo crea un dataset *inventato* ma realistico.

Output:
- data/raw/questions_bank.csv
- data/raw/student_answers.csv

Modello generativo (in parole semplici):
- Ogni studente ha una "abilità" per topic (0..1).
- Ogni domanda ha una difficoltà (1..5).
- La probabilità di risposta corretta dipende da (abilità - difficoltà_normalizzata).
- Se la risposta è sbagliata, assegniamo un tipo di errore plausibile.

Nota importante: non usiamo dati reali. Student_id è anonimo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .config import (
    QUESTIONS_BANK_CSV,
    STUDENT_ANSWERS_CSV,
    RAW_DATA_DIR,
    N_STUDENTS,
    N_TESTS,
    QUESTIONS_PER_TEST,
    RANDOM_SEED,
)


# ----------------------------
# 1) Definizioni di dominio
# ----------------------------

# Argomenti e sotto-abilità (esempi realistici, ma tenuti semplici)
TOPICS: Dict[str, List[str]] = {
    "Algebra": ["frazioni", "segni", "scomposizione", "equazioni_lineari"],
    "Funzioni": ["dominio", "grafico", "composizione"],
    "Derivate": ["regole_base", "prodotto", "catena"],
    "Fisica_Dinamica": ["newton", "attrito", "forze"],
    "Fisica_Energia": ["lavoro", "energia_cinetica", "conservazione"],
}

ERROR_TYPES = [
    "none",            # corretto
    "distrazione",     # errore casuale
    "segno",           # + / -
    "algebra",         # passaggi algebrici
    "formula",         # formula sbagliata
    "concetto",        # fraintendimento
]


@dataclass(frozen=True)
class Question:
    question_id: str
    test_id: str
    topic: str
    subskill: str
    difficulty: int  # 1..5
    correct_answer: float


# ----------------------------
# 2) Funzioni matematiche base
# ----------------------------

def sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    """Sigmoide: trasforma un valore reale in una probabilità 0..1."""
    return 1 / (1 + np.exp(-x))


def difficulty_to_scale(difficulty: int) -> float:
    """Normalizza difficulty 1..5 in 0..1 (più alto = più difficile)."""
    return (difficulty - 1) / 4


# ----------------------------
# 3) Generazione banca domande
# ----------------------------

def generate_questions(rng: np.random.Generator) -> pd.DataFrame:
    """Crea una banca domande semplice e ripetibile."""

    questions: List[Question] = []

    # Per semplicità, ogni test pesca domande da tutti i topic
    for t in range(1, N_TESTS + 1):
        test_id = f"test_{t:02d}"

        for q in range(1, QUESTIONS_PER_TEST + 1):
            # Scegliamo topic e subskill
            topic = rng.choice(list(TOPICS.keys()))
            subskill = rng.choice(TOPICS[topic])

            # Difficoltà 1..5
            difficulty = int(rng.integers(1, 6))

            # Risposta corretta: un numero float fittizio (non ci interessa il contenuto matematico qui)
            # Serve solo per simulare "answer_given".
            correct_answer = float(np.round(rng.normal(loc=10.0, scale=5.0), 2))

            question_id = f"{test_id}_q_{q:02d}"

            questions.append(
                Question(
                    question_id=question_id,
                    test_id=test_id,
                    topic=topic,
                    subskill=subskill,
                    difficulty=difficulty,
                    correct_answer=correct_answer,
                )
            )

    df_q = pd.DataFrame([q.__dict__ for q in questions])

    # Ordine colonne esplicito
    df_q = df_q[
        [
            "question_id",
            "test_id",
            "topic",
            "subskill",
            "difficulty",
            "correct_answer",
        ]
    ]

    return df_q


# ----------------------------
# 4) Generazione risposte studenti
# ----------------------------

def sample_student_skills(rng: np.random.Generator) -> Dict[str, float]:
    """Crea abilità per topic (0..1)."""
    # Beta dà distribuzioni realistiche (molti medi, pochi estremi)
    return {topic: float(rng.beta(4, 4)) for topic in TOPICS.keys()}


def choose_error_type(rng: np.random.Generator, topic: str) -> str:
    """Sceglie un tipo di errore plausibile.

    Esempio: su Algebra è comune 'segno'/'algebra'; su Derivate spesso 'formula'/'concetto'.
    """
    if topic == "Algebra":
        probs = [0.0, 0.15, 0.35, 0.35, 0.10, 0.05]
    elif topic == "Derivate":
        probs = [0.0, 0.10, 0.10, 0.15, 0.40, 0.25]
    elif topic.startswith("Fisica"):
        probs = [0.0, 0.10, 0.05, 0.10, 0.25, 0.50]
    else:
        probs = [0.0, 0.20, 0.15, 0.20, 0.20, 0.25]

    return str(rng.choice(ERROR_TYPES, p=probs))


def perturb_answer(rng: np.random.Generator, correct: float, error_type: str) -> float:
    """Crea una risposta sbagliata in modo coerente col tipo di errore."""
    if error_type == "segno":
        return float(np.round(-correct, 2))

    if error_type == "distrazione":
        return float(np.round(correct + rng.normal(0, 3.0), 2))

    if error_type == "algebra":
        return float(np.round(correct + rng.normal(0, 2.0) + rng.choice([-2, -1, 1, 2]), 2))

    if error_type == "formula":
        return float(np.round(correct * rng.uniform(0.6, 1.4), 2))

    if error_type == "concetto":
        return float(np.round(correct + rng.normal(0, 6.0), 2))

    # fallback
    return float(np.round(correct + rng.normal(0, 4.0), 2))


def simulate_answers(df_questions: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Simula le risposte per tutti gli studenti su tutti i test."""

    rows: List[dict] = []

    for s in range(1, N_STUDENTS + 1):
        student_id = f"student_{s:04d}"  # anonimo

        # Abilità latente per topic
        skills = sample_student_skills(rng)

        # (opzionale) una "velocità" di base dello studente: alcuni sono più rapidi
        speed_factor = float(rng.normal(loc=1.0, scale=0.15))
        speed_factor = float(np.clip(speed_factor, 0.7, 1.3))

        for _, q in df_questions.iterrows():
            topic = str(q["topic"])
            difficulty = int(q["difficulty"])
            correct_answer = float(q["correct_answer"])

            # Probabilità di correttezza
            # abilità alta + difficoltà bassa => p alto
            skill = skills[topic]
            diff = difficulty_to_scale(difficulty)

            # "centratura": se skill == diff -> 0.5
            p_correct = float(sigmoid((skill - diff) * 4.0))

            is_correct = int(rng.random() < p_correct)

            if is_correct:
                error_type = "none"
                answer_given = correct_answer
            else:
                error_type = choose_error_type(rng, topic)
                answer_given = perturb_answer(rng, correct_answer, error_type)

            # Tempo: base cresce con difficoltà e cala con abilità
            base_time = 40 + 25 * diff  # secondi
            time_seconds = base_time * (1.2 - 0.6 * skill) * speed_factor

            # Rumore realistico sul tempo
            time_seconds = float(np.clip(time_seconds + rng.normal(0, 8.0), 10, 240))

            # "Confidenza" (1..5): cresce con abilità e cala se ha sbagliato
            confidence = 1 + 4 * skill
            if not is_correct:
                confidence -= 0.8
            confidence = int(np.clip(np.round(confidence), 1, 5))

            rows.append(
                {
                    "student_id": student_id,
                    "test_id": str(q["test_id"]),
                    "question_id": str(q["question_id"]),
                    "topic": topic,
                    "subskill": str(q["subskill"]),
                    "difficulty": difficulty,
                    "correct_answer": correct_answer,
                    "answer_given": float(answer_given),
                    "is_correct": is_correct,
                    "error_type": error_type,
                    "time_seconds": float(np.round(time_seconds, 2)),
                    "confidence": confidence,
                }
            )

    df_a = pd.DataFrame(rows)
    return df_a


# ----------------------------
# 5) Entry point (esecuzione)
# ----------------------------

def generate_and_save_synthetic_dataset() -> None:
    """Genera e salva i CSV nella cartella data/raw.

    Nota: esiste come funzione separata perché `src/main.py` la può richiamare.
    """

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(RANDOM_SEED)

    df_q = generate_questions(rng)
    df_a = simulate_answers(df_q, rng)

    df_q.to_csv(QUESTIONS_BANK_CSV, index=False)
    df_a.to_csv(STUDENT_ANSWERS_CSV, index=False)

    print(f"✅ Salvato: {QUESTIONS_BANK_CSV}")
    print(f"✅ Salvato: {STUDENT_ANSWERS_CSV}")
    print(f"Domande: {len(df_q)} | Risposte: {len(df_a)}")


def main() -> None:
    """Alias CLI: mantiene compatibilità con `python -m src.data_generation`."""
    generate_and_save_synthetic_dataset()


if __name__ == "__main__":
    main()
