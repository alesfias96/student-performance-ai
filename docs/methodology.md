# Methodology

## 1) Dataset sintetico
Ogni studente ha una **abilità latente** per topic (valore 0–1).  
Ogni domanda ha una **difficoltà** 1–5.  
La probabilità di risposta corretta è funzione di:
- abilità dello studente sul topic
- difficoltà della domanda
- rumore controllato (variabilità realistica)

In caso di errore, viene campionato un `error_type` plausibile:
- `segno`, `algebra`, `formula`, `concetto`, `distrazione`, `none`

In più, vengono simulati `time_seconds` e `confidence` in modo coerente:
- maggiore abilità → meno tempo medio, confidenza più alta
- maggiore difficoltà → più tempo medio, confidenza più bassa

## 2) Scoring
A partire dalle risposte:
- accuracy per topic
- tempo medio per topic
- confidenza media per topic
- distribuzione errori per topic

## 3) Profiling
Le accuracy vengono mappate in livelli:
- beginner / intermediate / advanced

e in etichette:
- strength / weakness / neutral

## 4) Recommendations
Regole trasparenti basate su:
- topic più deboli
- errori più frequenti
- tempo medio elevato

## 5) Report
Report HTML (Jinja2) con:
- overview
- grafici (matplotlib) inseriti come immagini base64
- raccomandazioni prioritarie
