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

## Planned pipeline
1. Data collection / dataset format definition
2. Data cleaning and exploratory analysis (EDA)
3. Feature engineering (accuracy by topic, time, error frequency, etc.)
4. Baseline model (classification or scoring system)
5. Evaluation and validation
6. Report generation (PDF/HTML or dashboard)

## Tech stack
- Python (Pandas, NumPy)
- SQL for data storage and analytics
- scikit-learn (baseline ML models)
- Jupyter Notebooks

## Project structure
```text
student-performance-ai/
  notebooks/            # EDA and experiments
  src/                  # reusable python modules
  data/                 # empty (dataset not included)
  reports/              # generated reports and figures
  README.md
  requirements.txt
```

## Status
Work in progress.

## Notes
No private student data is included in this repository.
