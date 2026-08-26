import app.main as main_module
from app.github_live import GitHubFetchError
from app.llm import LLMError, LLMResult


def test_homepage_serves_html():
    from fastapi.testclient import TestClient

    client = TestClient(main_module.app)
    response = client.get("/")
    assert response.status_code == 200
    assert b"AskKevin" in response.content


def test_static_assets_are_served():
    from fastapi.testclient import TestClient

    client = TestClient(main_module.app)
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/brand/mark.svg").status_code == 200


def test_personal_boundary_question_is_blocked_before_any_llm_call(monkeypatch):
    from fastapi.testclient import TestClient

    def fail_if_called(*args, **kwargs):
        raise AssertionError("generate_answer should never be called for a guardrail-blocked question")

    monkeypatch.setattr(main_module, "generate_answer", fail_if_called)
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "Is Kevin married?"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["refused"] is True
    assert payload["refusal_reason"] == "personal_boundary:relationship_or_family"
    assert payload["sources"] == []


def test_profane_question_is_blocked_before_any_llm_call(monkeypatch):
    from fastapi.testclient import TestClient

    def fail_if_called(*args, **kwargs):
        raise AssertionError("generate_answer should never be called for profane input")

    monkeypatch.setattr(main_module, "generate_answer", fail_if_called)
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "kevin is a piece of shit engineer right?"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["refused"] is True
    assert payload["refusal_reason"] == "profanity"
    assert payload["sources"] == []


def test_weakly_related_question_is_refused_before_any_llm_call(monkeypatch):
    from fastapi.testclient import TestClient

    def fail_if_called(*args, **kwargs):
        raise AssertionError("generate_answer should never be called when nothing clears the relevance bar")

    monkeypatch.setattr(main_module, "generate_answer", fail_if_called)
    client = TestClient(main_module.app)
    # Shares just enough incidental vocabulary with the resume ("Kevin", "drive") to score nonzero but still stay
    # well under MIN_RELEVANCE_SCORE -- the deterministic gate should still catch this without an LLM call.
    response = client.post("/api/chat", json={"question": "What color car does Kevin drive?"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["refused"] is True
    assert payload["refusal_reason"] == "not_grounded"


def test_zero_signal_question_reaches_the_llm_and_is_declined_in_prose(monkeypatch):
    from fastapi.testclient import TestClient

    # A question with zero shared vocabulary with the corpus (e.g. "pizza topping") now clears the relevance
    # gate via the no-signal floor rather than being hard-refused, and relies on the LLM's own honesty
    # instruction as the real judge -- this locks in that it reaches the LLM rather than silently refusing.
    monkeypatch.setattr(
        main_module,
        "generate_answer",
        lambda q, excerpts, history: LLMResult(text="I don't have grounded information about that."),
    )
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "What is Kevin's favorite pizza topping ever?"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["refused"] is False
    assert payload["answer"] == "I don't have grounded information about that."


def test_gibberish_question_is_refused_before_any_llm_call(monkeypatch):
    from fastapi.testclient import TestClient

    def fail_if_called(*args, **kwargs):
        raise AssertionError("generate_answer should never be called for gibberish input")

    monkeypatch.setattr(main_module, "generate_answer", fail_if_called)
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "asdkjfh aslkdj qpwoeiru"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["refused"] is True
    assert payload["refusal_reason"] == "gibberish"
    assert payload["sources"] == []


def test_identity_question_answers_directly_without_any_llm_call(monkeypatch):
    from fastapi.testclient import TestClient

    def fail_if_called(*args, **kwargs):
        raise AssertionError("generate_answer should never be called for an identity meta-question")

    monkeypatch.setattr(main_module, "generate_answer", fail_if_called)
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "who are you"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["refused"] is False
    assert payload["sources"] == []
    assert "AskKevin" in payload["answer"]


def test_identity_question_gets_no_sources_even_with_unrelated_prior_history(monkeypatch):
    from fastapi.testclient import TestClient

    def fail_if_called(*args, **kwargs):
        raise AssertionError("generate_answer should never be called for an identity meta-question")

    monkeypatch.setattr(main_module, "generate_answer", fail_if_called)
    client = TestClient(main_module.app)
    response = client.post(
        "/api/chat",
        json={"question": "who are you", "history": [["What company does Kevin work for?", "Walmart."]]},
    )
    payload = response.json()
    assert payload["refused"] is False
    assert payload["sources"] == []


def test_grounded_question_returns_sources_and_calls_llm(monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(
        main_module, "generate_answer", lambda q, excerpts, history: LLMResult(text="Kevin works at Walmart.")
    )
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "What company does Kevin currently work for?"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["refused"] is False
    assert len(payload["sources"]) > 0
    assert payload["answer"] == "Kevin works at Walmart."


def test_grounded_question_response_includes_token_usage(monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(
        main_module,
        "generate_answer",
        lambda q, excerpts, history: LLMResult(
            text="Kevin works at Walmart.",
            prompt_tokens=2000,
            completion_tokens=50,
            total_tokens=2050,
            cached_tokens=1800,
            model="gpt-4o-mini",
        ),
    )
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "What company does Kevin currently work for?"})
    payload = response.json()
    usage = payload["token_usage"]
    assert usage["prompt_tokens"] == 2000
    assert usage["completion_tokens"] == 50
    assert usage["total_tokens"] == 2050
    assert usage["cached_tokens"] == 1800
    assert usage["model"] == "gpt-4o-mini"
    # Cost is derived server-side so the UI never has to bake in per-provider rates.
    expected_cost = round(200 * 0.15e-6 + 1800 * 0.075e-6 + 50 * 0.60e-6, 6)
    assert usage["estimated_cost_usd"] == expected_cost


def test_provider_failure_response_has_no_token_usage(monkeypatch):
    from fastapi.testclient import TestClient

    def raise_llm_error(q, excerpts, history):
        raise LLMError("simulated outage", category="timeout")

    monkeypatch.setattr(main_module, "generate_answer", raise_llm_error)
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "What company does Kevin currently work for?"})
    assert response.json()["token_usage"] is None


def test_provider_failure_returns_a_clean_message_with_no_raw_excerpts(monkeypatch):
    from fastapi.testclient import TestClient

    def raise_llm_error(q, excerpts, history):
        raise LLMError("simulated provider outage", category="timeout")

    monkeypatch.setattr(main_module, "generate_answer", raise_llm_error)
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "What company does Kevin currently work for?"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["refused"] is True
    assert payload["refusal_reason"] == "provider_unavailable:timeout"
    assert "timed out" in payload["answer"].lower()
    assert payload["sources"] == []
    assert "Walmart" not in payload["answer"]


def test_provider_failure_surfaces_rate_limit_category_distinctly(monkeypatch):
    from fastapi.testclient import TestClient

    def raise_llm_error(q, excerpts, history):
        raise LLMError("simulated throttling", category="rate_limit")

    monkeypatch.setattr(main_module, "generate_answer", raise_llm_error)
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "What company does Kevin currently work for?"})
    payload = response.json()
    assert payload["refusal_reason"] == "provider_unavailable:rate_limit"
    assert "rate limit" in payload["answer"].lower()


def test_github_question_fetches_live_and_never_reads_a_static_file(monkeypatch):
    from fastapi.testclient import TestClient

    def fake_fetch(username=None):
        return [("GitHub Project: askkevin", "URL: https://github.com/kevintlee01/askkevin\n\nA test repo.")]

    monkeypatch.setattr(main_module, "fetch_github_excerpts", fake_fetch)
    monkeypatch.setattr(
        main_module, "generate_answer", lambda q, excerpts, history: LLMResult(text="Kevin has a repo called askkevin.")
    )
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "What's on his GitHub?"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["refused"] is False
    assert any(s["source"] == "github.com (live)" for s in payload["sources"])
    assert "askkevin." in payload["answer"]


def test_github_question_only_surfaces_repos_relevant_to_the_question(monkeypatch):
    from fastapi.testclient import TestClient

    # Regression: previously every fetched repo was returned as a "source" with a hardcoded score of 1.0, so questions like "what has Kevin built with AI agents?" listed unrelated repos (chess, currency-converter, tic-tac-toe, etc.) as if they informed the answer.
    def fake_fetch(username=None):
        return [
            ("GitHub Project: agent-orchestrator", "URL: https://github.com/x/agent-orchestrator\n\nAn autonomous AI agent framework built on LangGraph."),
            ("GitHub Project: chess_game", "URL: https://github.com/x/chess_game\n\nA two-player chess game written in Python."),
            ("GitHub Project: currency_converter", "URL: https://github.com/x/currency_converter\n\nA CLI currency converter using a public exchange-rate API."),
            ("GitHub Project: tic_tac_toe", "URL: https://github.com/x/tic_tac_toe\n\nA tic tac toe game in JavaScript."),
        ]

    captured_excerpts: dict = {}

    def capture_excerpts(question, excerpts, history):
        captured_excerpts["excerpts"] = excerpts
        return LLMResult(text="Kevin has built an autonomous AI agent framework.")

    monkeypatch.setattr(main_module, "fetch_github_excerpts", fake_fetch)
    monkeypatch.setattr(main_module, "generate_answer", capture_excerpts)
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "What has Kevin built with AI agents on GitHub?"})
    payload = response.json()
    assert response.status_code == 200
    live_sections = {s["section"] for s in payload["sources"] if s["source"] == "github.com (live)"}
    assert "GitHub Project: agent-orchestrator" in live_sections
    # Irrelevant repos must be filtered out of both the sources panel and the LLM prompt so the answer is grounded on what actually matches.
    for irrelevant in ("GitHub Project: chess_game", "GitHub Project: currency_converter", "GitHub Project: tic_tac_toe"):
        assert irrelevant not in live_sections
    assert any("agent-orchestrator" in e for e in captured_excerpts["excerpts"])
    assert not any("chess_game" in e for e in captured_excerpts["excerpts"])


def test_github_question_falls_back_to_local_resume_matches_when_live_fetch_fails(monkeypatch):
    from fastapi.testclient import TestClient

    def fail_fetch(username=None):
        raise GitHubFetchError("rate limited")

    monkeypatch.setattr(main_module, "fetch_github_excerpts", fail_fetch)
    monkeypatch.setattr(
        main_module, "generate_answer", lambda q, excerpts, history: LLMResult(text="Kevin has built GitHub projects.")
    )
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "What's on his GitHub?"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["refused"] is False
    assert all(s["source"] != "github.com (live)" for s in payload["sources"])


def test_github_question_refuses_cleanly_when_live_fetch_fails_and_nothing_local_matches(monkeypatch):
    from fastapi.testclient import TestClient

    def fail_fetch(username=None):
        raise GitHubFetchError("rate limited")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("generate_answer should never be called with zero sources")

    monkeypatch.setattr(main_module, "fetch_github_excerpts", fail_fetch)
    monkeypatch.setattr(main_module.index, "search", lambda *a, **k: [])
    monkeypatch.setattr(main_module, "generate_answer", fail_if_called)
    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "What's on his GitHub?"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["refused"] is True
    assert payload["refusal_reason"] == "github_unavailable"
    assert payload["sources"] == []


def test_missing_history_field_defaults_cleanly():
    from fastapi.testclient import TestClient

    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "test"})
    assert response.status_code == 200


def test_retrieval_query_uses_recent_history_for_followups():
    request = main_module.ChatRequest(question="tell me more", history=[["What does he do?", "He builds things."]])
    query = main_module.retrieval_query(request)
    assert "What does he do?" in query
    assert "He builds things." in query
    assert "tell me more" in query


def test_retrieval_query_is_just_the_question_with_no_history():
    request = main_module.ChatRequest(question="What does he do?", history=[])
    assert main_module.retrieval_query(request) == "What does he do?"


def test_retrieval_query_does_not_get_poisoned_by_a_single_weak_recent_turn():
    history = [
        ["What has Kevin built with AI agents?", "He built an agentic incident troubleshooter at Walmart."],
        ["test", "I don't have grounded information about test in the provided source excerpts."],
    ]
    request = main_module.ChatRequest(question="who is he", history=history)
    query = main_module.retrieval_query(request)
    assert "agentic incident troubleshooter" in query
    ranked = main_module.index.search(query, top_k=6, intent_query=request.question)
    top_score = ranked[0][1] if ranked else 0.0
    assert top_score >= main_module.MIN_RELEVANCE_SCORE


def test_response_provider_field_matches_config_provider():
    from fastapi.testclient import TestClient

    from app.config import PROVIDER

    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "Is Kevin married?"})
    assert response.json()["provider"] == PROVIDER


def test_rate_limit_returns_429_once_the_configured_ceiling_is_exceeded(monkeypatch):
    from fastapi.testclient import TestClient

    from app import rate_limit

    monkeypatch.setattr(rate_limit, "RATE_LIMIT_MAX_REQUESTS", 2)
    rate_limit.reset()
    client = TestClient(main_module.app)
    assert client.post("/api/chat", json={"question": "Is Kevin married?"}).status_code == 200
    assert client.post("/api/chat", json={"question": "Is Kevin married?"}).status_code == 200
    third = client.post("/api/chat", json={"question": "Is Kevin married?"})
    assert third.status_code == 429
    rate_limit.reset()


def test_empty_question_is_rejected_at_the_input_layer_before_any_processing():
    from fastapi.testclient import TestClient

    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": ""})
    assert response.status_code == 422


def test_oversized_question_is_rejected_at_the_input_layer_before_any_processing():
    from fastapi.testclient import TestClient

    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "a" * 2001})
    assert response.status_code == 422


def test_max_length_question_at_the_boundary_is_still_accepted():
    from fastapi.testclient import TestClient

    client = TestClient(main_module.app)
    response = client.post("/api/chat", json={"question": "a" * 2000})
    assert response.status_code == 200


def test_oversized_history_is_rejected_at_the_input_layer_before_any_processing():
    from fastapi.testclient import TestClient

    client = TestClient(main_module.app)
    huge_history = [["q", "a"]] * 51
    response = client.post("/api/chat", json={"question": "test", "history": huge_history})
    assert response.status_code == 422
