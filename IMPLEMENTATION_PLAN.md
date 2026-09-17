# Healthcare Strategy Briefing Assistant — Revised Implementation Plan

## Recommendation: build a conventional web app, not a ReAct agent

The intended interaction is a structured search and review workflow: enter a condition or symptom, resolve scope if needed, inspect the stored standard procedure and sourced treatment records, then optionally open a treatment detail. A conventional web app with explicit states is the best fit. “ReAct” usually refers to an agent pattern (reasoning and acting in a loop), rather than a frontend framework. An agent loop would add uncertainty and make the response harder to keep deterministic, while this demo needs exact stored content, explicit provenance, and clear ambiguity handling.

Use a normal browser frontend backed by a small API/service. The service should classify intent, resolve query scope, and select record IDs; the UI should render those records. Use hybrid exact/alias and embedding search to find candidate concepts. An LLM presentation call can organize the retrieved, sourced records, but must not author canonical procedure content or add treatment claims. Keep deterministic fallback behavior when model configuration is unavailable.

## What is already in the repository

- `DEMO_DEVELOPMENT_GUIDELINE.md`: required response order, exact-text requirements, provenance rules, ambiguity behavior, and acceptance criteria.
- `demo_std_ptc_data/standard_procedures.json`: 10 versioned illustrative standard procedure records, each with a stable ID, condition, aliases, structured sections, source, and review date.
- `demo_emg_trt_data/emerging_treatments.json`: 30 emerging-treatment records across the same 10 condition areas, including stage/status, reported result, organization, source type/URL, and review date.
- `test_set/queries.json`: 25 positive and 5 negative/out-of-scope queries with expected IDs and behavior, including ambiguous, multi-condition, exact-text, urgent, and personal-treatment cases.
- `architecture.mmd`: initial architecture diagram.
- `backend/`: initial FastAPI backend with intent classification, semantic/lexical concept retrieval, optional LLM presentation, search/detail endpoints, and focused tests. Python dependencies are not installed in the current environment, so this slice still needs execution and test validation.
- `README.md`: dataset context, intended interaction, limitations, and backend setup links.

These files are demo seed/evaluation artifacts, not a production-ready clinical knowledge base. The sample content itself says clinical review and live status revalidation are needed before real use. Preserve the artifacts and build around them; do not silently treat their illustrative records as approved clinical guidance.

## Intended user interaction

1. **Landing/search:** The user sees a clear research-aid purpose statement and one prominent query box: “Enter a condition, symptom, or treatment.” Offer a few example searches drawn from the test set.
2. **Submit:** The web client sends the query to the API. The API validates empty/placeholder input and classifies out-of-scope, personal-care, and urgent requests before normal retrieval.
3. **Resolve scope:** For one unambiguous condition, show the resolved scope and the terms that matched (for example, “emphysema → COPD”). For ambiguous symptoms such as breathlessness, show selectable possible scopes and ask the user to choose. For a multi-condition query, show separate scopes/results rather than merging them.
4. **Review results:** Render sections in the mandated order: visible scope; exact stored standard-procedure text; emerging-treatment table; sources and last-reviewed/data-status details. Make the studied condition on each treatment row visible even when it differs from the query scope.
5. **Inspect a treatment:** Selecting a treatment opens an inline detail panel or detail view with available sourced information. Return approved detail content verbatim when present; otherwise say that no approved detail record is available and show the sourced summary.
6. **Refine or repeat:** Keep the query and selected scope visible so the user can refine the query, switch interpretations, or start a new search. Do not imply that displayed treatments are recommendations.

## Implementation tasks

### Phase 1 — Establish the demo contract and frontend flow

- [ ] Agree target users, initial demo scope, geography, and intended use. Use the 10 condition areas in the supplied data as the proposed starting set, subject to stakeholder confirmation.
- [ ] Select a straightforward web stack that is easy to run locally and deploy for a demo; record the choice in `README.md`. Prefer a conventional frontend plus API over an autonomous agent framework.
- [ ] Define API request/response shapes for search, scope selection, and treatment-detail lookup, including record IDs, versions, match rationale, and data-status flags.
- [ ] Define user-facing copy for research-aid limitations, ambiguity, unsupported queries, missing procedures, stale/conflicting sources, urgent symptoms, and personalized treatment requests.
- [ ] Map all 30 test queries to expected UI states and results before implementation; clarify whether the UI supports multiple scopes in one result page.
- [ ] Sketch or implement the core screens/states: landing/search, clarification choices, results, treatment detail, empty/out-of-scope response, and urgent/personalized request handling.

### Phase 2 — Validate and normalize the existing data

- [ ] Inspect both JSON datasets and `test_set/queries.json` with automated parsing; preserve original files as source artifacts.
- [ ] Add schemas and validation for required fields, unique IDs, versions, aliases, section ordering, source values, review dates, treatment status, organization, and result wording.
- [ ] Normalize inconsistent fields and condition names through a migration/adapter layer without losing the original source wording or identifiers.
- [ ] Add explicit approval state and applicability fields for canonical procedures (population, subtype, setting, geography); mark supplied illustrative records unapproved until reviewed.
- [ ] Add a structured distinction between investigational status, approved status by jurisdiction, study status, and evidence/result status. Avoid inferring one from another.
- [ ] Validate links and identify registry-search URLs that require a precise study identifier or live verification before display.
- [ ] Add treatment-detail schema/seed records only where an approved detail exists; otherwise represent detail availability explicitly.
- [ ] Create a condition concept/alias mapping from standard-procedure aliases, treatment indications, and test-set vocabulary. Record ambiguity and mapping rationale.
- [ ] Document data limitations and ownership/update responsibilities in the relevant dataset READMEs.

### Phase 3 — Build the retrieval service

- [ ] Implement query validation and handling for empty, placeholder, out-of-scope, urgent, and personal-treatment prompts using the negative test cases.
- [ ] Implement exact condition and alias matching with a normalized lexical fallback; preserve the original query text.
- [ ] Implement scope resolution for single-condition, broad/ambiguous, and multi-condition queries. Never infer a diagnosis from symptoms alone.
- [ ] Return candidate scopes with matching term and rationale when clarification is needed; support a second request carrying the user’s selected scope.
- [ ] Retrieve canonical procedure by stable ID and applicable version only when approval and applicability allow it; otherwise report unavailable.
- [ ] Retrieve emerging records by their stored indication and related concept mapping; retain exact studied condition, stable ID, source, organization, status, result, and review date.
- [ ] Implement deterministic ordering and filtering so expected IDs in `test_set/queries.json` are reproducible.
- [ ] Implement detail lookup by treatment record ID; return exact approved detail or a clear unavailable result.
- [ ] Add freshness/conflict checks and response metadata for stale records, uncertain statuses, and unavailable sources.
- [ ] Build an embedding index over condition concepts, aliases, synonyms, and related terminology; retain model/version and matched concept rationale.
- [ ] Combine embedding candidates with exact aliases and lexical matching; exact known matches must take precedence over fuzzy candidates.
- [ ] Add an optional constrained LLM presentation call that only receives retrieved records, returns a validated structured response, and cannot rewrite canonical procedure text or add unsupported claims.
- [ ] Keep a deterministic response path when embedding weights or LLM configuration are unavailable; report the fallback status.

### Phase 4 — Build the web interface and connect it to the service

- [ ] Implement the landing page with purpose statement, search field, submit action, and example queries.
- [ ] Implement loading, empty, error, and retry states.
- [ ] Implement clarification UI with scope candidates and explicit selection; preserve query text across selection.
- [ ] Implement a results layout following the required order: scope, canonical procedure, emerging-treatment table, sources/data status.
- [ ] Render canonical sections in stored order and exact wording; do not route them through generated prose.
- [ ] Render treatment rows with treatment, studied condition/symptom, stage/status, reported result, organization, and source/date. Make uncertainty and jurisdiction-specific approval clear.
- [ ] Make source links and review dates accessible beside the claims they support.
- [ ] Implement treatment selection and the approved-detail panel/view.
- [ ] Implement separate result groupings for multi-condition queries and display each scope’s own procedure and matching treatment records.
- [ ] Implement safe, direct responses for urgent and personalized-treatment queries according to the test set.
- [ ] Add visible research/strategy-aid framing and ensure the page does not look like a patient-specific recommendation tool.
- [ ] Check keyboard use, readable table layout, small-screen behavior, and basic accessibility.

### Phase 5 — Content governance and traceability

- [ ] Assign a clinical content owner to review/approve canonical procedure wording and applicability before the demo presents it as established standard procedure.
- [ ] Assign a research/content owner to verify emerging-treatment claims and status against their cited sources, especially time-sensitive registry records.
- [ ] Define review cadence, correction process, version promotion, retirement, and stale-data thresholds.
- [ ] Log query ID, selected scope, returned record IDs/versions, match rationale, and data-status checks without storing unnecessary personal health information.
- [ ] Provide a source/record trace path from each result row back to the stored record and cited source.
- [ ] Document local data refresh/import steps and keep an audit history for content changes.

### Phase 6 — Verify the end-to-end experience

- [ ] Run all 30 supplied queries through the API and browser UI; assert expected record IDs and expected behavior.
- [ ] Verify identical applicable searches render byte-for-byte identical canonical procedure wording and section order.
- [ ] Verify ambiguous queries (especially Q21, Q22, Q25) ask for scope selection or present clearly separated interpretations.
- [ ] Verify multi-condition query Q23 returns separate canonical records and the expected relevant emerging records.
- [ ] Verify source, organization, studied indication, stage/status, result, and review date are preserved from each selected treatment record.
- [ ] Verify negative cases do not return invented procedures, diagnoses, or personalized treatment recommendations; Q29 clearly routes urgent chest pain to immediate local emergency services.
- [ ] Verify unavailable detail, stale content, conflicting status, source/link failure, and no-result states are honest and visible.
- [ ] Conduct a stakeholder walkthrough using the test set, fix issues, and record known limitations and data review dates.
- [ ] Add run/deploy instructions and demo operation notes to `README.md`.

## Proposed build order

1. Confirm the 10-condition demo scope and choose the frontend stack.
2. Validate the backend locally, run focused tests, and evaluate the API against all 30 supplied queries.
3. Validate the existing content artifacts and get the approval/status model in place.
4. Build the webpage states around the API contract and connect the treatment-detail action.
5. Run the full test set end-to-end and have stakeholders review the output.
6. Tune semantic retrieval and constrained LLM presentation against the test set; keep final record selection and canonical text rendering deterministic.

## Definition of done for the first demo

- A user can search in a webpage, understand or choose the resolved scope, view results in the required order, and open a treatment detail.
- The supplied test set runs with expected behaviors and record IDs.
- Canonical procedure content is returned exactly from a reviewed, applicable, versioned record or is explicitly unavailable.
- Emerging-treatment information is traceable to records and sources and clearly distinguishes study scope, status, and results.
- Ambiguous, multi-condition, urgent, personalized, and unsupported queries are handled explicitly.
- The demo startup, data update, limitations, and content review dates are documented.
