"""
gitfold-proxy — the AI backend for gitfold.

Users call this server; the Featherless key never leaves your infra.

Endpoints:
  POST /generate/commit        → generate a commit message
  POST /generate/commit/regen  → regenerate with higher temperature
  POST /generate/pr            → generate a PR title + body
  GET  /health                 → liveness check

Deploy on Railway / Render / Fly.io, set FEATHERLESS_API_KEY in env vars,
and point GITFOLD_PROXY_URL in the package to your deployed URL.
"""

import os
import time
from typing import Optional

import openai
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ── Config ────────────────────────────────────────────────────────
FEATHERLESS_API_KEY = os.environ.get("FEATHERLESS_API_KEY", "")
MODEL = "meta-llama/Llama-3.3-70B-Instruct"
PROVIDER = "Featherless"

if not FEATHERLESS_API_KEY:
    raise RuntimeError(
        "FEATHERLESS_API_KEY environment variable is not set. "
        "Add it to your deployment environment."
    )

ai_client = openai.OpenAI(
    api_key=FEATHERLESS_API_KEY,
    base_url="https://api.featherless.ai/v1",
)

# ── Rate limiting (per IP) ────────────────────────────────────────
# 30 requests/minute per IP — generous for a CLI tool, blocks abuse
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="gitfold-proxy", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Request / Response models ──────────────────────────────────────
class CommitRequest(BaseModel):
    diff: str


class PRRequest(BaseModel):
    diff: str
    commit_message: str
    branch_name: str


class CommitResponse(BaseModel):
    message: str
    provider: str


class PRResponse(BaseModel):
    title: str
    body: str
    provider: str


# ── Helpers ───────────────────────────────────────────────────────
COMMIT_PROMPT = """You are an expert software engineer writing Git commit messages.
Based on the following git diff, write a clear, concise commit message.

Rules:
- Use conventional commit format: type(scope): short description
- Types: feat, fix, chore, refactor, docs, style, test
- Keep the first line under 72 characters
- Add a short bullet-point body if there are multiple changes
- Do NOT include any explanation or preamble — just the commit message

Git diff:
{diff}
"""

COMMIT_REGEN_PROMPT = """You are an expert software engineer writing Git commit messages.
Based on the following git diff, write a clear, concise commit message.

Rules:
- Use conventional commit format: type(scope): short description
- Types: feat, fix, chore, refactor, docs, style, test
- Keep the first line under 72 characters
- Add a short bullet-point body if there are multiple changes
- Do NOT include any explanation or preamble — just the commit message
- Write a DIFFERENT variation from what you might have written before

Git diff:
{diff}
"""

PR_PROMPT = """You are an expert software engineer writing a GitHub Pull Request description.

Branch: {branch_name}
Commit message: {commit_message}

Based on the git diff below, write a clear PR description with:
1. A short PR title (first line) — plain text only, no markdown, no asterisks, no bold
2. A blank line
3. A ## Summary section explaining what was changed and why
4. A ## Changes section with bullet points of key changes

Keep it professional and developer-friendly. No preamble — just the PR content.

Git diff:
{diff}
"""


def _call_ai(prompt: str, temperature: float, max_tokens: int = 300) -> str:
    """Call Featherless and return the full response string."""
    response = ai_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


# ── Routes ────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "provider": PROVIDER, "model": MODEL}


@app.post("/generate/commit", response_model=CommitResponse)
@limiter.limit("30/minute")
def generate_commit(body: CommitRequest, request: Request):
    if not body.diff or not body.diff.strip():
        return CommitResponse(message="chore: minor updates", provider=PROVIDER)
    try:
        prompt = COMMIT_PROMPT.format(diff=body.diff[:4000])
        message = _call_ai(prompt, temperature=0.4)
        return CommitResponse(message=message, provider=PROVIDER)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI call failed: {e}")


@app.post("/generate/commit/regen", response_model=CommitResponse)
@limiter.limit("30/minute")
def regenerate_commit(body: CommitRequest, request: Request):
    if not body.diff or not body.diff.strip():
        return CommitResponse(message="chore: minor updates", provider=PROVIDER)
    try:
        prompt = COMMIT_REGEN_PROMPT.format(diff=body.diff[:4000])
        message = _call_ai(prompt, temperature=0.7)
        return CommitResponse(message=message, provider=PROVIDER)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI call failed: {e}")


@app.post("/generate/pr", response_model=PRResponse)
@limiter.limit("30/minute")
def generate_pr(body: PRRequest, request: Request):
    if not body.diff or not body.diff.strip():
        return PRResponse(title="Minor updates", body="No significant changes detected.", provider=PROVIDER)
    try:
        prompt = PR_PROMPT.format(
            diff=body.diff[:4000],
            commit_message=body.commit_message,
            branch_name=body.branch_name,
        )
        full_response = _call_ai(prompt, temperature=0.4, max_tokens=500)

        lines = full_response.strip().split("\n")
        pr_title = lines[0].strip() if lines else body.commit_message
        pr_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

        # Strip markdown bold/italic from title
        for ch in ["**", "__", "*", "`"]:
            pr_title = pr_title.replace(ch, "")
        pr_title = pr_title.strip()

        return PRResponse(title=pr_title, body=pr_body, provider=PROVIDER)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI call failed: {e}")
