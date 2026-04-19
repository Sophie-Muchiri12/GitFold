import os
import re
import webbrowser
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"


def get_headers():
    """Return the authorization headers for GitHub API requests."""
    if not GITHUB_TOKEN:
        raise Exception(
            "GitHub token not found. Please set GITHUB_TOKEN in your .env file."
        )
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def parse_repo_info(remote_url: str):
    """
    Extract the GitHub owner and repo name from the remote URL.
    Supports both HTTPS and SSH formats.
    """
    # HTTPS: https://github.com/owner/repo.git
    https_match = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
    if https_match:
        return https_match.group(1), https_match.group(2)

    # SSH: git@github.com:owner/repo.git
    ssh_match = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)

    raise Exception(
        f"Could not parse GitHub owner/repo from remote URL: {remote_url}"
    )


def create_pull_request(
    remote_url: str,
    head_branch: str,
    base_branch: str,
    pr_title: str,
    pr_body: str,
) -> dict:
    """
    Create a pull request on GitHub via the API.
    Returns the PR data including the HTML URL.
    """
    owner, repo = parse_repo_info(remote_url)

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls"

    payload = {
        "title": pr_title,
        "body": pr_body,
        "head": head_branch,
        "base": base_branch,
        "draft": False,
    }

    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code == 201:
        pr_data = response.json()
        print(f"✔ Pull request created: {pr_data['html_url']}")
        return pr_data

    elif response.status_code == 422:
        # PR already exists or no commits between branches
        error_msg = response.json().get("message", "")
        if "already exists" in error_msg.lower() or "no commits" in error_msg.lower():
            print(f"⚠️  PR already exists or no new commits to compare.")
            # Try to fetch existing PR URL
            existing_pr = get_existing_pr(owner, repo, head_branch, base_branch)
            if existing_pr:
                return existing_pr
        raise Exception(f"GitHub API error 422: {response.json()}")

    else:
        raise Exception(
            f"Failed to create PR. Status {response.status_code}: {response.json()}"
        )


def get_existing_pr(owner: str, repo: str, head_branch: str, base_branch: str):
    """
    Fetch an existing open PR for the given branches.
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls"
    params = {"state": "open", "head": f"{owner}:{head_branch}", "base": base_branch}
    response = requests.get(url, headers=get_headers(), params=params)

    if response.status_code == 200 and response.json():
        pr = response.json()[0]
        print(f"✔ Existing PR found: {pr['html_url']}")
        return pr

    return None


def open_pr_in_browser(pr_url: str):
    """Open the pull request in the default browser."""
    print(f"\n🌐 Opening PR in browser: {pr_url}")
    webbrowser.open(pr_url)


def open_compare_url_in_browser(remote_url: str, head_branch: str, base_branch: str):
    """
    Open the GitHub compare page in the browser so the developer
    can manually review and create the PR themselves.
    """
    try:
        owner, repo = parse_repo_info(remote_url)
        compare_url = (
            f"https://github.com/{owner}/{repo}/compare/{base_branch}...{head_branch}"
        )
        print(f"\n🌐 Opening GitHub compare page: {compare_url}")
        webbrowser.open(compare_url)
    except Exception as e:
        print(f"⚠️  Could not open browser: {e}")


def check_token_permissions():
    """
    Verify that the GitHub token is valid and has the right permissions.
    """
    response = requests.get(f"{GITHUB_API_BASE}/user", headers=get_headers())
    if response.status_code == 200:
        user = response.json()
        print(f"✔ GitHub token valid. Authenticated as: {user['login']}")
        return True
    else:
        raise Exception(
            f"GitHub token invalid or expired. Status {response.status_code}."
        )