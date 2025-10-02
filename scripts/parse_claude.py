"""Parse Claude Code session data from ~/.claude/projects/"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional


def extract_repo_from_cwd(cwd: str) -> str:
    """Extract meaningful name from working directory"""
    if not cwd:
        return "unknown"

    path = Path(cwd)

    # Home directory
    if path == Path.home():
        return "Home"

    # Check if in ~/git/* structure (your actual directory layout)
    parts = path.parts
    if "git" in parts:
        idx = parts.index("git")
        if idx + 1 < len(parts):
            return parts[idx + 1]

    # Fallback: use last directory name
    return path.name if path.name else "unknown"


# Global cache: directory slug -> cwd path
_slug_cache = {}


def find_field_in_session(lines: List[str], field: str) -> Optional[Any]:
    """
    Walk session lines until we find a non-null value for the given field.
    Some sessions start with summary objects; metadata appears on line 2+.
    """
    for line in lines[:10]:  # Check first 10 lines max
        try:
            obj = json.loads(line)
            value = obj.get(field)
            if value and value != "null":
                return value
        except json.JSONDecodeError:
            continue
    return None


def resolve_cwd_from_slug(slug: str) -> Optional[str]:
    """
    Resolve cwd using cached slug→cwd mappings.
    Slug format: -Users-davidrose-git-ai-tools-website
    Can't decode directly due to hyphens in real dir names.
    """
    return _slug_cache.get(slug)


def parse_claude_sessions(sessions_dir: Path, days_back: int = 7) -> Dict[str, Any]:
    """
    Parse all Claude sessions within the time window.

    Strategy:
    1. Primary: Walk each file until we find non-null cwd (handles summary-first files)
    2. Fallback: Use slug→cwd cache from previous sessions
    3. Validation: Compare slug vs cwd when both present

    Returns:
        dict with sessions_Xd, turns_Xd, repos, last_session
    """
    cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
    cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)

    sessions_7d = []
    sessions_30d = []

    # Find all session files
    session_files = list(sessions_dir.rglob("*.jsonl"))

    # First pass: build slug cache from sessions with valid cwd
    for session_file in session_files:
        try:
            with open(session_file, 'r') as f:
                lines = f.readlines()

            if not lines:
                continue

            cwd = find_cwd_in_session(lines)
            if cwd:
                slug = session_file.parent.name
                _slug_cache[slug] = cwd
        except Exception:
            continue

    # Second pass: parse sessions with fallback to cache
    for session_file in session_files:
        try:
            with open(session_file, 'r') as f:
                lines = f.readlines()

            if not lines:
                continue

            # Find cwd (walks multiple lines for summary-first files)
            cwd = find_field_in_session(lines, "cwd")

            # Fallback: use slug cache
            if not cwd:
                slug = session_file.parent.name
                cwd = resolve_cwd_from_slug(slug)

            if not cwd:
                continue  # Still no cwd, skip session

            # Find timestamp (also walks multiple lines)
            timestamp_str = find_field_in_session(lines, "timestamp")
            session_id = find_field_in_session(lines, "sessionId")

            if not timestamp_str:
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
