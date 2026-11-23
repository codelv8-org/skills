# CODEX.md - OpenAI Codex Configuration & Skill Index

See [AGENTS.md](file:///d:/Projects/skills/AGENTS.md) for full AI agent guidelines.

## 🚀 Quick Setup for Codex
To install all skills into your Codex environment:

### Windows (PowerShell)
```powershell
.\scripts\install-skill.ps1 -Skill all -Agent codex -Scope global
```

### macOS / Linux (Bash)
```bash
./scripts/install-skill.sh --skill all --agent codex --scope global
```

### Workspace Installation
To enable skills only in this repository or a specific project:
```powershell
.\scripts\install-skill.ps1 -Skill all -Agent codex -Scope workspace
```
This deploys the skills to `.codex/skills/`.
