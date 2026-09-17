from typing import Literal

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    selected_scope_id: str | None = None


class ScopeCandidate(BaseModel):
    id: str
    condition: str
    reason: str
    confidence: float


class TreatmentRecord(BaseModel):
    id: str
    treatment: str
    studied_condition: str
    type: str
    stage: str
    result: str
    organization: str
    source: str
    source_type: str
    review_date: str
    retrieval_reason: str
    similarity: float | None = None


class ProcedureRecord(BaseModel):
    id: str
    condition: str
    version: str
    review_date: str
    source: str
    sections: dict[str, str]
    approval_status: Literal["illustrative_unapproved", "approved"]


class ScopeResult(BaseModel):
    scope: ScopeCandidate
    standard_procedure: ProcedureRecord | None
    illustrative_procedure: ProcedureRecord | None = None
    procedure_status: str
    emerging_treatments: list[TreatmentRecord]


class SearchResponse(BaseModel):
    query: str
    intent: Literal[
        "briefing", "clarification", "out_of_scope", "urgent", "personalized_request", "incomplete"
    ]
    message: str | None = None
    scope_options: list[ScopeCandidate] = Field(default_factory=list)
    results: list[ScopeResult] = Field(default_factory=list)
    presentation: dict | None = None
    data_status: list[str] = Field(default_factory=list)


class DetailResponse(BaseModel):
    treatment_id: str
    available: bool
    message: str
    record: TreatmentRecord | None = None
    approved_detail: dict | None = None
