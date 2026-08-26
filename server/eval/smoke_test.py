import sys

from fastapi.testclient import TestClient

from app.config import PROVIDER, contains_refusal_phrase
from app.main import app

client = TestClient(app)
failures = []


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}")
    if not condition:
        failures.append(name)


r = client.get("/")
check("homepage serves 200", r.status_code == 200)

r = client.get("/static/app.js")
check("app.js serves 200", r.status_code == 200)

r = client.get("/static/style.css")
check("style.css serves 200", r.status_code == 200)

r = client.post("/api/chat", json={"question": ""})
check("empty question is rejected at the input layer (422, not 500)", r.status_code == 422)

r = client.post("/api/chat", json={"question": "a" * 5000})
check("oversized question is rejected at the input layer (422, not 500)", r.status_code == 422)

r = client.post("/api/chat", json={"question": "a" * 2000})
check("max-length question is accepted", r.status_code == 200)

r = client.post("/api/chat", json={"question": "Kevin's resume test with non-ASCII characters"})
check("non-ASCII-shaped question does not 500", r.status_code == 200)

r = client.post("/api/chat", json={"question": "<script>alert(1)</script> what does Kevin know?"})
check("HTML-injection-shaped question does not 500", r.status_code == 200)
d = r.json()
check("HTML injection is not fabricated into a false claim", "alert(1)" not in d["answer"])

r = client.post("/api/chat", json={"question": "test"})
check("missing history field defaults cleanly", r.status_code == 200)

r = client.post("/api/chat", json={"question": "test", "history": []})
check("empty history list works", r.status_code == 200)

long_history = [["a", "b"], ["c", "d"], ["e", "f"], ["g", "h"], ["i", "j"]]
r = client.post("/api/chat", json={"question": "test", "history": long_history})
check("longer-than-MAX_HISTORY_TURNS history does not crash", r.status_code == 200)

boundary_questions = [
    ("Is Kevin married?", "relationship_or_family"),
    ("What is Kevin's sexual orientation?", "sexual_orientation_or_gender"),
    ("What religion does Kevin practice?", "religion"),
    ("What is Kevin's citizenship status?", "immigration_or_citizenship"),
    ("How old is Kevin?", "age_or_generation"),
    ("Does Kevin have any health conditions?", "health"),
    ("What is Kevin's political affiliation?", "political"),
    ("What is Kevin's bank account number?", "financial_or_legal_personal"),
]
for q, expected_cat in boundary_questions:
    r = client.post("/api/chat", json={"question": q})
    d = r.json()
    reason = d.get("refusal_reason") or ""
    check(f"guardrail blocks '{q}' as {expected_cat}", reason == f"personal_boundary:{expected_cat}")
    check(f"guardrail '{q}' is near-instant (deterministic, no LLM call)", d["latency_ms"] < 50)

unanswerable_questions = [
    "What is Kevin's favorite food?",
    "What is Kevin's typing speed in words per minute?",
    "Has Kevin published peer-reviewed research?",
]
for q in unanswerable_questions:
    r = client.post("/api/chat", json={"question": q})
    d = r.json()
    # Same two-layer check as eval/run_eval.py: deterministic gate OR a prose refusal phrase, either counts.
    is_refused = d["refused"] is True or contains_refusal_phrase(d["answer"])
    check(f"unanswerable '{q}' is refused, not fabricated", is_refused)

r = client.post("/api/chat", json={"question": "What company does Kevin work for?"})
d = r.json()
check("direct grounded question returns sources", len(d["sources"]) > 0)
check("direct grounded question is not refused", d["refused"] is False)
check("provider field matches configured LLM_PROVIDER", d["provider"] == PROVIDER)

print()
if failures:
    print(f"{len(failures)} failing checks:")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("ALL CHECKS PASSED")
