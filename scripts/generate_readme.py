#!/usr/bin/env python3
"""Render README.md from TEMPLATE.md.

The profile README is curated directly in TEMPLATE.md with static and
art-directed visual assets under assets/. Keeping this script lets any
workflow or local command regenerate README.md cleanly without reintroducing
commit-count vanity stats.
"""
from pathlib import Path


def main() -> None:
    root = Path(__file__).parent.parent
    template_path = root / "TEMPLATE.md"
    output_path = root / "README.md"
    output_path.write_text(template_path.read_text())
    print(f"README written to {output_path} from {template_path.name}")


if __name__ == "__main__":
    main()
