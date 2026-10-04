# Feature Specification — Ask the Documents

**Status:** approved
**Author:** Student
**Reviewers:** assignment rubric
**Date:** 2026-10-04

## 1. Intent

Library staff need a way to ask policy questions in plain English and receive an answer grounded in the organisation’s official policy documents rather than a guess. This feature answers a document-backed question, attaches citations to the answer, and refuses to show a result when a document does not support it. It is meant to help people find the right policy quickly without forcing them to read every document manually.

## 2. User stories

- As a library employee, I want to ask a natural-language question about borrowing, fines, or policy terms so that I can quickly confirm the current rule.
- As a staff member, I want each answer to include citations from the policy set so that I can verify the source and the wording before acting on it.
- As an operator, I want the endpoint to degrade gracefully when the model is unavailable or the question has no grounded answer so that the system remains transparent rather than misleading.
- As a policy maintainer, I want contradictory guidance to resolve in favour of the newest relevant document so that the answer reflects current policy rather than stale FAQ text.

## 3. Acceptance criteria

1. Given a non-empty question that matches one or more policy documents, when `GET /documents/answer?q=...` is called, then the endpoint returns HTTP 200, `answer` is a plain-language string, and `citations` contains one or more valid document references.
2. Given the same question has answers in more than one relevant document, when the endpoint resolves the answer, then it chooses the newest relevant document and cites that source instead of a stale FAQ or older guidance.
3. Given the question has no supporting passage in the document set, when the endpoint is called, then the response returns HTTP 200, `answer` is `null`, `citations` is an empty list, and `reason` is set to a short explanation such as `no supporting passage found`.
4. Given a blank or whitespace-only question, when the endpoint is called, then the request is rejected with HTTP 422 and an error body is returned.
5. Given the model returns a citation whose `doc_id` is not present in the document set, when the response is assembled, then the invalid citation is discarded and the route returns `answer: null` with `reason: "no valid citations"` rather than surfacing a fabricated reference.
6. Given the model raises `ModelUnavailable` or `ModelTimeout`, when the endpoint is called, then the response still returns HTTP 200, `answer` is `null`, `citations` is an empty list, and `reason` contains the model failure text; it must not return a 5xx error.

## 4. Scope and non-goals

**In scope:**
- Searching the repository’s policy documents for the closest answer to a plain-English question.
- Returning a concise answer plus document citations.
- Rejecting blank input, invalid citations, and model failures without breaking the request.
- Resolving contradictory policy sources by selecting the newest relevant document.

**Explicitly out of scope:**
- User authentication, authorization, or access control.
- Creating or editing policy documents.
- Querying anything outside the repository’s `data/documents/` directory.
- A general-purpose chat interface or multi-turn conversation state.

## 5. Interfaces and contracts

Request:

```http
GET /documents/answer?q=How%20long%20can%20a%20loan%20last%3F
```

Successful response:

```json
{
  "answer": "Loans run for 21 days.",
  "citations": [
    {"doc_id": "policy-loans", "quote": "Standard loans run for 21 days for all borrower classes."}
  ],
  "reason": null,
  "model": {
    "value": {"answer": "...", "citations": [{"doc_id": "policy-loans", "quote": "..."}]},
    "confidence": 0.81,
    "model_version": "v1",
    "latency_ms": 0
  }
}
```

No-answer response:

```json
{
  "answer": null,
  "citations": [],
  "reason": "no supporting passage found",
  "model": null
}
```

Invalid-citation response:

```json
{
  "answer": null,
  "citations": [],
  "reason": "no valid citations",
  "model": {"value": ..., "confidence": 0.81, "model_version": "v1", "latency_ms": 0}
}
```

The path is `/documents/answer` and it always returns a `DocumentAnswerResponse` model from `app/models.py`. The request and response shapes are not ad hoc dictionaries; they are declared once and reused by the API layer.

## 6. Constraints

- **Grounding:** every answer must be backed by a valid document and citation in `data/documents/`.
- **Contradiction handling:** when two relevant documents disagree, the newest relevant document wins; the older FAQ is not treated as the source of truth if a later policy document supersedes it.
- **Input validation:** `q` must be non-empty after trimming whitespace; an empty string is rejected with HTTP 422.
- **Invalid citations:** a `citation.doc_id` that is not in the document set is discarded; the route does not show fabricated citations.
- **Model degradation:** if the model fails or times out, the endpoint still returns HTTP 200 with `answer: null`, `citations: []`, and a `reason` string; the endpoint never surfaces a 5xx from the model layer.
- **Model access:** access goes through `app.model_client.get_client()`, and all model-backed responses include the returned `confidence` and `model_version` values.
- **Response contract:** the endpoint must return the standard `ErrorBody` shape for any 4xx or 5xx exception and the custom document answer response for successful or degraded model responses.

## 7. Test plan

The implementation is verified at the API layer with tests in `tests/test_documents.py`. Each acceptance criterion is mapped directly to a test with the `test_acN_...` naming convention used in this repository.

| Criterion | Test |
|---|---|
| AC1 | a real question returns a grounded answer and citations |
| AC2 | contradictory policy sources choose the newest relevant document |
| AC3 | no supporting passage has `answer: null` and a reason |
| AC4 | blank input is rejected with HTTP 422 |
| AC5 | invalid citations are stripped and rejected |
| AC6 | model failure degrades cleanly with HTTP 200 |

## 8. Open questions

- Should low-confidence model answers be suppressed when they are grounded but still under 0.5 confidence, or should callers make that choice themselves?
- When a policy is amended by a later document, should the system also show the superseded document in the citation set, or only the controlling one?
- Should this endpoint ever return multiple citations when the answer is a synthesis of several documents, or should it always prefer the single newest policy source?
