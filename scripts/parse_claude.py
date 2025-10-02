"""Parse Claude Code session data from ~/.claude/projects/"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List, Any


def extract_repo_from_cwd(cwd: str) -> str:
    """Extract repo name from cwd path like /Users/davidrose/git/stopsign_ai"""
    if not cwd:
        return "unknown"
    parts = Path(cwd).parts
    if "git" in parts:
        git_idx = parts.index("git")
        if git_idx + 1 < len(parts):
            return parts[git_idx + 1]
    return "unknown"


def parse_claude_sessions(sessions_dir: Path, days_back: int = 7) -> Dict[str, Any]:
    """
    Parse all Claude sessions within the time window.

    Returns:
        dict with sessions_Xd, turns_Xd, repos, last_session
    """
    cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
    cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)

    sessions_7d = []
    sessions_30d = []

    # Find all session files
    session_files = list(sessions_dir.rglob("*.jsonl"))

    for session_file in session_files:
        try:
            with open(session_file, 'r') as f:
                lines = f.readlines()

            if not lines:
                continue

            # Parse first line to get session metadata
            first_line = json.loads(lines[0])
            timestamp_str = first_line.get("timestamp")
            cwd = first_line.get("cwd")
            session_id = first_line.get("sessionId")

            if not timestamp_str or not cwd:
                continue

            # Parse timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            repo = extract_repo_from_cwd(cwd)
            turn_count = len(lines)

            session_data = {
                "repo": repo,
                "timestamp": timestamp,
                "turns": turn_count,
                "session_id": session_id
            }

            # Categorize by time window
            if timestamp >= cutoff_7d:
                sessions_7d.append(session_data)
            if timestamp >= cutoff_30d:
                sessions_30d.append(session_data)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Skip malformed sessions
            continue

    # Aggregate by repo
    def aggregate_repos(sessions: List[Dict]) -> List[Dict[str, Any]]:
        repo_stats = defaultdict(lambda: {"sessions": 0, "turns": 0})
        for session in sessions:
            repo = session["repo"]
            repo_stats[repo]["sessions"] += 1
            repo_stats[repo]["turns"] += session["turns"]

        return [
            {"repo": repo, "sessions": stats["sessions"], "turns": stats["turns"]}
            for repo, stats in sorted(repo_stats.items(), key=lambda x: x[1]["sessions"], reverse=True)
        ]

    # Find last session
    last_session = None
    if sessions_7d:
        latest = max(sessions_7d, key=lambda s: s["timestamp"])
        hours_ago = (datetime.now(timezone.utc) - latest["timestamp"]).total_seconds() / 3600
        last_session = {
            "repo": latest["repo"],
            "timestamp": latest["timestamp"].isoformat(),
            "hours_ago": round(hours_ago, 2)
        }

    return {
        "sessions_7d": len(sessions_7d),
        "sessions_30d": len(sessions_30d),
        "turns_7d": sum(s["turns"] for s in sessions_7d),
        "turns_30d": sum(s["turns"] for s in sessions_30d),
        "repos": aggregate_repos(sessions_7d),
        "last_session": last_session
    }


def main():
    """Test the parser with fixtures"""
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "claude"

    if not fixtures_dir.exists():
        print(f"Fixtures directory not found: {fixtures_dir}")
        return

    result = parse_claude_sessions(fixtures_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
