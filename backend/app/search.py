import logging
import re
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold()))


@dataclass
class Candidate:
    concept: dict
    score: float
    reason: str


class SemanticIndex:
    """Local sentence-transformers embeddings with deterministic lexical fallback."""

    def __init__(self, concepts: list[dict], model_name: str):
        self.concepts = concepts
        self.model = None
        self.term_texts = [term for concept in concepts for term in concept["terms"]]
        self.term_owner = [concept for concept in concepts for _ in concept["terms"]]
        self.term_embeddings = None
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name)
            self.term_embeddings = self.model.encode(self.term_texts, normalize_embeddings=True)
            logger.info("Loaded embedding model %s", model_name)
        except Exception as exc:  # model downloads/dependencies may be unavailable in local demo
            logger.warning("Embedding model unavailable; lexical retrieval active: %s", exc)

    def find(self, query: str, top_k: int = 8) -> list[Candidate]:
        norm = " ".join(_tokens(query))
        q_tokens = _tokens(query)
        by_id: dict[str, Candidate] = {}
        for term, concept in zip(self.term_texts, self.term_owner):
            term_norm = " ".join(_tokens(term))
            term_tokens = _tokens(term)
            score, reason = 0.0, ""
            if term_norm and re.search(rf"(?<!\w){re.escape(term_norm)}(?!\w)", query.casefold()):
                score, reason = 1.0, f"Exact condition or alias match: {term}"
            elif term_tokens and term_tokens.issubset(q_tokens):
                score, reason = 0.9, f"Condition/alias terms found: {term}"
            else:
                overlap = len(term_tokens & q_tokens) / max(1, len(term_tokens))
                if overlap >= 0.6:
                    score, reason = 0.45 + overlap * 0.25, f"Lexical concept overlap: {term}"
            if score:
                previous = by_id.get(concept["id"])
                if previous is None or score > previous.score:
                    by_id[concept["id"]] = Candidate(concept, score, reason)

        if self.model is not None and self.term_embeddings is not None:
            query_embedding = self.model.encode([query], normalize_embeddings=True)[0]
            similarities = np.asarray(self.term_embeddings) @ query_embedding
            for index in np.argsort(similarities)[::-1][:top_k * 2]:
                concept = self.term_owner[int(index)]
                score = float(similarities[int(index)])
                if score < 0.24:
                    continue
                current = by_id.get(concept["id"])
                # Strong exact/alias matches always outrank fuzzy semantic candidates.
                if current is None or (current.score < 0.9 and score > current.score):
                    by_id[concept["id"]] = Candidate(
                        concept, score, f"Semantic match to concept term: {self.term_texts[int(index)]}"
                    )
        return sorted(by_id.values(), key=lambda item: item.score, reverse=True)[:top_k]
