#!/usr/bin/env python3
"""Generate README from template and profile data.

The project lists in TEMPLATE.md are curated by hand. This script only fills
the dynamic build-cadence numbers and language badges from the collected data.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def generate_language_badges(data: Dict[str, Any]) -> str:
    """Top-3 language badges from the 30-day commit breakdown."""
    languages = data["github"]["languages_30d"][:3]

    badge_colors = {
        "Python": "3776AB",
        "TypeScript": "3178C6",
        "JavaScript": "F7DF1E",
        "Go": "00ADD8",
        "Rust": "000000",
        "Shell": "89e051",
        "Swift": "F05138",
        "C++": "00599C",
    }

    badges = []
    for lang in languages:
        name = lang["name"]
        color = badge_colors.get(name, "gray")
        slug = name.lower().replace("+", "%2B")
        badges.append(
            f"![{name}](https://img.shields.io/badge/{name}-{color}"
            f"?style=flat-square&logo={slug}&logoColor=white)"
        )

    return " ".join(badges)


def generate_readme(data: Dict[str, Any]) -> str:
    template_path = Path(__file__).parent.parent / "TEMPLATE.md"
    with open(template_path) as f:
        template = f.read()

    gh = data["github"]
    agg = data["aggregate"]

    # 30-day agent sessions across all providers.
    ai_sessions_30d = sum(
        data[tool].get("sessions_30d", 0)
        for tool in ("claude", "codex", "cursor", "gemini")
    )

    replacements = {
        "{{LANGUAGE_BADGES}}": generate_language_badges(data),
        "{{COMMITS_30D}}": f"{gh['commits_30d']:,}",
        "{{REPOS_30D}}": str(gh["repos_active_30d"]),
        "{{AI_SESSIONS_30D}}": str(ai_sessions_30d),
        "{{UPDATED_AT}}": datetime.fromisoformat(
            data["generated_at"].replace("Z", "+00:00")
        ).strftime("%Y-%m-%d %H:%M UTC"),
    }

    readme = template
    for placeholder, value in replacements.items():
        readme = readme.replace(placeholder, value)

    return readme


def main():
    data_file = Path(__file__).parent.parent / "data" / "profile-data.json"
    output_file = Path(__file__).parent.parent / "README.md"

    if not data_file.exists():
        print(f"Error: {data_file} not found. Run collect_data.py first.")
        return

    with open(data_file) as f:
        data = json.load(f)

    print("📝 Generating README from template...")
    readme = generate_readme(data)

    with open(output_file, "w") as f:
        f.write(readme)

    print(f"✅ README written to {output_file}")


if __name__ == "__main__":
    main()
