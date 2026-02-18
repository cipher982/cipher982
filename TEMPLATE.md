<p align="center">
  <img src="./hero.svg" alt="AI-Native Development Dashboard" />
</p>

I build AI-powered applications and infrastructure. Most of my work involves autonomous agents, LLM tooling, and shipping real products — from computer vision systems to full-stack web apps. The dashboard above tracks my AI pair programming workflow in real time.

---

## Projects

### AI & Agents

| Project | Description |
|---------|-------------|
| 🏛️ [**Longhouse**](https://longhouse.ai) | Centralized platform for managing AI agent sessions, insights, memory, and orchestration |
| ⚡ [**LLM Benchmarks**](https://llm-benchmarks.com) | Benchmarking LLM inference speeds across providers — 13 stars |
| 🐣 [**Hatch**](https://github.com/cipher982/zerg/tree/main/packages/hatch-agent) | CLI tool for spawning headless AI agents (Claude, Codex, Gemini) |
| 🔧 [**MCP Tools**](https://github.com/cipher982/mcp-tools) | Lightweight MCP server facades for Claude Code — 90%+ token reduction |
| 🎁 [**Code Wrapped**](https://github.com/cipher982/code-wrapped) | Spotify Wrapped for your AI pair programming year |
| 📜 [**Agentlog**](https://github.com/cipher982/agentlog) | Canonical parser for AI agent session logs (Claude, Codex, Gemini, Cursor) |

### Apps & Sites

| Project | Description |
|---------|-------------|
| 🛑 [**Stop Sign Nanny**](https://crestwoodstopsign.com) | AI + IP camera system that tracks and scores vehicle behavior at intersections |
| 🌅 [**HDR Pop**](https://github.com/cipher982/hdr) | Transform standard photos into HDR using AI-powered gain map generation |
| 🏀 [**March Madness LLM**](https://marchmadness.drose.io) | NCAA bracket simulator with AI-powered decisions and a React frontend |
| 🍷 [**This Wine Does Not Exist**](https://thiswinedoesnotexist.com) | Generating fake wines with GPT-2 + StyleGAN |
| 🌊 [**FloodMap USA**](https://drose.io/floodmap) | Interactive flood risk mapping with elevation data |
| 🤖 [**AI Tools Directory**](https://aitools.drose.io) | AI agents that discover, catalog, and organize emerging AI tools |
| 🖥️ [**Pixel Pilot**](https://github.com/cipher982/pixel-pilot) | AI agent for completing computer tasks via screen control |

### Earlier Work

| Project | Description |
|---------|-------------|
| 🚗 [**MPC Vehicle Controller**](https://github.com/cipher982/MPC-vehicle-controller) | Model predictive control + computer vision for autonomous vehicle steering — 21 stars |
| 🦾 [**Robotic Control with DRL**](https://github.com/cipher982/Robotic-Control-in-Unity-with-DRL) | Deep reinforcement learning for robotic control in Unity |
| 🎯 [**PID Control**](https://github.com/cipher982/PID-Control) | PID vehicle controller for autonomous driving |
| 🛣️ [**Lane Tracking**](https://github.com/cipher982/HiFi-Lane-Tracking) | Image processing pipeline for autonomous lane detection |

---

## Active This Week

{{SHIPPING_TABLE}}

## How I Build

The dashboard at the top updates automatically every 6 hours. It tracks my AI-native development workflow — combining traditional git commits with AI pair programming sessions across multiple tools.

- **4 AI coding agents** running in parallel: Claude Code, OpenAI Codex, Gemini, Cursor
- **Avg {{AVG_TURNS}} turns/session** — deep problem-solving, not quick prompts
- All metrics computed locally and via the [Longhouse](https://longhouse.ai) API

{{LANGUAGE_BADGES}}

<details>
<summary>Data sources</summary>

- **Git activity**: GitHub API + local `git log`
- **Claude sessions**: `~/.claude/projects/`
- **Codex sessions**: `~/.codex/sessions/`
- **Cursor sessions**: `state.vscdb` (SQLite)
- **Gemini sessions**: `~/.gemini/tmp/*/logs.json`

</details>

---

<details>
<summary>Detailed Stats (Last 30 Days)</summary>

- **Commits**: {{COMMITS_30D}}
- **Languages**: {{LANGUAGES_30D}}
- **AI Sessions**: Claude {{CLAUDE_30D}} · Codex {{CODEX_30D}} · Cursor {{CURSOR_30D}} · Gemini {{GEMINI_30D}}
- **Total Turns**: {{TURNS_30D}}

</details>

*Last updated: {{UPDATED_AT}}*
