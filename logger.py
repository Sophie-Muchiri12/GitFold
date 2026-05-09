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


def _stream(text: str, delay: float = 0.022, color: str = "", newline: bool = True):
    """
    Print text character by character with a streaming effect.
    delay controls speed — lower = faster.
    """
    for char in text:
        sys.stdout.write(f"{color}{char}{RESET if color else ''}")
        sys.stdout.flush()
        time.sleep(delay)
    if newline:
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
    time.sleep(0.15)
    _stream("  ◈ fold it. commit it. ship it. ◈", delay=0.04, color=f"{GREEN}{BOLD}")
    time.sleep(0.1)
    _stream("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", delay=0.008, color=DIM)
    _stream("  v0.1.0  ·  AI-powered git workflow  ·  open source", delay=0.018, color=DIM)
    _stream("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", delay=0.008, color=DIM)
    time.sleep(0.2)

    # Onboarding instructions
    _stream(f"\n  How to use Gitfold:", delay=0.025, color=BOLD)
    time.sleep(0.1)

    instructions = [
        (GREEN,  "  › Run gitfold          — fully automated mode"),
        (YELLOW, "  › Run gitfold --manual  — confirm each step yourself"),
        (CYAN,   "  › Run gitfold --no-push — commit only, skip push & PR"),
        (CYAN,   "  › Run gitfold --no-pr   — push but skip PR creation"),
        (DIM,    "  ›  Press Ctrl+C at any time to pause and switch to manual mode"),
    ]
    for color, line in instructions:
        _stream(line, delay=0.015, color=color)
        time.sleep(0.05)

    _stream("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", delay=0.008, color=DIM)
    print()
    time.sleep(0.3)


def step(message: str):
    """Print a workflow step with streaming effect."""
    time.sleep(0.1)
    _stream(f"{ARROW} {message}", delay=0.018, color=CYAN)


def success(message: str):
    """Print a success message with streaming effect."""
    time.sleep(0.05)
    _stream(f"{CHECKMARK} {message}", delay=0.018, color=GREEN)


def warning(message: str):
    """Print a warning message with streaming effect."""
    time.sleep(0.05)
    _stream(f"⚠️   {message}", delay=0.018, color=YELLOW)


def error(message: str):
    """Print an error message with streaming effect."""
    time.sleep(0.05)
    _stream(f"{CROSS} Error: {message}", delay=0.018, color=RED)


def info(message: str):
    """Print a neutral info message with streaming effect."""
    time.sleep(0.05)
    _stream(f"  {message}", delay=0.015, color=DIM)


def divider():
    """Print a visual divider line."""
    _stream("  ──────────────────────────────────────────────────", delay=0.006, color=DIM)


def section(title: str):
    """Print a section header with a short pause."""
    time.sleep(0.35)
    _stream(f"\n[ {title} ]", delay=0.03, color=BOLD)
    divider()
    time.sleep(0.1)


def spinner(message: str, duration: float = 1.5):
    """Show an animated spinner for a brief moment."""
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        frame = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
        sys.stdout.write(f"\r{CYAN}{frame}{RESET} {message}")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write(f"\r{GREEN}{CHECKMARK}{RESET} {message}\n")
    sys.stdout.flush()


def print_changed_files(files: list):
    """Display the list of changed files with streaming effect."""
    if not files:
        _stream("  No changed files detected.", delay=0.018, color=DIM)
        return
    _stream("  Changed files:", delay=0.018, color=DIM)
    for f in files:
        time.sleep(0.07)
        _stream(f"    ~ {f}", delay=0.015, color=YELLOW)


def print_summary(results: dict):
    """Print a final summary of everything Gitfold did."""
    time.sleep(0.3)

    _stream(f"\n{'═' * 52}", delay=0.006, color=f"{BOLD}{CYAN}")
    _stream(f"  Gitfold Summary — {datetime.now().strftime('%H:%M:%S')}", delay=0.02, color=f"{BOLD}{CYAN}")
    _stream(f"{'═' * 52}", delay=0.006, color=f"{BOLD}{CYAN}")
    print()

    steps = [
        ("staged",     "Files staged"),
        ("committed",  "Changes committed"),
        ("pulled",     "Pulled from dev branch"),
        ("merged",     "Merged dev into branch"),
        ("pushed",     "Pushed to remote"),
        ("pr_created", "Pull request created"),
        ("pr_exists",  "Existing PR found and opened"),
    ]

    for key, label in steps:
        value = results.get(key)
        time.sleep(0.1)
        if value is True:
            _stream(f"  {CHECKMARK} {label}", delay=0.018, color=GREEN)
        elif value is False:
            _stream(f"  {CROSS} {label} — skipped or failed", delay=0.018, color=RED)
        elif isinstance(value, str):
            _stream(f"  {CHECKMARK} {label}: {value}", delay=0.015, color=GREEN)

    pr_url = results.get("pr_url")
    if pr_url:
        time.sleep(0.1)
        print()
        _stream(f"  🔗 PR: {pr_url}", delay=0.015, color=CYAN)

    errors = results.get("errors", [])
    if errors:
        print()
        _stream("  Errors encountered:", delay=0.018, color=RED)
        for err in errors:
            time.sleep(0.05)
            _stream(f"    • {err}", delay=0.012, color=RED)

    time.sleep(0.15)
    print()
    _stream(f"{'═' * 52}", delay=0.006, color=f"{BOLD}{CYAN}")
    print()


def manual_mode_notice():
    """Notify the developer that manual mode is active."""
    time.sleep(0.2)
    _stream("\n  ⚙  Manual mode enabled.", delay=0.025, color=f"{YELLOW}{BOLD}")
    time.sleep(0.1)
    _stream("  Gitfold will prompt you before each step.", delay=0.018, color=DIM)
    _stream("  Tip: run 'gitfold' without --manual for full automation.", delay=0.018, color=DIM)
    print()
    time.sleep(0.2)


def confirm_step(message: str) -> bool:
    """Ask the developer to confirm before proceeding with a step."""
    print()
    answer = input(f"{YELLOW}?{RESET} {message} [y/n]: ").strip().lower()
    return answer == "y" or answer == ""


def prompt_switch_to_manual() -> bool:
    """
    Called when the user presses Ctrl+C mid-flow.
    Asks if they want to switch to manual mode and continue
    rather than exiting entirely.
    """
    print()
    time.sleep(0.1)
    _stream("\n  ⚡ Interrupted!", delay=0.03, color=f"{YELLOW}{BOLD}")
    time.sleep(0.1)
    _stream("  You paused Gitfold mid-flow.", delay=0.018, color=DIM)
    print()
    answer = input(
        f"{YELLOW}?{RESET} Switch to manual mode and continue from here? [y/n]: "
    ).strip().lower()
    return answer == "y" or answer == ""