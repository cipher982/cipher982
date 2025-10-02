# AI-Native Development Dashboard - MVP

## 🎯 What We Built

A **dynamic GitHub profile README** that showcases your unique "AI-native developer" workflow by combining:
- Traditional git commit metrics
- Claude Code session data
- OpenAI Codex session data

**The MVP validates:**
1. Can we collect and parse AI session data?  ✅
2. Is the data interesting/compelling? ✅
3. Can we visualize it cleanly? ✅
4. Does it tell a story? ✅

## 📊 Real Data (Last 7 Days)

- **120 commits** across 6 repos
- **96 AI pair programming sessions** (46 Claude, 50 Codex)
- **32,372 conversation turns** (~337 avg per session!)
- Nearly **even split** between Claude and Codex (47.9% / 52.1%)

## 🏗️ Architecture

```
cipher982/
├── scripts/
│   ├── parse_claude.py       # Extract Claude session data
│   ├── parse_codex.py        # Extract Codex session data
│   ├── parse_github.py       # Extract git commit data
│   ├── collect_data.py       # Orchestrator - combines all data
│   ├── generate_svg.py       # Render hero.svg
│   ├── generate_readme.py    # Populate README from template
│   └── update_local.sh       # One-command update script
├── data/
│   └── profile-data.json     # Aggregated metrics cache
├── tests/
│   └── fixtures/             # Test data for parsers
├── hero.svg                  # Dynamic dashboard graphic
├── README.md                 # Generated profile (what visitors see)
├── TEMPLATE.md               # README template with placeholders
└── .github/workflows/
    └── update-profile.yml    # Placeholder for future automation
```

## 🚀 Usage

### Update Locally (Recommended for MVP)

```bash
./scripts/update_local.sh
```

This runs the full pipeline:
1. Collects data from git/Claude/Codex
2. Aggregates metrics into `data/profile-data.json`
3. Generates `hero.svg`
4. Populates `README.md` from template

Then commit and push:
```bash
git add README.md hero.svg data/profile-data.json
git commit -m "chore: update profile dashboard"
git push
```

### Individual Components

```bash
# Just collect data
python scripts/collect_data.py

# Just regenerate SVG
python scripts/generate_svg.py

# Just regenerate README
python scripts/generate_readme.py
```

## 📈 Data Schema

See `scripts/schema.json` for the complete JSON schema.

Key metrics:
- `github`: commits, repos, languages, last_push
- `claude`: sessions, turns, repos, last_session
- `codex`: sessions, turns, repos, last_session
- `aggregate`: combined AI metrics, top repos by activity score

## 🎨 Visualization

**Hero SVG** (`hero.svg`):
- Clean, GitHub-dark-theme design
- Key metrics: AI sessions, turns, commits, active repos
- Claude vs Codex split bar
- Last activity timestamp

**README Table**:
- Top 5 repos by combined activity score
- Activity score = commits + (AI sessions × 2)
- Shows both git and AI engagement

## 🔮 Future Enhancements

### v2 - Real-Time & Visual Polish
- [ ] Cloudflare Worker for sub-hour updates
- [ ] Proper sparklines for trends
- [ ] Per-repo drill-down pages
- [ ] Tool usage heatmap (bash/edit/read commands)

### v3 - Data Enrichment
- [ ] Sync session data to S3/R2 for Actions access
- [ ] Integrate deployment status from Coolify
- [ ] AI-generated weekly narrative summaries
- [ ] Code complexity trends

### v4 - Interactive
- [ ] Embed actual chart.js graphs (via Cloudflare Worker)
- [ ] Session timeline view
- [ ] Language evolution over time

## ✅ MVP Success Criteria - All Met!

- ✅ Collects data from 3 sources (git, Claude, Codex)
- ✅ Aggregates into unified metrics
- ✅ Generates clean SVG visualization
- ✅ Auto-populates README from template
- ✅ One-command update workflow
- ✅ Real data proves the concept (32k turns!)

## 🤔 Key Learnings

**What worked:**
- TDD approach with fixtures made parsers easy to validate
- Simple SVG rendering (no external libs) kept it lightweight
- Activity score (commits + AI sessions) surfaces true engagement
- The data is genuinely impressive (337 avg turns/session!)

**Limitations:**
- GitHub Actions can't access local session data yet
- Manual updates required (but fast: <10 seconds)
- Static SVG (no interactivity)
- Language detection is simplistic (file extension based)

**Surprising insights:**
- Near 50/50 Claude/Codex split shows thoughtful tool selection
- "zeta" repo has 16 AI sessions but 0 commits (pure exploration?)
- 337 avg turns/session proves deep problem-solving vs quick prompts

## 🎉 Next Steps

**To deploy this MVP:**
1. Run `./scripts/update_local.sh`
2. Commit and push
3. Watch GitHub profile update with dynamic dashboard!

**For iteration:**
- Gather user feedback on what metrics are most interesting
- Consider which v2 features would add most value
- Decide if Actions automation is worth the complexity
