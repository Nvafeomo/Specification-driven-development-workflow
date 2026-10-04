# Feature Specification — Ask the Documents

**Status:** draft
**Author:** Student
**Reviewers:** assignment rubric
**Date:** 2026-10-04

## 1. Intent

Library staff need a way to ask policy questions in plain English and receive an answer grounded in the project’s policy documents instead of a guess. This feature lets a caller ask a question, receives a short answer, and sees which documents support it so they can verify the answer themselves. The endpoint is designed for policy lookup, not general chat.

## 2. User stories

- As a library employee, I want to ask a policy question in natural language so that I can quickly find the answer without reading every document.
- As a staff member, I want citations for any answer so that I can confirm the source and decide whether the answer is trustworthy.
- As an operator, I want the system to fail gracefully when the model is unavailable or the question has no answer so that users do not get a misleading result.

## 3. Acceptance criteria

1. Given a non-empty policy question that matches at least one document, when `GET /documents/answer?q=...` is called, then the response has HTTP 200, a non-empty `answer`, and one or more valid `citations`.
2. Given a question that does not match any supporting passage in the document set, when the endpoint is called, then the response has HTTP 200, `answer` is `null`, `citations` is an empty list, and `reason` explains that no supporting passage was found.
3. Given a blank or whitespace-only question, when the endpoint is called, then the API rejects the request with HTTP 422.
4. Given the model returns a citation whose `doc_id` does not exist in the repository, when the answer is assembled, then the invalid citation is discarded and the route does not return a fabricated document reference.
5. Given the model raises `ModelUnavailable` or `ModelTimeout`, when the endpoint is called, then the response still returns HTTP 200, `answer` is `null`, and `reason` contains the model failure text instead of returning a 5xx error.

## 4. Scope and non-goals

**In scope:**
- Answering a plain-English question against the document set in `data/documents/`.
- Returning citations with `doc_id` and a quote from the cited passage.
- Handling empty input, no-answer cases, invalid citations, and model failures.

**Explicitly out of scope:**
- Creating a new document index or a search engine service.
- Full-text search beyond the repository’s local document set.
- User authentication or authorisation.
- Answering questions outside the library policies in this repository.

## 5. Interfaces and contracts

`GET /documents/answer?q=How%20long%20can%20a%20loan%20last%3F`

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

The endpoint uses the repository’s standard API contract: request and response shapes are defined in `app/models.py`, and all request/response bodies are Pydantic models rather than ad hoc dictionaries.

## 6. Constraints

- The answer must always be grounded in a document from `data/documents/`.
- Invalid citations are rejected; a citation must match a real `doc_id` in the document set.
- Empty input is rejected with HTTP 422.
- Model errors are degraded responses, not 5xx failures for this endpoint.
- The model is called through `app.model_client.get_client()`, exactly as the other model-backed routes do.
- Document citations are returned as a list of `{doc_id, quote}` pairs; the route must not invent a document or quote.
- When multiple documents mention the same fact, the most recent relevant document wins unless a human review explicitly overrides it.

## 7. Test plan

The feature is validated at the API layer with one test per acceptance criterion in `tests/test_documents.py`, named `test_ac#_...`.

| Acceptance criterion | Test coverage |
|---|---|
| AC1 | a real document-backed question returns a populated answer and valid citations |
| AC2 | a no-match question returns `answer: null` and a reason |
| AC3 | whitespace input is rejected with HTTP 422 |
| AC4 | invalid model citations are stripped before the response is returned |
| AC5 | a model failure still returns HTTP 200 with a degraded response |

## 8. Open questions

- Should the system surface low-confidence model answers if they are backed by valid citations but the score is below 0.5?
- Should the system automatically prefer the newest relevant document for every contradictory answer, or should some topics require manual review?
- Should the API include the raw model answer when it is rejected on grounding grounds, or only the final answer and the reason?
