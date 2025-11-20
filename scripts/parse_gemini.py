#!/usr/bin/env python3
"""
Parse Gemini CLI session data from ~/.gemini/tmp/*/logs.json
"""
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any


def parse_gemini_sessions() -> Dict[str, Any]:
    """
    Parse Gemini CLI sessions from logs.json files.

    Returns:
        Dict with sessions_7d, sessions_30d, turns_7d, turns_30d, and daily_sessions
    """
    gemini_dir = Path.home() / ".gemini"
    tmp_dir = gemini_dir / "tmp"

    if not tmp_dir.exists():
        print(f"   ⚠️  No Gemini tmp directory found at {tmp_dir}")
        return {
            "sessions_7d": 0,
            "sessions_30d": 0,
            "turns_7d": 0,
            "turns_30d": 0,
            "daily_sessions": []
        }

    # Find all logs.json files
    logs_files = list(tmp_dir.rglob("logs.json"))
    print(f"   Found {len(logs_files)} logs files")

    if not logs_files:
        print(f"   ⚠️  No logs.json files found")
        return {
            "sessions_7d": 0,
            "sessions_30d": 0,
            "turns_7d": 0,
            "turns_30d": 0,
            "daily_sessions": []
        }

    # Track sessions and turns
    sessions_7d = set()
    sessions_30d = set()
    turns_7d = 0
    turns_30d = 0

    # Track daily sessions
    daily_sessions = defaultdict(int)

    # Parse all logs
    for logs_file in logs_files:
        try:
            with open(logs_file, 'r') as f:
                messages = json.load(f)

            for msg in messages:
                if msg.get("type") != "user":
                    continue

                session_id = msg.get("sessionId")
                timestamp_str = msg.get("timestamp")
                message_id = msg.get("messageId", 0)

                if not session_id or not timestamp_str:
                    continue

                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except:
                    continue

                now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
                days_ago = (now - timestamp).days

                # Add to 30-day tracking
                sessions_30d.add(session_id)
                turns_30d += 1

                # Track daily sessions (30 days)
                date_str = timestamp.strftime("%Y-%m-%d")
                daily_sessions[date_str] += 1

                # Add to 7-day tracking
                if days_ago <= 7:
                    sessions_7d.add(session_id)
                    turns_7d += 1

        except Exception as e:
            print(f"   ⚠️  Error parsing {logs_file}: {e}")
            continue

    # Convert daily sessions to sorted list (last 30 days)
    today = datetime.now().date()
    daily_list = []
    for i in range(30):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        daily_list.append({
            "date": date_str,
            "sessions": daily_sessions[date_str]
        })
    daily_list.reverse()

    return {
        "sessions_7d": len(sessions_7d),
        "sessions_30d": len(sessions_30d),
        "turns_7d": turns_7d,
        "turns_30d": turns_30d,
        "daily_sessions": daily_list
    }


if __name__ == "__main__":
    data = parse_gemini_sessions()
    print(json.dumps(data, indent=2))
