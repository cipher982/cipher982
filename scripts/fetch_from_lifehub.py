#!/usr/bin/env python3
"""
Fetch AI agent session data from the Longhouse API.

This module fetches data from the Longhouse instance (previously Life Hub)
to allow the GitHub profile to update from GitHub Actions.

Usage:
    Set LONGHOUSE_DEVICE_TOKEN and optionally LONGHOUSE_API_URL, then:

    from fetch_from_lifehub import fetch_all_providers

    data = fetch_all_providers()
    # Returns dict with 'claude', 'codex', 'cursor', 'gemini' keys

Environment Variables:
    LONGHOUSE_DEVICE_TOKEN: Required. Device token (zdt_...) for Longhouse API.
    LIFE_HUB_API_KEY: Fallback alias (same token, different env var name).
    LONGHOUSE_API_URL: Optional. Base URL (default: https://david010.longhouse.ai)
"""

import os
import requests
from typing import Dict, Any, Optional, List
from collections import defaultdict
from datetime import datetime, timedelta, timezone


DEFAULT_API_URL = "https://david010.longhouse.ai"
PAGE_SIZE = 100


def get_device_token() -> Optional[str]:
    """Get Longhouse device token from environment."""
    return os.environ.get("LONGHOUSE_DEVICE_TOKEN") or os.environ.get("LIFE_HUB_API_KEY")


def get_api_url() -> str:
    return os.environ.get("LONGHOUSE_API_URL", DEFAULT_API_URL)


def _fetch_sessions_page(token: str, days_back: int, offset: int) -> Optional[Dict[str, Any]]:
    url = f"{get_api_url()}/api/agents/sessions"
    headers = {"X-Agents-Token": token}
    params = {
        "days_back": days_back,
        "limit": PAGE_SIZE,
        "offset": offset,
        "include_test": "false",
        "hide_autonomous": "true",
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Longhouse API request failed: {e}")
        return None


def _fetch_all_sessions(token: str, days_back: int) -> Optional[List[Dict[str, Any]]]:
    """Fetch all sessions for the given window, paginating as needed."""
    first = _fetch_sessions_page(token, days_back, 0)
    if first is None:
        return None

    sessions = list(first.get("sessions", []))
    total = first.get("total", 0)

    offset = PAGE_SIZE
    while offset < total:
        page = _fetch_sessions_page(token, days_back, offset)
        if page is None:
            break
        sessions.extend(page.get("sessions", []))
        offset += PAGE_SIZE

    return sessions


def compute_daily_breakdown(sessions: List[Dict[str, Any]], days: int = 7) -> List[Dict[str, Any]]:
    daily = defaultdict(lambda: {"sessions": 0, "turns": 0})
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    for session in sessions:
        started_at = session.get("started_at")
        if not started_at:
            continue
        try:
            ts = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts < cutoff:
            continue
        date_str = ts.date().isoformat()
        daily[date_str]["sessions"] += 1
        daily[date_str]["turns"] += session.get("user_messages") or 1

    return [
        {"date": date, "sessions": data["sessions"], "turns": data["turns"]}
        for date, data in sorted(daily.items())
    ]


def compute_repos_from_sessions(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    repo_stats = defaultdict(lambda: {"sessions": 0, "turns": 0})
    for session in sessions:
        project = session.get("project")
        if not project:
            continue
        repo_stats[project]["sessions"] += 1
        repo_stats[project]["turns"] += session.get("user_messages") or 1

    return [
        {"repo": repo, "sessions": stats["sessions"], "turns": stats["turns"]}
        for repo, stats in sorted(repo_stats.items(), key=lambda x: x[1]["sessions"], reverse=True)
    ]


def find_last_session(sessions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not sessions:
        return None
    latest = None
    latest_ts = None
    for session in sessions:
        started_at = session.get("started_at")
        if not started_at:
            continue
        try:
            ts = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if latest_ts is None or ts > latest_ts:
            latest = session
            latest_ts = ts

    if not latest or not latest_ts:
        return None

    hours_ago = (datetime.now(timezone.utc) - latest_ts).total_seconds() / 3600
    return {
        "repo": latest.get("project", "unknown"),
        "timestamp": latest_ts.isoformat(),
        "hours_ago": round(hours_ago, 2),
    }


def _build_provider_data(
    sessions_7d: List[Dict[str, Any]],
    sessions_30d: List[Dict[str, Any]],
    provider: str,
) -> Dict[str, Any]:
    p7 = [s for s in sessions_7d if s.get("provider", "").lower() == provider.lower()]
    p30 = [s for s in sessions_30d if s.get("provider", "").lower() == provider.lower()]

    turns_7d = sum(s.get("user_messages") or 0 for s in p7)
    turns_30d = sum(s.get("user_messages") or 0 for s in p30)

    return {
        "sessions_7d": len(p7),
        "sessions_30d": len(p30),
        "turns_7d": turns_7d,
        "turns_30d": turns_30d,
        "repos": compute_repos_from_sessions(p7),
        "last_session": find_last_session(p7),
        "daily_sessions": compute_daily_breakdown(p7, days=7),
    }


def fetch_all_providers() -> Optional[Dict[str, Dict[str, Any]]]:
    """Fetch data for all providers from Longhouse API."""
    token = get_device_token()
    if not token:
        print("   ⚠️  No Longhouse device token found (LONGHOUSE_DEVICE_TOKEN or LIFE_HUB_API_KEY)")
        return None

    print("   Fetching 7-day sessions...")
    sessions_7d = _fetch_all_sessions(token, days_back=7)
    if sessions_7d is None:
        return None
    print(f"   ✓ Got {len(sessions_7d)} sessions (7d)")

    print("   Fetching 30-day sessions...")
    sessions_30d = _fetch_all_sessions(token, days_back=30)
    if sessions_30d is None:
        print("   ⚠️  Failed to fetch 30-day sessions, using 7-day for 30d stats")
        sessions_30d = sessions_7d

    result = {}
    for provider in ["claude", "codex", "cursor", "gemini"]:
        result[provider] = _build_provider_data(sessions_7d, sessions_30d, provider)
        print(
            f"   ✓ {provider}: {result[provider]['sessions_7d']} sessions, "
            f"{result[provider]['turns_7d']} turns (7d)"
        )

    return result


def main():
    """Test the Longhouse API fetch."""
    import json

    token = get_device_token()
    if not token:
        print("Error: set LONGHOUSE_DEVICE_TOKEN or LIFE_HUB_API_KEY")
        return

    result = fetch_all_providers()
    if result:
        print("\n✅ Successfully fetched data from Longhouse API")
        for provider, data in result.items():
            print(f"\n{provider}:")
            print(f"  Sessions (7d): {data['sessions_7d']}")
            print(f"  Sessions (30d): {data['sessions_30d']}")
            print(f"  Turns (7d): {data['turns_7d']}")
    else:
        print("\n❌ Failed to fetch data from Longhouse API")


if __name__ == "__main__":
    main()
