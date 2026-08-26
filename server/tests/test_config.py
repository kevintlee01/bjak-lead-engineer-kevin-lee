import importlib

from app import config


def test_default_provider_is_gemini_when_env_unset():
    assert config.PROVIDER in {"openai", "anthropic", "gemini"}


def test_provider_down_message_is_category_specific():
    timeout_msg = config.provider_down_message("timeout")
    rate_limit_msg = config.provider_down_message("rate_limit")
    auth_msg = config.provider_down_message("auth")
    assert "timed out" in timeout_msg.lower()
    assert "rate limit" in rate_limit_msg.lower()
    assert "key" in auth_msg.lower()
    assert timeout_msg != rate_limit_msg != auth_msg


def test_provider_down_message_falls_back_to_generic_error_for_unknown_category():
    assert config.provider_down_message("some-made-up-category") == config.PROVIDER_DOWN_MESSAGES["error"]


def test_active_api_key_matches_configured_provider(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER", "gemini")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-gemini-key")
    assert config.active_api_key() == "fake-gemini-key"

    monkeypatch.setattr(config, "PROVIDER", "openai")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "fake-openai-key")
    assert config.active_api_key() == "fake-openai-key"

    monkeypatch.setattr(config, "PROVIDER", "anthropic")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "fake-anthropic-key")
    assert config.active_api_key() == "fake-anthropic-key"


def test_refusal_message_mentions_resume_not_cv():
    assert "resume" in config.REFUSAL_MESSAGE.lower()
    assert " cv" not in config.REFUSAL_MESSAGE.lower()


def test_numeric_env_vars_have_sane_defaults():
    assert config.TOP_K > 0
    assert 0 <= config.MIN_RELEVANCE_SCORE <= 1
    assert config.REQUEST_TIMEOUT_SECONDS > 0
    assert config.MAX_HISTORY_TURNS >= 0
    assert config.GITHUB_MAX_REPOS > 0


def test_env_override_is_picked_up_on_reimport(monkeypatch):
    monkeypatch.setenv("TOP_K", "9")
    monkeypatch.setenv("GITHUB_USERNAME", "someoneelse")
    reloaded = importlib.reload(config)
    try:
        assert reloaded.TOP_K == 9
        assert reloaded.GITHUB_USERNAME == "someoneelse"
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_startup_warnings_is_empty_for_a_known_provider_with_a_key(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER", "gemini")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")
    assert config.startup_warnings() == []


def test_startup_warnings_flags_an_unknown_provider(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER", "not-a-real-provider")
    warnings = config.startup_warnings()
    assert len(warnings) == 1
    assert "not-a-real-provider" in warnings[0]


def test_startup_warnings_flags_a_missing_api_key(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER", "openai")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    warnings = config.startup_warnings()
    assert len(warnings) == 1
    assert "openai" in warnings[0]


def test_contains_refusal_phrase_matches_the_contraction_form():
    assert config.contains_refusal_phrase("I don't have grounded information about that.") is True


def test_contains_refusal_phrase_matches_the_do_not_form():
    # Regression: a live LLM paraphrases "don't" as "do not" run to run, and both must count as a refusal.
    assert config.contains_refusal_phrase("I do not have grounded information on that topic.") is True


def test_contains_refusal_phrase_is_case_insensitive():
    assert config.contains_refusal_phrase("I DO NOT HAVE GROUNDED INFORMATION here.") is True


def test_contains_refusal_phrase_is_false_for_a_real_grounded_answer():
    assert config.contains_refusal_phrase("Kevin works at Walmart as a Senior Software Engineer.") is False
