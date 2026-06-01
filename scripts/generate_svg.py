#!/usr/bin/env python3
"""Generate the profile hero SVG.

The hero leads with *what gets shipped* — identity, flagship projects, and
real build cadence — not a leaderboard of which AI tools were used. Metrics
are pulled live from data/profile-data.json so the strip stays current; the
identity copy and flagship list are stable constants below.
"""
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

# --- Identity (stable) -------------------------------------------------------
NAME = "David Rose"
ROLE = "AI Systems Engineer"
TAGLINE = "I build autonomous agents, LLM tooling, and ship real products."
HANDLE = "@cipher982"

# Flagship work shown as chips in the hero. Keep to three — the full list
# lives in the README body.
FLAGSHIP = ["Longhouse", "Stop Sign Nanny", "LLM Benchmarks"]

# --- Layout ------------------------------------------------------------------
WIDTH = 900
HEIGHT = 300
PAD = 36


def format_number(num: int) -> str:
    return f"{num:,}"


def build_contribution_grid(
    daily_commits: List[Dict[str, Any]], x: float, y: float
) -> str:
    """A GitHub-style contribution grid of the last ~4 weeks of commits.

    Intensity → opacity bucket, so the strip reads as "consistently active"
    with no up/down slope. The current (partial) day is excluded so a quiet
    morning never reads as a slump; missing days render as empty cells.
    """
    cell = 11       # square size
    gap = 3         # gap between squares
    weeks = 6       # columns
    rows = 5        # rows — 6×5 = last 30 days

    by_date = {d["date"]: d["commits"] for d in daily_commits}

    # The grid ends yesterday (today is partial). Build a contiguous run of
    # weeks*rows days ending there, oldest first.
    if by_date:
        latest = max(date.fromisoformat(d) for d in by_date)
    else:
        latest = date.today()
    end = min(latest, date.today() - timedelta(days=1))
    total_days = weeks * rows
    days = [end - timedelta(days=i) for i in range(total_days - 1, -1, -1)]

    counts = [by_date.get(d.isoformat(), 0) for d in days]

    def opacity(c: int) -> float:
        # Fixed commit-count buckets (not scaled to peak) so a single
        # outlier day doesn't wash everything else into the dimmest tint.
        if c == 0:
            return 0.08          # empty-cell tint
        if c <= 3:
            return 0.40
        if c <= 8:
            return 0.62
        if c <= 15:
            return 0.82
        return 1.0

    squares = []
    for idx, c in enumerate(counts):
        col = idx // rows
        row = idx % rows
        cx = x + col * (cell + gap)
        cy = y + row * (cell + gap)
        squares.append(
            f'<rect x="{cx:.0f}" y="{cy:.0f}" width="{cell}" height="{cell}" '
            f'rx="3" class="cell" fill-opacity="{opacity(c):.2f}"/>'
        )
    return "\n  ".join(squares)


def chip(label: str, x: float, y: float) -> str:
    """A rounded pill chip with a leading marker. Width is estimated from
    character count (SVG has no text metrics) — good enough at this size."""
    w = 22 + len(label) * 8.2
    return f'''
    <g transform="translate({x:.0f}, {y:.0f})">
      <rect width="{w:.0f}" height="30" rx="15" class="chip-bg"/>
      <circle cx="16" cy="15" r="3" class="chip-dot"/>
      <text x="28" y="20" class="chip-text">{label}</text>
    </g>''', w


def generate_hero_svg(data: Dict[str, Any]) -> str:
    gh = data["github"]
    commits_30d = gh.get("commits_30d", 0)
    repos_30d = gh.get("repos_active_30d", 0)

    # Contribution grid (last 30 days) — right-aligned. 6 cols × 5 rows of
    # 11px cells + 3px gaps = 81px wide, 67px tall.
    grid_w = 6 * (11 + 3) - 3
    grid_x = WIDTH - PAD - grid_w
    grid = build_contribution_grid(gh.get("daily_commits", []), grid_x, 218)

    # Flagship chips, laid out left-to-right with consistent gaps.
    chips_svg = ""
    cx = PAD
    for name in FLAGSHIP:
        markup, w = chip(name, cx, 150)
        chips_svg += markup
        cx += w + 12

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{NAME} — {ROLE}">
  <defs>
    <style>
      .bg {{ fill: #0d1117; }}
      .frame {{ stroke: #30363d; fill: none; }}
      .name {{ font: 700 34px 'Segoe UI', -apple-system, system-ui, sans-serif; fill: #e6edf3; }}
      .role {{ font: 600 17px 'Segoe UI', -apple-system, system-ui, sans-serif; fill: #58a6ff; letter-spacing: 0.3px; }}
      .tagline {{ font: 400 15px 'Segoe UI', -apple-system, system-ui, sans-serif; fill: #8b949e; }}
      .handle {{ font: 500 13px 'SF Mono', ui-monospace, 'Consolas', monospace; fill: #6e7681; }}
      .chip-bg {{ fill: #161b22; stroke: #30363d; stroke-width: 1; }}
      .chip-dot {{ fill: #58a6ff; }}
      .chip-text {{ font: 500 13px 'Segoe UI', -apple-system, system-ui, sans-serif; fill: #c9d1d9; }}
      .stat-num {{ font: 700 22px 'SF Mono', ui-monospace, 'Consolas', monospace; fill: #e6edf3; }}
      .stat-label {{ font: 400 12px 'Segoe UI', -apple-system, system-ui, sans-serif; fill: #8b949e; }}
      .cell {{ fill: #58a6ff; }}
      .divider {{ stroke: #21262d; stroke-width: 1; }}

      @media (prefers-color-scheme: light) {{
        .bg {{ fill: #ffffff; }}
        .frame {{ stroke: #d0d7de; }}
        .name {{ fill: #1f2328; }}
        .role {{ fill: #0969da; }}
        .tagline {{ fill: #636c76; }}
        .handle {{ fill: #818b98; }}
        .chip-bg {{ fill: #f6f8fa; stroke: #d0d7de; }}
        .chip-dot {{ fill: #0969da; }}
        .chip-text {{ fill: #1f2328; }}
        .stat-num {{ fill: #1f2328; }}
        .stat-label {{ fill: #636c76; }}
        .cell {{ fill: #0969da; }}
        .divider {{ stroke: #eaeef2; }}
      }}

      @keyframes fade-in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
      .grid {{ animation: fade-in 1.2s ease-out forwards; }}
    </style>
  </defs>

  <rect width="{WIDTH}" height="{HEIGHT}" class="bg" rx="12"/>
  <rect x="1" y="1" width="{WIDTH - 2}" height="{HEIGHT - 2}" class="frame" stroke-width="1" rx="12"/>

  <!-- Identity -->
  <text x="{PAD}" y="62" class="name">{NAME}</text>
  <text x="{WIDTH - PAD}" y="40" class="handle" text-anchor="end">{HANDLE}</text>
  <text x="{PAD}" y="90" class="role">{ROLE}</text>
  <text x="{PAD}" y="120" class="tagline">{TAGLINE}</text>

  <!-- Flagship chips -->
  {chips_svg}

  <line x1="{PAD}" y1="198" x2="{WIDTH - PAD}" y2="198" class="divider"/>

  <!-- Shipping metrics -->
  <g transform="translate({PAD}, 224)">
    <text x="0" y="0" class="stat-num">{format_number(commits_30d)}</text>
    <text x="0" y="18" class="stat-label">commits · 30d</text>

    <text x="150" y="0" class="stat-num">{repos_30d}</text>
    <text x="150" y="18" class="stat-label">active repos</text>
  </g>

  <!-- Contribution grid (last 30 days, right-aligned) -->
  <text x="{WIDTH - PAD}" y="210" class="stat-label" text-anchor="end">commit activity · 30d</text>
  <g class="grid">
  {grid}
  </g>
</svg>'''
    return svg


def main():
    data_file = Path(__file__).parent.parent / "data" / "profile-data.json"
    output_file = Path(__file__).parent.parent / "hero.svg"

    if not data_file.exists():
        print(f"Error: {data_file} not found. Run collect_data.py first.")
        return

    with open(data_file) as f:
        data = json.load(f)

    print("🎨 Generating hero SVG...")
    svg = generate_hero_svg(data)

    with open(output_file, "w") as f:
        f.write(svg)

    print(f"✅ SVG written to {output_file} ({WIDTH}×{HEIGHT})")


if __name__ == "__main__":
    main()
