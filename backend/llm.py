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


class LLMTimeout(LLMError):
    """Provider did not answer in time."""


class LLMRateLimited(LLMError):
    """Provider kept answering 429 (free-tier token limit)."""


class LLMBadOutput(Exception):
    """Provider answered, but not with usable JSON."""


_TRANSIENT = {408, 429, 500, 502, 503, 504}


def call_llm(system: str, user: str, json_mode: bool = True) -> str:
    """Send one chat completion; retry once on transient failure."""
    if config.LLM_MOCK:
        from . import mock_llm

        return mock_llm.respond(system, user)
    config.require_key()
    payload = {
        "model": config.LLM_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if config.LLM_MODEL.startswith("openai/gpt-oss"):
        payload["reasoning_effort"] = "low"  # fewer hidden tokens: Groq free tier is token-limited
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {config.LLM_API_KEY}"}
    url = config.LLM_BASE_URL.rstrip("/") + "/chat/completions"

    last: Exception | None = None
    for attempt in range(3):
        try:
            r = httpx.post(url, json=payload, headers=headers, timeout=config.LLM_TIMEOUT_S)
            if r.status_code in _TRANSIENT:
                last = LLMError(f"provider status {r.status_code}")
                if r.status_code == 429:  # rate limited: wait as long as the provider asks
                    try:
                        wait = min(float(r.headers.get("retry-after", "10")), 30.0)
                    except ValueError:
                        wait = 10.0
                    if attempt < 2:
                        time.sleep(wait + 1)
                    continue
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
    if isinstance(last, LLMError) and "429" in str(last):
        raise LLMRateLimited("rate limited")
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
