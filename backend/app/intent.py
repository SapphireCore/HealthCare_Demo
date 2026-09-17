import re


URGENT = re.compile(r"\b(chest pain right now|right now.{0,30}chest pain|can't breathe|cannot breathe|severe shortness of breath|heart attack.{0,40}(wait|tomorrow))\b", re.I)
PERSONAL = re.compile(r"\b(i personally|for me|should i take|should i use|my treatment|instead of seeing my doctor|recommend (a|an|the)?\s*(drug|treatment|medicine))\b", re.I)
OUT_OF_SCOPE = re.compile(r"\b(kitchen faucet|leaking faucet|weather|sports score|stock price)\b", re.I)
PLACEHOLDER = re.compile(r"\[(condition|organization)\]", re.I)


def classify(query: str) -> tuple[str, str | None]:
    q = query.strip()
    if not q or q.casefold() in {"what is the treatment", "treatment", "help"}:
        return "incomplete", "Which condition, symptom, or treatment would you like to explore?"
    if PLACEHOLDER.search(q):
        return "incomplete", "Please replace the bracketed placeholder with a condition or organization."
    if URGENT.search(q):
        return "urgent", "This assistant cannot assess urgent symptoms. Contact local emergency services now for chest pain or severe breathing difficulty."
    if PERSONAL.search(q):
        return "personalized_request", "I can provide sourced research information, but cannot recommend a treatment for an individual. Please discuss treatment decisions with a qualified clinician."
    if OUT_OF_SCOPE.search(q):
        return "out_of_scope", "This assistant covers condition-focused healthcare strategy briefings. Please enter a medical condition or related symptom."
    return "briefing", None
