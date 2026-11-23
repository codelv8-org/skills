# 🧠 Personal Skill Library & Catalog

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](#)
[![Skills: Curated](https://img.shields.io/badge/Skills-Curated-success.svg)](#)
[![Views: Card | List | Table](https://img.shields.io/badge/Catalog_Views-Card_%7C_List_%7C_Table-orange.svg)](#)
[![Platform: AI_Agents](https://img.shields.io/badge/Platform-Antigravity_%2F_Gemini_%2F_Claude-purple.svg)](#)

คลังรวบรวม **AI Agent Skills ส่วนตัว** สำหรับยกระดับขีดความสามารถของ AI Coding Assistants (เช่น Google Antigravity, Gemini CLI, Claude, และ Agent อื่นๆ) พร้อมระบบ **Web Catalog (`index.html`)** ในตัว ที่ช่วยให้ผู้ใช้งานสามารถค้นหา เปรียบเทียบ และเลือกนำ Skill ไปติดตั้งใช้งานได้อย่างสะดวกรวดเร็ว

---

## 🌟 จุดเด่นและฟีเจอร์หลัก (Key Features)

### 1. 🖥️ Interactive Web Catalog (`index.html`)
ระบบหน้าเว็บสำหรับการเรียกดูและจัดการคลัง Skill โดยไม่ต้องเปิดอ่านโค้ดทีละโฟลเดอร์:
- **🎴 Card View**: แสดงภาพรวมแบบการ์ดสวยงาม เห็นชื่อ หมวดหมู่ คำอธิบายย่อ และแท็ก เหมาะสำหรับการค้นหาแบบเร็ว
- **📋 List View**: แสดงผลแบบรายการกระชับ อ่านง่าย เหมาะสำหรับการกวาดสายตาดูรายการจำนวนมาก
- **📊 Table View**: แสดงข้อมูลเชิงลึกในรูปแบบตาราง เปรียบเทียบประเภท เวอร์ชัน ความเข้ากันได้ และ path ไฟล์ได้ทันที
- **🔍 Smart Search & Filtering**: ค้นหาด้วยคีย์เวิร์ด, กรองตามหมวดหมู่ (Category), และแท็ก (Tags)
- **📖 Quick Details Modal**: กดดูรายละเอียดตัวเต็มของแต่ละ Skill (Trigger Conditions, ตัวอย่าง Prompt, เอกสารประกอบ) พร้อมปุ่มคลิกเดียวเพื่อคัดลอกคำสั่งติดตั้ง

### 2. 🧩 Standardized Skill Structure
- จัดเก็บตามโครงสร้างมาตรฐานของ Agent Skills (`SKILL.md` พร้อม YAML Frontmatter)
- มีการแยกหมวดหมู่ชัดเจน ทั้งงาน UI/UX, Architecture Design, Optimization, Code Analysis, Data Visualization และอื่นๆ

### 3. 🚀 Ready to Use & Portable
- นำไปติดตั้งและใช้งานได้ทันที ทั้งในระดับ Global (สำหรับเครื่องส่วนตัว) หรือระดับ Project Workspace

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
skills/
├── index.html              # 🌐 หน้า Catalog หลัก (Card, List, Table view)
├── README.md               # 📄 เอกสารแนะนำโปรเจกต์
├── data/                   # 📦 ข้อมูลรายการ Skill สำหรับ Catalog (JSON)
│   └── skills.json         #    (หรือฝังไว้ใน index.html สำหรับ Standalone)
├── assets/                 # 🎨 สไตล์ ชีต, ไอคอน หรือสคริปต์เสริม
│   ├── css/
│   └── js/
└── skills/                 # 📂 คลังโฟลเดอร์รวบรวมแต่ละ Skill
    ├── user-manual-writer/
    │   └── SKILL.md        # คู่มือทีละขั้นพร้อมภาพจากระบบทดสอบ
    ├── ui-ux-pro-max/
    │   ├── SKILL.md        # ไฟล์คำสั่งและ Metadata หลัก
    │   └── ...
    ├── thai-token-optimizer/
    │   ├── SKILL.md
    │   └── ...
    └── [skill-name]/
        ├── SKILL.md
        ├── scripts/        # (Optional) สคริปต์ช่วยเหลือ
        └── references/     # (Optional) เอกสารอ้างอิงเพิ่มเติม
```

---

## 🚀 วิธีเปิดใช้งานหน้า Web Catalog

คุณสามารถเปิดดูรายการ Skill ผ่านเบราว์เซอร์ได้ทันทีโดยไม่ต้องติดตั้ง Backend:

### วิธีที่ 1: เปิดไฟล์โดยตรง (Direct Open)
- ดับเบิลคลิกที่ไฟล์ `index.html` หรือคลิกขวาแล้วเลือก **Open with Browser** (Chrome, Edge, Firefox)

### วิธีที่ 2: รันผ่าน Local Web Server (แนะนำ)
การรันผ่าน Local Server ช่วยให้เบราว์เซอร์โหลดไฟล์ JSON และ Assets ได้อย่างราบรื่น:

```bash
# ใช้ Python (มีติดเครื่องเกือบทุกระบบ)
python -m http.server 3000

# หรือใช้ Node.js npx serve
npx serve .

# หรือใช้ PHP
php -S localhost:3000
```
จากนั้นเปิดเบราว์เซอร์ไปที่: `http://localhost:3000`

---

## 📥 วิธีนำ Skill ไปใช้งาน (Installation & Usage)

ผู้ใช้สามารถนำ Skill จากคลังนี้ไปติดตั้งใน AI Agent ได้ตามรูปแบบที่ต้องการ:

### 1. ติดตั้งแบบ Global (ใช้งานได้กับทุกโปรเจกต์ในเครื่อง)

สำหรับ **Google Antigravity / Gemini CLI**:
คัดลอกโฟลเดอร์ของ Skill ที่ต้องการไปวางที่ไดเรกทอรีส่วนตัว:

- **Windows**:
  ```powershell
  Copy-Item -Path ".\skills\<skill-name>" -Destination "$env:USERPROFILE\.gemini\config\skills\" -Recurse
  ```
- **macOS / Linux**:
  ```bash
  cp -r ./skills/<skill-name> ~/.gemini/config/skills/
  ```

### 2. ติดตั้งเฉพาะโปรเจกต์ (Workspace Level)

หากต้องการนำ Skill เข้าไปใช้เฉพาะในโปรเจกต์ใดโปรเจกต์หนึ่ง:
- สร้างโฟลเดอร์ `.agent/skills/` หรือ `.gemini/skills/` ในรากของโปรเจกต์ปลายทาง
- วางโฟลเดอร์ Skill ลงไป AI Agent จะตรวจจับและโหลด Skill ขึ้นมาใช้งานโดยอัตโนมัติ

### 3. การเรียกใช้งานในบทสนทนา (Activation)

AI Agent จะตรวจสอบเงื่อนไขการทำงานใน `SKILL.md` และเปิดใช้งานให้โดยอัตโนมัติเมื่อ Prompt ตรงกับความสามารถของ Skill หรือเรียกใช้งานโดยตรง:
```text
"ช่วยออกแบบ UI ตามแนวทางของ ui-ux-pro-max"
"ช่วยวิเคราะห์โค้ดด้วย archify skill"
"ช่วยลดความยาวและประหยัด token ภาษาไทยด้วย thai-token-optimizer"
```

---

## 🛠️ โครงสร้างมาตรฐานของแต่ละ Skill (`SKILL.md`)

แต่ละ Skill จะมีไฟล์ `SKILL.md` เป็นหัวใจสำคัญ ประกอบด้วย 2 ส่วนหลัก:

```markdown
---
name: skill-name
description: คำอธิบายสั้นๆ เกี่ยวกับหน้าที่ของ Skill และสถานการณ์ที่ควรเรียกใช้
---

# Skill Instructions

## เมื่อไหร่ที่ควรใช้ Skill นี้
- ระบุสถานการณ์ คีย์เวิร์ด หรือปัญหาที่ Skill นี้เข้ามาแก้ไข

## ขั้นตอนการทำงาน (Workflow / Rules)
1. ขั้นตอนที่ 1 ...
2. ขั้นตอนที่ 2 ...

## ตัวอย่างคำสั่งและแนวทางปฏิบัติ (Examples & Guidelines)
...
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
