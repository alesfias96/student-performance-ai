# Uso con uno studente reale (correzione manuale)

## Idea
Tu fai fare un test (domande predefinite). Poi compili un CSV *semplice* con:
- `question_id`
- `answer_given`
- `is_correct` (0/1)
- `error_type` (`none`, `segno`, `algebra`, `formula`, `concetto`, `distrazione`)
- (opzionale) `time_seconds` e `confidence`

Lo script `src/ingest_manual_test.py` fa merge con `questions_bank.csv` e produce
`data/raw/student_answers.csv` compatibile con la pipeline.

---

## Step-by-step (reale)

### 0) Preparazione (una volta sola)
Assicurati di avere una banca domande:
- `data/raw/questions_bank.csv`

> In pratica: ogni domanda deve avere un `question_id` univoco (es. `test_01_q_01`).

### 1) Crea il CSV semplice delle risposte
Parti dal template:
- `templates/manual_responses_TEMPLATE.csv`

Crea, ad esempio:
- `data/raw/manual_responses_student_real_001.csv`

### 2) Converti in `student_answers.csv`
```bash
python -m src.ingest_manual_test \
  --responses data/raw/manual_responses_student_real_001.csv \
  --student-id student_real_001 \
  --test-id test_01
```

Output:
- `data/raw/student_answers.csv`

> Se vuoi tenere *più studenti* nello stesso file:
```bash
python -m src.ingest_manual_test \
  --responses data/raw/manual_responses_student_real_002.csv \
  --student-id student_real_002 \
  --test-id test_01 \
  --append
```

### 3) Genera scoring + report
```bash
python -m src.main --score
python -m src.main --report --student-id student_real_001
```

Output:
- `reports/report_student_real_001.html`

Apri il file in un browser.

---

## Regole importanti (per evitare errori)
- Se `is_correct = 1` allora `error_type` deve essere `none`.
- Se `is_correct = 0` allora `error_type` NON deve essere `none`.
- `confidence` deve essere 1–5 (se non la metti, default=3).
- `time_seconds` se mancante va in default=60.
