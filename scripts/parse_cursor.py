"""Parse Cursor IDE session data from SQLite database"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, Any


def parse_cursor_sessions(db_path: Path = None, days_back: int = 7) -> Dict[str, Any]:
    """
    Parse Cursor IDE composer sessions from global storage database.

    Args:
        db_path: Path to state.vscdb (defaults to standard location)
        days_back: Number of days to include in analysis

    Returns:
        dict with sessions_Xd, turns_Xd, repos (empty for now), last_session
    """
    if db_path is None:
        db_path = Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"

    if not db_path.exists():
        print(f"⚠️  Cursor database not found: {db_path}")
        return _empty_result()

    cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
    cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # First pass: count messages (bubbles) per composer
        cursor.execute("SELECT key FROM cursorDiskKV WHERE key LIKE 'bubbleId:%'")
        message_counts = defaultdict(int)
        for (key,) in cursor.fetchall():
            parts = key.split(':')
            if len(parts) >= 2:
                composer_id = parts[1]
                message_counts[composer_id] += 1

        # Second pass: get composer metadata
        cursor.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'")

        sessions_7d = []
        sessions_30d = []
        sessions_by_date = defaultdict(lambda: {"sessions": 0, "turns": 0})

        for key, value_blob in cursor.fetchall():
            try:
                if not value_blob:
                    continue

                composer_id = key.split(':')[1]
                data = json.loads(value_blob)

                created_at = data.get('createdAt')
                if not created_at:
                    continue

                timestamp = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)

                # Get actual message count from bubbles
                message_count = message_counts.get(composer_id, 0)
                turns = message_count if message_count > 0 else 1  # Min 1 for session creation

                session_data = {
                    "composerId": composer_id,
                    "timestamp": timestamp,
                    "mode": data.get('unifiedMode', 'unknown'),
                    "turns": turns
                }

                # Categorize by time window
                if timestamp >= cutoff_7d:
                    sessions_7d.append(session_data)
                    session_date = timestamp.date().isoformat()
                    sessions_by_date[session_date]["sessions"] += 1
                    sessions_by_date[session_date]["turns"] += turns

                if timestamp >= cutoff_30d:
                    sessions_30d.append(session_data)

            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        conn.close()

    except sqlite3.Error as e:
        print(f"⚠️  SQLite error: {e}")
        return _empty_result()

    # Find last session
    last_session = None
    if sessions_7d:
        latest = max(sessions_7d, key=lambda s: s["timestamp"])
        hours_ago = (datetime.now(timezone.utc) - latest["timestamp"]).total_seconds() / 3600
        last_session = {
            "mode": latest["mode"],
            "timestamp": latest["timestamp"].isoformat(),
            "hours_ago": round(hours_ago, 2)
        }

    # Convert daily sessions to sorted array
    daily_sessions = [
        {"date": date, "sessions": data["sessions"], "turns": data["turns"]}
        for date, data in sorted(sessions_by_date.items())
    ]

    return {
        "sessions_7d": len(sessions_7d),
        "sessions_30d": len(sessions_30d),
        "turns_7d": sum(s["turns"] for s in sessions_7d),
        "turns_30d": sum(s["turns"] for s in sessions_30d),
        "repos": [],  # Cursor doesn't track per-repo like Claude/Codex
        "last_session": last_session,
        "daily_sessions": daily_sessions
    }


def _empty_result() -> Dict[str, Any]:
    """Return empty result structure when Cursor data unavailable"""
    return {
        "sessions_7d": 0,
        "sessions_30d": 0,
        "turns_7d": 0,
        "turns_30d": 0,
        "repos": [],
        "last_session": None,
        "daily_sessions": []
    }


def main():
    """Test the parser"""
    result = parse_cursor_sessions()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
