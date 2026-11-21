# GitHub profile README

This repository renders above the pinned repositories on the `cipher982`
GitHub profile.

- Fetch before editing (`git pull --ff-only`).
- Keep durable copy in `TEMPLATE.md` and regenerate `README.md` with
  `python3 scripts/generate_readme.py`.
- Visual showcase cards live in `assets/` (`g55-truck.svg`, `g55-eval.png`,
  `longhouse.svg`, `hdrpop.png`, `rayban-meta.svg`, `llm-benchmarks.png`,
  `floodmap.jpg`). Keep images in the same HTML table row at identical aspect
  ratios so rows align flush on GitHub.
- Run `python3 scripts/check_links.py README.md TEMPLATE.md` before pushing.
- Account-level display name, bio, pinned repos, and profile URL are controlled
  in GitHub account settings, not this repository.
