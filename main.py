import click
import sys
from git_handler import (
    get_repo,
    get_changed_files,
    stage_all_files,
    get_diff,
    commit,
    detect_branches,
    pull_from_branch,
    merge_branch,
    push_to_remote,
    has_remote,
    get_remote_url,
)
from ai_integration import (
    generate_commit_message,
    generate_pr_description,
    confirm_message,
)
from config_manager import (
    ensure_config,
    get_default_branch,
    get_dev_branch,
    get_auto_push,
    get_auto_pr,
)
from github_api import (
    create_pull_request,
    open_pr_in_browser,
    open_compare_url_in_browser,
    check_token_permissions,
)
from logger import (
    header,
    step,
    success,
    warning,
    error,
    section,
    divider,
    print_changed_files,
    print_summary,
    manual_mode_notice,
    confirm_step,
    prompt_switch_to_manual,
)


@click.command()
@click.option("--manual", is_flag=True, help="Step through each action manually.")
@click.option("--no-push", is_flag=True, help="Skip pushing to remote.")
@click.option("--no-pr", is_flag=True, help="Skip creating a pull request.")
@click.option("--branch", default=None, help="Override the target base branch.")
def done(manual, no_push, no_pr, branch):
    """
    Gitfold — one command to stage, commit, merge, push, and open a PR.

    Aliases: gitfold, gf
    """

    header()

    # Handle Ctrl+C gracefully anywhere in the flow
    try:
        _run(manual, no_push, no_pr, branch)
    except KeyboardInterrupt:
        if prompt_switch_to_manual():
            print()
            _run(manual=True, no_push=no_push, no_pr=no_pr, branch=branch)
        else:
            print(f"\nGitfold exited. Your staged changes are safe.\n")
            sys.exit(0)


def _run(manual, no_push, no_pr, branch):
    state = {
        "staged": False,
        "committed": False,
        "pulled": False,
        "merged": False,
        "pushed": False,
        "pr_created": False,
        "pr_url": None,
        "errors": [],
    }

    if manual:
        manual_mode_notice()

    # ── Step 1: Load repo ──────────────────────────────────────────
    section("Repository")
    try:
        repo = get_repo()
        success(f"Repo found: {repo.working_dir}")
    except Exception as e:
        error(str(e))
        sys.exit(1)

    # ── Step 2: Detect branches ────────────────────────────────────
    branch_info = detect_branches(repo)
    success(f"Current branch: {branch_info['current']}")
    if branch_info["dev"]:
        success(f"Dev branch detected: {branch_info['dev']}")
    if branch_info["default"]:
        success(f"Default branch: {branch_info['default']}")

    # ── Step 3: Load or create config ──────────────────────────────
    section("Config")
    config = ensure_config(branch_info)
    base_branch = branch or get_dev_branch(config, branch_info["dev"]) or get_default_branch(config, branch_info["default"])
    success(f"Target base branch: {base_branch}")

    # ── Step 4: Show changed files ─────────────────────────────────
    section("Changed Files")
    changed_files = get_changed_files(repo)
    if not changed_files:
        warning("No changed files detected. Nothing to commit.")
        sys.exit(0)
    print_changed_files(changed_files)

    # ── Step 5: Stage all files ────────────────────────────────────
    section("Staging")
    if manual and not confirm_step("Stage all changed files?"):
        warning("Staging skipped. Exiting.")
        sys.exit(0)

    try:
        step("Staging all files...")
        stage_all_files(repo)
        results["staged"] = True
        success("All files staged.")
    except Exception as e:
        error(str(e))
        results["errors"].append(str(e))
        sys.exit(1)

    # ── Step 6: Get diff and generate commit message ───────────────
    section("Commit Message")
    try:
        diff = get_diff(repo)
        commit_message = None

        while not commit_message:
            commit_message = generate_commit_message(diff)
            commit_message = confirm_message(commit_message, "commit message")
            # None means user wants to regenerate
    except Exception as e:
        error(f"AI commit message generation failed: {e}")
        commit_message = input("Enter commit message manually: ").strip()

    # ── Step 7: Commit ─────────────────────────────────────────────
    section("Committing")
    if manual and not confirm_step(f"Commit with message: '{commit_message}'?"):
        warning("Commit skipped. Exiting.")
        sys.exit(0)

    try:
        step("Committing changes...")
        commit(repo, commit_message)
        results["committed"] = True
        success("Committed successfully.")
    except Exception as e:
        error(str(e))
        results["errors"].append(str(e))
        sys.exit(1)

    # ── Step 8: Pull and merge from base branch ────────────────────
    if not no_push and base_branch != branch_info["current"]:
        section("Syncing with Base Branch")
        if manual and not confirm_step(f"Pull and merge from '{base_branch}'?"):
            warning("Sync skipped.")
        else:
            try:
                step(f"Pulling latest from '{base_branch}'...")
                pull_from_branch(repo, base_branch)
                results["pulled"] = True

                step(f"Merging '{base_branch}' into '{branch_info['current']}'...")
                merge_branch(repo, base_branch)
                results["merged"] = True
                success("Sync complete.")
            except Exception as e:
                error(str(e))
                results["errors"].append(str(e))
                warning("Skipping push and PR due to sync failure.")
                print_summary(results)
                sys.exit(1)

    # ── Step 9: Push to remote ─────────────────────────────────────
    if not no_push and get_auto_push(config):
        section("Pushing")
        if not has_remote(repo):
            warning("No remote origin found. Skipping push.")
        else:
            if manual and not confirm_step(f"Push '{branch_info['current']}' to remote?"):
                warning("Push skipped.")
            else:
                try:
                    step(f"Pushing '{branch_info['current']}' to remote...")
                    push_to_remote(repo, branch_info["current"])
                    results["pushed"] = True
                    success("Pushed to remote.")
                except Exception as e:
                    error(str(e))
                    results["errors"].append(str(e))
                    warning("Push failed. Skipping PR.")
                    print_summary(results)
                    sys.exit(1)

    # ── Step 10: Create Pull Request ───────────────────────────────
    if not no_pr and results["pushed"] and get_auto_pr(config):
        section("Pull Request")
        remote_url = get_remote_url(repo)

        if not remote_url:
            warning("Could not determine remote URL. Skipping PR.")
        else:
            if manual and not confirm_step("Create a pull request?"):
                warning("PR skipped.")
                open_compare_url_in_browser(remote_url, branch_info["current"], base_branch)
            else:
                try:
                    step("Generating PR description...")
                    pr_title, pr_body = generate_pr_description(
                        diff, commit_message, branch_info["current"]
                    )
                    pr_title = confirm_message(pr_title, "PR title")

                    step("Creating pull request on GitHub...")
                    pr_data = create_pull_request(
                        remote_url=remote_url,
                        head_branch=branch_info["current"],
                        base_branch=base_branch,
                        pr_title=pr_title,
                        pr_body=pr_body,
                    )
                    results["pr_created"] = True
                    results["pr_url"] = pr_data["html_url"]
                    success(f"PR created: {pr_data['html_url']}")
                    open_pr_in_browser(pr_data["html_url"])

                except Exception as e:
                    error(str(e))
                    results["errors"].append(str(e))
                    warning("PR creation failed. Opening compare page instead.")
                    open_compare_url_in_browser(
                        remote_url, branch_info["current"], base_branch
                    )

    # ── Final Summary ──────────────────────────────────────────────
    print_summary(results)


if __name__ == "__main__":
    done()