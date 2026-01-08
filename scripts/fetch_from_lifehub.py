#!/usr/bin/env python3
"""
Fetch AI agent session data from the Life Hub API.

This module fetches aggregated stats from https://data.drose.io/api/agents/stats
instead of parsing local log files directly. This allows the GitHub profile
to update even when running from GitHub Actions (where local files aren't available).

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
from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta


# Default API configuration
DEFAULT_API_URL = "https://data.drose.io"
API_ENDPOINT = "/api/agents/stats"


def get_api_key() -> Optional[str]:
    """Get the API key from environment."""
    return os.environ.get("LIFE_HUB_API_KEY")


def get_api_url() -> str:
    """Get the API base URL from environment or use default."""
    return os.environ.get("LIFE_HUB_API_URL", DEFAULT_API_URL)


def fetch_stats(since_days: int = 7) -> Optional[Dict[str, Any]]:
    """
    Fetch agent stats from Life Hub API.

    Args:
        since_days: Number of days to look back

    Returns:
        Raw API response dict, or None if request fails
    """
    api_key = get_api_key()
    if not api_key:
        print("   ⚠️  LIFE_HUB_API_KEY not set")
        return None

    url = f"{get_api_url()}{API_ENDPOINT}"
    headers = {"X-API-Key": api_key}
    params = {"since_days": since_days}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Life Hub API request failed: {e}")
        return None


def transform_provider_data(
    stats_7d: Dict[str, Any],
    stats_30d: Dict[str, Any],
    provider: str
) -> Dict[str, Any]:
    """
    Transform Life Hub API response into local parser format.

    The local parsers return:
    {
        "sessions_7d": int,
        "sessions_30d": int,
        "turns_7d": int,    # mapped from 'events' in API
        "turns_30d": int,
        "repos": [{"repo": str, "sessions": int, "turns": int}],
        "last_session": {...} or None,
        "daily_sessions": [{"date": str, "sessions": int, "turns": int}]
    }

    The Life Hub API returns:
    {
        "totals": {"total_sessions": int, "total_events": int, "total_user_messages": int, ...},
        "by_provider": [{"provider": str, "sessions": int, "events": int, "user_messages": int}],
        "by_project": [{"project": str, "sessions": int, "events": int}]
    }
    """
    # Find this provider in the 7-day stats
    provider_7d = None
    for p in stats_7d.get("by_provider", []):
        if p.get("provider", "").lower() == provider.lower():
            provider_7d = p
            break

    # Find this provider in the 30-day stats
    provider_30d = None
    for p in stats_30d.get("by_provider", []):
        if p.get("provider", "").lower() == provider.lower():
            provider_30d = p
            break

    sessions_7d = provider_7d.get("sessions", 0) if provider_7d else 0
    sessions_30d = provider_30d.get("sessions", 0) if provider_30d else 0

    # Life Hub API returns 'events' which corresponds to 'turns' in the local parsers
    # But the parsers actually count lines (including metadata), so we use user_messages
    # as a closer proxy to what "turns" means (user interactions)
    turns_7d = provider_7d.get("user_messages", 0) if provider_7d else 0
    turns_30d = provider_30d.get("user_messages", 0) if provider_30d else 0

    # Build repos list from by_project (filtered by this provider)
    # Note: Life Hub's by_project doesn't filter by provider, so we can't perfectly
    # match the local parser behavior. We'll return an empty list for now.
    # The aggregate function in collect_data.py handles repos from git commits anyway.
    repos = []

    # We don't have daily breakdown from the API (would need additional endpoint)
    # Return empty - the aggregate function will handle this gracefully
    daily_sessions = []

    return {
        "sessions_7d": sessions_7d,
        "sessions_30d": sessions_30d,
        "turns_7d": turns_7d,
        "turns_30d": turns_30d,
        "repos": repos,
        "last_session": None,  # API doesn't provide this currently
        "daily_sessions": daily_sessions,
    }


def fetch_all_providers() -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Fetch data for all providers from Life Hub API.

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

    # Transform data for each provider
    providers = ["claude", "codex", "cursor", "gemini"]
    result = {}

    for provider in providers:
        result[provider] = transform_provider_data(stats_7d, stats_30d, provider)
        print(f"   ✓ {provider}: {result[provider]['sessions_7d']} sessions, {result[provider]['turns_7d']} turns (7d)")

    return result


def main():
    """Test the Life Hub API fetch."""
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
    else:
        print("\n❌ Failed to fetch data from Life Hub API")


if __name__ == "__main__":
    main()
