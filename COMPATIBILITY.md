# 📋 Phase 1 Multi-Agent Compatibility Specification

เอกสารกำหนดมาตรฐานทางเทคนิคของ **Phase 1** ในการทำให้ทุก Skill ในคลังรองรับ **Google Antigravity**, **Anthropic Claude Code**, และ **OpenAI Codex** ได้อย่างสมบูรณ์แบบโดยไม่มีข้อขัดแย้ง (Zero Conflict & Cross-Platform Compatible)

---

## 🎯 วัตถุประสงค์ของ Phase 1 (Phase 1 Objectives)

1. **One Source of Truth**: มีคลัง Skill เพียงชุดเดียว (`skills/<name>`) ที่สามารถติดตั้งและทำงานร่วมกับ AI Coding Assistants ได้ทุกค่าย
2. **Deterministic Discovery**: AI Agent แต่ละค่ายสามารถค้นพบ (Discover), จับคู่ความสามารถ (Intent Matching), และโหลดคำสั่งขึ้นมาทำงานได้อย่างแม่นยำ
3. **Cross-Platform Scripting**: สคริปต์เสริม (Automation Scripts) ต้องรองรับทั้งระบบปฏิบัติการ Windows (PowerShell) และ macOS / Linux (POSIX Bash)
4. **Zero Configuration Friction**: ผู้ใช้สามารถสั่งติดตั้งไปยัง Agent ใดๆ หรือทุก Agent พร้อมกันผ่าน Universal Installer ได้ในคำสั่งเดียว

---

## 🏛️ ตารางเปรียบเทียบสถาปัตยกรรม (Architectural Mapping)

| หมวดหมู่ | 🔮 Google Antigravity | 🟧 Anthropic Claude Code | 🟩 OpenAI Codex |
|---|---|---|---|
| **รูปแบบคำสั่ง** | `SKILL.md` (YAML Frontmatter) | `SKILL.md` (YAML Frontmatter) | `SKILL.md` (YAML Frontmatter) |
| **ตำแหน่งติดตั้ง (Global)** | `~/.gemini/config/skills/<name>` | `~/.claude/skills/<name>` | `~/.codex/skills/<name>` |
| **ตำแหน่งติดตั้ง (Workspace)** | `.agent/skills/<name>` หรือ `.gemini/` | `.claude/skills/<name>` | `.codex/skills/<name>` |
| **ไฟล์บริบทโปรเจกต์** | Workspace Guidelines | `CLAUDE.md` | `AGENTS.md` / `CODEX.md` |
| **เครื่องมืออ่านไฟล์** | `read_file` | `Read`, `Glob`, `Grep` | File Reader / Shell CLI |
| **เครื่องมือเขียน/แก้ไฟล์** | `write_file`, `edit_file` | `Write`, `Edit`, `MultiEdit` | File Writer / Patch CLI |
| **เครื่องมือรันคำสั่ง** | `run_command` | `Bash` | Shell Execution |
| **การตรวจจับ Trigger** | Semantic intent + triggers list | YAML `description` intent match | Prompt match + instructions |

---

## 📑 มาตรฐาน YAML Frontmatter สำหรับ Phase 1

ไฟล์ `SKILL.md` ทุกไฟล์ต้องเริ่มต้นด้วย Frontmatter ในบรรทัดที่ 1:

```yaml
---
name: <skill-folder-name>
description: <คำอธิบายโดยละเอียด พร้อมคีย์เวิร์ดกระตุ้นการทำงาน>
category: <Document | UIUX | Architecture | Optimization | Tools>
tags: [<tag1>, <tag2>, ..., multi-agent]
version: 1.0.0
agents:
  - antigravity
  - claude-code
  - codex
compatibility:
  antigravity: ">=1.0.0"
  claude-code: ">=1.0.0"
  codex: ">=1.0.0"
---
```

### กฎข้อบังคับ (Strict Rules):
1. ฟิลด์ `name` ต้องตรงกับชื่อโฟลเดอร์ของ Skill อย่างแม่นยำ
2. ฟิลด์ `description` ต้องมีคำค้นหาสำคัญ (Trigger Keywords) ทั้งภาษาไทยและภาษาอังกฤษ
3. ต้องประกาศ `agents` ระบุทั้ง 3 ตัว ได้แก่ `antigravity`, `claude-code`, และ `codex`
4. ต้องระบุ `compatibility` ระดับเวอร์ชันขั้นต่ำ

---

## 📁 โครงสร้างโฟลเดอร์ภายในแต่ละ Skill

```text
skills/<skill-name>/
├── SKILL.md              # 📄 ไฟล์คำสั่งและ Metadata หลัก (Universal Frontmatter)
├── templates/            # 📑 โครงสร้างไฟล์แม่แบบ (HTML, Markdown, Config)
├── scripts/              # ⚙️ สคริปต์สำหรับรันคำสั่ง (ต้องมีทั้ง .ps1 และ .sh หากมีการรันอัตโนมัติ)
│   ├── script-name.ps1   #    สำหรับ Windows
│   └── script-name.sh    #    สำหรับ macOS / Linux
└── references/           # 📚 เอกสารอ้างอิง สไตล์ไกด์ และพจนานุกรมคำศัพท์
```

---

## ⚡ สคริปต์ติดตั้งอัตโนมัติ (Universal Multi-Agent Installer)

ในโฟลเดอร์ `scripts/` มีสคริปต์ติดตั้ง 2 ภาษา:

### 1. `install-skill.ps1` (PowerShell สำหรับ Windows)
```powershell
# ติดตั้งทั้งหมด
.\scripts\install-skill.ps1 -Skill all -Agent all -Scope global

# ติดตั้งเฉพาะ Agent
.\scripts\install-skill.ps1 -Skill webapp-user-manual -Agent claude
.\scripts\install-skill.ps1 -Skill webapp-user-manual-pdf -Agent codex
```

### 2. `install-skill.sh` (Bash สำหรับ macOS / Linux / WSL)
```bash
# ติดตั้งทั้งหมด
./scripts/install-skill.sh --skill all --agent all --scope global

# ติดตั้งเฉพาะ Agent
./scripts/install-skill.sh --skill webapp-user-manual --agent antigravity
```

---

## 🚀 แผนพัฒนาในเฟสถัดไป (Phase 2 Preview)

- **Automated Skill Linting & CI Testing**: ตรวจสอบความถูกต้องของ YAML Frontmatter และโครงสร้างไฟล์อัตโนมัติผ่าน GitHub Actions
- **MCP Bridge Adapters**: การเชื่อมต่อคำสั่ง Skill เข้ากับ Model Context Protocol (MCP) Tools
- **Dynamic Catalog Search API**: เพิ่ม REST/JSON Endpoint สำหรับการดึงข้อมูล Skill แบบอัตโนมัติ
