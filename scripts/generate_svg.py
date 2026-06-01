#!/usr/bin/env python3
"""Generate the profile hero SVG.

The hero leads with *what gets shipped* — identity, flagship projects, and
real build cadence — not a leaderboard of which AI tools were used. Metrics
are pulled live from data/profile-data.json so the strip stays current; the
identity copy and flagship list are stable constants below.
"""
import json
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


def build_area_path(values: List[int], x: float, y: float, w: float, h: float):
    """Return (line_path, area_path) for a filled-area sparkline.

    line_path traces the top edge; area_path closes it down to the baseline
    for the gradient fill. Coordinates are absolute (no nested viewBox) so the
    gradient renders consistently across GitHub's SVG sanitizer.
    """
    if not values or len(values) < 2:
        return "", ""

    max_val = max(values)
    min_val = min(values)
    rng = (max_val - min_val) or 1
    step = w / (len(values) - 1)

    pts = []
    for i, v in enumerate(values):
        px = x + i * step
        # Leave a little headroom so the peak isn't flush with the top.
        norm = (v - min_val) / rng
        py = y + h - (norm * (h - 6)) - 3
        pts.append((px, py))

    line = "M " + " L ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    area = (
        f"M {pts[0][0]:.1f},{y + h:.1f} "
        + "L " + " L ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        + f" L {pts[-1][0]:.1f},{y + h:.1f} Z"
    )
    return line, area


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

    # Commit sparkline from the daily series (oldest -> newest). Confined to
    # the right half so it doesn't collide with the stat numbers on the left.
    daily = [d["commits"] for d in gh.get("daily_commits", [])]
    spark_x = 360
    spark_line, spark_area = build_area_path(daily, spark_x, 224, WIDTH - PAD - spark_x, 46)

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
      .spark-line {{ stroke: #58a6ff; stroke-width: 2; fill: none; }}
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
        .spark-line {{ stroke: #0969da; }}
        .divider {{ stroke: #eaeef2; }}
      }}

      @keyframes draw {{ from {{ stroke-dashoffset: 1400; }} to {{ stroke-dashoffset: 0; }} }}
      .spark-line {{ stroke-dasharray: 1400; animation: draw 1.6s cubic-bezier(0.22, 1, 0.36, 1) forwards; }}
    </style>

    <linearGradient id="area-fill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#58a6ff" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="#58a6ff" stop-opacity="0"/>
    </linearGradient>
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

  <!-- Commit sparkline (right-aligned, ~60% width) -->
  <text x="{WIDTH - PAD}" y="216" class="stat-label" text-anchor="end">daily commits</text>
  <path d="{spark_area}" fill="url(#area-fill)"/>
  <path d="{spark_line}" class="spark-line"/>
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
