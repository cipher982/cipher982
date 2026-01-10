#!/usr/bin/env python3
"""
Fetch AI agent session data from the Life Hub API.

This module fetches data from https://data.drose.io instead of parsing local
log files directly. This allows the GitHub profile to update even when running
from GitHub Actions (where local files aren't available).

Usage:
    Set LIFE_HUB_API_KEY environment variable, then:

    from fetch_from_lifehub import fetch_all_providers

    data = fetch_all_providers()
    # Returns dict with 'claude', 'codex', 'cursor', 'gemini' keys
    # Each has same structure as local parsers return

Environment Variables:
    LIFE_HUB_API_KEY: Required. API key for authenticating with Life Hub.
    LIFE_HUB_API_URL: Optional. Base URL (default: https://data.drose.io)
"""

import os
import requests
from typing import Dict, Any, Optional, List
from collections import defaultdict
from datetime import datetime, timedelta, timezone


# Default API configuration
DEFAULT_API_URL = "https://data.drose.io"


def get_api_key() -> Optional[str]:
    """Get the API key from environment."""
    return os.environ.get("LIFE_HUB_API_KEY")


def get_api_url() -> str:
    """Get the API base URL from environment or use default."""
    return os.environ.get("LIFE_HUB_API_URL", DEFAULT_API_URL)


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    Make an authenticated request to the Life Hub API.

    Args:
        endpoint: API endpoint path (e.g., "/api/agents/stats")
        params: Optional query parameters

    Returns:
        JSON response dict, or None if request fails
    """
    api_key = get_api_key()
    if not api_key:
        print("   ⚠️  LIFE_HUB_API_KEY not set")
        return None

    url = f"{get_api_url()}{endpoint}"
    headers = {"X-API-Key": api_key}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Life Hub API request failed: {e}")
        return None


def fetch_stats(since_days: int = 7) -> Optional[Dict[str, Any]]:
    """
    Fetch aggregate agent stats from Life Hub API.

    Args:
        since_days: Number of days to look back

    Returns:
        Raw API response dict, or None if request fails
    """
    return _make_request("/api/agents/stats", {"since_days": since_days})


def fetch_sessions(
    provider: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 500
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch agent sessions from Life Hub API.

    Args:
        provider: Filter by provider (claude, codex, gemini, cursor)
        since: Filter sessions started after this time
        limit: Maximum number of sessions to return

    Returns:
        List of session dicts, or None if request fails
    """
    params = {"limit": limit}
    if provider:
        params["provider"] = provider
    if since:
        params["since"] = since.isoformat()

    result = _make_request("/query/agents/sessions", params)
    if result:
        return result.get("data", [])
    return None


def compute_daily_breakdown(
    sessions: List[Dict[str, Any]],
    days: int = 7
) -> List[Dict[str, Any]]:
    """
    Compute daily session breakdown from session list.

    Args:
        sessions: List of session dicts with 'started_at' and 'events_total' fields
        days: Number of days to include

    Returns:
        List of {"date": str, "sessions": int, "turns": int} sorted by date
    """
    daily = defaultdict(lambda: {"sessions": 0, "turns": 0})

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    for session in sessions:
        started_at = session.get("started_at")
        if not started_at:
            continue

        # Parse timestamp (handle both string and datetime)
        if isinstance(started_at, str):
            try:
                ts = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            except ValueError:
                continue
        else:
            ts = started_at

        # Only include sessions within the time window
        if ts < cutoff:
            continue

        date_str = ts.date().isoformat()
        daily[date_str]["sessions"] += 1
        daily[date_str]["turns"] += session.get("events_total", 0) or session.get("user_messages", 0) or 1

    # Convert to sorted list
    return [
        {"date": date, "sessions": data["sessions"], "turns": data["turns"]}
        for date, data in sorted(daily.items())
    ]


def compute_repos_from_sessions(
    sessions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Compute per-repo stats from session list.

    Uses the 'project' field from sessions (extracted from cwd by Life Hub).

    Args:
        sessions: List of session dicts with 'project' and 'events_total' fields

    Returns:
        List of {"repo": str, "sessions": int, "turns": int} sorted by sessions desc
    """
    repo_stats = defaultdict(lambda: {"sessions": 0, "turns": 0})

    for session in sessions:
        project = session.get("project")
        if not project:
            continue

        repo_stats[project]["sessions"] += 1
        repo_stats[project]["turns"] += session.get("events_total", 0) or session.get("user_messages", 0) or 1

    # Convert to sorted list
    return [
        {"repo": repo, "sessions": stats["sessions"], "turns": stats["turns"]}
        for repo, stats in sorted(repo_stats.items(), key=lambda x: x[1]["sessions"], reverse=True)
    ]


def find_last_session(sessions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Find the most recent session from a list.

    Args:
        sessions: List of session dicts

    Returns:
        Dict with repo, timestamp, hours_ago or None
    """
    if not sessions:
        return None

    # Find session with latest started_at
    latest = None
    latest_ts = None

    for session in sessions:
        started_at = session.get("started_at")
        if not started_at:
            continue

        if isinstance(started_at, str):
            try:
                ts = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            except ValueError:
                continue
        else:
            ts = started_at

        if latest_ts is None or ts > latest_ts:
            latest = session
            latest_ts = ts

    if not latest or not latest_ts:
        return None

    hours_ago = (datetime.now(timezone.utc) - latest_ts).total_seconds() / 3600

    return {
        "repo": latest.get("project", "unknown"),
        "timestamp": latest_ts.isoformat(),
        "hours_ago": round(hours_ago, 2)
    }


def transform_provider_data(
    stats_7d: Dict[str, Any],
    stats_30d: Dict[str, Any],
    sessions_7d: List[Dict[str, Any]],
    sessions_30d: List[Dict[str, Any]],
    provider: str
) -> Dict[str, Any]:
    """
    Transform Life Hub API response into local parser format.

    The local parsers return:
    {
        "sessions_7d": int,
        "sessions_30d": int,
        "turns_7d": int,
        "turns_30d": int,
        "repos": [{"repo": str, "sessions": int, "turns": int}],
        "last_session": {...} or None,
        "daily_sessions": [{"date": str, "sessions": int, "turns": int}]
    }
    """
    # Find this provider in the stats
    provider_7d = None
    for p in stats_7d.get("by_provider", []):
        if p.get("provider", "").lower() == provider.lower():
            provider_7d = p
            break

    provider_30d = None
    for p in stats_30d.get("by_provider", []):
        if p.get("provider", "").lower() == provider.lower():
            provider_30d = p
            break

    sessions_count_7d = provider_7d.get("sessions", 0) if provider_7d else 0
    sessions_count_30d = provider_30d.get("sessions", 0) if provider_30d else 0

    # Use user_messages for turns (actual conversation turns, not raw event count)
    turns_7d = provider_7d.get("user_messages", 0) if provider_7d else 0
    turns_30d = provider_30d.get("user_messages", 0) if provider_30d else 0

    # Filter sessions for this provider
    provider_sessions_7d = [s for s in sessions_7d if s.get("provider", "").lower() == provider.lower()]
    provider_sessions_30d = [s for s in sessions_30d if s.get("provider", "").lower() == provider.lower()]

    # Compute repos from 7-day sessions
    repos = compute_repos_from_sessions(provider_sessions_7d)

    # Compute daily breakdown from 7-day sessions
    daily_sessions = compute_daily_breakdown(provider_sessions_7d, days=7)

    # Find last session
    last_session = find_last_session(provider_sessions_7d)

    return {
        "sessions_7d": sessions_count_7d,
        "sessions_30d": sessions_count_30d,
        "turns_7d": turns_7d,
        "turns_30d": turns_30d,
        "repos": repos,
        "last_session": last_session,
        "daily_sessions": daily_sessions,
    }


def fetch_all_providers() -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Fetch data for all providers from Life Hub API.

    Fetches both aggregate stats (fast) and individual sessions (for daily
    breakdown and per-repo stats).

    Returns:
        Dict with keys 'claude', 'codex', 'cursor', 'gemini',
        each containing data in the same format as local parsers.
        Returns None if API call fails.
    """
    print("   Fetching 7-day stats...")
    stats_7d = fetch_stats(since_days=7)
    if not stats_7d:
        return None

    print("   Fetching 30-day stats...")
    stats_30d = fetch_stats(since_days=30)
    if not stats_30d:
        return None

    # Fetch individual sessions for daily breakdown and repos
    print("   Fetching 7-day sessions...")
    since_7d = datetime.now(timezone.utc) - timedelta(days=7)
    sessions_7d = fetch_sessions(since=since_7d, limit=500)
    if sessions_7d is None:
        print("   ⚠️  Failed to fetch sessions, continuing with stats only")
        sessions_7d = []

    print("   Fetching 30-day sessions...")
    since_30d = datetime.now(timezone.utc) - timedelta(days=30)
    sessions_30d = fetch_sessions(since=since_30d, limit=500)
    if sessions_30d is None:
        print("   ⚠️  Failed to fetch sessions, continuing with stats only")
        sessions_30d = []

    # Transform data for each provider
    providers = ["claude", "codex", "cursor", "gemini"]
    result = {}

    for provider in providers:
        result[provider] = transform_provider_data(
            stats_7d, stats_30d, sessions_7d, sessions_30d, provider
        )
        repos_count = len(result[provider].get("repos", []))
        daily_count = len(result[provider].get("daily_sessions", []))
        print(f"   ✓ {provider}: {result[provider]['sessions_7d']} sessions, "
              f"{result[provider]['turns_7d']} turns, {repos_count} repos, "
              f"{daily_count} days (7d)")

    return result


def main():
    """Test the Life Hub API fetch."""
    import json

    print("Testing Life Hub API fetch...")

    api_key = get_api_key()
    if not api_key:
        print("Error: LIFE_HUB_API_KEY environment variable not set")
        print("Set it with: export LIFE_HUB_API_KEY='your-key'")
        return

    result = fetch_all_providers()
    if result:
        print("\n✅ Successfully fetched data from Life Hub API")
        for provider, data in result.items():
            print(f"\n{provider}:")
            print(f"  Sessions (7d): {data['sessions_7d']}")
            print(f"  Sessions (30d): {data['sessions_30d']}")
            print(f"  Turns (7d): {data['turns_7d']}")
            print(f"  Turns (30d): {data['turns_30d']}")
            print(f"  Repos: {len(data.get('repos', []))}")
            if data.get("repos"):
                for repo in data["repos"][:3]:
                    print(f"    - {repo['repo']}: {repo['sessions']} sessions")
            print(f"  Daily sessions: {len(data.get('daily_sessions', []))} days")
            if data.get("last_session"):
                print(f"  Last session: {data['last_session']['repo']} "
                      f"({data['last_session']['hours_ago']:.1f}h ago)")
    else:
        print("\n❌ Failed to fetch data from Life Hub API")


if __name__ == "__main__":
    main()
