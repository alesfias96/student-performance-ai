# Student Performance AI

AI project to analyze students’ performance over time and identify weak and strong topics.
The goal is to generate a clear diagnostic report and suggest targeted improvements.

## Goals
- Track student performance across different topics/skills
- Detect recurring mistakes and weak areas
- Create a summary report for teachers/students

## Main ideas
This project treats learning as a dataset:
- each exercise attempt is a data point
- mistakes are categorized by topic and error type
- the model estimates which topics are mastered and which require practice

> All data is synthetic: no real people involved.

## Tech stack
- Python (Pandas, NumPy)
- scikit-learn
- Jupyter Notebooks

## Project Structure

```
student-performance-ai/
├── data/
│   ├── raw/          # generated raw CSV files (synthetic)
│   ├── processed/    # aggregated CSV files for profiling/reporting
│   └── schemas/      # (extendable) rubrics and mappings
├── reports/          # generated HTML reports
├── src/
│   ├── config.py
│   ├── data_generation.py
│   ├── scoring.py
│   ├── profiling.py
│   ├── recommendations.py
│   ├── visualization.py
│   ├── report_builder.py
│   └── main.py
└── requirements.txt
```

## Quickstart

### 1) Setup

```bash
python -m venv .venv
source .venv/bin/activate  # mac/linux
pip install -r requirements.txt
```

### 2) Run everything with a single command

```bash
python -m src.main
```

This will, in order:
1) generate a synthetic dataset in `data/raw/`
2) compute metrics in `data/processed/`
3) create an HTML report in `reports/`

### 3) Step-by-step commands

Generate data only:
```bash
python -m src.main --generate-data
```

Compute scoring only:
```bash
python -m src.main --score
```

Generate a report for a specific student:
```bash
python -m src.main --report --student-id student_0001
```

---

## Main Outputs

- `data/raw/questions_bank.csv` → question bank
- `data/raw/student_answers.csv` → simulated student answers

- `data/processed/student_topic_scores.csv` → metrics per (student, topic)
- `data/processed/student_overall_summary.csv` → overall metrics per student
- `data/processed/student_topic_error_matrix.csv` → error distribution per topic (long format)

- `reports/report_<student_id>.html` → final report with charts + recommendations

---

## Note on “AI”

This project uses a deliberately **transparent** approach:

- a coherent synthetic dataset (latent topic ability + difficulty)
- statistical scoring (means and distributions)
- rule-based profiling (readable thresholds)

This is an advantage in educational products: teachers must understand *why* the system is providing a certain recommendation.

---

## Notebooks

- `01_dataset_generation.ipynb` — generates the synthetic dataset and checks files in `data/raw/`
- `02_eda.ipynb` — exploratory analysis (accuracy/time/errors)
- `03_modeling.ipynb` — lightweight ML baseline (Logistic Regression)
- `04_report_demo.ipynb` — generates and inspects an HTML report

---

## Tests

Run:
```bash
pytest -q
```

## Status
Work in progress.
