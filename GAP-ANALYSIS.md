# Gap analysis

## 1. What the agent assumed during reconnaissance

The main thing the agent assumed was that the model answer should be shown if it sounded good and had a citation. That was a problem because the document set is the real source of truth, not the model. In this feature, a newer policy document can override an older FAQ, so the answer has to be grounded in the newest relevant document.

The agent also assumed that any non-empty question could be answered if it matched at least one document. That was not always true. Some questions had multiple relevant documents, and some had no good answer at all. The spec needed to be clearer about conflicting documents and bad citations.

## 2. Which acceptance criteria passed on the first blind handoff and which did not

The first handoff passed the basic failure cases, but it failed on the key grounding checks. The biggest issues were AC1 and AC5:

- AC1: a real question should return an answer with valid citations.
- AC5: a fake or missing citation should be rejected.

The second pass fixed these by making the document set the authority and by removing invalid citations before returning a response.

## 3. What was missing or ambiguous in version 1

The original v1 spec was too general about how conflicting answers should be handled. It said the endpoint should return an answer and some citations, but it did not say that the newest relevant document should win.

This is the important part that was missing:

> "Given a non-empty policy question that matches at least one document, when `GET /documents/answer?q=...` is called, then the response has HTTP 200, a non-empty `answer`, and one or more valid `citations`."

That was later revised to say:

> "Given the same question has answers in more than one relevant document, when the endpoint resolves the answer, then it chooses the newest relevant document and cites that source instead of a stale FAQ or older guidance."

That change mattered because it prevented the system from using an older FAQ answer when a newer policy document was the real source. The v1 spec also did not clearly say what to do when the model returned a citation that did not exist. The revised version made that clearer:

> "Given the model returns a citation whose `doc_id` is not present in the document set, when the response is assembled, then the invalid citation is discarded and the route returns `answer: null` with `reason: "no valid citations"` rather than surfacing a fabricated reference."

This made the outcome much more specific and testable.

## 4. What round 2 still got wrong and what would change in version 3

The second round did not fail the repo tests once the route was fixed. The main thing I would still want to define in a version 3 is how low-confidence model answers should be treated. If the answer is grounded but still below the 0.5 threshold, the spec should say whether it is shown, hidden, or reviewed by a person.

I would also tighten the meaning of “newest relevant document” so it only applies within the same topic area. That would stop the system from picking a newer but unrelated document just because it is newer.

## 5. Where the specification went too far and where it stopped too soon

The first version went a little too far in the interface section by acting like the exact wording of the answer was part of the contract. That was too specific. The real requirement was that the answer had to be grounded and cited, not that it had to use one exact sentence.

The second version fixed that by keeping the contract clear but leaving the wording of the answer to the implementation. It still defined the important behavior, like HTTP status, answer presence, citations, and reason codes, but it did not force the implementation to use one exact phrase.

That is the right balance. The spec should say what the system must do and what it must not do, without telling the implementation how to write the final sentence.
