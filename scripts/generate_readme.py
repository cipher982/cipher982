#!/usr/bin/env python3
"""Generate README from template and profile data"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def generate_shipping_table(data: Dict[str, Any]) -> str:
    """Generate markdown table for top repos"""
    repos = data["aggregate"]["top_repos_combined"]

    table = "| Repo | Commits | AI Sessions |\n"
    table += "|------|---------|-------------|\n"

    for repo in repos:
        table += f"| **{repo['repo']}** | {repo['commits']} | {repo['ai_sessions']} |\n"

    return table


def generate_language_badges(data: Dict[str, Any]) -> str:
    """Generate language badges"""
    languages = data["github"]["languages_30d"][:3]  # Top 3

    badge_colors = {
        "Python": "3776AB",
        "TypeScript": "3178C6",
        "JavaScript": "F7DF1E",
        "Go": "00ADD8",
        "Rust": "000000",
        "Shell": "89e051"
    }

    badges = []
    for lang in languages:
        name = lang["name"]
        color = badge_colors.get(name, "gray")
        badges.append(f"![{name}](https://img.shields.io/badge/{name}-{color}?style=flat-square&logo={name.lower()}&logoColor=white)")

    return " ".join(badges)


def format_number(num: int) -> str:
    """Format large numbers"""
    if num >= 1000:
        return f"{num/1000:.1f}k"
    return str(num)


def generate_readme(data: Dict[str, Any]) -> str:
    """Generate README from template"""
    template_path = Path(__file__).parent.parent / "TEMPLATE.md"

    with open(template_path, 'r') as f:
        template = f.read()

    # Calculate average turns per session
    total_sessions = data["aggregate"]["ai_sessions_7d"]
    total_turns = data["aggregate"]["ai_turns_7d"]
    avg_turns = int(total_turns / total_sessions) if total_sessions > 0 else 0

    # Generate components
    shipping_table = generate_shipping_table(data)
    language_badges = generate_language_badges(data)

    # Format languages for detailed stats
    languages_30d = ", ".join([f"{l['name']} ({l['commits']})" for l in data["github"]["languages_30d"]])

    # Replacements
    replacements = {
        "{{SHIPPING_TABLE}}": shipping_table,
        "{{AVG_TURNS}}": str(avg_turns),
        "{{LANGUAGE_BADGES}}": language_badges,
        "{{COMMITS_30D}}": str(data["github"]["commits_30d"]),
        "{{LANGUAGES_30D}}": languages_30d,
        "{{CLAUDE_30D}}": str(data["claude"]["sessions_30d"]),
        "{{CODEX_30D}}": str(data["codex"]["sessions_30d"]),
        "{{TURNS_30D}}": format_number(data["claude"]["turns_30d"] + data["codex"]["turns_30d"]),
        "{{UPDATED_AT}}": datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
    }

    # Apply replacements
    readme = template
    for placeholder, value in replacements.items():
        readme = readme.replace(placeholder, value)

    return readme


def main():
    """Generate README from template and data"""
    data_file = Path(__file__).parent.parent / "data" / "profile-data.json"
    output_file = Path(__file__).parent.parent / "README.md"

    if not data_file.exists():
        print(f"Error: {data_file} not found. Run collect_data.py first.")
        return

    with open(data_file, 'r') as f:
        data = json.load(f)

    print("📝 Generating README from template...")
    readme = generate_readme(data)

    with open(output_file, 'w') as f:
        f.write(readme)

    print(f"✅ README written to {output_file}")


if __name__ == "__main__":
    main()
