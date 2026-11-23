# AGENTS.md - Context & Instruction Guidelines for AI Coding Agents

This repository contains the **Personal AI Skill Library & Catalog**.
All skills are configured to follow the **Phase 1 Multi-Agent Standard**, supporting **OpenAI Codex**, **Anthropic Claude Code**, and **Google Antigravity**.

## 🧠 Multi-Agent Standard (Phase 1)
Every skill under `skills/<skill-name>/` strictly follows this specification:
1. **Standard Frontmatter (`SKILL.md`)**:
   - `name`: Must match the directory name.
   - `description`: Rich description with trigger conditions and keyword matching.
   - `agents`: `[antigravity, claude-code, codex]`
   - `compatibility`: Semantic version requirements.
2. **Deterministic Folder Layout**:
   - `SKILL.md`: Root instructions and workflows.
   - `templates/`: Boilerplates and design structures.
   - `scripts/`: Platform scripts (both `.ps1` for Windows and `.sh` for Linux/macOS).
   - `references/`: Supporting style guides and specifications.

## 🛠️ Codex CLI & Agent Workflows
- **Global skills location**: `~/.codex/skills/<skill-name>/`
- **Project workspace skills location**: `.codex/skills/<skill-name>/`
- **Installer Script**:
  - Windows: `.\scripts\install-skill.ps1 -Skill all -Agent codex`
  - Linux/macOS: `./scripts/install-skill.sh --skill all --agent codex`
