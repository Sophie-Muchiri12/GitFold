import git
import os
from pathlib import Path


# Files and folders that should never be committed
IGNORED_PATTERNS = [
    "__pycache__",
    ".pyc",
    ".egg-info",
    ".eggs",
    "dist/",
    "build/",
    ".DS_Store",
    "Thumbs.db",
    ".venv",
    "venv/",
    "env/",
    "node_modules/",
]


def get_repo():
    """Get the Git repository object from the current directory."""
    try:
        repo = git.Repo(Path.cwd(), search_parent_directories=True)
        return repo
    except git.InvalidGitRepositoryError:
        raise Exception(
            "No Git repository found in the current directory.\n"
            "  Tip: run 'git init' first to initialise a repo here."
        )


def ensure_git_pull_config(repo):
    """
    Silently ensure Git pull strategy is set so users never hit
    the 'Need to specify how to reconcile divergent branches' error.
    Sets pull.rebase=false (merge strategy) if not already configured.
    """
    try:
        config = repo.config_reader(config_level="global")
        try:
            config.get_value("pull", "rebase")
            # Already set — nothing to do
        except Exception:
            # Not set — configure it silently
            with repo.config_writer(config_level="global") as writer:
                writer.set_value("pull", "rebase", "false")
    except Exception:
        # If we can't read/write global config, set it at repo level
        try:
            with repo.config_writer(config_level="repository") as writer:
                writer.set_value("pull", "rebase", "false")
        except Exception:
            pass  # Best effort — we'll handle pull errors gracefully anyway


def is_ignored_file(filepath: str) -> bool:
    """Check if a file matches common patterns that should not be committed."""
    for pattern in IGNORED_PATTERNS:
        if pattern in filepath:
            return True
    return False


def get_changed_files(repo):
    """
    Return a list of all meaningful changed, staged, and untracked files.
    Automatically filters out cache files, build artifacts, and other noise.
    """
    try:
        changed = [item.a_path for item in repo.index.diff(None)]
    except Exception:
        changed = []

    try:
        staged = [item.a_path for item in repo.index.diff("HEAD")]
    except Exception:
        staged = []

    untracked = repo.untracked_files or []

    all_files = list(set(changed + staged + untracked))

    # Filter out noise — only show meaningful files
    meaningful = [f for f in all_files if not is_ignored_file(f)]
    return meaningful


def stage_all_files(repo):
    """Stage all changed and untracked files (git add .)"""
    try:
        repo.git.add(A=True)
    except git.GitCommandError as e:
        raise Exception(f"Failed to stage files: {e}")


def get_diff(repo):
    """
    Get the full diff of staged changes to send to the AI.
    Handles first commit scenario where there is no HEAD yet.
    """
    try:
        diff = repo.git.diff("HEAD", staged=True)
        if not diff:
            diff = repo.git.diff("HEAD")
        if not diff:
            # Nothing staged vs HEAD — get all cached changes
            diff = repo.git.diff("--cached")
        return diff
    except git.GitCommandError:
        # First commit — no HEAD exists yet
        try:
            return repo.git.diff("--cached")
        except Exception:
            return ""


def commit(repo, message):
    """
    Commit staged files with the given message.
    Handles the case where there is nothing new to commit.
    """
    try:
        if not repo.index.diff("HEAD") and not repo.untracked_files:
            raise Exception(
                "Nothing to commit. All files are already up to date."
            )
        repo.index.commit(message)
    except git.GitCommandError as e:
        if "nothing to commit" in str(e).lower():
            raise Exception(
                "Nothing new to commit. Make some changes first, then run gitfold again."
            )
        raise Exception(f"Commit failed: {e}")


def detect_branches(repo):
    """
    Detect the current branch, default branch (main/master),
    and development branch (dev/develop/development) if it exists.
    Also checks remote branches in case local ones haven't been checked out.
    """
    local_branches = [b.name for b in repo.branches]

    # Also check remote branches
    remote_branches = []
    try:
        remote_branches = [
            ref.name.replace("origin/", "")
            for ref in repo.remotes.origin.refs
            if "HEAD" not in ref.name
        ]
    except Exception:
        pass

    all_branches = list(set(local_branches + remote_branches))

    try:
        current = repo.active_branch.name
    except TypeError:
        # Detached HEAD state
        current = repo.head.commit.hexsha[:7]

    # Detect default branch
    default_branch = None
    for name in ["main", "master"]:
        if name in all_branches:
            default_branch = name
            break

    # Detect development branch
    dev_branch = None
    for name in ["dev", "develop", "development"]:
        if name in all_branches:
            dev_branch = name
            break

    return {
        "current": current,
        "default": default_branch,
        "dev": dev_branch,
        "all": all_branches,
    }


def pull_from_branch(repo, branch_name):
    """
    Pull latest changes from the specified remote branch.
    Handles all common pull failure scenarios gracefully.
    """
    # First ensure pull strategy is configured — silently fixes the
    # 'Need to specify how to reconcile divergent branches' error
    ensure_git_pull_config(repo)

    try:
        result = repo.git.pull("origin", branch_name, "--no-rebase")

        if "Already up to date" in result:
            return  # Nothing to pull — that's fine

    except git.GitCommandError as e:
        error_msg = str(e).lower()

        if "already up to date" in error_msg:
            return  # Fine — nothing new

        elif "conflict" in error_msg:
            raise Exception(
                f"Pull conflict detected on '{branch_name}'.\n"
                "  Please resolve conflicts manually, then re-run gitfold."
            )

        elif "no such ref" in error_msg or "couldn't find remote ref" in error_msg:
            raise Exception(
                f"Branch '{branch_name}' does not exist on the remote.\n"
                "  Tip: check your branch name in .gitfold.json or push the branch first."
            )

        elif "authentication" in error_msg or "permission" in error_msg:
            raise Exception(
                "GitHub authentication failed during pull.\n"
                "  Tip: check that your GITHUB_TOKEN in .env is valid and has 'repo' scope."
            )

        elif "network" in error_msg or "unable to connect" in error_msg or "could not resolve" in error_msg:
            raise Exception(
                "Network error — could not reach GitHub.\n"
                "  Tip: check your internet connection and try again."
            )

        elif "divergent" in error_msg or "reconcile" in error_msg:
            # This should be caught by ensure_git_pull_config but handle it anyway
            try:
                repo.git.pull("origin", branch_name, "--no-rebase", "--allow-unrelated-histories")
            except git.GitCommandError as e2:
                raise Exception(
                    f"Could not sync with '{branch_name}' — branches have diverged.\n"
                    "  Tip: run 'git pull origin {branch_name} --no-rebase' manually to resolve."
                )
        else:
            raise Exception(
                f"Failed to pull from '{branch_name}'.\n"
                f"  Detail: {str(e.stderr).strip()}"
            )


def merge_branch(repo, source_branch):
    """
    Merge the source branch into the current branch.
    Gives clear guidance on conflict resolution.
    """
    try:
        repo.git.merge(source_branch, "--no-edit")
    except git.GitCommandError as e:
        error_msg = str(e).lower()

        if "conflict" in error_msg or "CONFLICT" in str(e):
            # List the conflicting files to help the user
            conflicting = []
            try:
                conflicting = [
                    item.a_path
                    for item in repo.index.diff(None)
                    if item.a_path
                ]
            except Exception:
                pass

            conflict_list = "\n    • ".join(conflicting) if conflicting else "unknown files"
            raise Exception(
                f"Merge conflict detected when merging '{source_branch}'.\n"
                f"  Conflicting files:\n    • {conflict_list}\n"
                "  Please resolve the conflicts, then run 'git add .' and 'git commit'.\n"
                "  Once resolved, re-run gitfold to continue."
            )

        elif "already up to date" in error_msg:
            return  # Nothing to merge — that's fine

        else:
            raise Exception(
                f"Merge failed: {str(e.stderr).strip()}\n"
                "  Tip: resolve any issues manually and re-run gitfold."
            )


def push_to_remote(repo, branch_name):
    """
    Push the current branch to the remote origin.
    Handles common push failures with clear user guidance.
    """
    try:
        repo.git.push("origin", f"{branch_name}:{branch_name}")
    except git.GitCommandError as e:
        error_msg = str(e).lower()

        if "rejected" in error_msg and "non-fast-forward" in error_msg:
            raise Exception(
                f"Push rejected — remote has changes you don't have locally.\n"
                "  Tip: run 'git pull origin {branch_name}' first, then re-run gitfold."
            )

        elif "authentication" in error_msg or "permission" in error_msg or "403" in error_msg:
            raise Exception(
                "Push failed — GitHub authentication error.\n"
                "  Tip: check that your GITHUB_TOKEN in .env is valid and has 'repo' scope."
            )

        elif "no such ref" in error_msg:
            raise Exception(
                f"Branch '{branch_name}' not found on remote.\n"
                "  Tip: make sure you have committed something first."
            )

        elif "network" in error_msg or "unable to connect" in error_msg or "could not resolve" in error_msg:
            raise Exception(
                "Network error — could not reach GitHub.\n"
                "  Tip: check your internet connection and try again."
            )

        else:
            raise Exception(
                f"Push failed: {str(e.stderr).strip()}"
            )


def has_remote(repo):
    """Check if the repo has a remote origin configured."""
    return "origin" in [r.name for r in repo.remotes]


def get_remote_url(repo):
    """Get the remote origin URL (e.g. GitHub repo URL)."""
    try:
        return repo.remotes.origin.url
    except Exception:
        return None


def is_clean(repo):
    """Check if the working tree is clean — no uncommitted changes."""
    return not repo.is_dirty(untracked_files=True)