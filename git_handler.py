import git
import os
from pathlib import Path


def get_repo():
    """Get the Git repository object from the current directory."""
    try:
        repo = git.Repo(Path.cwd(), search_parent_directories=True)
        return repo
    except git.InvalidGitRepositoryError:
        raise Exception("No Git repository found in the current directory.")


def get_changed_files(repo):
    """Return a list of all changed, staged, and untracked files."""
    changed = [item.a_path for item in repo.index.diff(None)]
    staged = [item.a_path for item in repo.index.diff("HEAD")]
    untracked = repo.untracked_files
    return list(set(changed + staged + untracked))


def stage_all_files(repo):
    """Stage all changed and untracked files (git add .)"""
    repo.git.add(A=True)
    print("✔ All files staged.")


def get_diff(repo):
    """Get the full diff of staged changes to send to the AI."""
    try:
        diff = repo.git.diff("HEAD", staged=True)
        if not diff:
            diff = repo.git.diff("HEAD")
        return diff
    except git.GitCommandError:
        # First commit scenario — no HEAD yet
        diff = repo.git.diff("--cached")
        return diff


def commit(repo, message):
    """Commit staged files with the given message."""
    repo.index.commit(message)
    print(f"✔ Committed: {message}")


def detect_branches(repo):
    """
    Detect the current branch, default branch (main/master),
    and development branch (dev/develop/development) if it exists.
    """
    branches = [b.name for b in repo.branches]
    current = repo.active_branch.name

    # Detect default branch
    default_branch = None
    for name in ["main", "master"]:
        if name in branches:
            default_branch = name
            break

    # Detect development branch
    dev_branch = None
    for name in ["dev", "develop", "development"]:
        if name in branches:
            dev_branch = name
            break

    return {
        "current": current,
        "default": default_branch,
        "dev": dev_branch,
        "all": branches,
    }


def pull_from_branch(repo, branch_name):
    """Pull latest changes from the specified remote branch."""
    try:
        origin = repo.remotes.origin
        origin.pull(branch_name)
        print(f"✔ Pulled latest from '{branch_name}'.")
    except Exception as e:
        raise Exception(f"Failed to pull from '{branch_name}': {e}")


def merge_branch(repo, source_branch):
    """Merge the source branch into the current branch."""
    try:
        repo.git.merge(source_branch)
        print(f"✔ Merged '{source_branch}' into '{repo.active_branch.name}'.")
    except git.GitCommandError as e:
        if "CONFLICT" in str(e):
            raise Exception(
                "Merge conflict detected. Please resolve conflicts manually, then re-run gitfold."
            )
        raise Exception(f"Merge failed: {e}")


def push_to_remote(repo, branch_name):
    """Push the current branch to the remote origin."""
    try:
        origin = repo.remotes.origin
        origin.push(refspec=f"{branch_name}:{branch_name}")
        print(f"✔ Pushed '{branch_name}' to remote.")
    except Exception as e:
        raise Exception(f"Failed to push to remote: {e}")


def has_remote(repo):
    """Check if the repo has a remote origin configured."""
    return "origin" in [r.name for r in repo.remotes]


def get_remote_url(repo):
    """Get the remote origin URL (e.g. GitHub repo URL)."""
    try:
        return repo.remotes.origin.url
    except Exception:
        return None