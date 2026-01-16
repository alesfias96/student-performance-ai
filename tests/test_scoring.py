import pandas as pd
from src.scoring import compute_student_topic_scores, compute_student_overall_summary, compute_student_topic_error_shares

def _toy_answers_df():
    return pd.DataFrame({
        "student_id": ["s1","s1","s1","s2"],
        "test_id": ["t1","t1","t1","t1"],
        "question_id": ["q1","q2","q3","q1"],
        "topic": ["A","A","B","A"],
        "subskill": ["a1","a1","b1","a1"],
        "difficulty": [1,2,2,1],
        "correct_answer": [1.0,2.0,3.0,1.0],
        "answer_given": [1.0,0.0,3.0,0.0],
        "is_correct": [1,0,1,0],
        "error_type": ["none","algebra","none","segno"],
        "time_seconds": [10,20,30,15],
        "confidence": [4,2,5,1],
    })

def test_topic_scores_shape():
    df = _toy_answers_df()
    out = compute_student_topic_scores(df)
    assert set(out.columns) == {"student_id","topic","topic_n_questions","topic_accuracy","topic_avg_time_seconds","topic_avg_confidence"}
    assert len(out) == 3  # s1-A, s1-B, s2-A

def test_overall_scores():
    df = _toy_answers_df()
    out = compute_student_overall_summary(df)
    s1 = out[out["student_id"]=="s1"].iloc[0]
    assert abs(float(s1["overall_accuracy"]) - (2/3)) < 1e-6

def test_error_shares_sum_to_one_per_student_topic():
    df = _toy_answers_df()
    out = compute_student_topic_error_shares(df)
    grp = out.groupby(["student_id","topic"])["error_share"].sum().round(6)
    # ogni (studente,topic) deve sommare a 1
    assert all(grp == 1.0)
