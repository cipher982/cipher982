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

echo "✅ Profile updated successfully!"
echo ""
echo "📋 Next steps:"
echo "   git add README.md hero.svg data/profile-data.json"
echo "   git commit -m \"chore: update profile dashboard\""
echo "   git push"
