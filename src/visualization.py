"""visualization.py

Qui costruiamo i grafici per il report.

Scelte intenzionali:
- SOLO matplotlib (progetto più leggero e portabile)
- funzioni piccole e testabili

Grafici:
1) Bar chart: accuracy per topic
2) Radar chart: rappresentazione "da report"
3) Heatmap: distribuzione errori per topic
"""

from __future__ import annotations

import base64
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def fig_to_base64_png(fig, dpi: int = 140) -> str:
    """Converte una figura matplotlib in stringa base64 PNG (da embeddare in HTML)."""
    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def plot_accuracy_bar(topic_scores: pd.DataFrame, title: str = "Accuracy per topic"):
    """Bar chart: topic vs accuracy.

    topic_scores deve avere colonne:
    - topic
    - topic_accuracy
    """
    topics = topic_scores["topic"].astype(str).tolist()
    acc = topic_scores["topic_accuracy"].astype(float).to_numpy()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(topics, acc)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Accuracy")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=35)
    ax.grid(True, axis="y", linestyle=":", alpha=0.5)
    return fig


def plot_radar(topic_scores: pd.DataFrame, title: str = "Profilo (Radar)"):
    """Radar chart (grafico polare).

    topic_scores deve avere colonne:
    - topic
    - topic_accuracy
    """
    labels = topic_scores["topic"].astype(str).tolist()
    values = topic_scores["topic_accuracy"].astype(float).to_numpy()

    # chiudiamo il poligono (ripetiamo il primo punto)
    values = np.concatenate([values, values[:1]])
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    angles = np.concatenate([angles, angles[:1]])

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, values)
    ax.fill(angles, values, alpha=0.2)
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    return fig


def plot_error_heatmap(error_shares: pd.DataFrame, title: str = "Distribuzione errori per topic"):
    """Heatmap: topic (righe) x error_type (colonne), valori = error_share.

    error_shares deve avere colonne:
    - topic
    - error_type
    - error_share
    """
    pivot = error_shares.pivot_table(index="topic", columns="error_type", values="error_share", fill_value=0.0)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    im = ax.imshow(pivot.to_numpy(), aspect="auto")

    ax.set_title(title)
    ax.set_xlabel("error_type")
    ax.set_ylabel("topic")

    ax.set_xticks(np.arange(pivot.shape[1]))
    ax.set_xticklabels([str(c) for c in pivot.columns], rotation=35, ha="right")
    ax.set_yticks(np.arange(pivot.shape[0]))
    ax.set_yticklabels([str(i) for i in pivot.index])

    fig.colorbar(im, ax=ax, shrink=0.85)
    return fig
