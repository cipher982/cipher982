#!/usr/bin/env python3
"""Generate hero SVG from profile data"""
import json
from pathlib import Path
from typing import Dict, Any, List


def format_large_number(num: int) -> str:
    """Format large numbers with k suffix"""
    if num >= 1000:
        return f"{num/1000:.1f}k"
    return str(num)


def generate_sparkline_path(values: List[int], width: int, height: int) -> str:
    """
    Generate SVG path for sparkline.

    Args:
        values: List of values (e.g. [12, 18, 24, 21, 15, 10, 16])
        width: Path width in pixels
        height: Path height in pixels

    Returns:
        SVG path d attribute string
    """
    if not values or len(values) < 2:
        return ""

    max_val = max(values) if max(values) > 0 else 1
    min_val = min(values)
    range_val = max_val - min_val if max_val != min_val else 1

    step = width / (len(values) - 1)
    points = []

    for i, val in enumerate(values):
        x = i * step
        # Normalize to height, invert Y (SVG origin is top-left)
        normalized = (val - min_val) / range_val
        y = height - (normalized * height)
        points.append(f"{x:.2f},{y:.2f}")

    return "M " + " L ".join(points)


def generate_hero_svg(data: Dict[str, Any]) -> str:
    """
    Generate enhanced SVG hero image with sparklines and cards.

    Layout (900×300px):
    - Tier 1 (0-90px): Title + 4 key metrics
    - Tier 2 (90-190px): 2 sparklines (commits, AI sessions)
    - Tier 3 (190-280px): Side-by-side Claude/Codex cards
    - Footer (280-300px): Last activity
    """

    # Extract metrics
    ai_sessions = data["aggregate"]["ai_sessions_7d"]
    ai_turns = data["aggregate"]["ai_turns_7d"]
    commits = data["github"]["commits_7d"]
    repos = data["github"]["repos_active_7d"]

    claude_sessions = sum(r["sessions"] for r in data["claude"]["repos"])
    codex_sessions = sum(r["sessions"] for r in data["codex"]["repos"])
    claude_turns = data["claude"]["turns_7d"]
    codex_turns = data["codex"]["turns_7d"]

    claude_pct = data["aggregate"]["claude_percentage"]
    codex_pct = data["aggregate"]["codex_percentage"]

    # Get daily data for sparklines
    daily_breakdown = data["aggregate"].get("daily_breakdown_7d", [])
    daily_commits = [d["commits"] for d in daily_breakdown]
    daily_sessions = [d["total_sessions"] for d in daily_breakdown]

    # Calculate sparkline paths
    sparkline_commits = generate_sparkline_path(daily_commits, 180, 40) if daily_commits else ""
    sparkline_sessions = generate_sparkline_path(daily_sessions, 180, 40) if daily_sessions else ""

    # Calculate path lengths for animation
    def path_length(path: str) -> float:
        """Rough estimate of path length for animation"""
        return len(path.split("L")) * 30  # Approximate

    commits_path_len = path_length(sparkline_commits) if sparkline_commits else 0
    sessions_path_len = path_length(sparkline_sessions) if sparkline_sessions else 0

    # Find most recent activity
    last_git = data["github"].get("last_push")
    hours_ago = last_git["hours_ago"] if last_git else 999

    if hours_ago < 1:
        last_activity = f"{int(hours_ago * 60)}m ago"
    elif hours_ago < 24:
        last_activity = f"{int(hours_ago)}h ago"
    else:
        last_activity = f"{int(hours_ago / 24)}d ago"

    # SVG dimensions
    width = 900
    height = 300

    # Generate SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <style>
      /* Dark mode (default) */
      .bg {{ fill: #0d1117; }}
      .border {{ stroke: #30363d; fill: none; }}
      .text-primary {{ fill: #c9d1d9; }}
      .text-secondary {{ fill: #8b949e; }}
      .card-bg {{ fill: #161b22; }}
      .card-border {{ stroke: #30363d; fill: none; }}

      .title {{ font: bold 22px 'Segoe UI', -apple-system, sans-serif; }}
      .metric-value {{ font: bold 36px 'SF Mono', 'Consolas', monospace; fill: #58a6ff; }}
      .metric-label {{ font: 11px 'Segoe UI', -apple-system, sans-serif; letter-spacing: 0.5px; }}
      .sparkline-label {{ font: 13px 'Segoe UI', -apple-system, sans-serif; }}
      .card-title {{ font: bold 16px 'Segoe UI', -apple-system, sans-serif; }}
      .card-value {{ font: bold 28px 'SF Mono', 'Consolas', monospace; fill: #58a6ff; }}
      .card-stat {{ font: 13px 'Segoe UI', -apple-system, sans-serif; }}
      .footer {{ font: 13px 'Segoe UI', -apple-system, sans-serif; }}

      .sparkline-commits {{ stroke: #58a6ff; stroke-width: 2.5; fill: none; }}
      .sparkline-sessions {{ stroke: #a371f7; stroke-width: 2.5; fill: none; }}

      /* Light mode */
      @media (prefers-color-scheme: light) {{
        .bg {{ fill: #ffffff; }}
        .border {{ stroke: #d0d7de; }}
        .text-primary {{ fill: #1f2328; }}
        .text-secondary {{ fill: #636c76; }}
        .card-bg {{ fill: #f6f8fa; }}
        .card-border {{ stroke: #d0d7de; }}
        .metric-value {{ fill: #0969da; }}
        .card-value {{ fill: #0969da; }}
      }}

      /* Pulse animation for lightning bolt */
      @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
      }}
      .pulse {{ animation: pulse 3s ease-in-out infinite; }}
    </style>
  </defs>

  <!-- Background -->
  <rect width="{width}" height="{height}" class="bg" rx="10"/>
  <rect x="1" y="1" width="{width-2}" height="{height-2}" class="border" stroke-width="1" rx="10"/>

  <!-- Tier 1: Title & Metrics -->
  <text x="30" y="40" class="title text-primary">🤖 AI-Native Development Dashboard</text>

  <g transform="translate(30, 75)">
    <!-- AI Sessions -->
    <text x="0" y="0" class="metric-value">{ai_sessions}</text>
    <text x="0" y="18" class="metric-label text-secondary">AI SESSIONS</text>

    <!-- Turns -->
    <text x="220" y="0" class="metric-value">{format_large_number(ai_turns)}</text>
    <text x="220" y="18" class="metric-label text-secondary">TURNS</text>

    <!-- Commits -->
    <text x="420" y="0" class="metric-value">{commits}</text>
    <text x="420" y="18" class="metric-label text-secondary">COMMITS</text>

    <!-- Repos -->
    <text x="620" y="0" class="metric-value">{repos}</text>
    <text x="620" y="18" class="metric-label text-secondary">ACTIVE REPOS</text>
  </g>

  <!-- Tier 2: Sparklines -->
  <g transform="translate(30, 140)">
    <text x="0" y="0" class="sparkline-label text-secondary">Activity (Last 7 Days)</text>

    <!-- Commits sparkline -->
    <g transform="translate(0, 20)">
      <text x="0" y="25" class="sparkline-label text-secondary">Commits</text>
      <svg x="80" y="0" width="180" height="40" viewBox="0 0 180 40">
        <path d="{sparkline_commits}" class="sparkline-commits" stroke-dasharray="{commits_path_len}" stroke-dashoffset="{commits_path_len}">
          <animate attributeName="stroke-dashoffset" from="{commits_path_len}" to="0" dur="1.2s" fill="freeze"/>
        </path>
      </svg>
    </g>

    <!-- AI Sessions sparkline -->
    <g transform="translate(420, 20)">
      <text x="0" y="25" class="sparkline-label text-secondary">AI Sessions</text>
      <svg x="110" y="0" width="180" height="40" viewBox="0 0 180 40">
        <path d="{sparkline_sessions}" class="sparkline-sessions" stroke-dasharray="{sessions_path_len}" stroke-dashoffset="{sessions_path_len}">
          <animate attributeName="stroke-dashoffset" from="{sessions_path_len}" to="0" dur="1.2s" fill="freeze"/>
        </path>
      </svg>
    </g>
  </g>

  <!-- Tier 3: Tool Cards -->
  <g transform="translate(30, 210)">
    <!-- Claude Card -->
    <rect x="0" y="0" width="410" height="65" class="card-bg" rx="6"/>
    <rect x="0" y="0" width="410" height="65" class="card-border" stroke-width="1" rx="6"/>

    <text x="20" y="25" class="card-title text-primary">Claude Code</text>
    <text x="20" y="50" class="card-value">{claude_sessions}</text>
    <text x="90" y="50" class="card-stat text-secondary">sessions · {format_large_number(claude_turns)} turns · {claude_pct}%</text>

    <!-- Codex Card -->
    <rect x="440" y="0" width="410" height="65" class="card-bg" rx="6"/>
    <rect x="440" y="0" width="410" height="65" class="card-border" stroke-width="1" rx="6"/>

    <text x="460" y="25" class="card-title text-primary">OpenAI Codex</text>
    <text x="460" y="50" class="card-value">{codex_sessions}</text>
    <text x="530" y="50" class="card-stat text-secondary">sessions · {format_large_number(codex_turns)} turns · {codex_pct}%</text>
  </g>

  <!-- Footer: Last Activity -->
  <text x="30" y="{height - 15}" class="footer text-secondary">
    <tspan class="pulse">⚡</tspan> Last activity: {last_activity}
  </text>
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
    print(f"   Size: 900×300px")
    daily_days = len(data['aggregate'].get('daily_breakdown_7d', []))
    print(f"   Sparklines: {daily_days} days of data")


if __name__ == "__main__":
    main()
