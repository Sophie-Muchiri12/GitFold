import os
import json
from pathlib import Path

CONFIG_FILE_NAME = ".gitfold.json"


def get_config_path():
    """Find the config file in the current repo root or home directory."""
    # Check current directory and parent directories
    current = Path.cwd()
    for parent in [current, *current.parents]:
        config_path = parent / CONFIG_FILE_NAME
        if config_path.exists():
            return config_path

    # Fall back to home directory
    return Path.home() / CONFIG_FILE_NAME


def load_config() -> dict:
    """Load the Gitfold config file. Returns an empty dict if none exists."""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    """Save the config to the nearest config file location."""
    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"✔ Config saved to {config_path}")


def get_default_branch(config: dict, detected: str = None) -> str:
    """
    Return the configured default branch.
    Falls back to detected branch or 'main'.
    """
    return config.get("default_branch") or detected or "main"


def get_dev_branch(config: dict, detected: str = None):
    """
    Return the configured dev branch.
    Falls back to detected branch or None if not set.
    """
    return config.get("dev_branch") or detected or None


def setup_config_interactive(branch_info: dict) -> dict:
    """
    Run an interactive first-time setup to configure Gitfold.
    Called when no config file is found.
    """
    print("\n⚙️  Welcome to Gitfold! Let's set up your config.\n")

    config = {}

    # Default branch
    detected_default = branch_info.get("default", "main")
    answer = input(
        f"What is your default branch? (detected: '{detected_default}', press Enter to confirm): "
    ).strip()
    config["default_branch"] = answer if answer else detected_default

    # Dev branch
    detected_dev = branch_info.get("dev")
    if detected_dev:
        answer = input(
            f"Development branch detected as '{detected_dev}'. Use this? [y/n]: "
        ).strip().lower()
        config["dev_branch"] = detected_dev if answer != "n" else None
    else:
        answer = input(
            "Do you have a development branch (e.g. dev, develop)? Enter name or leave blank: "
        ).strip()
        config["dev_branch"] = answer if answer else None

    # Auto-push preference
    answer = input("Auto-push to remote after commit? [y/n] (default: y): ").strip().lower()
    config["auto_push"] = answer != "n"

    # Auto PR preference
    answer = input("Auto-open PR in browser after push? [y/n] (default: y): ").strip().lower()
    config["auto_pr"] = answer != "n"

    # GitHub username (optional, helps build PR URLs)
    answer = input("Your GitHub username (optional, press Enter to skip): ").strip()
    config["github_username"] = answer if answer else None

    save_config(config)
    print("\n✔ Config ready. You can edit it anytime in .gitfold.json\n")

    return config


def ensure_config(branch_info: dict) -> dict:
    """
    Load existing config or run first-time interactive setup.
    Always returns a valid config dict.
    """
    config = load_config()
    if not config:
        config = setup_config_interactive(branch_info)
    return config


def get_auto_push(config: dict) -> bool:
    """Whether to auto-push after commit."""
    return config.get("auto_push", True)


def get_auto_pr(config: dict) -> bool:
    """Whether to auto-open PR in browser after push."""
    return config.get("auto_pr", True)