"""Parse GitHub activity from local git repositories"""
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional


def get_git_repos(git_dir: Path) -> List[Path]:
    """Find all git repositories in the git directory"""
    repos = []
    for item in git_dir.iterdir():
        if item.is_dir() and (item / ".git").exists():
            repos.append(item)
    return repos


def get_commits_since(repo_path: Path, days: int) -> List[Dict[str, Any]]:
    """
    Get commits from a repo since N days ago.

    Returns list of {timestamp, message, files_changed}
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    since_arg = cutoff.strftime("%Y-%m-%d")

    try:
        # Get commit log with timestamp and message
        result = subprocess.run(
            ["git", "-C", str(repo_path), "log", f"--since={since_arg}",
             "--format=%H|%aI|%s", "--no-merges"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|", 2)
            if len(parts) != 3:
                continue

            commit_hash, timestamp_str, message = parts
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

            commits.append({
                "hash": commit_hash,
                "timestamp": timestamp,
                "message": message
            })

        return commits

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return []


def detect_language(repo_path: Path) -> Optional[str]:
    """
    Detect primary language of repo by file extensions.
    Simple heuristic for MVP.
    """
    extensions = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".rb": "Ruby",
        ".sh": "Shell",
        ".c": "C",
        ".cpp": "C++",
    }

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "ls-files"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return None

        # Count file extensions
        ext_counts = defaultdict(int)
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            suffix = Path(line).suffix
            if suffix in extensions:
                ext_counts[suffix] += 1

        if not ext_counts:
            return None

        # Return most common
        most_common = max(ext_counts.items(), key=lambda x: x[1])[0]
        return extensions[most_common]

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return None


def parse_github_activity(git_dir: Path) -> Dict[str, Any]:
    """
    Parse GitHub activity from local git repositories.

    Returns:
        dict with repos_active_Xd, commits_Xd, languages_30d, last_push, top_repos_7d
    """
    repos = get_git_repos(git_dir)

    repos_7d = set()
    repos_30d = set()
    commits_7d_total = 0
    commits_30d_total = 0

    repo_commits_7d = defaultdict(int)
    language_commits_30d = defaultdict(int)

    last_push_data = None
    last_push_time = None

    for repo_path in repos:
        repo_name = repo_path.name

        # Get commits for different windows
        commits_7d = get_commits_since(repo_path, 7)
        commits_30d = get_commits_since(repo_path, 30)

        if commits_7d:
            repos_7d.add(repo_name)
            commits_7d_total += len(commits_7d)
            repo_commits_7d[repo_name] = len(commits_7d)

            # Track last push
            latest_commit = max(commits_7d, key=lambda c: c["timestamp"])
            if last_push_time is None or latest_commit["timestamp"] > last_push_time:
                last_push_time = latest_commit["timestamp"]
                hours_ago = (datetime.now(timezone.utc) - latest_commit["timestamp"]).total_seconds() / 3600
                last_push_data = {
                    "repo": repo_name,
                    "timestamp": latest_commit["timestamp"].isoformat(),
                    "hours_ago": round(hours_ago, 2)
                }

        if commits_30d:
            repos_30d.add(repo_name)
            commits_30d_total += len(commits_30d)

            # Aggregate language stats
            language = detect_language(repo_path)
            if language:
                language_commits_30d[language] += len(commits_30d)

    # Top repos by commits in 7d
    top_repos = [
        {"repo": repo, "commits": count}
        for repo, count in sorted(repo_commits_7d.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Language distribution
    languages = [
        {"name": lang, "commits": count}
        for lang, count in sorted(language_commits_30d.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "repos_active_7d": len(repos_7d),
        "repos_active_30d": len(repos_30d),
        "commits_7d": commits_7d_total,
        "commits_30d": commits_30d_total,
        "languages_30d": languages,
        "last_push": last_push_data,
        "top_repos_7d": top_repos
    }


def main():
    """Test the parser with real git directory"""
    git_dir = Path.home() / "git"

    if not git_dir.exists():
        print(f"Git directory not found: {git_dir}")
        return

    import json
    result = parse_github_activity(git_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
