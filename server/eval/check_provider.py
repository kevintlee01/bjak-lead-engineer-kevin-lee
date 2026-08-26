import sys

from app.config import PROVIDER, active_api_key, startup_warnings
from app.llm import LLMError, generate_answer

print(f"Checking LLM_PROVIDER='{PROVIDER}' ...")

warnings = startup_warnings()
if warnings:
    for warning in warnings:
        print(f"[FAIL] {warning}")
    sys.exit(1)

if not active_api_key():
    print(f"[FAIL] No API key found for provider '{PROVIDER}'. Set it in your .env and try again.")
    sys.exit(1)

try:
    answer = generate_answer(
        question="What is Kevin's job?",
        excerpts=["Kevin is a Senior Software Engineer at Walmart."],
        history=[],
    )
except LLMError as error:
    print(f"[FAIL] Real API call to '{PROVIDER}' failed: {error}")
    print("Common causes: invalid API key, no network access to the provider's domain, expired/renamed model name.")
    sys.exit(1)

print(f"[PASS] '{PROVIDER}' responded: {answer.text[:120]!r}")
if answer.total_tokens is not None:
    print(f"Token usage: {answer.prompt_tokens} prompt + {answer.completion_tokens} completion = {answer.total_tokens} total")
print("Your API key and network access are both working end to end.")
