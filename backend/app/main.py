import logging
import re
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .catalog import Catalog
from .config import settings
from .intent import classify
from .presenter import Presenter
from .schemas import DetailResponse, SearchRequest, SearchResponse
from .search import SemanticIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Healthcare Strategy Briefing API",
    version="0.1.0",
    description="Semantic scope recognition and provenance-preserving healthcare research retrieval.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_catalog() -> Catalog:
    return Catalog(settings.standard_procedures_path, settings.emerging_treatments_path)


@lru_cache(maxsize=1)
def get_index() -> SemanticIndex:
    return SemanticIndex(get_catalog().concepts(), settings.embedding_model)


@lru_cache(maxsize=1)
def get_presenter() -> Presenter:
    return Presenter(settings.llm_provider, settings.llm_api_key, settings.llm_base_url, settings.llm_model)


@app.get("/health")
def health():
    catalog = get_catalog()
    return {
        "status": "ok",
        "standard_procedure_records": len(catalog.procedures),
        "emerging_treatment_records": len(catalog.treatments),
        "embedding_model": settings.embedding_model,
        "llm_enabled": get_presenter().enabled,
    }


def _procedure_record(procedure: dict | None):
    if not procedure:
        return None
    # Supplied demo records are illustrative; none has approval metadata in the source file.
    return {**procedure, "approval_status": "illustrative_unapproved"}


def _resolve(request: SearchRequest):
    catalog, index = get_catalog(), get_index()
    candidates = index.find(request.query)
    if request.selected_scope_id:
        candidates = [candidate for candidate in candidates if candidate.concept["id"] == request.selected_scope_id]
        if not candidates:
            procedure = catalog.by_id.get(request.selected_scope_id)
            if not procedure:
                raise HTTPException(status_code=400, detail="Unknown scope ID")
            from .search import Candidate
            candidates = [Candidate({"id": procedure["id"], "condition": procedure["condition"], "procedure": procedure}, 1.0, "User-selected scope")]

    if not candidates:
        return SearchResponse(query=request.query, intent="clarification", message="I could not identify a supported condition scope. Please add a condition or choose a related term.")

    normalized_query_for_scope = catalog.normalize(request.query)
    for candidate in candidates:
        if candidate.concept["id"] == "STD-T2D-001" and "diabetes" in normalized_query_for_scope and "type 2" not in normalized_query_for_scope:
            candidate.reason = "Possible type 2 diabetes match for broad 'diabetes' wording; subtype is unspecified and must be confirmed."

    # Explicitly named multiple conditions should remain separate result scopes.
    explicitly_named = []
    if not request.selected_scope_id:
        explicitly_named = [
            candidate for candidate in candidates
            if candidate.score >= 0.9 and any(
                catalog.normalize(term)
                and catalog.normalize(term) in catalog.normalize(request.query)
                for term in candidate.concept["terms"]
            )
        ]
        if len({c.concept["id"] for c in explicitly_named}) > 1:
            candidates = explicitly_named

    generic_symptoms = {"breathlessness", "shortness of breath", "chest pain", "chest discomfort", "wheezing", "headache", "memory loss", "tremor"}
    normalized_query = catalog.normalize(request.query)
    mentions_condition = any(
        any(catalog.normalize(term) in normalized_query for term in candidate.concept["terms"])
        for candidate in candidates
    )
    symptom_only = any(symptom in normalized_query for symptom in generic_symptoms) and not mentions_condition
    if not request.selected_scope_id and symptom_only and not explicitly_named:
        options = [
            {"id": c.concept["id"], "condition": c.concept["condition"], "reason": c.reason, "confidence": round(c.score, 3)}
            for c in candidates[:6]
        ]
        return SearchResponse(query=request.query, intent="clarification", message="This symptom can relate to more than one condition. Choose a scope to continue; this assistant cannot diagnose.", scope_options=options)

    # Strong aliases resolve directly. Symptom-like terms can map to multiple conditions;
    # similarly scored candidates are shown as alternatives rather than silently selected.
    if not request.selected_scope_id and len(candidates) > 1:
        first = candidates[0]
        materially_close = [c for c in candidates if c.score >= max(0.35, first.score - 0.12)]
        has_exact = first.score >= 0.9
        # Exact condition phrase wins; common symptom query may still be ambiguous.
        query_tokens = set(catalog.normalize(request.query).split())
        exact_condition = any(catalog.normalize(c.concept["condition"]) in catalog.normalize(request.query) for c in candidates)
        exact_alias = any(
            catalog.normalize(term) in catalog.normalize(request.query)
            for c in candidates for term in c.concept["terms"] if term != c.concept["condition"]
        )
        if not has_exact and not exact_alias and len(materially_close) > 1:
            options = [
                {"id": c.concept["id"], "condition": c.concept["condition"], "reason": c.reason, "confidence": round(c.score, 3)}
                for c in materially_close[:6]
            ]
            return SearchResponse(query=request.query, intent="clarification", message="I found several possible scopes. Choose one or refine the condition.", scope_options=options)

    if request.selected_scope_id:
        chosen = candidates
    elif len(candidates) > 1 and all(c.score >= 0.9 for c in candidates):
        chosen = candidates
    else:
        chosen = candidates[:1]
    scope_results = []
    for candidate in chosen:
        procedure = candidate.concept["procedure"]
        treatments = []
        for record in catalog.treatments:
            # Keep relation transparent: indicate exact indication match vs semantic candidate.
            indication = catalog.normalize(record.get("condition", ""))
            condition = catalog.normalize(candidate.concept["condition"])
            alias_terms = {catalog.normalize(x) for x in candidate.concept["terms"]}
            direct = indication == condition or indication in alias_terms or any(
                alias in indication.split() if len(alias) <= 3 else alias in indication
                for alias in alias_terms
            )
            if direct:
                treatments.append({
                    **record,
                    "studied_condition": record["condition"],
                    "retrieval_reason": "Treatment indication matches this condition concept.",
                    "similarity": None,
                })
        scope_results.append({
            "scope": {"id": procedure["id"], "condition": procedure["condition"], "reason": candidate.reason, "confidence": round(candidate.score, 3)},
            # The repo's records are explicitly illustrative and lack owner approval metadata.
            # Preserve them for demo review, but never expose them as canonical guidance.
            "standard_procedure": None,
            "illustrative_procedure": _procedure_record(procedure),
            "procedure_status": "No clinically approved standard procedure is available. An illustrative sample record is included for demo review only.",
            "emerging_treatments": treatments,
        })

    data_status = ["Supplied standard-procedure records are illustrative and lack clinical approval metadata; none is presented as approved guidance.",
                   "Seed treatment records have review dates but no separate publication/update-date field.",
                   "Emerging-treatment status may change; verify cited sources and jurisdiction before relying on it."]
    if any(result["scope"]["id"] == "STD-T2D-001" and "subtype is unspecified" in result["scope"]["reason"] for result in scope_results):
        data_status.insert(0, "The query says diabetes without a subtype; type 2 records are shown as a possible interpretation, not an established diagnosis or applicable procedure.")
    if any(result["scope"]["id"] == "STD-ACS-001" for result in scope_results) and re.search(
        r"\b(heart attack|acute coronary|chest pain)\b", request.query, re.I
    ):
        data_status.insert(0, "Possible heart attack or acute coronary symptoms require immediate emergency evaluation; do not delay care to review research information.")
    presentation = get_presenter().organize(request.query, scope_results)
    return SearchResponse(query=request.query, intent="briefing", results=scope_results, presentation=presentation, data_status=data_status)


@app.post("/api/search", response_model=SearchResponse)
def search(request: SearchRequest):
    intent, message = classify(request.query)
    if intent != "briefing":
        return SearchResponse(query=request.query, intent=intent, message=message)
    return _resolve(request)


@app.get("/api/treatments/{treatment_id}", response_model=DetailResponse)
def treatment_detail(treatment_id: str):
    treatment = get_catalog().treatments_by_id.get(treatment_id)
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment record not found")
    record = {
        **treatment,
        "studied_condition": treatment["condition"],
        "retrieval_reason": "Requested by stable treatment record ID.",
        "similarity": None,
    }
    # No approved detail corpus exists yet. Never fabricate a detailed procedure.
    return DetailResponse(
        treatment_id=treatment_id,
        available=False,
        message="No approved detailed treatment record is available. The sourced catalog summary is provided.",
        record=record,
        approved_detail=None,
    )


# The lightweight demo interface is served by the same process as the API.
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="frontend")
