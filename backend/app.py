"""FastAPI app: three stateless endpoints plus the static frontend."""
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config, llm, service
from .report import build_report
from .schemas import (AnalyzeRequest, AnalyzeResponse, AskRequest, AskResponse,
                      TranslateRequest, TranslateResponse)

app = FastAPI(title="Sendhome", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=[config.ALLOWED_ORIGIN],
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

# Translate carries the whole analysis back, so it gets a larger body cap.
BODY_LIMITS = {"/api/translate": 64 * 1024}
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
    }


@app.get("/api/report")
def report():
    return build_report()


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    return service.analyze(req.text)


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    return service.ask(req.text, req.question)


@app.post("/api/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    return service.translate(req.analysis, req.language)


ROOT = Path(__file__).resolve().parent.parent
app.mount("/samples", StaticFiles(directory=ROOT / "samples"), name="samples")
app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
