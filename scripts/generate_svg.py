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
NAME = "David W. Rose"
ROLE = "I tinker with machines. Some of them think."
TAGLINE = "Projects and notes, from CAN buses to context windows."
HANDLE = "@cipher982"

# Flagship work shown as chips in the hero. Keep to three — the full list
# lives in the README body.
FLAGSHIP = ["Longhouse", "Stop Sign Nanny", "LLM Benchmarks"]

# --- Layout ------------------------------------------------------------------
WIDTH = 900
HEIGHT = 372
PAD = 36


def format_number(num: int) -> str:
    return f"{num:,}"


# Contribution calendar geometry (GitHub-style: weeks as columns, weekdays
# as rows). 53 columns covers a full trailing year.
CAL_CELL = 9
CAL_GAP = 2
CAL_COLS = 53
CAL_ROWS = 7
CAL_W = CAL_COLS * (CAL_CELL + CAL_GAP) - CAL_GAP
CAL_H = CAL_ROWS * (CAL_CELL + CAL_GAP) - CAL_GAP


def _intensity(c: int) -> float:
    # Fixed activity buckets (not scaled to peak) so a single outlier day
    # doesn't wash everything else into the dimmest tint.
    if c == 0:
        return 0.09          # empty-cell tint
    if c <= 3:
        return 0.40
    if c <= 8:
        return 0.62
    if c <= 15:
        return 0.82
    return 1.0


_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_COL_STEP = CAL_CELL + CAL_GAP


def build_contribution_calendar(
    daily_commits: List[Dict[str, Any]], x: float, y: float
) -> str:
    """A full-year GitHub-style contribution heatmap with month + weekday labels.

    Columns are weeks (oldest left → newest right), rows are weekdays
    (Sunday top). Month labels along the top and weekday labels on the left
    make the time axis legible — so the boundaries read as "start of the
    window," not "didn't commit." Intensity is bucketed by activity (not
    scaled to peak) so the grid reads as consistent activity with no slope.
    Future days and days with no data render as faint empty cells.
    """
    by_date = {d["date"]: d["commits"] for d in daily_commits}

    today = date.today()
    # Start at the Sunday 52 weeks back so the final column ends on today.
    sunday_offset = (today.weekday() + 1) % 7  # Mon=0..Sun=6 -> days since Sun
    start = today - timedelta(days=sunday_offset + (CAL_COLS - 1) * 7)

    squares = []
    month_labels = []
    last_month = None

    for col in range(CAL_COLS):
        col_first = start + timedelta(days=col * 7)
        # Label a column when its first day falls in a new month, leaving a
        # little room at the right edge so the last label isn't clipped.
        if col_first.month != last_month and col < CAL_COLS - 1:
            month_labels.append(
                f'<text x="{x + col * _COL_STEP:.0f}" y="{y - 6:.0f}" '
                f'class="cal-label">{_MONTHS[col_first.month - 1]}</text>'
            )
            last_month = col_first.month

        for row in range(CAL_ROWS):
            d = col_first + timedelta(days=row)
            if d > today:
                continue
            c = by_date.get(d.isoformat(), 0)
            cx = x + col * _COL_STEP
            cy = y + row * _COL_STEP
            squares.append(
                f'<rect x="{cx:.0f}" y="{cy:.0f}" width="{CAL_CELL}" '
                f'height="{CAL_CELL}" rx="2" class="cell" '
                f'fill-opacity="{_intensity(c):.2f}"/>'
            )

    # Weekday labels (Mon/Wed/Fri) on the left, aligned to their rows.
    weekday_labels = []
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        ly = y + row * _COL_STEP + CAL_CELL - 1
        weekday_labels.append(
            f'<text x="{x - 8:.0f}" y="{ly:.0f}" class="cal-label" '
            f'text-anchor="end">{name}</text>'
        )

    return "\n  ".join(month_labels + weekday_labels + squares)


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

    # Full-year contribution calendar as its own band near the bottom, with
    # month + weekday labels. Offset right by the weekday-label gutter so the
    # grid + labels sit centered as a unit.
    gutter = 30
    cal_x = (WIDTH - CAL_W - gutter) / 2 + gutter
    cal_y = 278
    calendar = build_contribution_calendar(gh.get("daily_commits", []), cal_x, cal_y)

    # Flagship chips, laid out left-to-right with consistent gaps.
    chips_svg = ""
    cx = PAD
    for name in FLAGSHIP:
        markup, w = chip(name, cx, 150)
        chips_svg += markup
        cx += w + 12

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{NAME}, {ROLE}">
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
      .cal-label {{ font: 400 9px 'Segoe UI', -apple-system, system-ui, sans-serif; fill: #6e7681; }}
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
        .cal-label {{ fill: #818b98; }}
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
  <text x="{WIDTH - PAD}" y="224" class="stat-label" text-anchor="end">commit activity · past year</text>

  <!-- Full-year contribution calendar -->
  <g class="grid">
  {calendar}
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
