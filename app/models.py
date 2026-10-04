"""Request and response shapes. Everything crossing the API boundary is declared here."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Kind = Literal["central", "branch", "bookmobile", "research"]


class Library(BaseModel):
    """One facility. This is the record type the whole app is built around."""

    id: int
    name: str
    city: str
    state: str = Field(min_length=2, max_length=2)
    kind: Kind
    year_founded: int
    annual_visits: int
    has_makerspace: bool


class LibraryCreate(BaseModel):
    """The write path. Note that ``id`` is assigned by the server, never by the caller."""

    name: str = Field(min_length=1, max_length=120)
    city: str = Field(min_length=1, max_length=80)
    state: str = Field(min_length=2, max_length=2)
    kind: Kind
    year_founded: int = Field(ge=1700, le=2100)
    annual_visits: int = Field(ge=0)
    has_makerspace: bool = False


class Page(BaseModel):
    """Every list endpoint returns this shape. Copy it for new list endpoints."""

    items: list[Library]
    total: int
    limit: int
    offset: int


class ModelPayload(BaseModel):
    """How a model-backed endpoint reports what the model said.

    Every model-backed response embeds this, so a caller can always see the
    confidence and which model version produced the answer.
    """

    value: object
    confidence: float
    model_version: str
    latency_ms: int


class DescribeResponse(BaseModel):
    library_id: int
    description: str
    model: ModelPayload


class ErrorBody(BaseModel):
    """The one error shape. Every 4xx and 5xx this app raises looks like this."""

    detail: str
    code: str


class DocumentCitation(BaseModel):
    """A citation for a document-backed answer."""

    doc_id: str
    quote: str


class DocumentAnswerResponse(BaseModel):
    """`GET /documents/answer` — answer a plain-language question with citations."""

    answer: Optional[str]
    citations: list[DocumentCitation]
    reason: Optional[str] = None
    model: Optional[ModelPayload] = None


class SummaryResponse(BaseModel):
    """`GET /libraries/summary` — see specs/filtered-summary.md §5."""

    count: int
    filters: dict
    summary: Optional[str]
    word_count: int
    truncated: bool
    cached: bool
    model: Optional[ModelPayload]
    model_error: Optional[str]
