import os
from pathlib import Path

from dotenv import load_dotenv

# server/ root, computed from this file's own location so behavior never depends on the launch directory.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")
TOP_K = int(os.environ.get("TOP_K", "6"))
MIN_RELEVANCE_SCORE = float(os.environ.get("MIN_RELEVANCE_SCORE", "0.08"))
KNOWLEDGE_DIR = os.environ.get("KNOWLEDGE_DIR", str(BASE_DIR / "knowledge"))
MAX_HISTORY_TURNS = int(os.environ.get("MAX_HISTORY_TURNS", "3"))
REQUEST_TIMEOUT_SECONDS = float(os.environ.get("REQUEST_TIMEOUT_SECONDS", "20"))
LLM_RETRY_DELAY_SECONDS = float(os.environ.get("LLM_RETRY_DELAY_SECONDS", "1.5"))
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "40"))
RATE_LIMIT_WINDOW_SECONDS = float(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "kevintlee01")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_MAX_REPOS = int(os.environ.get("GITHUB_MAX_REPOS", "20"))

REFUSAL_PHRASE = "don't have grounded information"
REFUSAL_MESSAGE = (
    "I don't have grounded information about that in Kevin's resume, "
    "so I won't guess. Feel free to ask about his roles, projects, skills, "
    "education, certifications or awards instead."
)


def contains_refusal_phrase(answer: str) -> bool:
    # A live LLM paraphrases the refusal contraction inconsistently ("don't" vs "do not"), so check both.
    lowered = answer.lower()
    return REFUSAL_PHRASE in lowered or "do not have grounded information" in lowered

PROVIDER_DOWN_MESSAGES = {
    "timeout": "The AI provider timed out. This was retried once automatically and still didn't respond -- please try again in a moment.",
    "rate_limit": "The AI provider's rate limit was hit. This was retried once automatically and still got throttled -- please wait a bit and try again.",
    "connection": "Couldn't reach the AI provider's network. This was retried once automatically and still failed -- please try again in a moment.",
    "server_error": "The AI provider reported an internal error. This was retried once automatically and still failed -- please try again in a moment.",
    "auth": "The AI provider rejected the request (likely an invalid or missing API key). This is a configuration issue, not a transient one -- retrying won't help.",
    "bad_request": "The AI provider rejected the request as malformed. Please try rephrasing your question.",
    "error": "The AI provider is unavailable right now for an unexpected reason. Please try again in a moment.",
}


def provider_down_message(category: str) -> str:
    return PROVIDER_DOWN_MESSAGES.get(category, PROVIDER_DOWN_MESSAGES["error"])

GITHUB_UNAVAILABLE_MESSAGE = (
    "I couldn't reach GitHub's live API just now (network issue or rate limit), and there's nothing about that "
    "in Kevin's resume either, so I won't guess. Please try again in a moment."
)


def active_api_key() -> str:
    if PROVIDER == "anthropic":
        return ANTHROPIC_API_KEY
    if PROVIDER == "gemini":
        return GEMINI_API_KEY
    return OPENAI_API_KEY


KNOWN_PROVIDERS = {"openai", "anthropic", "gemini"}


def startup_warnings() -> list[str]:
    if PROVIDER not in KNOWN_PROVIDERS:
        return [f"LLM_PROVIDER '{PROVIDER}' is not one of {sorted(KNOWN_PROVIDERS)} -- every question will fail."]
    if not active_api_key():
        return [f"No API key is set for the active provider '{PROVIDER}' -- every question will fail until one is set."]
    return []
