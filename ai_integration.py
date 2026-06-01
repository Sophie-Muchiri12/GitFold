import os
import time
import openai
from dotenv import load_dotenv

load_dotenv()

# ── API Configuration ──────────────────────────────────────────────
# Gitfold supports Featherless, Groq, and OpenAI.
# Priority: Featherless → Groq → OpenAI
# Set the relevant key in your .env file.

FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if FEATHERLESS_API_KEY:
    client = openai.OpenAI(
        api_key=FEATHERLESS_API_KEY,
        base_url="https://api.featherless.ai/v1",
    )
    MODEL = "meta-llama/Llama-3.3-70B-Instruct"
    PROVIDER = "Featherless"

elif GROQ_API_KEY:
    client = openai.OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    MODEL = "llama-3.3-70b-versatile"
    PROVIDER = "Groq"

elif OPENAI_API_KEY:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    MODEL = "gpt-4o"
    PROVIDER = "OpenAI"

else:
    raise Exception(
        "\n  No AI API key found in your .env file.\n"
        "  Please add one of the following:\n"
        "    FEATHERLESS_API_KEY=your_key_here  (recommended — featherless.ai)\n"
        "    GROQ_API_KEY=your_key_here         (free — console.groq.com)\n"
        "    OPENAI_API_KEY=your_key_here       (platform.openai.com)\n"
    )


def generate_commit_message(diff: str) -> str:
    """
    Send the git diff to the AI and stream back a meaningful commit message.
    """
    if not diff or diff.strip() == "":
        return "chore: minor updates"

    prompt = f"""You are an expert software engineer writing Git commit messages.
Based on the following git diff, write a clear, concise commit message.

Rules:
- Use conventional commit format: type(scope): short description
- Types: feat, fix, chore, refactor, docs, style, test
- Keep the first line under 72 characters
- Add a short bullet-point body if there are multiple changes
- Do NOT include any explanation or preamble — just the commit message

Git diff:
{diff[:4000]}
"""

    print(f"\n🤖 Generating commit message via {PROVIDER}...\n")

    full_message = ""

    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=300,
            temperature=0.4,
        )

        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            print(token, end="", flush=True)
            time.sleep(0.03)
            full_message += token

        print("\n")
        return full_message.strip()

    except Exception as e:
        raise Exception(f"AI commit message generation failed: {e}")


def generate_commit_message_regenerate(diff: str) -> str:
    """
    Regenerate a commit message with higher temperature for more variety.
    """
    if not diff or diff.strip() == "":
        return "chore: minor updates"

    prompt = f"""You are an expert software engineer writing Git commit messages.
Based on the following git diff, write a clear, concise commit message.

Rules:
- Use conventional commit format: type(scope): short description
- Types: feat, fix, chore, refactor, docs, style, test
- Keep the first line under 72 characters
- Add a short bullet-point body if there are multiple changes
- Do NOT include any explanation or preamble — just the commit message
- Write a DIFFERENT variation from what you might have written before

Git diff:
{diff[:4000]}
"""

    print(f"\n🤖 Regenerating commit message via {PROVIDER}...\n")

    full_message = ""

    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=300,
            temperature=0.7,
        )

        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            print(token, end="", flush=True)
            time.sleep(0.03)
            full_message += token

        print("\n")
        return full_message.strip()

    except Exception as e:
        raise Exception(f"AI commit message regeneration failed: {e}")


def generate_pr_description(diff: str, commit_message: str, branch_name: str):
    """
    Generate a pull request title and description.
    Returns a tuple of (pr_title, pr_body).
    """
    if not diff or diff.strip() == "":
        return "Minor updates", "No significant changes detected."

    prompt = f"""You are an expert software engineer writing a GitHub Pull Request description.

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

    print(f"\n🤖 Generating PR description via {PROVIDER}...\n")

    full_response = ""

    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=500,
            temperature=0.4,
        )

        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            print(token, end="", flush=True)
            time.sleep(0.03)
            full_response += token

        print("\n")

        lines = full_response.strip().split("\n")
        pr_title = lines[0].strip() if lines else commit_message
        pr_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

        # Strip any markdown formatting from title
        pr_title = pr_title.replace("**", "").replace("__", "").replace("*", "").replace("`", "").strip()

        return pr_title, pr_body

    except Exception as e:
        raise Exception(f"PR description generation failed: {e}")


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