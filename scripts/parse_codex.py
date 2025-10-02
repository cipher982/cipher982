"""Parse OpenAI Codex session data from ~/.codex/sessions/"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List, Any


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


def parse_codex_sessions(sessions_dir: Path, days_back: int = 7) -> Dict[str, Any]:
    """
    Parse all Codex sessions within the time window.

    Codex format:
    - First line: {"type": "session_meta", "payload": {"cwd": "...", "timestamp": "..."}}
    - Subsequent lines: response_item with type message

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

            # Parse first line for session metadata
            first_line = json.loads(lines[0])

            # Codex stores metadata in payload
            if first_line.get("type") == "session_meta":
                payload = first_line.get("payload", {})
                timestamp_str = payload.get("timestamp") or first_line.get("timestamp")
                cwd = payload.get("cwd")
                session_id = payload.get("id")
            else:
                # Fallback if format differs
                timestamp_str = first_line.get("timestamp")
                cwd = first_line.get("payload", {}).get("cwd")
                session_id = session_file.stem

            if not timestamp_str:
                continue

            # Parse timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            repo = extract_repo_from_cwd(cwd) if cwd else "unknown"
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
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "codex"

    if not fixtures_dir.exists():
        print(f"Fixtures directory not found: {fixtures_dir}")
        return

    result = parse_codex_sessions(fixtures_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
