import time
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


def header():
    """Print the Gitfold welcome banner."""
    print(f"\n{BOLD}{GREEN}")
    print("  ██████╗ ██╗████████╗")
    print(" ██╔════╝ ██║╚══██╔══╝")
    print(" ██║  ███╗██║   ██║   ")
    print(" ██║   ██║██║   ██║   ")
    print(" ╚██████╔╝██║   ██║   ")
    print("  ╚═════╝ ╚═╝   ╚═╝   ")
    print(f"{RESET}{BOLD}{CYAN}")
    print(" ███████╗ ██████╗ ██╗     ██████╗ ")
    print(" ██╔════╝██╔═══██╗██║     ██╔══██╗")
    print(" █████╗  ██║   ██║██║     ██║  ██║")
    print(" ██╔══╝  ██║   ██║██║     ██║  ██║")
    print(" ██║     ╚██████╔╝███████╗██████╔╝")
    print(" ╚═╝      ╚═════╝ ╚══════╝╚═════╝ ")
    print(f"{RESET}")
    print(f"{GREEN}{BOLD}  ◈ fold it. commit it. ship it. ◈{RESET}")
    print(f"{DIM}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{DIM}  v0.1.0  ·  AI-powered git workflow  ·  open source{RESET}")
    print(f"{DIM}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")


def step(message: str):
    """Print a step in the workflow."""
    print(f"{CYAN}{ARROW}{RESET} {message}")


def success(message: str):
    """Print a success message."""
    print(f"{GREEN}{CHECKMARK}{RESET} {message}")


def warning(message: str):
    """Print a warning message."""
    print(f"{YELLOW}⚠️  {message}{RESET}")


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
    """Print a section header."""
    print(f"\n{BOLD}[ {title} ]{RESET}")
    divider()


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
    """Display the list of changed files."""
    if not files:
        print(f"  {DIM}No changed files detected.{RESET}")
        return
    print(f"  {DIM}Changed files:{RESET}")
    for f in files:
        print(f"    {YELLOW}~{RESET} {f}")


def print_summary(results: dict):
    """
    Print a final summary of everything Gitfold did.
    results is a dict with keys like staged, committed, pushed, pr_url, errors.
    """
    print(f"\n{BOLD}{CYAN}{'═' * 52}{RESET}")
    print(f"{BOLD}{CYAN}  Gitfold Summary — {datetime.now().strftime('%H:%M:%S')}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 52}{RESET}\n")

    steps = [
        ("staged",    "Files staged"),
        ("committed", "Changes committed"),
        ("pulled",    "Pulled from dev branch"),
        ("merged",    "Merged dev into branch"),
        ("pushed",    "Pushed to remote"),
        ("pr_created","Pull request created"),
    ]

    for key, label in steps:
        value = results.get(key)
        if value is True:
            print(f"  {GREEN}{CHECKMARK}{RESET} {label}")
        elif value is False:
            print(f"  {RED}{CROSS}{RESET} {label} — skipped or failed")
        elif isinstance(value, str):
            print(f"  {GREEN}{CHECKMARK}{RESET} {label}: {DIM}{value}{RESET}")

    # PR URL
    pr_url = results.get("pr_url")
    if pr_url:
        print(f"\n  {CYAN}🔗 PR:{RESET} {pr_url}")

    # Errors
    errors = results.get("errors", [])
    if errors:
        print(f"\n  {RED}Errors encountered:{RESET}")
        for err in errors:
            print(f"    {RED}•{RESET} {err}")

    print(f"\n{BOLD}{CYAN}{'═' * 52}{RESET}\n")


def manual_mode_notice():
    """Notify the developer that manual mode is active."""
    print(f"\n{YELLOW}{BOLD}  Manual mode enabled.{RESET}")
    print(f"  {DIM}Gitfold will stage files but prompt you before each step.{RESET}")
    print(f"  {DIM}Tip: run 'gitfold' without --manual for full automation.{RESET}\n")


def confirm_step(message: str) -> bool:
    """Ask the developer to confirm before proceeding with a step."""
    answer = input(f"\n{YELLOW}?{RESET} {message} [y/n]: ").strip().lower()
    return answer == "y" or answer == ""