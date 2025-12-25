def _register_user(client, email="bob@example.com"):
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Bob"},
    )
    assert register.status_code == 201, register.text
    return register


def test_full_gameplay_flow(client, seeded_content):
    _register_user(client)

    urns = client.get("/api/v1/urns")
    assert urns.status_code == 200, urns.text
    assert any(u["slug"] == "cao-dinh" for u in urns.json())

    urn_detail = client.get("/api/v1/urns/cao-dinh")
    assert urn_detail.status_code == 200, urn_detail.text
    assert urn_detail.json()["urn"]["slug"] == "cao-dinh"

    motif_id = str(seeded_content["motif"].id)
    motif = client.get(f"/api/v1/motifs/{motif_id}")
    assert motif.status_code == 200, motif.text
    lesson = motif.json()["lesson"]
    assert lesson
    assert lesson["historical_context"] == "Bối cảnh lịch sử về họa tiết Hổ."
    assert lesson["symbolism"] == "Ý nghĩa biểu tượng của họa tiết Hổ."
    assert lesson["fun_fact"] == "Sự thật thú vị về họa tiết Hổ."
    assert lesson["is_ai_generated"] is True

    unlock = client.post(
        "/progress/unlock",
        json={"motif_id": motif_id, "mesh_name": seeded_content["motif"].mesh_name},
    )
    assert unlock.status_code == 200, unlock.text
    assert unlock.json()["status"] == "discovered"
    assert unlock.json()["xp_awarded"] >= 25  # discovery + maybe badge bonus

    quiz_locked = client.get(f"/api/v1/motifs/{motif_id}/quiz")
    assert quiz_locked.status_code == 400

    complete = client.post(f"/api/v1/motifs/{motif_id}/complete-lesson")
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] in ("learned", "mastered")

    quiz = client.get(f"/api/v1/motifs/{motif_id}/quiz")
    assert quiz.status_code == 200, quiz.text
    assert "correct_answer" not in quiz.text

    qid = str(seeded_content["question"].id)

    wrong = client.post(
        "/api/v1/quizzes/submit",
        json={
            "motif_id": motif_id,
            "answers": [{"question_id": qid, "answer": "B. Rồng"}],
        },
    )
    assert wrong.status_code == 200, wrong.text
    assert wrong.json()["passed"] is False
    assert wrong.json()["status"] == "learned"
    assert (
        wrong.json()["results"][0]["explanation"]
        == "Đáp án đúng là Hổ: họa tiết mô tả con hổ."
    )

    correct = client.post(
        "/api/v1/quizzes/submit",
        json={
            "motif_id": motif_id,
            "answers": [{"question_id": qid, "answer": "A. Hổ"}],
        },
    )
    assert correct.status_code == 200, correct.text
    assert correct.json()["passed"] is True
    assert correct.json()["status"] == "mastered"
    assert (
        correct.json()["results"][0]["explanation"]
        == "Đáp án đúng là Hổ: họa tiết mô tả con hổ."
    )

    badges = client.get("/api/v1/users/me/badges")
    assert badges.status_code == 200, badges.text
    badge_slugs = {b["badge"]["slug"] for b in badges.json()}
    assert "first-discovery" in badge_slugs
    assert "first-mastered" in badge_slugs

    streak = client.get("/api/v1/users/me/streak")
    assert streak.status_code == 200, streak.text
    assert streak.json()["current_streak"] >= 1

    leaderboard = client.get("/api/v1/leaderboard?limit=10")
    assert leaderboard.status_code == 200, leaderboard.text
    assert any(entry["display_name"] == "Bob" for entry in leaderboard.json())
