"""recommendations.py

Trasforma (lacune + distribuzione errori) in consigli pratici.

Obiettivo: consigli *spiegabili* e specifici, non una "black box".

Input:
- weaknesses: lista di topic dove lo studente è sotto soglia
- student_topic_error_df: output di scoring (formato long)
- student_topic_scores_df: output di scoring

Output:
- lista di Recommendation (titolo, perché, come fare, priorità)
"""

from __future__ import annotations

from dataclasses import dataclass

from typing import List, Tuple

import pandas as pd


@dataclass
class Recommendation:
    title: str
    why: str
    how: List[str]
    priority: int  # 1 alta, 2 media, 3 bassa


def _top_error_types_for_topic(
    student_id: str,
    topic: str,
    student_topic_error_df: pd.DataFrame,
    top_k: int = 2,
) -> List[Tuple[str, float]]:
    """Ritorna i top error_type per (student_id, topic) come (error_type, share)."""

    sub = student_topic_error_df[
        (student_topic_error_df["student_id"] == student_id)
        & (student_topic_error_df["topic"] == topic)
    ].copy()

    if sub.empty:
        return []

    sub = sub.sort_values("error_share", ascending=False)
    out: List[Tuple[str, float]] = []
    for _, r in sub.head(top_k).iterrows():
        out.append((str(r["error_type"]), float(r["error_share"])))
    return out


def generate_recommendations(
    student_id: str,
    weaknesses: List[str],
    student_topic_error_df: pd.DataFrame,
    student_topic_scores_df: pd.DataFrame,
    max_recommendations: int = 5,
) -> List[Recommendation]:
    """Genera raccomandazioni operative.

    Strategia:
    1) prendo i topic deboli e li ordino per accuracy crescente (più grave prima)
    2) per ogni topic guardo gli errori più frequenti (segno/algebra/concetto/...)
    3) genero consigli mirati
    """

    if not weaknesses:
        return [
            Recommendation(
                title="Mantieni il ritmo",
                why="Non emergono lacune marcate: continua con esercizi di consolidamento.",
                how=[
                    "Esercizi misti 3 volte a settimana (mix di topic)",
                    "Aggiungi 1 esercizio più difficile per topic per alzare il livello",
                ],
                priority=2,
            )
        ]

    sub_scores = student_topic_scores_df[student_topic_scores_df["student_id"] == student_id].copy()
    sub_scores = sub_scores[sub_scores["topic"].isin(weaknesses)].sort_values("topic_accuracy", ascending=True)

    recs: List[Recommendation] = []

    for _, r in sub_scores.iterrows():
        topic = str(r["topic"])
        acc = float(r["topic_accuracy"])
        avg_time = float(r["topic_avg_time_seconds"])

        top_errors = _top_error_types_for_topic(student_id, topic, student_topic_error_df, top_k=2)

        why_parts = [f"Accuracy {acc:.0%}"]
        if avg_time > 90:
            why_parts.append(f"tempo medio alto ({avg_time:.0f}s)")
        if top_errors:
            why_parts.append("errori prevalenti: " + ", ".join([e for e, _ in top_errors]))
        why = f"Nel topic **{topic}**: " + "; ".join(why_parts) + "."

        how: List[str] = []
        priorities: List[int] = []

        for err, _share in top_errors:
            err = err.lower()

            if err == "segno":
                how += [
                    "Scrivi ogni passaggio e fai un check finale sui segni (+/-)",
                    "Fai 10 esercizi brevi al giorno SOLO su passaggi di segno",
                ]
                priorities.append(1)
            elif err == "algebra":
                how += [
                    "Ripassa regole base (distributiva, frazioni, scomposizione)",
                    "Esercizi guidati: prima con soluzione, poi senza guardare",
                ]
                priorities.append(1)
            elif err == "formula":
                how += [
                    "Crea una mini-scheda formule (max 10) e ripetila ogni giorno",
                    "Allenati a riconoscere quale formula usare con esempi rapidi",
                ]
                priorities.append(2)
            elif err == "concetto":
                how += [
                    "Ripasso teoria con 2-3 esempi semplici (poi aumenti difficoltà)",
                    "Spiega a voce il concetto in 60 secondi (se non riesci, non è chiaro)",
                ]
                priorities.append(1)
            elif err == "distrazione":
                how += [
                    "Check finale obbligatorio: unità, segno, ordine di grandezza",
                    "Riduci la velocità del 10%: prima zero errori, poi tempo",
                ]
                priorities.append(2)
            elif err == "none":
                # "none" = corretto. Di solito non guida raccomandazioni.
                continue

        if not how:
            how = [
                "Risolvi 15 esercizi del topic dal facile al medio, segnando gli errori",
                "Dopo 2 giorni, rifai gli stessi esercizi senza guardare",
            ]
            priorities.append(2)

        if avg_time > 120:
            how.append("Aggiungi 5 esercizi a tempo (timer 60-90s) per automatizzare")
            priorities.append(2)

        # Dedup suggerimenti
        dedup: List[str] = []
        seen = set()
        for h in how:
            if h not in seen:
                dedup.append(h)
                seen.add(h)

        recs.append(
            Recommendation(
                title=f"Migliora {topic}",
                why=why,
                how=dedup,
                priority=min(priorities) if priorities else 2,
            )
        )

        if len(recs) >= max_recommendations:
            break

    recs.sort(key=lambda x: x.priority)
    return recs
