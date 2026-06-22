from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Gitfold AI Backend", version="1.0.0")

# ── AI Client (Groq by default) ────────────────────────────────────
FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    client = openai.OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    MODEL = "llama-3.3-70b-versatile"
    PROVIDER = "Groq"
elif FEATHERLESS_API_KEY:
    client = openai.OpenAI(
        api_key=FEATHERLESS_API_KEY,
        base_url="https://api.featherless.ai/v1",
    )
    MODEL = "meta-llama/Llama-3.3-70B-Instruct"
    PROVIDER = "Featherless"
else:
    raise RuntimeError(
        "No AI API key found. Set GROQ_API_KEY or FEATHERLESS_API_KEY in your environment."
    )


# ── Request Models ─────────────────────────────────────────────────
class CommitRequest(BaseModel):
    diff: str
    regenerate: bool = False


class PRRequest(BaseModel):
    diff: str
    commit_message: str
    branch_name: str


# ── Health Check ───────────────────────────────────────────────────
@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Gitfold AI Backend",
        "provider": PROVIDER,
        "model": MODEL,
    }


# ── Commit Message Endpoint ────────────────────────────────────────
@app.post("/generate/commit")
def generate_commit(request: CommitRequest):
    """
    Generate an AI commit message from a git diff.
    Streams the response token by token.
    """
    if not request.diff or request.diff.strip() == "":
        return {"message": "chore: minor updates"}

    temperature = 0.7 if request.regenerate else 0.4

    prompt = f"""You are an expert software engineer writing Git commit messages.
Based on the following git diff, write a clear, concise commit message.

Rules:
- Use conventional commit format: type(scope): short description
- Types: feat, fix, chore, refactor, docs, style, test
- Keep the first line under 72 characters
- Add a short bullet-point body if there are multiple changes
- Do NOT include any explanation or preamble — just the commit message
{"- Write a DIFFERENT variation from what you might have written before" if request.regenerate else ""}

Git diff:
{request.diff[:4000]}
"""

    def stream_response():
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=300,
            temperature=temperature,
        )
        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            yield token

    return StreamingResponse(stream_response(), media_type="text/plain")


# ── PR Description Endpoint ────────────────────────────────────────
@app.post("/generate/pr")
def generate_pr(request: PRRequest):
    """
    Generate an AI PR title and description from a git diff.
    Streams the response token by token.
    """
    if not request.diff or request.diff.strip() == "":
        return {"title": "Minor updates", "body": "No significant changes detected."}

    prompt = f"""You are an expert software engineer writing a GitHub Pull Request description.

Branch: {request.branch_name}
Commit message: {request.commit_message}

Based on the git diff below, write a clear PR description with:
1. A short PR title (first line) — plain text only, no markdown, no asterisks, no bold
2. A blank line
3. A ## Summary section explaining what was changed and why
4. A ## Changes section with bullet points of key changes

Keep it professional and developer-friendly. No preamble — just the PR content.

Git diff:
{request.diff[:4000]}
"""

    def stream_response():
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=500,
            temperature=0.4,
        )
        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            yield token

    return StreamingResponse(stream_response(), media_type="text/plain") 