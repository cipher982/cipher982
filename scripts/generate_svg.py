#!/usr/bin/env python3
"""Generate hero SVG from profile data"""
import json
from pathlib import Path
from typing import Dict, Any


def format_large_number(num: int) -> str:
    """Format large numbers with k suffix"""
    if num >= 1000:
        return f"{num/1000:.1f}k"
    return str(num)


def generate_hero_svg(data: Dict[str, Any]) -> str:
    """
    Generate a clean, professional SVG hero image.

    Layout:
    - Top: Big metrics (AI sessions, turns, commits, repos)
    - Middle: Claude vs Codex split bar
    - Bottom: Last activity indicator
    """

    # Extract metrics
    ai_sessions = data["aggregate"]["ai_sessions_7d"]
    ai_turns = data["aggregate"]["ai_turns_7d"]
    commits = data["github"]["commits_7d"]
    repos = data["github"]["repos_active_7d"]

    claude_pct = data["aggregate"]["claude_percentage"]
    codex_pct = data["aggregate"]["codex_percentage"]

    # Find most recent activity (git or AI)
    last_git = data["github"].get("last_push")
    last_claude = data["claude"].get("last_session")
    last_codex = data["codex"].get("last_session")

    last_activity = "Unknown"
    if last_git:
        hours_ago = last_git["hours_ago"]
        if hours_ago < 1:
            last_activity = f"{int(hours_ago * 60)}m ago"
        elif hours_ago < 24:
            last_activity = f"{int(hours_ago)}h ago"
        else:
            last_activity = f"{int(hours_ago / 24)}d ago"

    # SVG dimensions
    width = 900
    height = 200

    # Colors (GitHub native palette)
    bg_color = "#0d1117"
    border_color = "#30363d"
    text_primary = "#c9d1d9"
    text_secondary = "#8b949e"
    claude_color = "#58a6ff"  # GitHub blue
    codex_color = "#8b949e"   # GitHub gray
    accent_color = "#58a6ff"

    # Generate SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <style>
      .title {{ font: bold 20px 'Segoe UI', Ubuntu, sans-serif; fill: {text_primary}; }}
      .metric-value {{ font: bold 32px 'Segoe UI', Ubuntu, monospace; fill: {accent_color}; }}
      .metric-label {{ font: 12px 'Segoe UI', Ubuntu, sans-serif; fill: {text_secondary}; }}
      .bar-label {{ font: 13px 'Segoe UI', Ubuntu, sans-serif; fill: {text_primary}; }}
      .last-activity {{ font: 14px 'Segoe UI', Ubuntu, sans-serif; fill: {text_secondary}; }}
    </style>
  </defs>

  <!-- Background -->
  <rect width="{width}" height="{height}" fill="{bg_color}" rx="8"/>
  <rect x="1" y="1" width="{width-2}" height="{height-2}" fill="none" stroke="{border_color}" stroke-width="1" rx="8"/>

  <!-- Title -->
  <text x="30" y="35" class="title">🤖 AI-Native Development Dashboard</text>

  <!-- Metrics Row -->
  <g transform="translate(30, 70)">
    <!-- AI Sessions -->
    <text x="0" y="0" class="metric-value">{ai_sessions}</text>
    <text x="0" y="20" class="metric-label">AI SESSIONS</text>

    <!-- Turns -->
    <text x="200" y="0" class="metric-value">{format_large_number(ai_turns)}</text>
    <text x="200" y="20" class="metric-label">TURNS</text>

    <!-- Commits -->
    <text x="380" y="0" class="metric-value">{commits}</text>
    <text x="380" y="20" class="metric-label">COMMITS</text>

    <!-- Repos -->
    <text x="530" y="0" class="metric-value">{repos}</text>
    <text x="530" y="20" class="metric-label">ACTIVE REPOS</text>
  </g>

  <!-- AI Split Bar -->
  <g transform="translate(30, 130)">
    <text x="0" y="0" class="metric-label">LAST 7 DAYS</text>

    <!-- Claude segment -->
    <rect x="0" y="10" width="{claude_pct * 8}" height="24" fill="{claude_color}" rx="2"/>
    <text x="10" y="28" class="bar-label">Claude {claude_pct}%</text>

    <!-- Codex segment -->
    <rect x="{claude_pct * 8}" y="10" width="{codex_pct * 8}" height="24" fill="{codex_color}" rx="2"/>
    <text x="{claude_pct * 8 + 10}" y="28" class="bar-label">Codex {codex_pct}%</text>
  </g>

  <!-- Last Activity -->
  <text x="30" y="{height - 20}" class="last-activity">⚡ Last activity: {last_activity}</text>
</svg>'''

    return svg


def main():
    """Generate SVG from profile data"""
    data_file = Path(__file__).parent.parent / "data" / "profile-data.json"
    output_file = Path(__file__).parent.parent / "hero.svg"

    if not data_file.exists():
        print(f"Error: {data_file} not found. Run collect_data.py first.")
        return

    with open(data_file, 'r') as f:
        data = json.load(f)

    print("🎨 Generating hero SVG...")
    svg = generate_hero_svg(data)

    with open(output_file, 'w') as f:
        f.write(svg)

    print(f"✅ SVG written to {output_file}")


if __name__ == "__main__":
    main()
