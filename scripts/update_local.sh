#!/bin/bash
# Local update script - run this manually to update your profile

set -e

echo "🔄 Updating profile dashboard..."
echo ""

# Collect data
python3 scripts/collect_data.py
echo ""

# Generate SVG
python3 scripts/generate_svg.py
echo ""

# Generate README
python3 scripts/generate_readme.py
echo ""

# Commit with amend to avoid spam
git add README.md hero.svg data/profile-data.json
if git diff --quiet && git diff --staged --quiet; then
  echo "📋 No changes to commit"
else
  # Check if last commit was an auto-update
  LAST_MSG=$(git log -1 --pretty=%B)
  if [[ "$LAST_MSG" == "chore: auto-update profile dashboard" ]]; then
    # Amend the existing auto-update commit
    git commit --amend --no-edit --date="$(date)"
    git push --force-with-lease origin main
    echo "✅ Profile updated (amended existing commit) and pushed"
  else
    # Create new auto-update commit
    git commit -m "chore: auto-update profile dashboard"
    git push origin main
    echo "✅ Profile updated (new commit) and pushed"
  fi
fi
