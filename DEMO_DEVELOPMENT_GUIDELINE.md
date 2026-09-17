# Healthcare Strategy Briefing Assistant — Development Guideline

## 1. Purpose

Build a search-based assistant for a health system strategy team. The assistant helps users explore a medical condition by presenting:

1. An established standard procedure for treatment.
2. A concise view of emerging or experimental treatments and the institutes or organizations associated with them.
3. Further details on a selected emerging treatment when requested.

The demo is a research and strategy aid. It must label experimental evidence clearly and must not present experimental treatments as established clinical recommendations.

## 2. User input and search

- Users enter a medical condition or a related query.
- Inputs may be broad or ambiguous (for example, a disease family, symptom, or condition with multiple subtypes), not only a specific diagnosis.
- Search should prioritize semantic matching so that related terminology, symptoms, and disease concepts can be found even when the wording differs.
- The assistant should identify the likely scope of a broad query and make the scope visible in its response. If materially different interpretations would produce different results, ask a concise clarifying question or present the likely interpretations for selection.
- Search results should preserve the distinction between the condition requested, related symptoms or conditions, and the condition actually studied in a treatment record.

## 3. Standard procedure

- Present the established standard procedure first, before emerging treatments.
- The standard procedure must be organized into a fixed, structured text format with consistent titles and sections.
- For the same condition and same applicable version of the procedure, return exactly the same wording and organization. Do not paraphrase or regenerate this section on each request.
- Store or retrieve standard procedure content as an approved, versioned canonical record. Do not create it dynamically from the emerging-treatment database.
- A clinical content owner should define and approve canonical procedures and their applicability (such as condition subtype, population, or care setting). Each record should include its source, review date, and version.
- If the user’s broad query does not map unambiguously to one canonical procedure, explain the ambiguity and ask for clarification or show the available scopes. Do not silently substitute a different procedure.
- If no approved procedure is available, state that it is unavailable rather than generating one as though it were established.

## 4. Emerging-treatment information

Emerging treatments may be selected from a searchable database containing records for diseases and symptoms, experimental treatments, reported results, and associated institutes or organizations.

Each treatment record should support, where available:

- Treatment name and mechanism or type.
- Studied disease, subtype, symptom, or population.
- Development stage and study status.
- Reported results, including the source and relevant date.
- Associated company, institute, research group, or other organization.
- Evidence source identifiers or links, and the date the record was last reviewed.

Show emerging treatments in a brief table. Clearly label their development stage and evidence status. The client’s assumption that stored results may be effective is a data assumption, not a claim the assistant should make: report results as recorded and sourced, including negative, mixed, or unknown results when present. Do not imply that a treatment is approved, effective, or suitable for a patient unless the cited evidence supports that statement.

## 5. Output behavior

The response should follow this order:

1. **Scope** — the condition or interpretation used for the search, with ambiguity noted where relevant.
2. **Standard procedure** — the canonical structured text, reproduced exactly from its approved record.
3. **Emerging treatments** — a concise table. Suggested columns: treatment, condition or symptom studied, stage/status, reported result, associated organization, and source/date.
4. **Sources and data status** — provide source links or identifiers and indicate when records were last reviewed.

When a user asks for details about an emerging treatment, return the exact approved detailed procedure or content record for that treatment, using the same no-paraphrase rule as the standard procedure. If no such approved detail record exists, say so and offer the available sourced summary; do not invent a procedure.

## 6. Data and content management

- Keep canonical standard procedures separate from emerging-treatment records.
- Give canonical procedure and detailed treatment records stable IDs and version numbers so identical applicable requests resolve to identical text.
- Preserve provenance for every factual treatment claim: source, publication or update date, and record review date.
- Support synonyms and condition relationships for semantic search, while retaining the original terms and exact match rationale for review.
- Make missing, stale, conflicting, or uncertain information visible rather than silently filling gaps.
- Define a clinical review and update process before presenting content as an established standard procedure.

## 7. Initial implementation sequence

1. Agree on the first conditions, intended users, care settings, and geographic scope.
2. Define the canonical standard-procedure template and obtain clinically approved records for the initial conditions.
3. Define the emerging-treatment data schema, provenance requirements, and the meaning of development stages and results.
4. Build semantic search across condition, symptom, treatment, and organization fields, with clear scope handling for broad queries.
5. Implement deterministic retrieval and rendering of canonical records, plus a concise sourced table for emerging treatments.
6. Add a detail lookup that returns the exact approved treatment record when requested.
7. Review representative outputs with clinical and strategy stakeholders, focusing on correct scope, exact-text consistency, source traceability, and clear experimental labeling.

## 8. Demo acceptance criteria

- A specific condition returns its approved standard procedure before the emerging-treatment table.
- Repeating the same applicable query returns byte-for-byte identical standard-procedure wording and section order.
- Broad or ambiguous input is handled transparently and does not silently select an unsupported interpretation.
- Emerging-treatment entries can be traced to stored records and sources, with associated organizations shown when available.
- Stored results are represented faithfully and are not automatically described as effective.
- A request for treatment details returns the exact approved detailed record, or clearly states that no such record is available.
- Missing or outdated content is disclosed rather than generated as fact.
