"""Exam-integrity tests (Correctness Property 5; Requirements 4.2, 27.1).

Task 15.1 (security-hardening-remediation). These tests assert the two halves of
the server-authoritative exam contract for the URN exam endpoints in
``backend.main``:

* **Fetch hides the answer key (Req 4.2).** ``GET /api/v1/urns/{slug}/exam`` returns
  ``UrnExamResponse`` whose questions are serialized through ``QuizQuestionOut`` --
  a model that has no ``correct_answer`` / ``explanation`` field. We recurse the
  entire JSON response to prove no answer-key field leaks at any depth.

* **Score is server-authoritative (Req 4.1, 4.5).** ``POST
  /api/v1/urns/{slug}/exam/submit`` computes the score from the server-held
  ``QuizQuestion.correct_answer`` ("A. Hổ" for the seeded question). Submitting the
  correct answer yields a full score; a wrong answer yields zero; and a bogus
  client-supplied ``score`` field in the request body is ignored -- the returned
  score reflects actual correctness only.

Fail-on-unfixed / pass-on-fixed reasoning (Req 27.1, 27.2): before Task 8.1 the
pre-submission payload shipped ``correct_answer``/``explanation`` to the client, so
``test_exam_fetch_excludes_answer_key`` would fail. Before Task 8.4 a client could
influence grading; ``test_score_is_server_authoritative_ignores_client_score``
would fail if the endpoint trusted a client-provided score instead of recomputing
it from server-held answers.

Reuses the shared ``client``, ``db_session``, and ``seeded_content`` fixtures from
``conftest.py``. The seeded content provides urn "cao-dinh", one motif "Hổ", and a
multiple-choice question whose ``correct_answer`` is "A. Hổ".
"""

from sqlalchemy import select

from backend.models import UnlockStatus
from backend.models import UrnExam
from backend.models import User
from backend.models import UserProgress


EMAIL = "exam_integrity@example.com"


def _register(client) -> None:
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": EMAIL,
            "password": "password123",
            "display_name": "Exam Integrity",
        },
    )
    assert res.status_code == 201, res.text


def _get_user(db_session) -> User:
    return db_session.execute(
        select(User).where(User.email == EMAIL)
    ).scalar_one()


def _make_eligible(db_session, seeded_content):
    """Master every active motif of the urn and create the UrnExam row.

    The exam endpoints gate on ``_ensure_urn_exam_eligibility`` (all motifs
    mastered) and the submit path requires a ``UrnExam`` row to record the
    attempt, so we seed both here using the shared request session.
    """
    user = _get_user(db_session)
    motif = seeded_content["motif"]
    urn = seeded_content["urn"]

    db_session.add(
        UserProgress(
            user_id=user.id,
            motif_id=motif.id,
            status=UnlockStatus.mastered,
        )
    )
    db_session.add(UrnExam(urn_id=urn.id, questions=[]))
    db_session.commit()
    return user


def _collect_keys(obj, found=None):
    """Recursively collect every dict key appearing anywhere in a JSON value."""
    if found is None:
        found = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            found.add(key)
            _collect_keys(value, found)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, found)
    return found


# ---------------------------------------------------------------------------
# Property 5a: exam fetch never leaks the answer key (Req 4.2)
# ---------------------------------------------------------------------------
def test_exam_fetch_excludes_answer_key(client, db_session, seeded_content):
    """Validates: Requirements 4.2"""
    _register(client)
    _make_eligible(db_session, seeded_content)

    urn = seeded_content["urn"]
    res = client.get(f"/api/v1/urns/{urn.slug}/exam")
    assert res.status_code == 200, res.text

    body = res.json()

    # Sanity: the payload actually contains the seeded question, so the
    # absence-of-answer-key assertion below is exercised against real data.
    question_ids = {q["id"] for q in body["questions"]}
    assert str(seeded_content["question"].id) in question_ids

    # Recurse the entire response: no answer-key field at ANY depth.
    keys = _collect_keys(body)
    assert "correct_answer" not in keys, body
    assert "explanation" not in keys, body

    # Belt-and-suspenders: the literal answer string must not appear anywhere
    # in the serialized payload.
    assert "correct_answer" not in res.text
    assert seeded_content["question"].correct_answer not in res.text


# ---------------------------------------------------------------------------
# Property 5b: submitted score equals the server-computed score (Req 4.1, 4.5)
# ---------------------------------------------------------------------------
def test_submit_correct_answer_yields_full_server_score(
    client, db_session, seeded_content
):
    """Validates: Requirements 4.2"""
    _register(client)
    _make_eligible(db_session, seeded_content)

    urn = seeded_content["urn"]
    question = seeded_content["question"]

    res = client.post(
        f"/api/v1/urns/{urn.slug}/exam/submit",
        json={
            "answers": [{"question_id": str(question.id), "answer": "A. Hổ"}],
            "time_taken_seconds": 42,
        },
    )
    assert res.status_code == 200, res.text
    payload = res.json()

    # Score is computed server-side from the server-held correct_answer.
    assert payload["score"] == 1
    assert payload["max_score"] == 1
    assert payload["percentage"] == 100
    assert payload["passed"] is True
    assert payload["results"][0]["correct"] is True


def test_submit_wrong_answer_yields_zero_server_score(
    client, db_session, seeded_content
):
    """Validates: Requirements 4.2"""
    _register(client)
    _make_eligible(db_session, seeded_content)

    urn = seeded_content["urn"]
    question = seeded_content["question"]

    res = client.post(
        f"/api/v1/urns/{urn.slug}/exam/submit",
        json={
            "answers": [{"question_id": str(question.id), "answer": "B. Rồng"}],
            "time_taken_seconds": 42,
        },
    )
    assert res.status_code == 200, res.text
    payload = res.json()

    # The server grades against its own answer key: a wrong answer is zero.
    assert payload["score"] == 0
    assert payload["percentage"] == 0
    assert payload["passed"] is False
    assert payload["results"][0]["correct"] is False


def test_score_is_server_authoritative_ignores_client_score(
    client, db_session, seeded_content
):
    """Validates: Requirements 4.2

    A client cannot dictate its own grade. We submit a *wrong* answer together
    with a bogus client-supplied ``score`` field; the authoritative response
    must reflect the actual (zero) correctness, never the injected value.
    """
    _register(client)
    _make_eligible(db_session, seeded_content)

    urn = seeded_content["urn"]
    question = seeded_content["question"]

    res = client.post(
        f"/api/v1/urns/{urn.slug}/exam/submit",
        json={
            "answers": [{"question_id": str(question.id), "answer": "B. Rồng"}],
            "time_taken_seconds": 42,
            # Bogus client-provided grading fields the server must ignore.
            "score": 999,
            "percentage": 100,
            "passed": True,
        },
    )
    assert res.status_code == 200, res.text
    payload = res.json()

    # Server-derived result wins over the injected client values.
    assert payload["score"] == 0
    assert payload["percentage"] == 0
    assert payload["passed"] is False
