# Healthcare Strategy Briefing Demo

FastAPI service for intent classification, scope resolution, semantic retrieval, and provenance-preserving response assembly. It also serves the lightweight browser interface from `backend/app/static/`.

## Local setup

Requires Python 3.10 or newer. From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
uvicorn backend.app.main:app --reload
```

The local sentence-transformers model is loaded on first search and may need to download weights. If its dependency or weights are unavailable, the service logs a warning and falls back to lexical/alias retrieval. Edit `backend/.env` to configure the optional LLM; keep API keys out of source control.

Open the demo at `http://127.0.0.1:8000/`. OpenAPI docs are served at `http://127.0.0.1:8000/docs`. Main endpoints:

- `GET /health`
- `POST /api/search` with `{ "query": "...", "selected_scope_id": "..." }`
- `GET /api/treatments/{treatment_id}`

Optional LLM presentation requires `LLM_PROVIDER`, `LLM_API_KEY`, and `LLM_MODEL` environment variables; `LLM_BASE_URL` may point at an OpenAI-compatible endpoint. Do not commit API keys. If the LLM is not configured or a call fails, the API returns deterministic presentation text. The LLM receives retrieved source records only; canonical procedure content is kept outside the generated presentation path.

## Content boundary

The supplied standard-procedure data is explicitly described as illustrative and not clinically approved. It has no approval metadata. The backend therefore returns no approved `standard_procedure`; it exposes a matching record only as `illustrative_procedure`, labeled `illustrative_unapproved`. Do not change this until an authorized clinical content owner approves applicable, versioned records.

No approved detailed-treatment corpus currently exists. Detail lookup returns the sourced catalog summary and explicitly reports that approved detail is unavailable.

## Test

```powershell
python -m pytest backend\tests -q
python -m backend.evaluate_test_set
```

The evaluation command runs all 30 cases through the API and checks expected scope/treatment IDs. The first run downloads the configured embedding model; subsequent runs can use its local cache. Extend intent/safety assertions as retrieval behavior evolves.
