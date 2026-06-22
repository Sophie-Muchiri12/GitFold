import os
import sys
import time
import requests
import openai
from config_manager import load_env

load_env()

# ── AI Configuration ───────────────────────────────────────────────
# Priority: local Groq key → hosted backend
# Users with GROQ_API_KEY in .env call Groq directly.
# Everyone else uses the hosted backend (no key required).

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

GITFOLD_BACKEND_URL = os.getenv(
    "GITFOLD_BACKEND_URL",
    "https://gitfold-production.up.railway.app",
)

_client = None
_MODEL = None
_PROVIDER = None


def _use_local() -> bool:
    return bool(GROQ_API_KEY or FEATHERLESS_API_KEY or OPENAI_API_KEY)


def _init_local_client():
    global _client, _MODEL, _PROVIDER
    if _client is not None:
        return

    if GROQ_API_KEY:
        _client = openai.OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        _MODEL = "llama-3.3-70b-versatile"
        _PROVIDER = "Groq"
    elif FEATHERLESS_API_KEY:
        _client = openai.OpenAI(
            api_key=FEATHERLESS_API_KEY,
            base_url="https://api.featherless.ai/v1",
        )
        _MODEL = "meta-llama/Llama-3.3-70B-Instruct"
        _PROVIDER = "Featherless"
    elif OPENAI_API_KEY:
        _client = openai.OpenAI(api_key=OPENAI_API_KEY)
        _MODEL = "gpt-4o"
        _PROVIDER = "OpenAI"


def _stream_local(prompt: str, temperature: float, max_tokens: int) -> str:
    _init_local_client()
    print(f"\n🤖 Generating via {_PROVIDER}...\n")

    full_text = ""
    stream = _client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        sys.stdout.write(token)
        sys.stdout.flush()
        time.sleep(0.03)
        full_text += token

    print("\n")
    return full_text.strip()


def _stream_backend(endpoint: str, payload: dict, label: str = "Generating") -> str:
    print(f"\n🤖 {label}...\n")

    full_text = ""
    response = requests.post(
        f"{GITFOLD_BACKEND_URL}{endpoint}",
        json=payload,
        stream=True,
        timeout=30,
    )

    if response.status_code != 200:
        raise Exception(f"Backend error {response.status_code}: {response.text}")

    for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
        if chunk:
            sys.stdout.write(chunk)
            sys.stdout.flush()
            time.sleep(0.03)
            full_text += chunk

    print("\n")
    return full_text.strip()


def _commit_prompt(diff: str, regenerate: bool = False) -> str:
    return f"""You are an expert software engineer writing Git commit messages.
Based on the following git diff, write a clear, concise commit message.

Rules:
- Use conventional commit format: type(scope): short description
- Types: feat, fix, chore, refactor, docs, style, test
- Keep the first line under 72 characters
- Add a short bullet-point body if there are multiple changes
- Do NOT include any explanation or preamble — just the commit message
{"- Write a DIFFERENT variation from what you might have written before" if regenerate else ""}

Git diff:
{diff[:4000]}
"""


def _pr_prompt(diff: str, commit_message: str, branch_name: str) -> str:
    return f"""You are an expert software engineer writing a GitHub Pull Request description.

Branch: {branch_name}
Commit message: {commit_message}

Based on the git diff below, write a clear PR description with:
1. A short PR title (first line) — plain text only, no markdown, no asterisks, no bold
2. A blank line
3. A ## Summary section explaining what was changed and why
4. A ## Changes section with bullet points of key changes

Keep it professional and developer-friendly. No preamble — just the PR content.

Git diff:
{diff[:4000]}
"""


def generate_commit_message(diff: str) -> str:
    if not diff or diff.strip() == "":
        return "chore: minor updates"

    try:
        if _use_local():
            return _stream_local(_commit_prompt(diff), temperature=0.4, max_tokens=300)
        return _stream_backend(
            "/generate/commit",
            {"diff": diff[:4000], "regenerate": False},
            label="Generating commit message",
        )
    except requests.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Gitfold backend.\n"
            "  Check your internet connection and try again.\n"
            "  Or add GROQ_API_KEY to your .env (free at console.groq.com)."
        )
    except requests.exceptions.Timeout:
        raise Exception("Gitfold backend timed out. Please try again in a moment.")
    except Exception as e:
        raise Exception(f"Commit message generation failed: {e}")


def generate_commit_message_regenerate(diff: str) -> str:
    if not diff or diff.strip() == "":
        return "chore: minor updates"

    try:
        if _use_local():
            return _stream_local(_commit_prompt(diff, regenerate=True), temperature=0.7, max_tokens=300)
        return _stream_backend(
            "/generate/commit",
            {"diff": diff[:4000], "regenerate": True},
            label="Regenerating commit message",
        )
    except requests.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Gitfold backend.\n"
            "  Check your internet connection and try again."
        )
    except Exception as e:
        raise Exception(f"Commit message regeneration failed: {e}")


def generate_pr_description(diff: str, commit_message: str, branch_name: str):
    if not diff or diff.strip() == "":
        return "Minor updates", "No significant changes detected."

    try:
        if _use_local():
            full_response = _stream_local(
                _pr_prompt(diff, commit_message, branch_name),
                temperature=0.4,
                max_tokens=500,
            )
        else:
            full_response = _stream_backend(
                "/generate/pr",
                {
                    "diff": diff[:4000],
                    "commit_message": commit_message,
                    "branch_name": branch_name,
                },
                label="Generating PR description",
            )

        lines = full_response.strip().split("\n")
        pr_title = lines[0].strip() if lines else commit_message
        pr_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        pr_title = pr_title.replace("**", "").replace("__", "").replace("*", "").replace("`", "").strip()
        return pr_title, pr_body

    except requests.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Gitfold backend.\n"
            "  Check your internet connection and try again."
        )
    except Exception as e:
        raise Exception(f"PR description generation failed: {e}")


def confirm_message(message: str, label: str = "commit message") -> str:
    print(f"\n--- Accept the {label} above? ---")

    while True:
        choice = input(
            f"\nAccept this {label}? [y]es / [e]dit / [r]egenerate: "
        ).strip().lower()

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
            return None

        else:
            print("Please enter y, e, or r.")
