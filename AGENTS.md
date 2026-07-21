# GitHub profile README

This repository renders above the pinned repositories on the `cipher982`
GitHub profile.

- Fetch immediately before editing; the scheduled dashboard workflow pushes
  generated metric updates and can race a stale local checkout.
- Keep durable identity copy in `README.template.md` and the generator
  constants. Regenerate `README.md` and `assets/hero.svg` from those sources.
- Treat `data/profile-data.json` and rendered dashboard metrics as generated
  output. Do not hand-edit them or overwrite a fresh automation update.
- Account-level display name, bio, and profile URL are not controlled by this
  repository and require a separately approved GitHub token with `user` scope.
