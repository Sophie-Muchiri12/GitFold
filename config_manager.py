import os
import json
import time
import sys
from pathlib import Path

CONFIG_FILE_NAME = ".gitfold.json"
ENV_FILE_NAME = ".env"

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _stream(text: str, delay: float = 0.018, color: str = ""):
    """Stream print text character by character."""
    for char in text:
        sys.stdout.write(f"{color}{char}{RESET if color else ''}")
        sys.stdout.flush()
        time.sleep(delay)
    print()


def get_config_path():
    """Find the config file starting from current directory up to home."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        config_path = parent / CONFIG_FILE_NAME
        if config_path.exists():
            return config_path
    return Path.cwd() / CONFIG_FILE_NAME


def get_env_path():
    """Return the .env path in the current working directory."""
    return Path.cwd() / ENV_FILE_NAME


def load_config() -> dict:
    """Load the Gitfold config file. Returns empty dict if none exists."""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    """Save config to the current directory."""
    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def env_has_github_token() -> bool:
    """Check if a GitHub token exists in the .env file."""
    env_path = get_env_path()
    if not env_path.exists():
        return False
    with open(env_path, "r") as f:
        content = f.read()
    return "GITHUB_TOKEN=" in content and len(
        content.split("GITHUB_TOKEN=")[-1].strip()
    ) > 10


def save_github_token(github_token: str):
    """Save the GitHub token to the .env file."""
    env_path = get_env_path()

    existing = ""
    if env_path.exists():
        with open(env_path, "r") as f:
            existing = f.read()

    if "GITHUB_TOKEN=" not in existing:
        with open(env_path, "a") as f:
            f.write(f"\nGITHUB_TOKEN={github_token}\n")
    else:
        # Replace existing token
        lines = existing.splitlines()
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("GITHUB_TOKEN="):
                    f.write(f"GITHUB_TOKEN={github_token}\n")
                else:
                    f.write(f"{line}\n")

    ensure_gitignore()


def ensure_gitignore():
    """Make sure .env and .gitfold.json are in .gitignore."""
    gitignore_path = Path.cwd() / ".gitignore"
    entries = [".env", ".gitfold.json"]

    existing = ""
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            existing = f.read()

    with open(gitignore_path, "a") as f:
        for entry in entries:
            if entry not in existing:
                f.write(f"\n{entry}")


def first_time_setup(branch_info: dict) -> dict:
    """
    First time setup for new Gitfold users.
    Only asks for GitHub token and branch preferences.
    The AI is handled by Gitfold's backend — no API keys needed.
    """
    time.sleep(0.2)
    print(f"\n{BOLD}{CYAN}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    _stream("  Welcome to Gitfold! Looks like it's your first time.", delay=0.025, color=f"{BOLD}{GREEN}")
    _stream("  Let's get you set up — it only takes a minute.", delay=0.02, color=DIM)
    print(f"{DIM}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")
    time.sleep(0.3)

    config = {}

    # ── Step 1: GitHub Token ───────────────────────────────────────
    _stream("  Step 1 of 2 — GitHub Token", delay=0.02, color=f"{BOLD}{YELLOW}")
    time.sleep(0.1)
    _stream("  Gitfold needs a GitHub token to create pull requests", delay=0.018, color=DIM)
    _stream("  on your behalf. Here's how to get one:\n", delay=0.018, color=DIM)
    _stream("  1. Go to github.com → Settings", delay=0.015)
    _stream("  2. Scroll down → Developer settings", delay=0.015)
    _stream("  3. Personal access tokens → Tokens (classic)", delay=0.015)
    _stream("  4. Click 'Generate new token (classic)'", delay=0.015)
    _stream("  5. Give it a name e.g. 'gitfold'", delay=0.015)
    _stream("  6. Tick 'repo' and 'read:user' scopes", delay=0.015)
    _stream("  7. Click Generate token and copy it\n", delay=0.015)

    while True:
        github_token = input(f"  {YELLOW}Paste your GitHub token:{RESET} ").strip()
        if github_token:
            break
        _stream("  GitHub token is required to use Gitfold.", delay=0.018, color=YELLOW)
        retry = input("  Try again? [y/n]: ").strip().lower()
        if retry != "y":
            _stream("  Skipping for now. You can add it to your .env file later.", delay=0.018, color=DIM)
            _stream("  Note: PR creation will be unavailable until you add it.", delay=0.018, color=DIM)
            github_token = ""
            break

    if github_token:
        save_github_token(github_token)
        print()
        _stream("  ✔ GitHub token saved to .env", delay=0.018, color=GREEN)
        _stream("  ✔ .env added to .gitignore — your token is safe.", delay=0.018, color=GREEN)

    # ── Step 2: Branch Config ──────────────────────────────────────
    print()
    time.sleep(0.2)
    _stream("  Step 2 of 2 — Branch Setup", delay=0.02, color=f"{BOLD}{YELLOW}")
    time.sleep(0.1)

    detected_default = branch_info.get("default", "main")
    detected_dev = branch_info.get("dev")

    _stream(f"  Detected default branch: {detected_default}", delay=0.018, color=DIM)
    answer = input(
        f"\n  Use '{detected_default}' as your default branch? [y/n] (default: y): "
    ).strip().lower()
    config["default_branch"] = detected_default if answer != "n" else input(
        "  Enter your default branch name: "
    ).strip()

    if detected_dev:
        _stream(f"\n  Detected dev branch: {detected_dev}", delay=0.018, color=DIM)
        answer = input(
            f"  Use '{detected_dev}' as your dev branch? [y/n] (default: y): "
        ).strip().lower()
        config["dev_branch"] = detected_dev if answer != "n" else None
    else:
        answer = input(
            "\n  Do you have a dev branch? Enter its name or press Enter to skip: "
        ).strip()
        config["dev_branch"] = answer if answer else None

    print()
    answer = input("  Auto-push after commit? [y/n] (default: y): ").strip().lower()
    config["auto_push"] = answer != "n"

    answer = input("  Auto-open PR in browser after push? [y/n] (default: y): ").strip().lower()
    config["auto_pr"] = answer != "n"

    # Save config
    save_config(config)
    ensure_gitignore()

    # Done
    print()
    time.sleep(0.2)
    print(f"{BOLD}{CYAN}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    _stream("  ✔ All set! Gitfold is ready to go.", delay=0.025, color=f"{BOLD}{GREEN}")
    _stream("  Running your workflow now...", delay=0.02, color=DIM)
    print(f"{DIM}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")
    time.sleep(0.5)

    return config


def ensure_config(branch_info: dict) -> dict:
    """
    Load existing config or run first time setup.
    Always returns a valid config dict.
    """
    config = load_config()
    if not config:
        config = first_time_setup(branch_info)
    return config


def get_default_branch(config: dict, detected: str = None) -> str:
    return config.get("default_branch") or detected or "main"


def get_dev_branch(config: dict, detected: str = None):
    return config.get("dev_branch") or detected or None


def get_auto_push(config: dict) -> bool:
    return config.get("auto_push", True)


def get_auto_pr(config: dict) -> bool:
    return config.get("auto_pr", True)