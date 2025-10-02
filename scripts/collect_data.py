#!/usr/bin/env python3
"""Main orchestrator to collect all profile data"""
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
from collections import defaultdict

from parse_claude import parse_claude_sessions
from parse_codex import parse_codex_sessions
from parse_github import parse_github_activity

# Repos to exclude from dashboard (work projects, private exploration, etc.)
EXCLUDED_REPOS = [
    "zeta",
]


def aggregate_metrics(github_data: Dict, claude_data: Dict, codex_data: Dict) -> Dict[str, Any]:
    """
    Combine GitHub, Claude, and Codex data with aggregate metrics.

    Returns complete profile-data.json structure
    """

    # Filter out excluded repos from all data sources
    def filter_repos(repo_list):
        return [r for r in repo_list if r["repo"] not in EXCLUDED_REPOS]

    github_data["top_repos_7d"] = filter_repos(github_data["top_repos_7d"])
    claude_data["repos"] = filter_repos(claude_data["repos"])
    codex_data["repos"] = filter_repos(codex_data["repos"])

    # Recalculate AI metrics after filtering
    claude_sessions_filtered = sum(r["sessions"] for r in claude_data["repos"])
    codex_sessions_filtered = sum(r["sessions"] for r in codex_data["repos"])
    claude_turns_filtered = sum(r["turns"] for r in claude_data["repos"])
    codex_turns_filtered = sum(r["turns"] for r in codex_data["repos"])

    ai_sessions_7d = claude_sessions_filtered + codex_sessions_filtered
    ai_turns_7d = claude_turns_filtered + codex_turns_filtered

    claude_pct = (claude_sessions_filtered / ai_sessions_7d * 100) if ai_sessions_7d > 0 else 0
    codex_pct = (codex_sessions_filtered / ai_sessions_7d * 100) if ai_sessions_7d > 0 else 0

    # Combine top repos (commits + AI sessions)
    repo_scores = defaultdict(lambda: {"commits": 0, "ai_sessions": 0})

    # Add git commits
    for repo_data in github_data["top_repos_7d"]:
        repo_scores[repo_data["repo"]]["commits"] = repo_data["commits"]

    # Add Claude sessions
    for repo_data in claude_data["repos"]:
        repo_scores[repo_data["repo"]]["ai_sessions"] += repo_data["sessions"]

    # Add Codex sessions
    for repo_data in codex_data["repos"]:
        repo_scores[repo_data["repo"]]["ai_sessions"] += repo_data["sessions"]

    # Sort by total activity (commits + sessions) and take top 5
    top_repos_combined = []
    for repo, data in repo_scores.items():
        top_repos_combined.append({
            "repo": repo,
            "commits": data["commits"],
            "ai_sessions": data["ai_sessions"]
        })

    # Sort by commits first, then sessions
    top_repos_combined.sort(key=lambda x: (x["commits"] + x["ai_sessions"]), reverse=True)
    top_repos_combined = top_repos_combined[:5]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "github": github_data,
        "claude": claude_data,
        "codex": codex_data,
        "aggregate": {
            "ai_sessions_7d": ai_sessions_7d,
            "ai_turns_7d": ai_turns_7d,
            "claude_percentage": round(claude_pct, 1),
            "codex_percentage": round(codex_pct, 1),
            "top_repos_combined": top_repos_combined
        }
    }


def main():
    """Collect all data and write to data/profile-data.json"""

    # Define paths
    home = Path.home()
    git_dir = home / "git"
    claude_sessions = home / ".claude" / "projects"
    codex_sessions = home / ".codex" / "sessions"
    output_file = Path(__file__).parent.parent / "data" / "profile-data.json"

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print("🔍 Collecting GitHub activity...")
    github_data = parse_github_activity(git_dir)
    print(f"   ✓ {github_data['commits_7d']} commits, {github_data['repos_active_7d']} repos (7d)")

    print("🔍 Collecting Claude sessions...")
    claude_data = parse_claude_sessions(claude_sessions)
    print(f"   ✓ {claude_data['sessions_7d']} sessions, {claude_data['turns_7d']} turns (7d)")

    print("🔍 Collecting Codex sessions...")
    codex_data = parse_codex_sessions(codex_sessions)
    print(f"   ✓ {codex_data['sessions_7d']} sessions, {codex_data['turns_7d']} turns (7d)")

    print("📊 Aggregating metrics...")
    profile_data = aggregate_metrics(github_data, claude_data, codex_data)

    print(f"💾 Writing to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(profile_data, f, indent=2)

    print("✅ Done!")
    print(f"\n📈 Summary:")
    print(f"   Git: {profile_data['github']['commits_7d']} commits across {profile_data['github']['repos_active_7d']} repos")
    print(f"   AI:  {profile_data['aggregate']['ai_sessions_7d']} sessions, {profile_data['aggregate']['ai_turns_7d']} turns")
    print(f"   Split: Claude {profile_data['aggregate']['claude_percentage']}%, Codex {profile_data['aggregate']['codex_percentage']}%")


if __name__ == "__main__":
    main()
