from app.pricing import PRICING, estimate_cost


def test_estimate_cost_computes_uncached_input_plus_cached_input_plus_output():
    # gpt-4o-mini rates: input $0.15/M, cached $0.075/M, output $0.60/M.
    cost = estimate_cost("gpt-4o-mini", prompt_tokens=2000, completion_tokens=100, cached_tokens=1800)
    expected = 200 * 0.15e-6 + 1800 * 0.075e-6 + 100 * 0.60e-6
    assert cost == round(expected, 6)


def test_estimate_cost_treats_missing_cached_tokens_as_zero_uncached_input():
    cost = estimate_cost("gpt-4o-mini", prompt_tokens=1000, completion_tokens=50, cached_tokens=None)
    expected = 1000 * 0.15e-6 + 50 * 0.60e-6
    assert cost == round(expected, 6)


def test_estimate_cost_uses_anthropic_haiku_10_percent_cache_read_rate():
    # Regression: Anthropic's cache_read is 10% of input (not 50% like OpenAI), so the discount curve must be provider-specific, not a shared constant.
    cost = estimate_cost("claude-3-5-haiku-latest", prompt_tokens=4000, completion_tokens=200, cached_tokens=1900)
    expected = 2100 * 0.80e-6 + 1900 * 0.08e-6 + 200 * 4.00e-6
    assert cost == round(expected, 6)


def test_estimate_cost_uses_gemini_flash_lite_25_percent_cache_rate():
    cost = estimate_cost("gemini-flash-lite-latest", prompt_tokens=2000, completion_tokens=100, cached_tokens=1500)
    expected = 500 * 0.10e-6 + 1500 * 0.025e-6 + 100 * 0.40e-6
    assert cost == round(expected, 6)


def test_estimate_cost_returns_none_for_unknown_model():
    # Guards against silently pricing a new model at $0 -- the UI hides the field when this is None.
    assert estimate_cost("some-future-model", prompt_tokens=100, completion_tokens=10, cached_tokens=0) is None


def test_estimate_cost_returns_none_when_usage_numbers_are_missing():
    assert estimate_cost("gpt-4o-mini", prompt_tokens=None, completion_tokens=10, cached_tokens=0) is None
    assert estimate_cost("gpt-4o-mini", prompt_tokens=100, completion_tokens=None, cached_tokens=0) is None
    assert estimate_cost(None, prompt_tokens=100, completion_tokens=10, cached_tokens=0) is None


def test_pricing_table_covers_the_three_configured_default_models():
    # Regression: if a config default gains a new model, add it to PRICING or estimate_cost silently returns None.
    from app.config import ANTHROPIC_MODEL, GEMINI_MODEL, OPENAI_MODEL

    assert OPENAI_MODEL in PRICING
    assert ANTHROPIC_MODEL in PRICING
    assert GEMINI_MODEL in PRICING


def test_pricing_table_entries_have_all_three_required_rates():
    for model, rates in PRICING.items():
        assert "input" in rates, f"{model} missing input rate"
        assert "output" in rates, f"{model} missing output rate"
        assert "cached_input" in rates, f"{model} missing cached_input rate"
        assert rates["cached_input"] <= rates["input"], f"{model} cached rate must be a discount vs input"
