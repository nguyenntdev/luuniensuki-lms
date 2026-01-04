from backend.models import UrnExam


def _register_user(client, email="cert@example.com"):
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "Cert User"},
    )
    assert register.status_code == 201, register.text


def test_certificate_issued_on_urn_exam_pass(client, db_session, seeded_content):
    _register_user(client)

    urn = seeded_content["urn"]
    question = seeded_content["question"]

    db_session.add(UrnExam(urn_id=urn.id, questions=[]))
    db_session.commit()

    submit = client.post(
        f"/api/v1/urns/{urn.slug}/exam/submit",
        json={
            "answers": [
                {
                    "question_id": str(question.id),
                    "answer": "A. Hổ",
                }
            ],
            "time_taken_seconds": 42,
        },
    )
    assert submit.status_code == 200, submit.text
    payload = submit.json()
    assert payload["passed"] is True
    assert payload["certificate"]
    assert payload["certificate"]["issuer_name"] == "Lưu Niên Sử Kí"

    code = payload["certificate"]["code"]
    verify = client.get(f"/api/v1/certificates/{code}")
    assert verify.status_code == 200, verify.text
    verified = verify.json()
    assert verified["code"] == code
    assert verified["issuer_name"] == "Lưu Niên Sử Kí"
    assert verified["display_name"] == "Cert User"
