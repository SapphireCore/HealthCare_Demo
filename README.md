# Healthcare Strategy Briefing Assistant

A demo search assistant for a health system strategy team. A user enters a medical condition, symptom, or related phrase and receives a structured briefing with an established treatment overview first, followed by a concise, sourced view of emerging treatments and their associated organizations. Users can request more detail about a listed treatment.

The demo is a research and strategy aid. It is not a diagnostic tool or a source of personalized treatment advice. Emerging treatments must be identified as investigational where applicable, and study results must be represented as reported, including mixed, negative, or unavailable findings.

## How the demo is intended to work

1. The user submits a condition, symptom, or treatment query.
2. Search resolves the query to a supported condition or set of possible conditions. Broad or ambiguous symptom searches (for example, breathlessness) must show possible scopes or ask the user to clarify rather than guess a diagnosis.
3. The assistant retrieves the approved, versioned standard procedure record for the selected scope. It renders the stored text verbatim, so the same applicable record has exactly the same wording on repeated searches.
4. The assistant retrieves related emerging-treatment records and displays a short table with treatment, studied condition, stage/status, reported result, associated organization, and source.
5. A detail request returns an approved stored treatment-detail record verbatim when one exists. Otherwise, the assistant gives the available sourced summary and says that no approved detail record is available.

The canonical procedure store is separate from the emerging-treatment catalog. Experimental findings are not presented as standard care or as a recommendation for an individual.

## Sample datasets and how they were prepared

The current seed data covers 10 condition areas: asthma, COPD, type 2 diabetes, chronic kidney disease, heart failure with reduced ejection fraction, acute coronary syndrome, migraine, rheumatoid arthritis, Alzheimer disease, and Parkinson disease. The selection includes overlapping symptoms and related concepts to exercise semantic retrieval and ambiguity handling.

### Standard treatment procedures

[`demo_std_ptc_data/standard_procedures.json`](demo_std_ptc_data/standard_procedures.json) contains 10 short structured records. Each has a stable ID, condition name, aliases, version, review date, source URL, and fixed text sections. The records were assembled as concise paraphrased overviews from publicly available guidelines and authoritative clinical resources. They are demo seed content, not verbatim guideline protocols and not yet clinically approved canonical procedures.

Sources represented include:

- [GINA asthma strategy reports](https://ginasthma.org/2025-gina-strategy-report/)
- [GOLD COPD reports](https://goldcopd.org/2025-gold-report/)
- [American Diabetes Association Standards of Care](https://diabetesjournals.org/care/issue/48/Supplement_1)
- [KDIGO CKD guideline](https://kdigo.org/guidelines/ckd-evaluation-and-management/)
- [ACC/AHA heart failure guideline resource](https://professional.heart.org/en/science-news/2022-guideline-for-the-management-of-heart-failure)
- [ACC/AHA acute coronary syndrome guideline](https://professional.heart.org/en/guidelines-statements/2025-accahaacepnaemspscai-guideline-for-the-management-of-patients-with-acutecir0000000000001309)
- [NICE headache guideline](https://www.nice.org.uk/guidance/cg150)
- [American College of Rheumatology rheumatoid arthritis guidelines](https://rheumatology.org/clinical-practice-guidelines/rheumatoid-arthritis)
- [National Institute on Aging Alzheimer treatment overview](https://www.nia.nih.gov/health/alzheimers-treatment/how-alzheimers-disease-treated)
- [NICE Parkinson disease guideline](https://www.nice.org.uk/guidance/ng71)

### Emerging treatments

[`demo_emg_trt_data/emerging_treatments.json`](demo_emg_trt_data/emerging_treatments.json) contains 30 short records associated with the same condition areas. Records include the candidate or treatment, mechanism/type, studied condition, development or jurisdiction-specific status, available result summary, associated organization, source URL/type, and review date.

Records were selected from public clinical-trial registries, peer-reviewed publications, regulator resources, guideline updates, and research organization announcements. Each record includes a source link. Some links go directly to a trial or publication; others are registry searches because a candidate can have several studies and its status changes over time. Before a result is used in a live demo, open and check the cited source, confirm the exact studied population and latest trial status, and update the record. The sample intentionally distinguishes a research candidate from an approved treatment; a few recent innovations are included with their approval status called out to exercise that distinction.

The `organization` field names a sponsor, developer, or research organization when identified in the source. It does not necessarily identify every institution or clinical site participating in a trial. For site-level information, inspect a trial registry record's contacts and locations.

### Search and response tests

[`test_set/queries.json`](test_set/queries.json) contains 25 positive queries and 5 negative or out-of-scope queries. Cases cover synonyms, broad symptoms, overlapping conditions, multi-condition requests, exact-text retrieval, urgent symptoms, incomplete requests, and personalized-treatment requests. Positive cases include expected record IDs and behavioral requirements; ambiguous symptom cases should produce scope options or a clarification rather than a diagnosis.

## Proposed front-end and back-end design

The lightweight application is implemented in `backend/` as a FastAPI service with a static HTML/CSS/JavaScript front end served by the same process. The design is consistent with the [development guideline](DEMO_DEVELOPMENT_GUIDELINE.md), [implementation plan](IMPLEMENTATION_PLAN.md), and [architecture diagram](architecture.mmd).

For a presentation-ready view of the end-to-end flow, see the [slide-ready component diagram](architecture.svg). The SVG is a vector graphic and can be inserted into presentation software; [architecture.mmd](architecture.mmd) is the editable Mermaid source.

### Front end

- A conventional web search interface with a query box accepting conditions, symptoms, or treatment names.
- Example queries, clear scope labels, and a concise research-aid notice.
- Explicit states for results, ambiguous scope selection, unsupported input, missing content, and urgent or personalized-care requests.
- A results view in a fixed order: resolved scope, canonical standard procedure, emerging-treatment table, and sources/data status.
- A treatment detail panel or page that displays approved detail text exactly when available.
- A clear path from each result to its source and review date.

### Back end

- A small API/service that validates and classifies a query, resolves supported condition scopes, retrieves records by stable ID, validates applicability/provenance, and returns a structured response for the UI to render.
- Use deterministic alias matching plus local sentence embeddings to find candidate scopes, with a lexical fallback. Ambiguous intent returns scope options; urgent, personal-treatment, incomplete, and out-of-scope requests are handled before retrieval. Any model step helps interpret wording but must not author standard procedures or treatment claims.
- Keep standard procedures, emerging-treatment records, and approved treatment-detail records as separate content types. The current JSON files are seed data; a later implementation can load them into a database without changing their stable IDs or content fields.
- Return canonical text and its version as stored. Keep narrative generation out of the standard-procedure path.
- Return treatment evidence with its studied condition, stage/status, result, organization, source, and review date intact. Flag uncertain, missing, stale, or conflicting data instead of filling gaps.
- Record query and selected record IDs for evaluation, while avoiding unnecessary storage of personal health information.

## Repository contents

| Path | Purpose |
|---|---|
| [`DEMO_DEVELOPMENT_GUIDELINE.md`](DEMO_DEVELOPMENT_GUIDELINE.md) | Client requirements and product behavior rules |
| [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) | Phased application implementation plan |
| [`architecture.mmd`](architecture.mmd) | Initial service and data-flow diagram |
| [`architecture.svg`](architecture.svg) | Slide-ready input-to-output process and component diagram |
| [`backend/`](backend/) | FastAPI retrieval service and browser interface |
| [`demo_std_ptc_data/`](demo_std_ptc_data/) | Canonical-style standard procedure demo records |
| [`demo_emg_trt_data/`](demo_emg_trt_data/) | Emerging treatment demo records |
| [`test_set/`](test_set/) | Positive and negative search test cases |

## Run locally

The demo uses Python, FastAPI, and Uvicorn. From the repository root in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
uvicorn backend.app.main:app --reload
```

Then open `http://127.0.0.1:8000/`. API documentation is at `http://127.0.0.1:8000/docs`; the health check is `http://127.0.0.1:8000/health`.

The first search attempts to load the configured Sentence Transformers model (`sentence-transformers/all-MiniLM-L6-v2` by default), which may download model files. If the dependency or model is unavailable, the backend logs a warning and falls back to deterministic lexical/alias retrieval. The optional LLM presenter can be configured with `LLM_PROVIDER`, `LLM_API_KEY`, and `LLM_MODEL`; no API key is needed for the demo. Canonical procedure text is not sent through the presenter.

The interface supports repeated searches in one conversation, scope selection for ambiguous queries, source links, and expandable treatment details. Selecting a scope reuses the original query and sends the chosen stable record ID to the API.

## Important content limitations

- Sample procedure summaries require review and approval by an appropriate clinical content owner before they are described as established procedures.
- Review dates in the sample identify when these demo records were assembled; they do not guarantee that a source or regulatory status remains current.
- Clinical trial records change. Recheck registry status and published results before each demonstration and establish a content update process for ongoing use.
- The examples are not exhaustive, may not cover all populations or jurisdictions, and must not be used to guide an individual patient's care.
