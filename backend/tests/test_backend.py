import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import main
from backend.app.search import Candidate


ROOT = Path(__file__).resolve().parents[2]
client = TestClient(main.app)


def test_health_uses_repository_seed_data():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["standard_procedure_records"] == 10
    assert response.json()["emerging_treatment_records"] == 30


def test_canonical_text_is_not_misrepresented_as_approved(monkeypatch):
    catalog = main.get_catalog()
    concept = next(item for item in catalog.concepts() if item["id"] == "STD-RA-001")

    class Index:
        def find(self, _query):
            return [Candidate(concept, 1.0, "Exact condition match: rheumatoid arthritis")]

    monkeypatch.setattr(main, "get_index", lambda: Index())
    monkeypatch.setattr(main, "get_presenter", lambda: main.Presenter("", "", "", ""))
    response = client.post("/api/search", json={"query": "Rheumatoid arthritis standard care and emerging drugs?"})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "briefing"
    result = body["results"][0]
    assert result["standard_procedure"] is None
    assert result["illustrative_procedure"]["approval_status"] == "illustrative_unapproved"

    source = json.loads((ROOT / "demo_std_ptc_data/standard_procedures.json").read_text(encoding="utf-8-sig"))
    expected = next(item for item in source if item["id"] == result["illustrative_procedure"]["id"])
    assert result["illustrative_procedure"]["sections"] == expected["sections"]
    assert {item["id"] for item in result["emerging_treatments"]} == {
        "EMG-RA-001", "EMG-RA-002", "EMG-RA-003"
    }


def test_urgent_and_personalized_intents_do_not_run_search():
    urgent = client.post("/api/search", json={"query": "I have chest pain right now; diagnose me"}).json()
    personal = client.post("/api/search", json={"query": "Which experimental drug should I personally take?"}).json()
    assert urgent["intent"] == "urgent"
    assert personal["intent"] == "personalized_request"
    assert urgent["results"] == []
    assert personal["results"] == []


def test_treatment_detail_discloses_missing_approved_detail():
    response = client.get("/api/treatments/EMG-ALZ-001")
    assert response.status_code == 200
    assert response.json()["available"] is False
    assert response.json()["approved_detail"] is None
    assert response.json()["record"]["id"] == "EMG-ALZ-001"
