# CLAUDE.md - AI Agent Context & Guidelines for Claude Code

This repository is a **Personal AI Skill Library & Interactive Catalog** curated for AI Coding Assistants.
In Phase 1, all skills in this library are standardized to be 100% compatible with **Anthropic Claude Code**, **Google Antigravity**, and **OpenAI Codex**.

## 📁 Repository Structure
- `skills/`: The skill repository. Each skill is self-contained with `SKILL.md` (YAML frontmatter + instructions), `templates/`, `scripts/`, and `references/`.
  - `skills/webapp-user-manual/`: Complete 10-pillar Web Application user manual generator (Interactive HTML & Markdown).
  - `skills/webapp-user-manual-pdf/`: Print-ready A4 publication-grade PDF manual generator with CSS Paged Media (`@page`).
- `data/skills.json`: Catalog dataset containing metadata, supported agents (`antigravity`, `claude-code`, `codex`), and triggers.
- `index.html`: Interactive web catalog with Card, List, and Table views, theme switching, and copy commands for all 3 agents.
- `scripts/`: Universal installation and helper scripts (`install-skill.ps1`, `install-skill.sh`).

## 🤖 Using Skills in Claude Code
When working in Claude Code:
1. **Trigger Recognition**: When a user asks for user manuals, documentation, web app guides, or PDF generation, consult the corresponding skill's `SKILL.md`.
2. **Accessing Templates**:
   - For web manual: `skills/webapp-user-manual/templates/manual-template.html` and `manual-template.md`
   - For PDF manual: `skills/webapp-user-manual-pdf/templates/pdf-manual-template.html`
3. **Running PDF Exporter**:
   - On macOS/Linux: `bash skills/webapp-user-manual-pdf/scripts/export-pdf.sh --input <input.html> --output <output.pdf>`
   - On Windows: `powershell -ExecutionPolicy Bypass -File skills/webapp-user-manual-pdf/scripts/export-pdf.ps1 -InputHtml "<input.html>" -OutputPdf "<output.pdf>"`

## 📦 Installing Skills Locally
To install skills to Claude Code's user configuration:
- Global: `bash scripts/install-skill.sh --skill all --agent claude --scope global`
  (Copies to `~/.claude/skills/`)
- Workspace: `bash scripts/install-skill.sh --skill all --agent claude --scope workspace`
  (Copies to `.claude/skills/`)
