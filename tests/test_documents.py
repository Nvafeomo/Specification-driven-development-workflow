from __future__ import annotations

from app import model_client as mc


def test_ac1_question_returns_answer_and_citations(client):
    body = client.get("/documents/answer", params={"q": "How long can a loan last?"}).json()
    assert body["answer"]
    assert body["answer"] == "Loans run for 21 days."
    assert body["citations"]
    assert {c["doc_id"] for c in body["citations"]} <= {"policy-loans", "notice-2019-fines"}
    assert body["model"]["confidence"] > 0


def test_ac2_no_supporting_passage_returns_null_answer(client):
    body = client.get("/documents/answer", params={"q": "Why is the moon made of cheese?"}).json()
    assert body["answer"] is None
    assert body["citations"] == []
    assert body["reason"]


def test_ac3_empty_question_is_rejected(client):
    r = client.get("/documents/answer", params={"q": "   "})
    assert r.status_code == 422
    assert r.json()["detail"]


def test_ac4_invalid_citation_is_ignored(client, monkeypatch):
    class FakeClient:
        def complete(self, task, payload):
            return mc.ModelResult(
                value={
                    "answer": "Loans are limited to fourteen days for every borrower class.",
                    "citations": [{"doc_id": "policy-99", "quote": "fourteen days"}],
                    "reason": None,
                },
                confidence=0.81,
                model_version="v1",
                latency_ms=0,
            )

    monkeypatch.setattr(mc, "get_client", lambda: FakeClient())
    body = client.get("/documents/answer", params={"q": "How long is a loan?"}).json()
    assert body["answer"] is None
    assert body["citations"] == []
    assert body["reason"] == "no valid citations"


def test_ac5_model_failure_still_returns_a_200_response(client, monkeypatch):
    monkeypatch.setenv("STUB_FAILURE_RATE", "1.0")
    mc.reset_client()
    r = client.get("/documents/answer", params={"q": "How long is a loan?"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] is None
    assert body["reason"]
    assert body["model"] is None
