# Per-token USD prices sourced from LiteLLM's canonical model_prices_and_context_window_backup.json (https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window_backup.json) as of 2025-11; we skip the `litellm` package itself because it pulls in every provider SDK it supports, which is heavy for a demo whose only need is a lookup table.

PRICING: dict[str, dict[str, float]] = {
    # OpenAI: cached input billed at 50% of standard input.
    "gpt-4o-mini": {"input": 0.15e-6, "output": 0.60e-6, "cached_input": 0.075e-6},
    "gpt-4o-mini-2024-07-18": {"input": 0.15e-6, "output": 0.60e-6, "cached_input": 0.075e-6},
    "gpt-4o": {"input": 2.50e-6, "output": 10.00e-6, "cached_input": 1.25e-6},
    # Anthropic: cached input (reads) billed at 10% of standard input.
    "claude-3-5-haiku-latest": {"input": 0.80e-6, "output": 4.00e-6, "cached_input": 0.08e-6},
    "claude-3-5-haiku-20241022": {"input": 0.80e-6, "output": 4.00e-6, "cached_input": 0.08e-6},
    "claude-3-5-sonnet-latest": {"input": 3.00e-6, "output": 15.00e-6, "cached_input": 0.30e-6},
    "claude-3-5-sonnet-20241022": {"input": 3.00e-6, "output": 15.00e-6, "cached_input": 0.30e-6},
    # Gemini: cached input billed at 25% of standard input.
    "gemini-flash-lite-latest": {"input": 0.10e-6, "output": 0.40e-6, "cached_input": 0.025e-6},
    "gemini-2.5-flash-lite": {"input": 0.10e-6, "output": 0.40e-6, "cached_input": 0.025e-6},
    "gemini-2.5-flash": {"input": 0.30e-6, "output": 2.50e-6, "cached_input": 0.075e-6},
}


def estimate_cost(
    model: str | None,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    cached_tokens: int | None,
) -> float | None:
    # Returns None if the model isn't in the table or usage numbers are missing, so the UI can hide the field instead of showing a fake $0.
    if model is None or prompt_tokens is None or completion_tokens is None:
        return None
    price = PRICING.get(model)
    if price is None:
        return None
    cached = cached_tokens or 0
    uncached_input = max(prompt_tokens - cached, 0)
    total = uncached_input * price["input"] + cached * price["cached_input"] + completion_tokens * price["output"]
    return round(total, 6)
