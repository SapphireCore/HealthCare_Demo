# Search assistant test set

`queries.json` contains 25 positive queries and 5 negative/out-of-scope queries. Positive cases cover condition synonyms, broad inputs, ambiguous symptoms, overlapping conditions, multi-condition requests, and exact-text retrieval. Each positive case lists expected standard-procedure and emerging-treatment record IDs or an expected ambiguity behavior. Negative cases cover irrelevant, personalized/inappropriate, incomplete, urgent, and placeholder input.

For ambiguous symptoms, acceptance means the assistant asks for clarification or displays separate possible scopes; it must not infer a diagnosis. The expected emerging IDs are retrieval examples, not clinical endorsements.
