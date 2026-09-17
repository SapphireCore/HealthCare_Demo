import json
import re
from pathlib import Path


class Catalog:
    def __init__(self, standard_path: Path, emerging_path: Path):
        self.procedures = json.loads(standard_path.read_text(encoding="utf-8-sig"))
        self.treatments = json.loads(emerging_path.read_text(encoding="utf-8-sig"))
        self._validate()
        self.by_id = {item["id"]: item for item in self.procedures}
        self.treatments_by_id = {item["id"]: item for item in self.treatments}

    def _validate(self):
        if len({p.get("id") for p in self.procedures}) != len(self.procedures):
            raise ValueError("Duplicate standard-procedure IDs")
        if len({t.get("id") for t in self.treatments}) != len(self.treatments):
            raise ValueError("Duplicate emerging-treatment IDs")
        for p in self.procedures:
            for field in ("id", "condition", "version", "review_date", "source", "sections"):
                if not p.get(field):
                    raise ValueError(f"Procedure {p.get('id')} is missing {field}")
        for t in self.treatments:
            for field in ("id", "condition", "treatment", "stage", "result", "organization", "source"):
                if not t.get(field):
                    raise ValueError(f"Treatment {t.get('id')} is missing {field}")

    @staticmethod
    def normalize(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()

    def concepts(self):
        result = []
        for procedure in self.procedures:
            terms = [procedure["condition"], *procedure.get("aliases", [])]
            # Include explicitly stated abbreviations such as COPD, CKD, HFrEF, and RA.
            terms += re.findall(r"\(([^()]+)\)", procedure["condition"])
            if procedure["id"] == "STD-CKD-001":
                terms.append("kidney disease")
            if procedure["id"] == "STD-T2D-001":
                # Search can surface the type 2 sample for broad diabetes queries,
                # but the response must disclose that subtype was not specified.
                terms.append("diabetes")
            if procedure["id"] == "STD-ACS-001":
                terms.append("atherosclerotic cardiovascular disease")
            # Treatment indications add searchable aliases without replacing source terms.
            terms += [
                t["condition"] for t in self.treatments
                if t["condition"].casefold() in procedure["condition"].casefold()
                or procedure["condition"].casefold() in t["condition"].casefold()
            ]
            result.append({"id": procedure["id"], "condition": procedure["condition"],
                           "terms": sorted(set(terms)), "procedure": procedure})
        return result
