import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Proxy Configuration ────────────────────────────────────────────
# gitfold calls your hosted proxy server so no API key is ever bundled
# in the package or stored on the user's machine.
#
# The default URL points to your production proxy.
# Users can override it with GITFOLD_PROXY_URL in their .env if they
# want to self-host, or if they prefer to use their own key directly
# (see "Bring-your-own-key" fallback below).
#
# After deploying the proxy server, replace the default URL here and
# republish to PyPI:
PROXY_BASE_URL = os.getenv(
    "GITFOLD_PROXY_URL",
    "https://gitfold-proxy.onrender.com",  # ← replace with your deployed URL
).rstrip("/")

# ── Bring-your-own-key fallback (optional for power users) ────────
# If the user supplies their own key, gitfold calls the AI provider
# directly — useful for teams with higher rate-limit needs.
import openai as _openai

_FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
_GROQ_API_KEY = os.getenv("GROQ_API_KEY")
_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

_client = None
_MODEL = None
_PROVIDER = None

def _use_proxy() -> bool:
    """True when no personal key is configured → route through the proxy."""
    return not (_FEATHERLESS_API_KEY or _GROQ_API_KEY or _OPENAI_API_KEY)


def _init_byo_client():
    """Lazily initialise a direct AI client when the user supplies their own key."""
    global _client, _MODEL, _PROVIDER
    if _client is not None:
        return
    if _FEATHERLESS_API_KEY:
        _client = _openai.OpenAI(
            api_key=_FEATHERLESS_API_KEY,
            base_url="https://api.featherless.ai/v1",
        )
        _MODEL = "meta-llama/Llama-3.3-70B-Instruct"
        _PROVIDER = "Featherless (your key)"
    elif _GROQ_API_KEY:
        _client = _openai.OpenAI(
            api_key=_GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        _MODEL = "llama-3.1-8b-instant"
        _PROVIDER = "Groq (your key)"
    elif _OPENAI_API_KEY:
        _client = _openai.OpenAI(api_key=_OPENAI_API_KEY)
        _MODEL = "gpt-4o"
        _PROVIDER = "OpenAI (your key)"


# ── Proxy helpers ─────────────────────────────────────────────────
def _proxy_post(endpoint: str, payload: dict) -> dict:
    """POST to the proxy and return parsed JSON. Raises on network/server error."""
    url = f"{PROXY_BASE_URL}{endpoint}"
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        raise Exception(
            f"\n  Could not reach the gitfold AI server ({PROXY_BASE_URL}).\n"
            "  Check your internet connection and try again.\n"
            "  Or add your own API key to .env to use it directly:\n"
            "    FEATHERLESS_API_KEY=your_key_here\n"
        )
    except requests.exceptions.Timeout:
        raise Exception(
            "\n  The gitfold AI server timed out.\n"
            "  It may be starting up (cold start) — wait a few seconds and retry.\n"
        )
    except requests.exceptions.HTTPError as e:
        detail = ""
        try:
            detail = resp.json().get("detail", "")
        except Exception:
            pass
        raise Exception(f"\n  AI server returned an error: {e}\n  {detail}\n")


def _stream_text(text: str):
    """Print text token by token to simulate streaming for UX consistency."""
    for char in text:
        print(char, end="", flush=True)
        time.sleep(0.012)
    print("\n")


# ── BYO-key direct call helpers ────────────────────────────────────
def _byo_stream(prompt: str, temperature: float, max_tokens: int = 300) -> str:
    _init_byo_client()
    full_message = ""
    stream = _client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        print(token, end="", flush=True)
        time.sleep(0.03)
        full_message += token
    print("\n")
    return full_message.strip()


# ── Public API ────────────────────────────────────────────────────
def generate_commit_message(diff: str) -> str:
    """Send the git diff and stream back a meaningful commit message."""
    if not diff or diff.strip() == "":
        return "chore: minor updates"

    if _use_proxy():
        print("\n🤖 Generating commit message...\n")
        data = _proxy_post("/generate/commit", {"diff": diff})
        _stream_text(data["message"])
        return data["message"]
    else:
        prompt = (
            "You are an expert software engineer writing Git commit messages.\n"
            "Based on the following git diff, write a clear, concise commit message.\n\n"
            "Rules:\n"
            "- Use conventional commit format: type(scope): short description\n"
            "- Types: feat, fix, chore, refactor, docs, style, test\n"
            "- Keep the first line under 72 characters\n"
            "- Add a short bullet-point body if there are multiple changes\n"
            "- Do NOT include any explanation or preamble — just the commit message\n\n"
            f"Git diff:\n{diff[:4000]}\n"
        )
        print(f"\n🤖 Generating commit message via {_PROVIDER}...\n")
        try:
            return _byo_stream(prompt, temperature=0.4)
        except Exception as e:
            raise Exception(f"AI commit message generation failed: {e}")


def generate_commit_message_regenerate(diff: str) -> str:
    """Regenerate a commit message with higher temperature for more variety."""
    if not diff or diff.strip() == "":
        return "chore: minor updates"

    if _use_proxy():
        print("\n🤖 Regenerating commit message...\n")
        data = _proxy_post("/generate/commit/regen", {"diff": diff})
        _stream_text(data["message"])
        return data["message"]
    else:
        prompt = (
            "You are an expert software engineer writing Git commit messages.\n"
            "Based on the following git diff, write a clear, concise commit message.\n\n"
            "Rules:\n"
            "- Use conventional commit format: type(scope): short description\n"
            "- Types: feat, fix, chore, refactor, docs, style, test\n"
            "- Keep the first line under 72 characters\n"
            "- Add a short bullet-point body if there are multiple changes\n"
            "- Do NOT include any explanation or preamble — just the commit message\n"
            "- Write a DIFFERENT variation from what you might have written before\n\n"
            f"Git diff:\n{diff[:4000]}\n"
        )
        print(f"\n🤖 Regenerating commit message via {_PROVIDER}...\n")
        try:
            return _byo_stream(prompt, temperature=0.7)
        except Exception as e:
            raise Exception(f"AI commit message regeneration failed: {e}")


def generate_pr_description(diff: str, commit_message: str, branch_name: str):
    """
    Generate a pull request title and description.
    Returns a tuple of (pr_title, pr_body).
    """
    if not diff or diff.strip() == "":
        return "Minor updates", "No significant changes detected."

    if _use_proxy():
        print("\n🤖 Generating PR description...\n")
        data = _proxy_post("/generate/pr", {
            "diff": diff,
            "commit_message": commit_message,
            "branch_name": branch_name,
        })
        full_response = f"{data['title']}\n\n{data['body']}"
        _stream_text(full_response)
        return data["title"], data["body"]
    else:
        prompt = (
            "You are an expert software engineer writing a GitHub Pull Request description.\n\n"
            f"Branch: {branch_name}\n"
            f"Commit message: {commit_message}\n\n"
            "Based on the git diff below, write a clear PR description with:\n"
            "1. A short PR title (first line) — plain text only, no markdown, no asterisks, no bold\n"
            "2. A blank line\n"
            "3. A ## Summary section explaining what was changed and why\n"
            "4. A ## Changes section with bullet points of key changes\n\n"
            "Keep it professional and developer-friendly. No preamble — just the PR content.\n\n"
            f"Git diff:\n{diff[:4000]}\n"
        )
        print(f"\n🤖 Generating PR description via {_PROVIDER}...\n")
        try:
            full_response = _byo_stream(prompt, temperature=0.4, max_tokens=500)
        except Exception as e:
            raise Exception(f"PR description generation failed: {e}")

        lines = full_response.strip().split("\n")
        pr_title = lines[0].strip() if lines else commit_message
        pr_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

        for ch in ["**", "__", "*", "`"]:
            pr_title = pr_title.replace(ch, "")
        pr_title = pr_title.strip()

        return pr_title, pr_body


def confirm_message(message: str, label: str = "commit message") -> str:
    """
    Show the generated message and ask for confirmation.
    Returns the final approved message or None to signal regeneration.
    """
    print(f"\n--- Accept the {label} above? ---")

    while True:
        choice = input(f"\nAccept this {label}? [y]es / [e]dit / [r]egenerate: ").strip().lower()

        if choice == "y" or choice == "":
            return message

        elif choice == "e":
            print(f"Enter your {label} (press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            return "\n".join(lines).strip()

        elif choice == "r":
            return None  # Signal to caller to regenerate

        else:
            print("Please enter y, e, or r.")
