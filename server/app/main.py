import logging
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import config
from app.config import (
    GITHUB_UNAVAILABLE_MESSAGE,
    MAX_HISTORY_TURNS,
    MIN_RELEVANCE_SCORE,
    PROVIDER,
    REFUSAL_MESSAGE,
    TOP_K,
    provider_down_message,
)
from app.github_live import GitHubFetchError, fetch_github_excerpts
from app.guardrails import (
    GIBBERISH_MESSAGE,
    IDENTITY_MESSAGE,
    PERSONAL_BOUNDARY_MESSAGE,
    PROFANITY_MESSAGE,
    detect_personal_boundary,
    is_gibberish,
    is_github_question,
    is_identity_question,
    is_profane,
)
from app.knowledge import build_index, rank_texts_by_query
from app.llm import LLMError, generate_answer
from app.pricing import estimate_cost
from app.rate_limit import RateLimitExceeded, check_rate_limit

logger = logging.getLogger("askkevin")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AskKevin — Grounded Career Assistant")
# static/ is a sibling of server/, so this works regardless of the launch directory.
STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
index = build_index()
logger.info("Knowledge index built with %d chunks.", len(index.chunks))
for warning in config.startup_warnings():
    logger.warning(warning)


class ChatRequest(BaseModel):
    # Bounds prevent an abusive client from forcing the server to vectorize/prompt on unbounded input.
    question: str = Field(min_length=1, max_length=2000)
    history: list[list[str]] = Field(default_factory=list, max_length=50)


class Source(BaseModel):
    source: str
    section: str
    excerpt: str
    score: float


class TokenUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cached_tokens: int | None = None
    model: str | None = None
    estimated_cost_usd: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    refused: bool
    refusal_reason: str | None
    provider: str
    latency_ms: int
    token_usage: TokenUsage | None = None


def retrieval_query(request: "ChatRequest") -> str:
    recent_history = request.history[-MAX_HISTORY_TURNS:]
    context_parts = [f"{turn_question} {turn_answer}" for turn_question, turn_answer in recent_history]
    context_parts.append(request.question)
    return " ".join(context_parts)


def _refusal_response(started: float, answer: str, reason: str) -> ChatResponse:
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return ChatResponse(
        answer=answer, sources=[], refused=True, refusal_reason=reason, provider=PROVIDER, latency_ms=elapsed_ms
    )


def _github_sources(request: "ChatRequest") -> list[Source]:
    live_sources: list[Source] = []
    try:
        fetched = list(fetch_github_excerpts())
        # Rank fetched repos against the actual question so the "Sources" panel reflects what informed the answer, not the entire public repo list.
        excerpts = [excerpt for _, excerpt in fetched]
        ranked = rank_texts_by_query(request.question, excerpts, MIN_RELEVANCE_SCORE, top_k=TOP_K)
        for i, score in ranked:
            section, excerpt = fetched[i]
            live_sources.append(
                Source(source="github.com (live)", section=section, excerpt=excerpt, score=round(score, 3))
            )
    except GitHubFetchError as error:
        logger.warning("Live GitHub fetch failed, falling back to local resume matches: %s", error)

    ranked = index.search(retrieval_query(request), top_k=TOP_K, intent_query=request.question)
    local_sources = [
        Source(source=chunk.source, section=chunk.section, excerpt=chunk.text, score=round(float(score), 3))
        for chunk, score in ranked
        if score >= MIN_RELEVANCE_SCORE
    ]
    return live_sources + local_sources


def _answer_from_sources(request: "ChatRequest", sources: list[Source], started: float) -> ChatResponse:
    token_usage = None
    try:
        history = [(pair[0], pair[1]) for pair in request.history[-MAX_HISTORY_TURNS:]]
        result = generate_answer(request.question, [s.excerpt for s in sources], history)
        answer = result.text
        token_usage = TokenUsage(
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            cached_tokens=result.cached_tokens,
            model=result.model,
            estimated_cost_usd=estimate_cost(
                result.model, result.prompt_tokens, result.completion_tokens, result.cached_tokens
            ),
        )
        refused = False
        refusal_reason = None
    except LLMError as error:
        logger.warning("LLM provider '%s' call failed (%s): %s", PROVIDER, error.category, error)
        answer = provider_down_message(error.category)
        sources = []
        refused = True
        refusal_reason = f"provider_unavailable:{error.category}"

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return ChatResponse(
        answer=answer,
        sources=sources,
        refused=refused,
        refusal_reason=refusal_reason,
        provider=PROVIDER,
        latency_ms=elapsed_ms,
        token_usage=token_usage,
    )


@app.get("/")
def serve_ui():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request):
    try:
        check_rate_limit(http_request.client.host if http_request.client else "unknown")
    except RateLimitExceeded:
        raise HTTPException(
            status_code=429, detail="Too many requests, please slow down and try again shortly."
        ) from None

    started = time.perf_counter()

    if is_profane(request.question):
        logger.info("Question refused: profanity")
        return _refusal_response(started, PROFANITY_MESSAGE, "profanity")

    if is_gibberish(request.question, index.known_stems):
        logger.info("Question refused: gibberish")
        return _refusal_response(started, GIBBERISH_MESSAGE, "gibberish")

    boundary_category = detect_personal_boundary(request.question)
    if boundary_category is not None:
        logger.info("Question refused: personal_boundary:%s", boundary_category)
        return _refusal_response(started, PERSONAL_BOUNDARY_MESSAGE, f"personal_boundary:{boundary_category}")

    if is_identity_question(request.question):
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return ChatResponse(
            answer=IDENTITY_MESSAGE,
            sources=[],
            refused=False,
            refusal_reason=None,
            provider=PROVIDER,
            latency_ms=elapsed_ms,
        )

    if is_github_question(request.question):
        sources = _github_sources(request)
        if not sources:
            logger.info("Question refused: github_unavailable")
            return _refusal_response(started, GITHUB_UNAVAILABLE_MESSAGE, "github_unavailable")
        return _answer_from_sources(request, sources, started)

    ranked = index.search(retrieval_query(request), top_k=TOP_K, intent_query=request.question)
    top_score = ranked[0][1] if ranked else 0.0

    if top_score < MIN_RELEVANCE_SCORE:
        logger.info("Question refused: not_grounded (top_score=%.3f)", top_score)
        return _refusal_response(started, REFUSAL_MESSAGE, "not_grounded")

    sources = [
        Source(source=chunk.source, section=chunk.section, excerpt=chunk.text, score=round(float(score), 3))
        for chunk, score in ranked
    ]
    return _answer_from_sources(request, sources, started)
