import time
import sys
from datetime import datetime


# ANSI color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
CHECKMARK = "✔"
CROSS = "✘"
ARROW = "→"
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def _stream_print(text: str, delay: float = 0.018, color: str = ""):
    """Print text character by character to simulate a streaming effect."""
    for char in text:
        sys.stdout.write(f"{color}{char}{RESET if color else ''}")
        sys.stdout.flush()
        time.sleep(delay)
    print()


def header():
    """Print the Gitfold welcome banner with streaming effect."""
    time.sleep(0.3)
    print(f"\n{BOLD}{GREEN}")
    banner_lines = [
        "  ██████╗ ██╗████████╗",
        " ██╔════╝ ██║╚══██╔══╝",
        " ██║  ███╗██║   ██║   ",
        " ██║   ██║██║   ██║   ",
        " ╚██████╔╝██║   ██║   ",
        "  ╚═════╝ ╚═╝   ╚═╝   ",
    ]
    for line in banner_lines:
        print(line)
        time.sleep(0.05)

    print(f"{RESET}{BOLD}{CYAN}")
    fold_lines = [
        " ███████╗ ██████╗ ██╗     ██████╗ ",
        " ██╔════╝██╔═══██╗██║     ██╔══██╗",
        " █████╗  ██║   ██║██║     ██║  ██║",
        " ██╔══╝  ██║   ██║██║     ██║  ██║",
        " ██║     ╚██████╔╝███████╗██████╔╝",
        " ╚═╝      ╚═════╝ ╚══════╝╚═════╝ ",
    ]
    for line in fold_lines:
        print(line)
        time.sleep(0.05)

    print(f"{RESET}")
    time.sleep(0.1)
    _stream_print("  ◈ fold it. commit it. ship it. ◈", delay=0.03, color=f"{GREEN}{BOLD}")
    time.sleep(0.1)
    print(f"{DIM}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{DIM}  v0.1.0  ·  AI-powered git workflow  ·  open source{RESET}")
    print(f"{DIM}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    time.sleep(0.2)

    # Onboarding instructions
    print(f"\n{BOLD}  How to use Gitfold:{RESET}")
    time.sleep(0.1)
    instructions = [
        f"  {GREEN}›{RESET} Run {BOLD}gitfold{RESET}          — fully automated mode",
        f"  {YELLOW}›{RESET} Run {BOLD}gitfold --manual{RESET}  — confirm each step yourself",
        f"  {CYAN}›{RESET} Run {BOLD}gitfold --no-push{RESET} — commit only, skip push & PR",
        f"  {CYAN}›{RESET} Run {BOLD}gitfold --no-pr{RESET}   — push but skip PR creation",
        f"  {DIM}›  Press Ctrl+C at any time to pause and switch to manual mode{RESET}",
    ]
    for line in instructions:
        print(line)
        time.sleep(0.08)

    print(f"{DIM}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")
    time.sleep(0.3)


def step(message: str):
    """Print a step in the workflow with a slight delay."""
    time.sleep(0.1)
    print(f"{CYAN}{ARROW}{RESET} {message}")


def success(message: str):
    """Print a success message."""
    time.sleep(0.05)
    print(f"{GREEN}{CHECKMARK}{RESET} {message}")


def warning(message: str):
    """Print a warning message."""
    print(f"{YELLOW}⚠️   {message}{RESET}")


def error(message: str):
    """Print an error message."""
    print(f"{RED}{CROSS} Error: {message}{RESET}")


def info(message: str):
    """Print a neutral info message."""
    print(f"{DIM}  {message}{RESET}")


def divider():
    """Print a visual divider line."""
    print(f"{DIM}  {'─' * 50}{RESET}")


def section(title: str):
    """Print a section header with a short pause to let users follow along."""
    time.sleep(0.3)
    print(f"\n{BOLD}[ {title} ]{RESET}")
    divider()
    time.sleep(0.1)


def spinner(message: str, duration: float = 1.5):
    """Show an animated spinner for a brief moment."""
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        frame = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
        print(f"\r{CYAN}{frame}{RESET} {message}", end="", flush=True)
        time.sleep(0.08)
        i += 1
    print(f"\r{GREEN}{CHECKMARK}{RESET} {message}")


def print_changed_files(files: list):
    """Display the list of changed files with a streaming feel."""
    if not files:
        print(f"  {DIM}No changed files detected.{RESET}")
        return
    print(f"  {DIM}Changed files:{RESET}")
    for f in files:
        time.sleep(0.06)
        print(f"    {YELLOW}~{RESET} {f}")


def print_summary(results: dict):
    """Print a final summary of everything Gitfold did."""
    time.sleep(0.3)
    print(f"\n{BOLD}{CYAN}{'═' * 52}{RESET}")
    print(f"{BOLD}{CYAN}  Gitfold Summary — {datetime.now().strftime('%H:%M:%S')}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 52}{RESET}\n")

    steps = [
        ("staged",     "Files staged"),
        ("committed",  "Changes committed"),
        ("pulled",     "Pulled from dev branch"),
        ("merged",     "Merged dev into branch"),
        ("pushed",     "Pushed to remote"),
        ("pr_created", "Pull request created"),
    ]

    for key, label in steps:
        value = results.get(key)
        time.sleep(0.08)
        if value is True:
            print(f"  {GREEN}{CHECKMARK}{RESET} {label}")
        elif value is False:
            print(f"  {RED}{CROSS}{RESET} {label} — skipped or failed")
        elif isinstance(value, str):
            print(f"  {GREEN}{CHECKMARK}{RESET} {label}: {DIM}{value}{RESET}")

    pr_url = results.get("pr_url")
    if pr_url:
        time.sleep(0.1)
        print(f"\n  {CYAN}🔗 PR:{RESET} {pr_url}")

    errors = results.get("errors", [])
    if errors:
        print(f"\n  {RED}Errors encountered:{RESET}")
        for err in errors:
            print(f"    {RED}•{RESET} {err}")

    time.sleep(0.1)
    print(f"\n{BOLD}{CYAN}{'═' * 52}{RESET}\n")


def manual_mode_notice():
    """Notify the developer that manual mode is active."""
    time.sleep(0.2)
    print(f"\n{YELLOW}{BOLD}  ⚙  Manual mode enabled.{RESET}")
    time.sleep(0.1)
    print(f"  {DIM}Gitfold will prompt you before each step.{RESET}")
    print(f"  {DIM}Tip: run 'gitfold' without --manual for full automation.{RESET}\n")
    time.sleep(0.2)


def confirm_step(message: str) -> bool:
    """Ask the developer to confirm before proceeding with a step."""
    answer = input(f"\n{YELLOW}?{RESET} {message} [y/n]: ").strip().lower()
    return answer == "y" or answer == ""


def prompt_switch_to_manual() -> bool:
    """
    Called when the user presses Ctrl+C mid-flow.
    Asks if they want to switch to manual mode and continue
    rather than exiting entirely.
    """
    print(f"\n\n{YELLOW}{BOLD}  ⚡ Interrupted!{RESET}")
    time.sleep(0.1)
    print(f"  {DIM}You paused Gitfold mid-flow.{RESET}")
    answer = input(
        f"\n{YELLOW}?{RESET} Switch to manual mode and continue from here? [y/n]: "
    ).strip().lower()
    return answer == "y" or answer == ""