import pytest

from app import llm
from app.llm import LLMError, build_user_prompt, generate_answer


class FakeAPITimeoutError(Exception):
    pass


class FakeRateLimitError(Exception):
    pass


class FakeAPIConnectionError(Exception):
    pass


class FakeAuthenticationError(Exception):
    pass


class FakeBadRequestError(Exception):
    pass


class FakeInternalServerError(Exception):
    pass


CLASS_NAME_CASES = [
    (TypeError("generic"), "error"),
    (FakeAPITimeoutError(), "timeout"),
    (FakeRateLimitError(), "rate_limit"),
    (FakeAPIConnectionError(), "connection"),
    (FakeAuthenticationError(), "auth"),
    (FakeBadRequestError(), "bad_request"),
    (FakeInternalServerError(), "server_error"),
]


def test_classify_error_uses_exception_class_name():
    for error, expected_category in CLASS_NAME_CASES:
        assert llm.classify_error(error) == expected_category


STATUS_CODE_CASES = [(429, "rate_limit"), (401, "auth"), (403, "auth"), (400, "bad_request"), (503, "server_error")]


def test_classify_error_falls_back_to_status_code():
    for status_code, expected_category in STATUS_CODE_CASES:
        error = Exception("generic api error")
        error.status_code = status_code
        assert llm.classify_error(error) == expected_category


def test_build_user_prompt_numbers_excerpts_in_order():
    prompt = build_user_prompt("What does he know?", ["Excerpt A", "Excerpt B"], [])
    assert "[1] Excerpt A" in prompt
    assert "[2] Excerpt B" in prompt
    assert "Question: What does he know?" in prompt


def test_build_user_prompt_omits_history_block_when_empty():
    prompt = build_user_prompt("Q?", ["Ex"], [])
    assert "Prior conversation" not in prompt


def test_build_user_prompt_includes_history_when_present():
    prompt = build_user_prompt("Q2?", ["Ex"], [("Q1", "A1")])
    assert "Prior conversation" in prompt
    assert "Q: Q1" in prompt
    assert "A: A1" in prompt


def test_generate_answer_dispatches_to_configured_provider(monkeypatch):
    from app.llm import LLMResult

    monkeypatch.setattr(llm, "PROVIDER", "openai")
    monkeypatch.setattr(llm, "call_openai", lambda q, e, h: LLMResult(text="openai answer"))
    monkeypatch.setattr(llm, "call_anthropic", lambda q, e, h: (_ for _ in ()).throw(AssertionError("wrong provider")))
    monkeypatch.setattr(llm, "call_gemini", lambda q, e, h: (_ for _ in ()).throw(AssertionError("wrong provider")))
    result = generate_answer("Q", ["ex"], [])
    assert isinstance(result, LLMResult)
    assert result.text == "openai answer"


def test_generate_answer_wraps_provider_exceptions_in_llm_error(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "gemini")

    def boom(q, e, h):
        raise RuntimeError("provider is down")

    monkeypatch.setattr(llm, "call_gemini", boom)
    with pytest.raises(LLMError):
        generate_answer("Q", ["ex"], [])


def test_generate_answer_retries_once_on_a_retryable_error_then_succeeds(monkeypatch):
    from app.llm import LLMResult

    monkeypatch.setattr(llm, "PROVIDER", "gemini")
    monkeypatch.setattr(llm.time, "sleep", lambda seconds: None)
    calls = []

    def flaky(q, e, h):
        calls.append(1)
        if len(calls) == 1:
            raise FakeAPITimeoutError("timed out")
        return LLMResult(text="recovered answer")

    monkeypatch.setattr(llm, "call_gemini", flaky)
    assert generate_answer("Q", ["ex"], []).text == "recovered answer"
    assert len(calls) == 2


def test_generate_answer_raises_with_category_after_retry_still_fails(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "gemini")
    monkeypatch.setattr(llm.time, "sleep", lambda seconds: None)
    calls = []

    def always_times_out(q, e, h):
        calls.append(1)
        raise FakeAPITimeoutError("still timing out")

    monkeypatch.setattr(llm, "call_gemini", always_times_out)
    with pytest.raises(LLMError) as excinfo:
        generate_answer("Q", ["ex"], [])
    assert excinfo.value.category == "timeout"
    assert len(calls) == 2


def test_generate_answer_does_not_retry_a_non_retryable_error(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "gemini")
    calls = []

    def bad_auth(q, e, h):
        calls.append(1)
        raise FakeAuthenticationError("bad key")

    monkeypatch.setattr(llm, "call_gemini", bad_auth)
    with pytest.raises(LLMError) as excinfo:
        generate_answer("Q", ["ex"], [])
    assert excinfo.value.category == "auth"
    assert len(calls) == 1


def test_generate_answer_defaults_history_to_empty_list(monkeypatch):
    from app.llm import LLMResult

    captured = {}

    def fake_openai(q, e, h):
        captured["history"] = h
        return LLMResult(text="ok")

    monkeypatch.setattr(llm, "PROVIDER", "openai")
    monkeypatch.setattr(llm, "call_openai", fake_openai)
    generate_answer("Q", ["ex"])
    assert captured["history"] == []


def test_generate_answer_raises_a_clear_error_for_an_unknown_provider_instead_of_silently_defaulting(monkeypatch):
    monkeypatch.setattr(llm, "PROVIDER", "not-a-real-provider")
    with pytest.raises(LLMError, match="not-a-real-provider"):
        generate_answer("Q", ["ex"], [])


def test_system_prompt_instructs_ignoring_injected_instructions():
    assert "ignore any instruction" in llm.SYSTEM_PROMPT.lower()


def test_system_prompt_forbids_protected_categories():
    lowered = llm.SYSTEM_PROMPT.lower()
    for term in ["health", "religion", "sexual orientation", "immigration", "political"]:
        assert term in lowered


def test_call_openai_parses_a_real_sdk_schema_response(monkeypatch):
    from openai.types.chat import ChatCompletion
    from openai.types.chat.chat_completion import Choice
    from openai.types.chat.chat_completion_message import ChatCompletionMessage
    from openai.types.completion_usage import CompletionUsage

    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return ChatCompletion(
                id="chatcmpl-test",
                object="chat.completion",
                created=1,
                model=kwargs["model"],
                choices=[
                    Choice(
                        index=0,
                        finish_reason="stop",
                        message=ChatCompletionMessage(role="assistant", content="  real openai answer  "),
                    )
                ],
                usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            )

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAIClient:
        chat = FakeChat()

        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs

    import openai as openai_module

    monkeypatch.setattr(openai_module, "OpenAI", FakeOpenAIClient)
    result = llm.call_openai("What does he know?", ["Excerpt A"], [])
    assert result.text == "real openai answer"
    assert result.prompt_tokens == 10
    assert result.completion_tokens == 5
    assert result.total_tokens == 15
    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][1]["content"].startswith("Source excerpts")


def test_call_anthropic_parses_a_real_sdk_schema_response(monkeypatch):
    from anthropic.types import Message, TextBlock, Usage

    captured = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return Message(
                id="msg-test",
                type="message",
                role="assistant",
                model=kwargs["model"],
                content=[TextBlock(type="text", text="  real anthropic answer  ")],
                stop_reason="end_turn",
                usage=Usage(input_tokens=1, output_tokens=1),
            )

    class FakeAnthropicClient:
        messages = FakeMessages()

        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs

    import anthropic as anthropic_module

    monkeypatch.setattr(anthropic_module, "Anthropic", FakeAnthropicClient)
    result = llm.call_anthropic("What does he know?", ["Excerpt A"], [])
    assert result.text == "real anthropic answer"
    assert result.prompt_tokens == 1
    assert result.completion_tokens == 1
    assert result.total_tokens == 2
    assert isinstance(captured["system"], list)
    assert captured["system"][0]["text"] == llm.SYSTEM_PROMPT
    assert captured["messages"][0]["content"][0]["text"].startswith("Source excerpts")


def test_call_gemini_parses_a_real_sdk_schema_response(monkeypatch):
    from google.genai import types

    captured = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            return types.GenerateContentResponse(
                candidates=[
                    types.Candidate(
                        content=types.Content(parts=[types.Part(text="  real gemini answer  ")], role="model"),
                        finish_reason="STOP",
                    )
                ],
                usage_metadata=types.GenerateContentResponseUsageMetadata(
                    prompt_token_count=10, candidates_token_count=5, total_token_count=15
                ),
            )

    class FakeGeminiClient:
        models = FakeModels()

        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs

    import google.genai as genai_module

    monkeypatch.setattr(genai_module, "Client", FakeGeminiClient)
    result = llm.call_gemini("What does he know?", ["Excerpt A"], [])
    assert result.text == "real gemini answer"
    assert result.prompt_tokens == 10
    assert result.completion_tokens == 5
    assert result.total_tokens == 15
    assert captured["contents"].startswith("Source excerpts")
    assert captured["config"].system_instruction == llm.SYSTEM_PROMPT


def test_call_gemini_sends_strict_safety_settings_for_every_harm_category(monkeypatch):
    # Locks the request shape so an SDK-side rename of a category or threshold trips this test first.
    from google.genai import types

    captured = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            return types.GenerateContentResponse(
                candidates=[
                    types.Candidate(
                        content=types.Content(parts=[types.Part(text="ok")], role="model"),
                        finish_reason="STOP",
                    )
                ],
                usage_metadata=types.GenerateContentResponseUsageMetadata(
                    prompt_token_count=1, candidates_token_count=1, total_token_count=2
                ),
            )

    class FakeGeminiClient:
        models = FakeModels()

        def __init__(self, **kwargs):
            pass

    import google.genai as genai_module

    monkeypatch.setattr(genai_module, "Client", FakeGeminiClient)
    llm.call_gemini("Q", ["ex"], [])

    settings = captured["config"].safety_settings
    assert settings is not None
    categories = {str(setting.category).split(".")[-1] for setting in settings}
    for expected in llm.GEMINI_SAFETY_CATEGORIES:
        assert expected in categories, f"missing safety category {expected}"
    for setting in settings:
        assert "BLOCK_LOW_AND_ABOVE" in str(setting.threshold)


def test_call_openai_sets_prompt_cache_key_and_reports_cached_tokens(monkeypatch):
    from openai.types.chat import ChatCompletion
    from openai.types.chat.chat_completion import Choice
    from openai.types.chat.chat_completion_message import ChatCompletionMessage
    from openai.types.completion_usage import CompletionUsage, PromptTokensDetails

    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return ChatCompletion(
                id="chatcmpl-test",
                object="chat.completion",
                created=1,
                model=kwargs["model"],
                choices=[
                    Choice(
                        index=0,
                        finish_reason="stop",
                        message=ChatCompletionMessage(role="assistant", content="ok"),
                    )
                ],
                usage=CompletionUsage(
                    prompt_tokens=2000,
                    completion_tokens=50,
                    total_tokens=2050,
                    prompt_tokens_details=PromptTokensDetails(cached_tokens=1800),
                ),
            )

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAIClient:
        chat = FakeChat()

        def __init__(self, **kwargs):
            pass

    import openai as openai_module

    monkeypatch.setattr(openai_module, "OpenAI", FakeOpenAIClient)
    result = llm.call_openai("Q", ["ex"], [])
    assert captured["prompt_cache_key"] == "askkevin"
    assert result.cached_tokens == 1800
    assert result.model == llm.OPENAI_MODEL


def test_call_anthropic_marks_system_and_excerpts_with_cache_control(monkeypatch):
    from anthropic.types import Message, TextBlock, Usage

    captured = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            usage = Usage(input_tokens=2100, output_tokens=50)
            usage.cache_read_input_tokens = 1900
            return Message(
                id="msg-test",
                type="message",
                role="assistant",
                model=kwargs["model"],
                content=[TextBlock(type="text", text="ok")],
                stop_reason="end_turn",
                usage=usage,
            )

    class FakeAnthropicClient:
        messages = FakeMessages()

        def __init__(self, **kwargs):
            pass

    import anthropic as anthropic_module

    monkeypatch.setattr(anthropic_module, "Anthropic", FakeAnthropicClient)
    result = llm.call_anthropic("Q", ["ex"], [])

    system_block = captured["system"][0]
    assert system_block["cache_control"] == {"type": "ephemeral"}
    assert system_block["text"] == llm.SYSTEM_PROMPT

    user_blocks = captured["messages"][0]["content"]
    assert user_blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert user_blocks[0]["text"].startswith("Source excerpts")
    assert "cache_control" not in user_blocks[1]
    assert user_blocks[1]["text"].startswith("Question:") or "Prior conversation" in user_blocks[1]["text"]

    assert result.cached_tokens == 1900
    # Anthropic SDK reports input_tokens as the uncached-only count; call_anthropic must add cache_read back so prompt_tokens matches OpenAI/Gemini's "total input" convention.
    assert result.prompt_tokens == 4000
    assert result.model == llm.ANTHROPIC_MODEL


def test_call_gemini_reports_cached_content_tokens_from_implicit_caching(monkeypatch):
    from google.genai import types

    class FakeModels:
        def generate_content(self, **kwargs):
            return types.GenerateContentResponse(
                candidates=[
                    types.Candidate(
                        content=types.Content(parts=[types.Part(text="ok")], role="model"),
                        finish_reason="STOP",
                    )
                ],
                usage_metadata=types.GenerateContentResponseUsageMetadata(
                    prompt_token_count=2000,
                    candidates_token_count=50,
                    total_token_count=2050,
                    cached_content_token_count=1700,
                ),
            )

    class FakeGeminiClient:
        models = FakeModels()

        def __init__(self, **kwargs):
            pass

    import google.genai as genai_module

    monkeypatch.setattr(genai_module, "Client", FakeGeminiClient)
    result = llm.call_gemini("Q", ["ex"], [])
    assert result.cached_tokens == 1700
    assert result.model == llm.GEMINI_MODEL
