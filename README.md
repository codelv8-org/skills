# 🧠 Personal Skill Library & Catalog

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](#)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Online-2ea44f?logo=github&logoColor=white)](https://codelv8-org.github.io/skills/)
[![UI: Bento Grid](https://img.shields.io/badge/UI-Bento_Grid-blueviolet.svg)](#)
[![Phase 1: Multi-Agent](https://img.shields.io/badge/Phase_1-Multi--Agent_Ready-purple.svg)](#)
[![AI: Google Antigravity](https://img.shields.io/badge/Antigravity-Supported-3b82f6.svg)](#)
[![AI: Claude Code](https://img.shields.io/badge/Claude_Code-Supported-ea580c.svg)](#)
[![AI: OpenAI Codex](https://img.shields.io/badge/OpenAI_Codex-Supported-10b981.svg)](#)

คลังรวบรวม **AI Agent Skills ส่วนตัว** สำหรับยกระดับขีดความสามารถของ AI Coding Assistants ชั้นนำ โดยใน **Phase 1** นี้ ทุก Skill ในคลังได้รับการปรับปรุงให้รองรับ **Google Antigravity**, **Anthropic Claude Code**, และ **OpenAI Codex** อย่างเต็มรูปแบบ พร้อมระบบ **Web Catalog ดีไซน์ Bento UI (`index.html`)** และ **สคริปต์ติดตั้งอัตโนมัติ (Universal Multi-Agent Installer)**

---

## 🌟 จุดเด่นและฟีเจอร์หลัก (Key Features)

### 1. 🤖 รองรับ Multi-Agent สมบูรณ์แบบ (Phase 1 Ready)
- **Google Antigravity:** รองรับทั้ง Global (`~/.gemini/config/skills/`) และ Workspace (`.agent/skills/`)
- **Anthropic Claude Code:** รองรับผ่าน `~/.claude/skills/`, Workspace `.claude/skills/` และคอนฟิก `CLAUDE.md`
- **OpenAI Codex:** รองรับผ่าน `~/.codex/skills/`, Workspace `.codex/skills/` และคอนฟิก `AGENTS.md` / `CODEX.md`
- โครงสร้าง YAML Frontmatter และเนื้อหาคำสั่งที่เป็นมิตรกับทุก Agent พร้อมสคริปต์ข้ามระบบทั้ง Windows (PowerShell) และ macOS/Linux (Bash)

### 2. 🖥️ Interactive Web Catalog พร้อมดีไซน์ Bento UI (`index.html`)
ระบบหน้าเว็บสำหรับการเรียกดูและจัดการคลัง Skill สไตล์ Apple / Vercel Bento Box:
- **📦 Bento Dashboard Hero**: แดชบอร์ดสรุปภาพรวมพร้อมสถานะ Multi-Agent Ecosystem, สถิติความพร้อมสด, และ Interactive Terminal 1-Click Copy
- **🍱 Bento Grid View (Flagship)**: แสดงผลแบบ Bento Box จัดสัดส่วนการ์ดอย่างเป็นระเบียบ สวยงาม พร้อมภาพพรีวิวและช่องสัดส่วนอสมมาตร
- **🎴 Uniform Cards View**: แสดงผลแบบการ์ดตารางเท่ากันสำหรับผู้ที่ต้องการความเรียบง่าย
- **📋 List View**: แสดงผลแบบรายการกระชับ อ่านง่าย พร้อมตัวกรอง Agent และหมวดหมู่
- **📊 Table View**: ตารางเปรียบเทียบข้อมูลเชิงลึก ระบุเฟส เวอร์ชัน และ Agent ที่รองรับ
- **🔍 Smart Search & Filtering**: ค้นหาด้วยคีย์เวิร์ด, กรองตามหมวดหมู่ (Category) และ AI Agent
- **📥 Direct ZIP Downloads**: ปุ่มดาวน์โหลดไฟล์ ZIP สำหรับทุก Skill โดยตรง สะดวกสำหรับการนำไปใช้งานแบบ Offline
- **📖 Quick Details Modal**: หน้าต่างรายละเอียดแบบ Bento Compartments พร้อม **Agent & Platform Selector** สลับคำสั่งติดตั้งสำหรับ Antigravity, Claude Code หรือ Codex ได้ทันที

### 3. ⚡ Universal Installer Scripts (`scripts/`)
- มีสคริปต์ `install-skill.ps1` (Windows) และ `install-skill.sh` (macOS/Linux) สั่งติดตั้ง Skill ใดๆ หรือทั้งหมดไปยัง Agent ที่เลือกได้ในคำสั่งเดียว

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
skills/
├── .github/
│   └── workflows/
│       └── deploy.yml      # 🚀 CI/CD Automated GitHub Pages Deployment
├── .nojekyll               # ⚙️ ป้องกัน GitHub Pages ประมวลผลด้วย Jekyll
├── 404.html                # 🧭 หน้าแจ้งเตือนกรณีไม่พบ URL ปลายทาง
├── robots.txt              # 🤖 กฎสำหรับ Web Crawlers / Search Engines
├── sitemap.xml             # 🗺️ แผนผังหน้าเว็บสำหรับ Search Engines
├── index.html              # 🌐 หน้า Catalog หลัก (Card, List, Table view พร้อม Agent Selector)
├── README.md               # 📄 เอกสารแนะนำโปรเจกต์
├── COMPATIBILITY.md        # 📋 ข้อมูลสเปกและมาตรฐาน Phase 1 Multi-Agent
├── CLAUDE.md               # 🟧 แนวทางการทำงานสำหรับ Anthropic Claude Code
├── AGENTS.md               # 🤖 คำแนะนำและ Context กลางสำหรับ AI Coding Agents
├── CODEX.md                # 🟩 คำแนะนำและวิธีติดตั้งสำหรับ OpenAI Codex
├── data/                   # 📦 ข้อมูลรายการ Skill สำหรับ Catalog (JSON)
│   └── skills.json         #    (พร้อม Metadata รองรับ Codex, Claude Code, Antigravity)
├── scripts/                # 🛠️ สคริปต์ตัวช่วยอเนกประสงค์
│   ├── install-skill.ps1   #    Universal Installer (PowerShell สำหรับ Windows)
│   └── install-skill.sh    #    Universal Installer (Bash สำหรับ macOS/Linux)
├── assets/                 # 🎨 ไอคอนและ Assets เสริม
│   └── favicon.svg         #    ไอคอนประจำหน้าเว็บ
└── skills/                 # 📂 คลังโฟลเดอร์รวบรวมแต่ละ Skill (Phase 1 Multi-Agent)
    ├── user-manual-writer/
    │   └── SKILL.md        # คู่มือทีละขั้นพร้อมภาพจากระบบทดสอบ
    ├── webapp-user-manual/
    │   ├── SKILL.md        # มาตรฐาน Multi-Agent + The 10-Pillar Framework
    │   ├── templates/      # manual-template.html, manual-template.md
    │   └── references/     # style-guide.md
    └── webapp-user-manual-pdf/
        ├── SKILL.md        # CSS Paged Media A4 + Multi-Agent Execution
        ├── templates/      # pdf-manual-template.html
        ├── scripts/        # export-pdf.ps1 (Win) & export-pdf.sh (Mac/Linux)
        └── references/     # pdf-styling-guide.md
```

---

## 📚 Documentation Skills

| Skill | Version | ขอบเขต |
|---|---|---|
| [Privacy-First Database Documentation Builder](skills/privacy-first-database-documentation-builder/SKILL.md) | 2.0.0 | Data Catalog, Data Dictionary, ERD, Classification, Lineage, Schema Diff, PDF + Markdown จาก metadata ที่ผ่านการรับรองเท่านั้น |
| [API Documentation Builder](skills/api-documentation-builder/SKILL.md) | 1.0.0 | API Catalog, Data Dictionary, OpenAPI, Consumer Guide, Governance, AI Agent/MCP Integration จาก contract ที่ผ่านการคัดกรองเท่านั้น |

ทั้งสอง Skill ห้ามอ่านข้อมูลส่วนบุคคลจริงหรือค่าข้อมูลอ่อนไหวจริง ไม่อนุญาตให้เชื่อมต่อฐานข้อมูลหรือเรียก API จริงเพื่อสร้างเอกสาร ใช้เฉพาะ metadata/contract ที่เจ้าของข้อมูลตรวจสอบก่อนส่งมอบ และตัวอย่างสมมุติเท่านั้น

---

## 🖼️ ตัวอย่างผลลัพธ์ Documentation Skills

| Skill | Overview / Example | เอกสารต้นฉบับ |
|---|---|---|
| Privacy-First Database Documentation Builder | [Example Showcase](https://codelv8-org.github.io/skills/skills/privacy-first-database-documentation-builder/examples/synthetic-demo/) | [Data Dictionary](skills/privacy-first-database-documentation-builder/examples/synthetic-demo/output/data-dictionary.md) |
| API Documentation Builder | [Example Showcase](https://codelv8-org.github.io/skills/skills/api-documentation-builder/examples/synthetic-demo/) | [API Consumer Guide](skills/api-documentation-builder/examples/synthetic-demo/output/api-consumer-guide.md) · [OpenAPI](skills/api-documentation-builder/examples/synthetic-demo/output/openapi.yaml) |

ทั้งสองชุดใช้ Synthetic Metadata/Contract เท่านั้น ไม่เรียกฐานข้อมูลหรือ API จริง ไม่ใช้ข้อมูลส่วนบุคคลหรือ credentials จริง ภาพ Overview แสดงโครงสร้างและผลลัพธ์ของตัวอย่าง ไม่ใช่ภาพหน้าจอของระบบจริง

**PDF ตัวอย่าง (7 + 6 เอกสาร)** สร้างใน GitHub Pages workflow จาก Markdown ที่ตรวจสอบแล้วก่อน Build ZIP โดยไม่ commit ไฟล์ PDF ที่สร้างซ้ำได้ลง repository เมื่อต้องการสร้างในเครื่อง ให้เตรียม Python 3.12, WeasyPrint system dependencies, ฟอนต์ Noto Sans Thai และ Poppler (pdftotext) แล้วรัน:

```bash
python -m pip install -r scripts/documentation-examples-requirements.txt
python scripts/build-documentation-examples.py
python scripts/build-skill-zips.py
```

จากนั้นเปิด `examples/synthetic-demo/index.html` ภายในโฟลเดอร์ Skill ที่ต้องการผ่าน Local Web Server

---

## Fantasy Character Production

[AAA Fantasy Character Studio](skills/aaa-fantasy-character-studio/SKILL.md) (v2.0.0 Beta) — Agent-native cloud-first generation of original Xianxia / Wuxia characters. STRICT_AGENT_CLOUD defaults to verified hosted Python execution without external 3D SaaS or local user generation. Includes MeshIR, a native GLB compiler, CPU bind-clay renderer, 12 retained evidence gates and 26 passing synthetic tests. No AAA-quality character certification. [Usage](skills/aaa-fantasy-character-studio/README.md) · [Changelog](skills/aaa-fantasy-character-studio/CHANGELOG.md) · [Roadmap](skills/aaa-fantasy-character-studio/ROADMAP.md).

### v2 native compiler fixture — COMPILED_ONLY

[Actual fixture showcase](assets/examples/fantasy-character/native-compiler-v2/index.html) · [GLB](assets/examples/fantasy-character/native-compiler-v2/fixture.glb) · [Compiler report](assets/examples/fantasy-character/native-compiler-v2/compiler.json) · [26-test log](assets/examples/fantasy-character/native-compiler-v2/test-log.txt)

18 triangles, 19 vertices, two joints, one authored clip, five actual CPU bind-clay views. The fixture is not a humanoid. Chat-hosted fixture execution tested; independent Agent execution and matched visual version/mode comparison NOT TESTED. Existing overview concept retained pending refresh. Historical v1 example below is a different scenario, not a before/after benchmark.

### G1 diagnostic prototype — Azure Celestial Sword Immortal

[Open the diagnostic showcase](assets/examples/fantasy-character/index.html) · [Actual CPU clay renders](assets/examples/fantasy-character/renders/clay-views.webp) · [Rigged blockout GLB](assets/examples/fantasy-character/export/sword-immortal-blockout.glb) · [Gate evidence](assets/examples/fantasy-character/evidence/gate-status.json)

This is an actual reference-traced **G1 blockout/rig diagnostic, not an AAA or game-ready model**. 56,992 triangles, 29 inferred joints and one test clip. The binary/skin checks passed; G1 visual fidelity failed. No production UV, texture baking, PBR lookdev or independent approval. Three.js viewer source is included; browser/runtime verification was not completed. Do not treat the concept preview as a rendered 3D asset.

## Workflow Diagrams — Archify

เปิดรายละเอียดของแต่ละ Skill แล้วเลือกขั้นตอนใน Workflow Diagram เพื่อดูคำอธิบาย เงื่อนไขการหยุด/แก้ไข และหลักฐาน `SKILL.md` ที่อ้างอิง commit ต้นทาง ทุก Skill ใน Catalog มีแผนภาพเฉพาะของตัวเอง ไม่ใช่ flow ตัวอย่างร่วมกัน

- `assets/skill-workflows/<id>.workflow.json`: แหล่งข้อมูล editable ตาม Workflow Schema v2 ของ [Archify](https://github.com/tt-a1i/archify) (Apache-2.0)
- `data/skills.json` และ Embedded Catalog: compact interactive flow ที่เปิดจากเครื่องได้โดยไม่ต้องเชื่อมต่ออินเทอร์เน็ตหรือโหลด CDN
- `assets/skill-workflows/<id>.html`: Native Archify standalone HTML ที่สร้างด้วย `finalize workflow` (validate, delivery, strict check และ browser-check) เมื่อ Build สำเร็จ จึงแสดงปุ่มเปิดตัวดู Interactive และเต็มจอในรายละเอียด Skill
- Workflow เป็นข้อกำหนดตามเอกสารของ Skill ไม่ได้แสดงว่างานของผู้ใช้กำลังรันหรือผ่าน QA จริง

สร้างหรือทดสอบในเครื่องจาก repository root (Node.js 22+, Git, Chrome/Chromium, Git history ที่มี commit ต้นทางครบถ้วน):

```bash
node scripts/build-skill-workflows.mjs --check
git clone https://github.com/tt-a1i/archify.git ../archify
git -C ../archify checkout --detach 3ca198d867ce4b616332f846ff66e5c8e5e60f95
node scripts/build-skill-workflows.mjs --archify=../archify
python -m http.server 3000
```

หากต้องการปรับ flow ให้แก้ Workflow JSON และ compact workflow ใน Catalog ทั้งสองชุดให้สอดคล้องกับ SKILL.md รุ่นที่อ้างถึง แล้วรัน build/check ใหม่ ห้ามใช้ข้อมูลจริงเป็นตัวอย่างในแผนภาพของ Privacy-First และ API Documentation Builder

---

## 🚀 วิธีเปิดใช้งานหน้า Web Catalog

คุณสามารถเปิดดูรายการ Skill ผ่านเบราว์เซอร์ได้ทันทีโดยไม่ต้องติดตั้ง Backend:

ปุ่ม **ดาวน์โหลด ZIP** จะดาวน์โหลดโฟลเดอร์ของ Skill ที่เลือกพร้อม `SKILL.md` และไฟล์ประกอบ GitHub Pages สร้าง ZIP ให้อัตโนมัติ สำหรับทดสอบจากเครื่องให้รัน `python scripts/build-skill-zips.py` ด้วย Python 3.10 ขึ้นไปก่อนเปิดหน้าแค็ตตาล็อก

### วิธีที่ 1: เปิดไฟล์โดยตรง (Direct Open)
- ดับเบิลคลิกที่ไฟล์ `index.html` หรือคลิกขวาแล้วเลือก **Open with Browser** (Chrome, Edge, Firefox)

### วิธีที่ 2: รันผ่าน Local Web Server (แนะนำสำหรับการพัฒนา)
```bash
# ใช้ Python
python -m http.server 3000

# หรือใช้ Node.js npx serve
npx serve .
```
จากนั้นเปิดเบราว์เซอร์ไปที่: `http://localhost:3000`

### วิธีที่ 3: เข้าชมออนไลน์ผ่าน GitHub Pages 🌐
👉 **[https://codelv8-org.github.io/skills/](https://codelv8-org.github.io/skills/)**

---

## 🤖 วิธีติดตั้งและนำ Skill ไปใช้งานในแต่ละ AI Agent

### ⚡ วิธีที่ 1: ใช้ Universal Multi-Agent Installer (แนะนำที่สุด)

เราเตรียมสคริปต์ติดตั้งอัตโนมัติที่ช่วยตรวจจับและคัดลอกไฟล์ไปยังไดเรกทอรีที่ถูกต้องของแต่ละ Agent:

#### บน Windows (PowerShell):
```powershell
# ติดตั้งทุก Skill ไปยังทุก Agent (Antigravity, Claude Code, Codex) ในระดับเครื่อง:
.\scripts\install-skill.ps1 -Skill all -Agent all -Scope global

# ติดตั้งเฉพาะ Skill ที่ต้องการ ไปยัง Claude Code:
.\scripts\install-skill.ps1 -Skill webapp-user-manual -Agent claude

# ติดตั้งไปยัง Codex ใน Workspace เฉพาะโปรเจกต์:
.\scripts\install-skill.ps1 -Skill all -Agent codex -Scope workspace -WorkspacePath "D:\Projects\my-app"
```

#### บน macOS / Linux (Bash):
```bash
# ติดตั้งทุก Skill ไปยังทุก Agent:
./scripts/install-skill.sh --skill all --agent all --scope global

# ติดตั้งเฉพาะ webapp-user-manual-pdf ไปยัง Claude Code:
./scripts/install-skill.sh --skill webapp-user-manual-pdf --agent claude
```

---

### 🛠️ วิธีที่ 2: คัดลอกโฟลเดอร์ด้วยตนเอง (Manual Copy)

#### 1. 🔮 สำหรับ Google Antigravity / Gemini CLI:
- **Global:**
  - Windows: `Copy-Item -Path ".\skills\<skill-name>" -Destination "$env:USERPROFILE\.gemini\config\skills\" -Recurse`
  - POSIX: `cp -r ./skills/<skill-name> ~/.gemini/config/skills/`
- **Workspace:** คัดลอกไปที่โฟลเดอร์ `.agent/skills/<skill-name>` หรือ `.gemini/skills/<skill-name>`

#### 2. 🟧 สำหรับ Anthropic Claude Code:
- **Global:**
  - Windows: `Copy-Item -Path ".\skills\<skill-name>" -Destination "$env:USERPROFILE\.claude\skills\" -Recurse`
  - POSIX: `cp -r ./skills/<skill-name> ~/.claude/skills/`
- **Workspace:** คัดลอกไปที่โฟลเดอร์ `.claude/skills/<skill-name>` (Claude Code จะอ่านเอกสาร `CLAUDE.md` ที่รากโปรเจกต์ควบคู่กัน)

#### 3. 🟩 สำหรับ OpenAI Codex:
- **Global:**
  - Windows: `Copy-Item -Path ".\skills\<skill-name>" -Destination "$env:USERPROFILE\.codex\skills\" -Recurse`
  - POSIX: `cp -r ./skills/<skill-name> ~/.codex/skills/`
- **Workspace:** คัดลอกไปที่โฟลเดอร์ `.codex/skills/<skill-name>` (Codex จะอ่าน `AGENTS.md` หรือ `CODEX.md` ที่รากโปรเจกต์)

---

## 📊 ตารางเปรียบเทียบการรองรับใน Phase 1 (Compatibility Matrix)

| คุณลักษณะ (Feature) | Google Antigravity | Anthropic Claude Code | OpenAI Codex |
|---|:---:|:---:|:---:|
| **ไฟล์คำสั่งหลัก** | `SKILL.md` (YAML Frontmatter) | `SKILL.md` (YAML Frontmatter) | `SKILL.md` (YAML Frontmatter) |
| **ตำแหน่งโฟลเดอร์ Global** | `~/.gemini/config/skills/` | `~/.claude/skills/` | `~/.codex/skills/` |
| **ตำแหน่งโฟลเดอร์ Workspace** | `.agent/skills/` หรือ `.gemini/` | `.claude/skills/` | `.codex/skills/` |
| **ไฟล์ Context ประจำโปรเจกต์** | Workspace Memory | `CLAUDE.md` | `AGENTS.md` / `CODEX.md` |
| **สคริปต์แปลง PDF (Windows)** | `export-pdf.ps1` (PowerShell) | `export-pdf.ps1` (PowerShell) | `export-pdf.ps1` (PowerShell) |
| **สคริปต์แปลง PDF (Mac/Linux)** | `export-pdf.sh` (Bash) | `export-pdf.sh` (Bash) | `export-pdf.sh` (Bash) |
| **สถานะ Phase 1** | ✅ **พร้อมใช้งาน 100%** | ✅ **พร้อมใช้งาน 100%** | ✅ **พร้อมใช้งาน 100%** |

---

## 🛠️ โครงสร้างมาตรฐาน Phase 1 (`SKILL.md`)

ทุก Skill ใน Phase 1 กำหนดหัว YAML Frontmatter และโครงร่างเนื้อหาดังนี้:

```markdown
---
name: skill-name
description: คำอธิบายหน้าที่ ความสามารถ และคีย์เวิร์ดกระตุ้นการทำงาน (Triggers)
category: Document
tags: [tag1, tag2]
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

# Skill Instructions

## 🎯 เมื่อไหร่ที่ควรใช้ Skill นี้ (Trigger Conditions)
- คำค้นหาและสถานการณ์ที่ควรเรียกใช้

## 🤖 การทำงานร่วมกับ AI Agent (Multi-Agent Support)
- รายละเอียดการทำงานกับ Antigravity, Claude Code, และ Codex

## 🏛️ ขั้นตอนการทำงานและแนวทางปฏิบัติ (Workflow)
1. ขั้นตอนที่ 1 ...
2. ขั้นตอนที่ 2 ...
```

---

## ➕ การเพิ่ม Skill ใหม่เข้าคลัง (Adding a New Skill)

1. **สร้างโฟลเดอร์ Skill**:
   - สร้างโฟลเดอร์ใหม่ในไดเรกทอรี `skills/<ชื่อ-skill>/`
   - สร้างไฟล์ `SKILL.md` ตามโครงสร้างมาตรฐานด้านบน
2. **อัปเดตข้อมูลเข้าสู่ Catalog**:
   - เพิ่มรายการ Skill ในไฟล์ `data/skills.json` (หรือใน Script ของ `index.html`) โดยระบุ:
     - `id`: ชื่อโฟลเดอร์
     - `name`: ชื่อที่แสดงผล
     - `category`: หมวดหมู่ (เช่น Frontend, Architecture, Tooling)
     - `tags`: แท็กสำหรับการค้นหา
     - `description`: คำอธิบายความสามารถ
     - `version`: เวอร์ชันปัจจุบัน
3. **เปิดหน้า `index.html`** เพื่อตรวจสอบการแสดงผลในมุมมอง Card, List และ Table view

---

## 🤝 การสนับสนุนและข้อเสนอแนะ (Feedback & Contributions)

หากพบข้อผิดพลาด ต้องการเสนอแนะ Skill ใหม่ หรือมีแนวทางการปรับปรุงระบบ Catalog สามารถเปิด Issue หรือส่ง Pull Request เข้ามาได้ยินดีต้อนรับทุกคำแนะนำครับ!

---

<p align="center">Made with ❤️ for AI Agent Power Users</p>


## Community Ratings & Reviews

The catalog supports versioned community reviews via public GitHub Issues and approved ratings generated at Pages build time. See [moderator setup and review documentation](docs/skill-reviews.md).

Phase 2 adds helpful reactions, approved GitHub attachments, comparison, quality analytics, static repository benchmarks and opt-in AI review summaries. See [the review documentation](docs/skill-reviews.md#community-edition--phase-2).
