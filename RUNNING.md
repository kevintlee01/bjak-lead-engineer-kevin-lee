# Running AskKevin locally

Operational cheatsheet: install, run, test, evaluate, containerise, regenerate brand assets. For the design and why-behind-the-decisions writeup, see [README.md](README.md).

## Prerequisites

- **Python 3.11** and [`uv`](https://docs.astral.sh/uv/) (or a plain `python3.11 -m venv` if you prefer stdlib venvs). All commands below use `uv`; adapt as needed.
- **An LLM provider API key** — Google Gemini (default) is free at [aistudio.google.com](https://aistudio.google.com), no card required. OpenAI or Anthropic keys work too if you have one.
- **Optional: Docker + Docker Compose** — only if you want to run the containerised version.
- **Optional: `rsvg-convert` and ImageMagick** — only if you want to regenerate brand assets (`brew install librsvg imagemagick`).

## Install and run the dev server (under 10 minutes)

```bash
cd server
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `LLM_PROVIDER` to `openai`, `anthropic`, or `gemini`, and paste the matching API key. Then, from `server/`:

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Ask something like *"What has Kevin built with AI agents?"* or *"What is Kevin's home address?"* (it will refuse the second one).

**Cost per question:** one short chat-completion call (~400–800 input tokens + a short answer). Free on Gemini's free tier (`gemini-flash-lite-latest`), or a few hundredths of a cent on `gpt-4o-mini` / `claude-3-5-haiku` if you switch providers.

## Configuration

Every env var is declared in [server/.env.example](server/.env.example). The most common ones:

| Variable | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | One of `openai`, `anthropic`, `gemini`. |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | (empty) | Only the active provider's key is required. |
| `TOP_K` | `6` | How many resume chunks the retriever passes to the LLM. |
| `MIN_RELEVANCE_SCORE` | `0.08` | Below this, the app refuses without calling the LLM. |
| `MAX_HISTORY_TURNS` | `3` | How many prior Q/A pairs the retriever and LLM see. |
| `REQUEST_TIMEOUT_SECONDS` | `20` | Per-provider client timeout. |
| `LLM_RETRY_DELAY_SECONDS` | `1.5` | Sleep before the one automatic retry on transient failures. |
| `RATE_LIMIT_MAX_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | `40` / `60` | Sliding-window per-client rate limit. |
| `GITHUB_USERNAME` / `GITHUB_TOKEN` / `GITHUB_MAX_REPOS` | `kevintlee01` / (empty) / `20` | Live GitHub fetch. Token is optional and only raises the rate limit. |

## Running the unit tests

Fast, deterministic, no network or LLM calls — ~5 seconds for the full suite. From `server/`:

```bash
uv pip install -r requirements-dev.txt
pytest
```

Same install also gets you `ruff` for linting:

```bash
ruff check app eval tests
```

## Running the behavioural eval (real live LLM)

29 labelled questions across six categories (direct, multi-source, ambiguous, unanswerable, adversarial, personal_boundary), scored end-to-end through the real FastAPI app via `TestClient`. Writes results to [server/eval/results.md](server/eval/results.md).

Needs a real API key for whichever provider is set in `.env`. From `server/`:

```bash
python -m eval.run_eval
```

Cost: **$0** on Gemini's free tier, since all 29 calls fit inside the daily quota for `gemini-flash-lite-latest`. Roughly a cent or two on OpenAI/Anthropic if you switch providers. See the design doc's "Evaluation" section for metric definitions and the current committed results.

## Running the smoke test

A non-graded battery covering edge cases the labelled dataset doesn't (empty/oversized/HTML-injection-shaped input, missing/malformed history, static asset serving, cross-checking every guardrail category fires near-instantly). From `server/`:

```bash
python -m eval.smoke_test
```

## Verifying your provider setup

One live call, clear pass/fail, no eval suite needed. Useful if you're switching providers or just installed a new key. From `server/`:

```bash
python -m eval.check_provider
```

## Docker

The repo ships a `Dockerfile` and `docker-compose.yml` at the root:

```bash
cp server/.env.example server/.env   # then edit with your provider + key
docker compose up --build
```

Open http://127.0.0.1:8000.

Notes:
- **Secrets never enter the image.** `server/.env` is excluded via `.dockerignore` and only reaches the container at *run* time via `env_file`.
- **Runs as a non-root user** (`askkevin`) inside the container.
- **A real `HEALTHCHECK`** hits `/` with stdlib `urllib` (no extra OS packages needed).

## Regenerating brand assets

If you edit the source SVG at [static/brand/favicon-source.svg](static/brand/favicon-source.svg), regenerate the derivatives from that single source so they never drift:

```bash
cd static/brand
rsvg-convert -w 512 -h 512 favicon-source.svg -o logo-512.png
rsvg-convert -w 180 -h 180 favicon-source.svg -o /tmp/touch-180.png
magick /tmp/touch-180.png -background white -alpha remove -alpha off ../apple-touch-icon.png
rsvg-convert -w 16 -h 16 favicon-source.svg -o /tmp/fav-16.png
rsvg-convert -w 32 -h 32 favicon-source.svg -o /tmp/fav-32.png
rsvg-convert -w 48 -h 48 favicon-source.svg -o /tmp/fav-48.png
magick /tmp/fav-16.png /tmp/fav-32.png /tmp/fav-48.png ../favicon.ico
```

Requires `rsvg-convert` and ImageMagick's `magick` (`brew install librsvg imagemagick`).
