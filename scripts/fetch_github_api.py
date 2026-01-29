#!/usr/bin/env python3
"""
Fetch GitHub activity via GitHub API.

Used in CI where local git repos aren't available. Returns the same format
as parse_github.py for compatibility.

Environment Variables:
    GITHUB_TOKEN: Required. Personal access token or GITHUB_TOKEN from Actions.
    GITHUB_USERNAME: Optional. Defaults to 'cipher982'.
"""

import os
import requests
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, Any, List, Optional


DEFAULT_USERNAME = "cipher982"

# Repos to exclude (work projects, private, etc.)
EXCLUDED_REPOS = [
    "zeta",
]


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment."""
    return os.environ.get("GITHUB_TOKEN")


def get_username() -> str:
    """Get GitHub username from environment or use default."""
    return os.environ.get("GITHUB_USERNAME", DEFAULT_USERNAME)


def _make_request(url: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """Make authenticated request to GitHub API."""
    token = get_github_token()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"   GitHub API request failed: {e}")
        return None


def _make_paginated_request(url: str, params: Optional[Dict] = None, max_pages: int = 10) -> List[Dict]:
    """Make paginated request to GitHub API."""
    token = get_github_token()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    all_items = []
    params = params or {}
    params["per_page"] = 100

    for page in range(1, max_pages + 1):
        params["page"] = page
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            items = response.json()
            if not items:
                break
            all_items.extend(items)
            if len(items) < 100:
                break
        except requests.exceptions.RequestException as e:
            print(f"   GitHub API request failed: {e}")
            break

    return all_items


def fetch_user_repos(username: str) -> List[Dict]:
    """Fetch all repos for a user (including private repos when authenticated)."""
    token = get_github_token()
    if token:
        # /user/repos includes private repos, requires PAT with repo scope
        url = "https://api.github.com/user/repos"
        return _make_paginated_request(url, {"type": "owner", "sort": "pushed"})
    else:
        url = f"https://api.github.com/users/{username}/repos"
        return _make_paginated_request(url, {"type": "owner", "sort": "pushed"})


def fetch_repo_commits(owner: str, repo: str, since: datetime) -> List[Dict]:
    """Fetch commits for a repo since a given date."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {
        "since": since.isoformat(),
        "author": owner,  # Only commits by the owner
    }
    return _make_paginated_request(url, params, max_pages=5)


def detect_language(repo: Dict) -> Optional[str]:
    """Get primary language from repo data."""
    return repo.get("language")


def fetch_github_activity(username: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch GitHub activity via API.

    Returns same format as parse_github.py:
        {
            "repos_active_7d": int,
            "repos_active_30d": int,
            "commits_7d": int,
            "commits_30d": int,
            "languages_30d": [{"name": str, "commits": int}],
            "last_push": {"repo": str, "timestamp": str, "hours_ago": float} or None,
            "top_repos_7d": [{"repo": str, "commits": int}],
            "daily_commits": [{"date": str, "commits": int}]
        }
    """
    username = username or get_username()
    now = datetime.now(timezone.utc)
    since_7d = now - timedelta(days=7)
    since_30d = now - timedelta(days=30)

    print(f"   Fetching repos for {username}...")
    repos = fetch_user_repos(username)
    print(f"   Found {len(repos)} repos")

    repos_7d = set()
    repos_30d = set()
    commits_7d_total = 0
    commits_30d_total = 0
    repo_commits_7d = defaultdict(int)
    language_commits_30d = defaultdict(int)
    daily_commits = defaultdict(int)
    last_push_data = None
    last_push_time = None

    # Filter to recently pushed repos to avoid too many API calls
    recent_repos = [r for r in repos if r.get("pushed_at")]
    recent_repos = [
        r for r in recent_repos
        if datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")) > since_30d
    ]

    print(f"   Checking {len(recent_repos)} recently active repos...")

    for repo in recent_repos:
        repo_name = repo["name"]

        # Skip excluded repos
        if repo_name in EXCLUDED_REPOS:
            continue

        # Skip forks unless they have commits
        if repo.get("fork"):
            continue

        commits = fetch_repo_commits(username, repo_name, since_30d)

        commits_7d_list = []
        commits_30d_list = []

        for commit in commits:
            commit_date_str = commit.get("commit", {}).get("author", {}).get("date")
            if not commit_date_str:
                continue

            commit_date = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))

            if commit_date > since_30d:
                commits_30d_list.append(commit)

                if commit_date > since_7d:
                    commits_7d_list.append(commit)
                    # Track daily commits
                    date_str = commit_date.date().isoformat()
                    daily_commits[date_str] += 1

                # Track last push
                if last_push_time is None or commit_date > last_push_time:
                    last_push_time = commit_date
                    hours_ago = (now - commit_date).total_seconds() / 3600
                    last_push_data = {
                        "repo": repo_name,
                        "timestamp": commit_date.isoformat(),
                        "hours_ago": round(hours_ago, 2)
                    }

        if commits_7d_list:
            repos_7d.add(repo_name)
            commits_7d_total += len(commits_7d_list)
            repo_commits_7d[repo_name] = len(commits_7d_list)

        if commits_30d_list:
            repos_30d.add(repo_name)
            commits_30d_total += len(commits_30d_list)

            # Track language
            language = detect_language(repo)
            if language:
                language_commits_30d[language] += len(commits_30d_list)

    # Format results
    top_repos = [
        {"repo": repo, "commits": count}
        for repo, count in sorted(repo_commits_7d.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    languages = [
        {"name": lang, "commits": count}
        for lang, count in sorted(language_commits_30d.items(), key=lambda x: x[1], reverse=True)
    ]

    daily_commits_list = [
        {"date": date, "commits": count}
        for date, count in sorted(daily_commits.items())
    ]

    return {
        "repos_active_7d": len(repos_7d),
        "repos_active_30d": len(repos_30d),
        "commits_7d": commits_7d_total,
        "commits_30d": commits_30d_total,
        "languages_30d": languages,
        "last_push": last_push_data,
        "top_repos_7d": top_repos,
        "daily_commits": daily_commits_list,
    }


def main():
    """Test the GitHub API fetch."""
    import json

    print("Testing GitHub API fetch...")

    token = get_github_token()
    if not token:
        print("Warning: GITHUB_TOKEN not set. API rate limits will be restrictive.")

    result = fetch_github_activity()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
