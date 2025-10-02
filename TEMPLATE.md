<p align="center">
  <img src="./hero.svg" alt="AI-Native Development Dashboard" />
</p>

## 🚀 Active This Week

{{SHIPPING_TABLE}}

## 💡 About

I'm a full-stack developer building AI-powered applications. This profile showcases my **AI-native development workflow** - combining traditional git commits with AI pair programming sessions from Claude Code and OpenAI Codex.

**What makes this unique?** Rather than just showing finished work (commits), this dashboard reveals the actual building process through:
- Real-time AI collaboration metrics
- Parallel development across multiple projects
- Deep problem-solving sessions (avg {{AVG_TURNS}} turns/session)

## 🛠️ Current Stack

{{LANGUAGE_BADGES}}

## 📊 How This Works

This README updates automatically every 6 hours via GitHub Actions. Data sources:
- **Git activity**: Parsed from local repositories via `git log`
- **Claude sessions**: Parsed from `~/.claude/projects/`
- **Codex sessions**: Parsed from `~/.codex/sessions/`

All metrics are computed locally and aggregated into a single JSON file, then visualized in the hero SVG above.

---

<details>
<summary>🔍 Detailed Stats (Last 30 Days)</summary>

- **Commits**: {{COMMITS_30D}}
- **Languages**: {{LANGUAGES_30D}}
- **AI Sessions**: Claude {{CLAUDE_30D}} · Codex {{CODEX_30D}}
- **Total Turns**: {{TURNS_30D}}

</details>

*Last updated: {{UPDATED_AT}}*
