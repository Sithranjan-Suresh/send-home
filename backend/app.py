"""FastAPI app: three stateless endpoints plus the static frontend."""
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import anakin, config, llm, service
from .report import build_report
from .schemas import (AnalyzeRequest, AnalyzeResponse, AskRequest, AskResponse,
                      TranslateRequest, TranslateResponse, VerifyRequest, VerifyResponse)

app = FastAPI(title="Sendhome", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=[config.ALLOWED_ORIGIN],
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

# Translate carries the whole analysis back, so it gets a larger body cap.
BODY_LIMITS = {"/api/translate": 64 * 1024, "/api/verify": 64 * 1024}
_hits: dict[str, deque] = defaultdict(deque)


def err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": message})


@app.middleware("http")
async def guard(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.method == "POST":
        limit = BODY_LIMITS.get(request.url.path, config.MAX_BODY_BYTES)
        length = request.headers.get("content-length")
        if length is None or not length.isdigit() or int(length) > limit:
            return err(413, "too_large", "That request is too large.")
        if config.RATE_LIMIT_PER_MIN:
            ip = request.client.host if request.client else "?"
            now = time.monotonic()
            q = _hits[ip]
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= config.RATE_LIMIT_PER_MIN:
                return err(429, "rate_limited", "Too many requests. Please wait a minute.")
            q.append(now)
    try:
        return await call_next(request)
    except Exception:  # never echo request content
        return err(500, "server_error", "Something went wrong on our side. Please try again.")


@app.exception_handler(service.UserError)
async def user_error(_: Request, e: service.UserError):
    return err(e.status, e.code, e.message)


@app.exception_handler(llm.LLMNotConfigured)
async def llm_nokey(_: Request, e):
    return err(503, "no_api_key", "This server has no AI key set, so only the built-in sample sheets work. "
                                  "Add LLM_API_KEY to .env to analyze your own text (see the README).")


@app.exception_handler(llm.LLMRateLimited)
async def llm_rate(_: Request, e):
    return err(429, "busy", "The AI is busy (free-tier limit). Wait about 20 seconds and press the button again.")


@app.exception_handler(llm.LLMTimeout)
async def llm_timeout(_: Request, e):
    return err(504, "timeout", "The AI took too long to answer. Please try again.")


@app.exception_handler(llm.LLMError)
async def llm_error(_: Request, e):
    return err(502, "llm_error", "The AI service had a problem. Please try again.")


@app.exception_handler(Exception)
async def anything(_: Request, e):
    return err(500, "server_error", "Something went wrong on our side. Please try again.")


@app.exception_handler(422)
async def bad_request(_: Request, e):
    return err(422, "bad_request", "That request wasn't formatted correctly.")


@app.on_event("startup")
def warm():
    import threading

    if config.WARM_SAMPLES and not config.LLM_MOCK and config.LLM_API_KEY:
        threading.Thread(target=service.warm_samples, daemon=True).start()


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/messages")
def messages():
    return {
        "refusal": config.REFUSAL_TEXT,
        "dose_missing": config.DOSE_MISSING_MSG,
        "quote_not_found": config.QUOTE_NOT_FOUND_MSG,
        "number_mismatch": config.NUMBER_MISMATCH_MSG,
        "max_chars": config.MAX_CHARS,
        "cache_meta": service.CACHE_META,
    }


@app.exception_handler(anakin.AnakinError)
async def anakin_error(_: Request, e):
    return err(502, "label_unavailable", "Couldn't reach the official label source right now. Please try again.")


@app.get("/api/label")
def label(name: str = ""):
    """Official label excerpt for one medicine name (only the name is sent to Anakin)."""
    if not anakin.valid_name(name):
        return err(400, "bad_name", "That doesn't look like a medicine name.")
    return anakin.lookup(name)


@app.get("/api/report")
def report():
    return build_report()


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    return service.analyze(req.text)


@app.post("/api/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest):
    return VerifyResponse(analysis=service.reverify(req.text, req.analysis))


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    return service.ask(req.text, req.question)


@app.post("/api/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    return service.translate(req.analysis, req.language)


ROOT = Path(__file__).resolve().parent.parent
app.mount("/samples", StaticFiles(directory=ROOT / "samples"), name="samples")
app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
