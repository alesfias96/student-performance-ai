"""report_builder.py

Genera un report HTML per uno studente.

Perché HTML e non PDF?
- HTML è immediato da aprire e condividere
- possiamo incorporare i grafici come immagini base64 senza dipendenze extra

Pipeline:
1) carica CSV processed (scoring)
2) costruisce profilo (profiling)
3) genera raccomandazioni (recommendations)
4) crea grafici (visualization)
5) assembla un template HTML (Jinja2)
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

import pandas as pd
from jinja2 import Template

from . import config
from .profiling import StudentProfile, build_student_profile
from .recommendations import Recommendation, generate_recommendations
from .visualization import (
    fig_to_base64_png,
    plot_accuracy_bar,
    plot_error_heatmap,
    plot_radar,
)


HTML_TEMPLATE = r"""
<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Report Studente - {{ student_id }}</title>
  <style>
    :root {
      --bg: #0b1020;
      --card: #121a33;
      --text: #e7e9ee;
      --muted: #b8bfd1;
      --ok: #43d19e;
      --warn: #ffcc66;
      --bad: #ff6b6b;
      --shadow: 0 10px 30px rgba(0,0,0,.35);
      --radius: 16px;
    }
    body { margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; background: var(--bg); color: var(--text); }
    .wrap { max-width: 1100px; margin: 32px auto; padding: 0 16px; }
    h1 { font-size: 28px; margin: 0 0 8px; }
    h2 { font-size: 18px; margin: 0 0 12px; color: var(--muted); font-weight: 600; }
    .grid { display: grid; gap: 16px; }
    .grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .grid-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .card { background: var(--card); border-radius: var(--radius); padding: 16px; box-shadow: var(--shadow); }
    .kpi { display: flex; flex-direction: column; gap: 6px; }
    .kpi .label { color: var(--muted); font-size: 12px; }
    .kpi .value { font-size: 20px; font-weight: 700; }
    .pill { display: inline-block; padding: 6px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    .pill.ok { background: rgba(67,209,158,.15); color: var(--ok); }
    .pill.warn { background: rgba(255,204,102,.15); color: var(--warn); }
    .pill.bad { background: rgba(255,107,107,.15); color: var(--bad); }
    .muted { color: var(--muted); }
    .row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
    .list { margin: 0; padding-left: 18px; }
    .img { width: 100%; border-radius: 12px; border: 1px solid rgba(255,255,255,.08); }
    .topic-table { width: 100%; border-collapse: collapse; }
    .topic-table th, .topic-table td { border-bottom: 1px solid rgba(255,255,255,.08); padding: 10px 6px; text-align: left; font-size: 13px; }
    .topic-table th { color: var(--muted); font-weight: 600; }
    @media (max-width: 900px) { .grid-3 { grid-template-columns: 1fr; } .grid-2 { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="row">
      <div>
        <h1>Report Studente — {{ student_id }}</h1>
        <div class="muted">Generato automaticamente da student-performance-ai</div>
      </div>
      <div class="pill {{ level_class }}">Livello: {{ overall_level }}</div>
    </div>

    <div style="height: 16px"></div>

    <div class="grid grid-3">
      <div class="card kpi">
        <div class="label">Accuracy totale</div>
        <div class="value">{{ (overall_accuracy*100)|round(1) }}%</div>
        <div class="muted">su {{ overall_n_questions }} domande</div>
      </div>
      <div class="card kpi">
        <div class="label">Tempo medio</div>
        <div class="value">{{ overall_avg_time_seconds|round(1) }}s</div>
        <div class="muted">per domanda</div>
      </div>
      <div class="card kpi">
        <div class="label">Punti forti</div>
        <div class="value">{{ strengths_count }}</div>
        <div class="muted">topic sopra soglia</div>
      </div>
    </div>

    <div style="height: 16px"></div>

    <div class="grid grid-2">
      <div class="card">
        <h2>Accuracy per topic</h2>
        <img class="img" src="data:image/png;base64,{{ bar_png }}" alt="bar" />
      </div>
      <div class="card">
        <h2>Profilo (Radar)</h2>
        <img class="img" src="data:image/png;base64,{{ radar_png }}" alt="radar" />
      </div>
    </div>

    <div style="height: 16px"></div>

    <div class="card">
      <h2>Errori per topic (heatmap)</h2>
      <img class="img" src="data:image/png;base64,{{ heat_png }}" alt="heat" />
      <div class="muted" style="margin-top: 8px; font-size: 12px;">Include anche <b>none</b> (risposte corrette). Se vuoi vedere solo gli errori, si può filtrare in seguito.</div>
    </div>

    <div style="height: 16px"></div>

    <div class="grid grid-2">
      <div class="card">
        <h2>Topic principali</h2>
        <table class="topic-table">
          <thead>
            <tr>
              <th>Topic</th>
              <th>Accuracy</th>
              <th>Tempo medio</th>
              <th>Etichetta</th>
            </tr>
          </thead>
          <tbody>
            {% for t in topics %}
            <tr>
              <td>{{ t.topic }}</td>
              <td>{{ (t.accuracy*100)|round(1) }}%</td>
              <td>{{ t.avg_time_seconds|round(1) }}s</td>
              <td>
                {% if t.label == 'strength' %}
                  <span class="pill ok">Punto forte</span>
                {% elif t.label == 'weakness' %}
                  <span class="pill bad">Lacuna</span>
                {% else %}
                  <span class="pill warn">Intermedio</span>
                {% endif %}
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>

      <div class="card">
        <h2>Raccomandazioni operative</h2>
        {% if recommendations|length == 0 %}
          <div class="muted">Nessuna raccomandazione disponibile.</div>
        {% endif %}
        {% for r in recommendations %}
          <div style="margin-bottom: 14px; padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,.08);">
            <div class="row">
              <div style="font-weight: 800;">{{ r.title }}</div>
              <div class="pill {% if r.priority == 1 %}bad{% elif r.priority == 2 %}warn{% else %}ok{% endif %}">Priorità {{ r.priority }}</div>
            </div>
            <div class="muted" style="margin: 6px 0 8px;">{{ r.why | safe }}</div>
            <ul class="list">
              {% for h in r.how %}
                <li>{{ h }}</li>
              {% endfor %}
            </ul>
          </div>
        {% endfor %}
      </div>
    </div>

    <div style="height: 24px"></div>
    <div class="muted" style="font-size: 12px;">
      Nota: i dati sono sintetici (inventati) e il sistema usa regole trasparenti e metriche statistiche.
    </div>
  </div>
</body>
</html>
"""


def _level_to_css_class(level: str) -> str:
    level = (level or "").lower()
    if level == "advanced":
        return "ok"
    if level == "beginner":
        return "bad"
    return "warn"


def build_student_report_html(
    student_id: str,
    topic_scores_df: pd.DataFrame,
    overall_df: pd.DataFrame,
    error_shares_df: pd.DataFrame,
) -> str:
    """Ritorna l'HTML del report per uno studente."""

    profile: StudentProfile = build_student_profile(student_id, topic_scores_df, overall_df)

    weaknesses_topics = [t.topic for t in profile.weaknesses]
    recs: List[Recommendation] = generate_recommendations(
        student_id=student_id,
        weaknesses=weaknesses_topics,
        student_topic_error_df=error_shares_df,
        student_topic_scores_df=topic_scores_df,
        max_recommendations=5,
    )

    topic_sub = topic_scores_df[topic_scores_df["student_id"] == student_id].copy()
    err_sub = error_shares_df[error_shares_df["student_id"] == student_id].copy()

    bar_png = fig_to_base64_png(plot_accuracy_bar(topic_sub, title="Accuracy per topic"))
    radar_png = fig_to_base64_png(plot_radar(topic_sub, title="Profilo (Radar)"))
    heat_png = fig_to_base64_png(plot_error_heatmap(err_sub, title="Distribuzione errori per topic"))

    topics_for_table = [asdict(t) for t in (profile.strengths + profile.neutrals + profile.weaknesses)]

    tpl = Template(HTML_TEMPLATE)
    return tpl.render(
        student_id=profile.student_id,
        overall_level=profile.overall_level,
        level_class=_level_to_css_class(profile.overall_level),
        overall_accuracy=profile.overall_accuracy,
        overall_avg_time_seconds=profile.overall_avg_time_seconds,
        overall_n_questions=profile.overall_n_questions,
        strengths_count=len(profile.strengths),
        bar_png=bar_png,
        radar_png=radar_png,
        heat_png=heat_png,
        topics=topics_for_table,
        recommendations=[asdict(r) for r in recs],
    )


def build_student_report(
    student_id: str,
    topic_scores_csv: Path = config.STUDENT_TOPIC_SCORES_CSV,
    overall_csv: Path = config.STUDENT_OVERALL_SUMMARY_CSV,
    error_shares_csv: Path = config.STUDENT_TOPIC_ERROR_CSV,
    out_dir: Path = config.REPORTS_DIR,
    out_name: Optional[str] = None,
) -> Path:
    """Genera e salva il report HTML. Ritorna il path creato."""

    out_dir.mkdir(parents=True, exist_ok=True)

    topic_scores_df = pd.read_csv(topic_scores_csv)
    overall_df = pd.read_csv(overall_csv)
    error_df = pd.read_csv(error_shares_csv)

    html = build_student_report_html(student_id, topic_scores_df, overall_df, error_df)

    if out_name is None:
        out_name = f"report_{student_id}.html"

    out_path = out_dir / out_name
    out_path.write_text(html, encoding="utf-8")
    return out_path
