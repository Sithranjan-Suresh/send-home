"""One LLM function. Provider: Groq (OpenAI-compatible chat completions).

Model: openai/gpt-oss-120b, JSON mode supported, temperature 0.
"""
import json
import re
import time

import httpx

from . import config


class LLMError(Exception):
    """Provider returned an error or was unreachable."""


class LLMNotConfigured(LLMError):
    """No API key on the server."""


class LLMTimeout(LLMError):
    """Provider did not answer in time."""


class LLMRateLimited(LLMError):
    """Provider kept answering 429 (free-tier token limit)."""


class LLMBadOutput(Exception):
    """Provider answered, but not with usable JSON."""


_TRANSIENT = {408, 429, 500, 502, 503, 504}


def call_llm(system: str, user: str, json_mode: bool = True) -> str:
    """Send one chat completion. Falls back to other models if the main one is out of daily tokens."""
    if config.LLM_MOCK:
        from . import mock_llm

        return mock_llm.respond(system, user)
    if not config.LLM_API_KEY:
        raise LLMNotConfigured("no key")
    last: Exception | None = None
    for model in [config.LLM_MODEL, *config.LLM_FALLBACK_MODELS]:
        try:
            return _call_model(model, system, user, json_mode)
        except LLMRateLimited as e:  # daily/minute budget gone for this model: try the next one
            last = e
    raise last or LLMError("no model available")


def _call_model(model: str, system: str, user: str, json_mode: bool) -> str:
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if model.startswith("openai/gpt-oss"):
        payload["reasoning_effort"] = "low"  # fewer hidden tokens: Groq free tier is token-limited
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {config.LLM_API_KEY}"}
    url = config.LLM_BASE_URL.rstrip("/") + "/chat/completions"

    last: Exception | None = None
    for attempt in range(3):
        try:
            r = httpx.post(url, json=payload, headers=headers, timeout=config.LLM_TIMEOUT_S)
            if r.status_code == 429:
                try:
                    wait = float(r.headers.get("retry-after", "10"))
                except ValueError:
                    wait = 10.0
                if wait > 30:  # a daily limit, not worth waiting for
                    raise LLMRateLimited("rate limited")
                last = LLMRateLimited("rate limited")
                if attempt < 2:
                    time.sleep(wait + 1)
                continue
            if r.status_code in _TRANSIENT:
                last = LLMError(f"provider status {r.status_code}")
            elif r.status_code >= 400:
                raise LLMError(f"provider status {r.status_code}")
            else:
                return r.json()["choices"][0]["message"]["content"]
        except httpx.TimeoutException:
            last = LLMTimeout("provider timed out")
        except httpx.HTTPError:
            last = LLMError("could not reach provider")
        except (KeyError, IndexError, ValueError):
            raise LLMError("unexpected provider response")
        if attempt < 1:
            time.sleep(1)
    raise last or LLMError("unknown provider failure")


def parse_json_strict(raw: str) -> dict:
    """Parse model output as a JSON object; tolerate code fences only."""
    s = raw.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    try:
        obj = json.loads(s)
    except json.JSONDecodeError as e:
        raise LLMBadOutput("model did not return valid JSON") from e
    if not isinstance(obj, dict):
        raise LLMBadOutput("model JSON was not an object")
    return obj
