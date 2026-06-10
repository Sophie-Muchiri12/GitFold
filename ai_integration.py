import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Backend Configuration ──────────────────────────────────────────
# Gitfold uses a hosted AI backend so users don't need their own API keys.
# The backend handles all AI calls securely.

GITFOLD_BACKEND_URL = os.getenv(
    "GITFOLD_BACKEND_URL",
    "https://gitfold-production.up.railway.app"
)


def generate_commit_message(diff: str) -> str:
    """
    Send the git diff to the Gitfold backend and stream back
    a meaningful commit message.
    """
    if not diff or diff.strip() == "":
        return "chore: minor updates"

    print("\n🤖 Generating commit message...\n")

    full_message = ""

    try:
        response = requests.post(
            f"{GITFOLD_BACKEND_URL}/generate/commit",
            json={"diff": diff[:4000], "regenerate": False},
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
                full_message += chunk

        print("\n")
        return full_message.strip()

    except requests.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Gitfold backend.\n"
            "  Check your internet connection and try again."
        )
    except requests.exceptions.Timeout:
        raise Exception(
            "Gitfold backend timed out.\n"
            "  Please try again in a moment."
        )
    except Exception as e:
        raise Exception(f"Commit message generation failed: {e}")


def generate_commit_message_regenerate(diff: str) -> str:
    """
    Regenerate a commit message with higher temperature for more variety.
    """
    if not diff or diff.strip() == "":
        return "chore: minor updates"

    print("\n🤖 Regenerating commit message...\n")

    full_message = ""

    try:
        response = requests.post(
            f"{GITFOLD_BACKEND_URL}/generate/commit",
            json={"diff": diff[:4000], "regenerate": True},
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
                full_message += chunk

        print("\n")
        return full_message.strip()

    except requests.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Gitfold backend.\n"
            "  Check your internet connection and try again."
        )
    except Exception as e:
        raise Exception(f"Commit message regeneration failed: {e}")


def generate_pr_description(diff: str, commit_message: str, branch_name: str):
    """
    Generate a pull request title and description via the Gitfold backend.
    Returns a tuple of (pr_title, pr_body).
    """
    if not diff or diff.strip() == "":
        return "Minor updates", "No significant changes detected."

    print("\n🤖 Generating PR description...\n")

    full_response = ""

    try:
        response = requests.post(
            f"{GITFOLD_BACKEND_URL}/generate/pr",
            json={
                "diff": diff[:4000],
                "commit_message": commit_message,
                "branch_name": branch_name,
            },
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
                full_response += chunk

        print("\n")

        lines = full_response.strip().split("\n")
        pr_title = lines[0].strip() if lines else commit_message
        pr_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

        # Strip any markdown formatting from title
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
    """
    Show the generated message and ask for confirmation.
    Returns the final approved message or None to signal regeneration.
    """
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
            return None  # Signal to caller to regenerate

        else:
            print("Please enter y, e, or r.")