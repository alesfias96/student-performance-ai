import pandas as pd
from src.profiling import build_student_profile

def test_build_profile_basic():
    topic_scores = pd.DataFrame({
        "student_id": ["s1","s1"],
        "topic": ["A","B"],
        "topic_n_questions": [10,10],
        "topic_accuracy": [0.9,0.4],
        "topic_avg_time_seconds": [20.0,50.0],
        "topic_avg_confidence": [4.5,2.0],
    })
    overall = pd.DataFrame({
        "student_id": ["s1"],
        "overall_n_questions": [20],
        "overall_accuracy": [0.65],
        "overall_avg_time_seconds": [35.0],
        "overall_avg_confidence": [3.2],
    })
    prof = build_student_profile("s1", topic_scores, overall)
    assert prof.student_id == "s1"
    assert len(prof.strengths) == 1
    assert len(prof.weaknesses) == 1
