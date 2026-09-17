import json
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You organize already-retrieved healthcare research records for a strategy briefing.
Return valid JSON with keys: scope_summary (string), emerging_intro (string), data_status (array of strings).
Use only supplied records. Do not add medical claims, recommendations, efficacy conclusions, or inferred approval.
Preserve uncertainty and clearly call records investigational when appropriate. Do not reproduce or rewrite
standard procedure text: the application injects canonical procedure text separately and verbatim.
If the records do not support a conclusion, say so. Keep the response concise."""


class Presenter:
    def __init__(self, provider: str, api_key: str, base_url: str, model: str):
        self.enabled = bool(provider and api_key and model)
        self.client = None
        self.model = model
        if self.enabled:
            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self.client = OpenAI(**kwargs)

    def organize(self, query: str, results: list[dict]) -> dict:
        fallback = {
            "scope_summary": "; ".join(r["scope"]["condition"] for r in results),
            "emerging_intro": "Emerging-treatment records below reflect the cited sources and review dates; they are not treatment recommendations.",
            "data_status": [],
        }
        if not self.enabled or not results:
            return fallback
        try:
            source_bundle = [{
                "scope": row["scope"]["condition"],
                "procedure_available": row["standard_procedure"] is not None,
                "treatments": [{k: t.get(k) for k in ("id", "treatment", "studied_condition", "stage", "result", "organization", "source", "review_date")} for t in row["emerging_treatments"]],
            } for row in results]
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps({"query": query, "records": source_bundle})},
                ],
            )
            parsed = json.loads(response.choices[0].message.content or "{}")
            return {**fallback, **parsed}
        except Exception as exc:
            logger.exception("LLM presentation failed; using deterministic response: %s", exc)
            return fallback
