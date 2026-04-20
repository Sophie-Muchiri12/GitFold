import os
import openai
from dotenv import load_dotenv

load_dotenv()

# Supports both Groq and OpenAI — just set the right key in your .env
# For Groq:   GROQ_API_KEY=your_key_here
# For OpenAI: OPENAI_API_KEY=your_key_here

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if GROQ_API_KEY:
    client = openai.OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    MODEL = "llama-3.1-8b-instant"
elif OPENAI_API_KEY:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    MODEL = "gpt-4o"
else:
    raise Exception(
        "No AI API key found. Please set GROQ_API_KEY or OPENAI_API_KEY in your .env file."
    )


def generate_commit_message(diff: str) -> str:
    """
    Send the git diff to the AI and get back a meaningful commit message.
    Streams the response so the developer sees it being written in real time.
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

    print("\n🤖 Generating commit message...\n")

    full_message = ""

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
        full_message += token

    print("\n")
    return full_message.strip()


def generate_pr_description(diff: str, commit_message: str, branch_name: str):
    """
    Generate a pull request title and description based on the diff and commit message.
    Streams the response in real time.
    Returns a tuple of (pr_title, pr_body).
    """
    if not diff or diff.strip() == "":
        return "Minor updates", "No significant changes detected."

    prompt = f"""You are an expert software engineer writing a GitHub Pull Request description.

Branch: {branch_name}
Commit message: {commit_message}

Based on the git diff below, write a clear PR description with:
1. A short PR title (first line)
2. A blank line
3. A ## Summary section explaining what was changed and why
4. A ## Changes section with bullet points of key changes

Keep it professional and developer-friendly. No preamble — just the PR content.

Git diff:
{diff[:4000]}
"""

    print("\n🤖 Generating PR description...\n")

    full_response = ""

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
        full_response += token

    print("\n")

    lines = full_response.strip().split("\n")
    pr_title = lines[0].strip() if lines else commit_message
    pr_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    return pr_title, pr_body


def confirm_message(message: str, label: str = "commit message") -> str:
    """
    Show the generated message to the developer and ask for confirmation.
    They can accept it, edit it, or regenerate.
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