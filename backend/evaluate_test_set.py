"""Run the repository's search acceptance queries against the local API."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import settings


def _expected_scopes(case: dict) -> set[str]:
    values = case.get("expected_standard_ids")
    if values is None and case.get("expected_standard_id"):
        values = [case["expected_standard_id"]]
    return set(values or [])


def run() -> int:
    test_set = json.loads(settings.query_test_set_path.read_text(encoding="utf-8-sig"))
    cases = test_set.get("positive", []) + test_set.get("negative", [])
    failures = []
    intents = {}
    with TestClient(app) as client:
        for case in cases:
            response = client.post("/api/search", json={"query": case["query"]})
            if response.status_code != 200:
                failures.append((case["id"], f"HTTP {response.status_code}"))
                continue
            body = response.json()
            intents[body["intent"]] = intents.get(body["intent"], 0) + 1
            wanted_scopes = _expected_scopes(case)
            if wanted_scopes:
                actual_scopes = {
                    row["scope"]["id"] for row in body.get("results", [])
                } | {row["id"] for row in body.get("scope_options", [])}
                if not wanted_scopes.issubset(actual_scopes):
                    failures.append((case["id"], f"scope IDs expected {sorted(wanted_scopes)}, got {sorted(actual_scopes)}"))

            wanted_treatments = set(case.get("expected_emerging_ids", []))
            if wanted_treatments and body["intent"] == "briefing":
                actual_treatments = {
                    record["id"]
                    for row in body.get("results", [])
                    for record in row.get("emerging_treatments", [])
                }
                if not wanted_treatments.issubset(actual_treatments):
                    failures.append((case["id"], f"treatment IDs missing {sorted(wanted_treatments - actual_treatments)}"))

    print(f"Evaluated {len(cases)} queries; intent counts: {intents}")
    if failures:
        print(f"Failures ({len(failures)}):")
        for case_id, message in failures:
            print(f"  {case_id}: {message}")
        return 1
    print("All expected scope and treatment IDs were returned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
