"""config.py

Qui mettiamo tutte le costanti del progetto in un unico posto.

Perché è utile:
- eviti "numeri magici" sparsi nel codice
- cambi un parametro qui e il resto si aggiorna
- rende il progetto più pulito e mantenibile
"""

from pathlib import Path

# Cartella base del progetto (student-performance-ai)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Percorsi dati
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SCHEMAS_DIR = DATA_DIR / "schemas"

# File principali (dataset sintetici)
QUESTIONS_BANK_CSV = RAW_DATA_DIR / "questions_bank.csv"
STUDENT_ANSWERS_CSV = RAW_DATA_DIR / "student_answers.csv"

# -----------------------------
# Output (dati processati)
# -----------------------------
STUDENT_TOPIC_SCORES_CSV = PROCESSED_DATA_DIR / "student_topic_scores.csv"
STUDENT_OVERALL_SUMMARY_CSV = PROCESSED_DATA_DIR / "student_overall_summary.csv"
STUDENT_TOPIC_ERROR_CSV = PROCESSED_DATA_DIR / "student_topic_error_matrix.csv"

# -----------------------------
# Report
# -----------------------------
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# -----------------------------
# Soglie (profilazione)
# -----------------------------
STRENGTH_ACCURACY_THRESHOLD = 0.80
WEAKNESS_ACCURACY_THRESHOLD = 0.55

LEVEL_BANDS = {
    "beginner": (0.00, 0.50),
    "intermediate": (0.50, 0.75),
    "advanced": (0.75, 1.01),
}

# Parametri dataset sintetico
N_STUDENTS = 200
N_TESTS = 3
QUESTIONS_PER_TEST = 25

# Seed per rendere riproducibile la generazione (stesso output a parità di seed)
RANDOM_SEED = 42
