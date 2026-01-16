# Student Performance AI — Project Overview

Questo progetto genera un dataset **sintetico** (inventato) di risposte a compiti di matematica/fisica e produce
un **profilo automatico dello studente** (punti di forza/debolezza) con **raccomandazioni operative** e un **report HTML**.

## Features del progetto
- Dataset sintetico **coerente** (abilità latenti per topic + difficoltà delle domande).
- Pipeline completa: **data generation → scoring → profiling → recommendations → report**.
- Codice modulare in `src/` + output riproducibili in `data/` e `reports/`.

## Output principali
- `data/raw/questions_bank.csv` — banca domande
- `data/raw/student_answers.csv` — risposte studenti
- `data/processed/student_topic_scores.csv` — punteggi per topic
- `data/processed/student_overall_summary.csv` — riassunto per studente
- `data/processed/student_topic_error_matrix.csv` — share errori per topic
- `reports/report_<student_id>.html` — report finale (con grafici)

## Come eseguire (end-to-end)
```bash
pip install -r requirements.txt
python -m src.main
```

## Esempi rapidi
Generare solo dati:
```bash
python -m src.main --generate-data
```

Generare report per uno studente specifico:
```bash
python -m src.main --report --student-id student_0001
```
