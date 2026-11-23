---
name: webapp-user-manual-pdf
description: Generate publication-grade, print-ready PDF user manuals for Web Applications using modern CSS Paged Media (@page, running headers/footers, A4 layout, cover page, and page-break optimization). Use when asked for PDF user manuals, คู่มือใช้งาน PDF, พิมพ์คู่มือเป็น PDF, เอกสารส่งมอบโครงการ, or formal documentation ready for printing. Compatible with Antigravity, Claude Code, and Codex.
category: Document
tags: [document, pdf, user-manual, print, css-paged-media, a4, webapp]
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

# Web Application User Manual PDF Skill (คู่มือใช้งานระบบรูปแบบ PDF พร้อมพิมพ์)

Skill พิเศษสำหรับจัดทำ**คู่มือการใช้งานระบบ Web Application ในรูปแบบ PDF เกรดสิ่งพิมพ์และส่งมอบโครงการ (Publication-Grade & Project Deliverable)** โดยใช้เทคโนโลยี **CSS Paged Media (`@page`)** ทำให้ได้เอกสารขนาด A4 ที่จัดหน้าสวยงาม มีหน้าปกทางการ, ตารางประวัติเอกสารและการอนุมัติ (Sign-off Matrix), สารบัญพร้อมเลขหน้า, หัวกระดาษ/ท้ายกระดาษอัตโนมัติ (Running Headers/Footers), และการควบคุมการตัดหน้า (Page Break) ที่แม่นยำ ไม่ตัดขาดกลางตารางหรือรูปภาพ

---

## 🎯 เมื่อไหร่ที่ควรใช้ Skill นี้ (Trigger Conditions)

เรียกใช้งาน Skill นี้เมื่อผู้ใช้ต้องการ:
- "สร้างคู่มือการใช้งานระบบเป็นไฟล์ PDF" / "เขียนคู่มือ PDF สำหรับส่งมอบงาน"
- "จัดหน้าคู่มือทำเล่มเอกสารสำหรับพิมพ์ A4" / "ทำ User Manual พร้อมปริ้นท์"
- "Generate print-ready PDF user manual for web application"
- ต้องการเอกสารที่มีหน้าปกเป็นทางการ, ตารางตรวจรับมอบงาน, สารบัญระบุหน้า, และจัดหน้ากระดาษไม่ให้ข้อความล้นหรือถูกตัดแบ่งอย่างไม่เหมาะสม

---

## ⚖️ ความแตกต่างระหว่าง HTML ทั่วไป vs PDF Paged Media

| คุณลักษณะ | คู่มือเว็บทั่วไป (HTML) | คู่มือ PDF สิ่งพิมพ์ (Skill นี้) |
|---|---|---|
| **ขอบเขตพื้นที่** | Continuous Scrolling (เลื่อนลงไม่สิ้นสุด) | **Fixed Paged (ขนาด A4: 210 x 297 mm)** |
| **หน้าปก (Cover)** | แบนเนอร์หัวเรื่องด้านบน | **Full-bleed Cover Page แยกหน้าเดี่ยว** |
| **การตรวจรับงาน** | ไม่มี | **ตารางประวัติแก้ไขและลายมือชื่ออนุมัติ (Sign-off)** |
| **หัว/ท้ายกระดาษ** | Sticky Topbar / Footer | **Running Header & Footer พร้อมเลขหน้า `หน้าที่ X / Y`** |
| **การขึ้นหน้าใหม่** | ไหลตามจอ | **คุมด้วย `break-before: page;` และ `break-inside: avoid;`** |
| **ตารางและรูปภาพ** | ย่อขยายตาม Responsive | **ล็อกขนาดพอดีคอลัมน์ A4 และไม่ถูกตัดครึ่งหน้า** |

---

## 🏛️ โครงสร้างเล่มเอกสารมาตรฐาน (Document Architecture)

เอกสาร PDF ที่สร้างขึ้นจะแบ่งออกเป็น 4 ส่วนหลักตามมาตรฐานสากล:

```text
[ส่วนที่ 1: ปกและข้อมูลควบคุม]
├── หน้า 1: หน้าปกหลัก (Official Cover Page)
└── หน้า 2: แผ่นควบคุมเอกสารและการตรวจรับ (Document Control & Sign-off)

[ส่วนที่ 2: สารบัญนำทาง]
├── หน้า 3: สารบัญเนื้อหา (Table of Contents with Dot Leaders)
└── หน้า 3: สารบัญภาพและตาราง (List of Figures & Tables)

[ส่วนที่ 3: เนื้อหาคู่มือหลัก (Chapters)]
├── บทที่ 1: บทนำและภาพรวมระบบ (Overview & Objectives)
├── บทที่ 2: ข้อกำหนดระบบและการเข้าใช้งาน (Requirements & Access)
├── บทที่ 3: โครงสร้างหน้าจอและเมนูนำทาง (UI Layout & Navigation)
├── บทที่ 4: ขั้นตอนการปฏิบัติงานแบบ Step-by-Step (Workflows)
├── บทที่ 5: พจนานุกรมฟิลด์และแบบฟอร์ม (Form Field Dictionary)
└── บทที่ 6: การรายงานและปัญหาที่พบบ่อย (Reports & Troubleshooting)

[ส่วนที่ 4: ปกหลังและข้อมูลช่วยเหลือ]
└── หน้าสุดท้าย: ช่องทางการติดต่อและความช่วยเหลือ (Support & Back Cover)
```

---

## 🎨 กฎการจัดหน้าด้วย CSS Paged Media (Key CSS Rules)

เพื่อให้เอกสารแปลงเป็น PDF ได้อย่างสมบูรณ์แบบ ให้ใช้กฎ CSS ดังนี้:

### 1. กำหนดขนาดกระดาษและขอบ (Page Size & Margins)
```css
@page {
  size: A4 portrait; /* 210mm x 297mm */
  margin: 20mm 15mm 20mm 15mm;
  @top-left { content: "{{SYSTEM_NAME}} - คู่มือการใช้งาน"; font-size: 8pt; color: #64748b; }
  @bottom-left { content: "เอกสารทางการ - ห้ามเผยแพร่โดยไม่ได้รับอนุญาต"; font-size: 8pt; color: #94a3b8; }
  @bottom-right { content: "หน้าที่ " counter(page) " จาก " counter(pages); font-size: 8pt; font-weight: bold; }
}

/* ยกเว้นหัว/ท้ายกระดาษในหน้าปก */
@page:first {
  margin: 0;
  @top-left { content: normal; }
  @bottom-left { content: normal; }
  @bottom-right { content: normal; }
}
```

### 2. การควบคุมการขึ้นหน้าใหม่และการป้องกันการตัดกลางวัตถุ
```css
/* บังคับขึ้นหน้าใหม่ก่อนขึ้นบทใหม่ */
.chapter-start {
  break-before: page;
  page-break-before: always;
}

/* ป้องกันไม่ให้การ์ดขั้นตอน ตาราง หรือรูปภาพถูกตัดแบ่งครึ่งหน้า */
.step-card, table, tr, .screenshot-wrapper, .callout {
  break-inside: avoid;
  page-break-inside: avoid;
}

/* ป้องกันหัวข้อลอยท้ายหน้าโดยไม่มีเนื้อหาตามมา (Orphan headings) */
h1, h2, h3 {
  break-after: avoid;
  page-break-after: avoid;
}
```

---

## 🤖 การทำงานร่วมกับ AI Agent (Multi-Agent Support)

Skill นี้ออกแบบตามมาตรฐาน Phase 1 เพื่อรองรับ AI Coding Agents ทั้ง 3 ค่ายอย่างสมบูรณ์แบบ:

### 1. 🔮 Google Antigravity
- **ตำแหน่งติดตั้ง:** `~/.gemini/config/skills/webapp-user-manual-pdf/` หรือ `.agent/skills/webapp-user-manual-pdf/`
- **การส่งออก PDF:** สั่งรัน PowerShell Script `scripts/export-pdf.ps1` ผ่าน `run_command` เพื่อแปลง HTML เป็น PDF อัตโนมัติ

### 2. 🟧 Anthropic Claude Code
- **ตำแหน่งติดตั้ง:** `~/.claude/skills/webapp-user-manual-pdf/` หรือ `.claude/skills/webapp-user-manual-pdf/`
- **การส่งออก PDF:** สั่งรัน Bash Script `scripts/export-pdf.sh` หรือคำสั่ง Headless Chrome ผ่าน Tool `Bash` (รองรับทั้ง macOS, Linux และ Windows)

### 3. 🟩 OpenAI Codex
- **ตำแหน่งติดตั้ง:** `~/.codex/skills/webapp-user-manual-pdf/` หรือ `.codex/skills/webapp-user-manual-pdf/`
- **การส่งออก PDF:** รันคำสั่งแปลงไฟล์ผ่าน Shell Execution โดยเลือกสคริปต์ที่สอดคล้องกับ OS ปลายทาง

---

## 🖨️ วิธีการส่งออกเป็นไฟล์ PDF (Export to PDF Methods)

### วิธีที่ 1: สคริปต์อัตโนมัติประจำแพลตฟอร์ม (แนะนำ)

#### บน Windows (PowerShell):
```powershell
.\scripts\export-pdf.ps1 -InputHtml "manual-pdf.html" -OutputPdf "User_Manual.pdf"
```

#### บน macOS / Linux (Bash):
```bash
bash ./scripts/export-pdf.sh --input manual-pdf.html --output User_Manual.pdf
```

### วิธีที่ 2: รันผ่าน Headless Browser CLI โดยตรง

```bash
# macOS / Linux (Google Chrome / Chromium)
google-chrome --headless --disable-gpu --run-all-compositor-stages-before-draw --print-to-pdf="User_Manual.pdf" --no-pdf-header-footer "manual-pdf.html"

# Windows (Microsoft Edge PowerShell)
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless --disable-gpu --run-all-compositor-stages-before-draw --print-to-pdf="User_Manual.pdf" --print-to-pdf-no-header "manual-pdf.html"
```

### วิธีที่ 3: ใช้หน้าต่างพิมพ์ของเบราว์เซอร์ (Browser Print Dialog)
1. ดับเบิลคลิกเปิดไฟล์ `manual-pdf.html` ใน Chrome หรือ Edge
2. กดปุ่ม <kbd>Ctrl</kbd> + <kbd>P</kbd> (Windows) หรือ <kbd>Cmd</kbd> + <kbd>P</kbd> (Mac)
3. ปลายทาง (Destination): เลือก **"บันทึกเป็น PDF" (Save as PDF)**
4. ขนาดกระดาษ (Paper size): **A4**
5. ระยะขอบ (Margins): **ไม่มี (None)** *(เพราะ CSS จัดการ Margin ให้แล้ว)*
6. ตัวเลือก (Options): **ติ๊กเครื่องหมายถูกที่ "กราฟิกพื้นหลัง" (Background graphics)**
7. คลิก **"บันทึก" (Save)**

---

## 📂 เทมเพลตและสคริปต์ใน Skill นี้

- [templates/pdf-manual-template.html](file:///d:/Projects/skills/skills/webapp-user-manual-pdf/templates/pdf-manual-template.html): โครงร่าง HTML ขนาด A4 พร้อม CSS `@page`, ปกทางการ, สารบัญ, และตารางตรวจรับมอบงาน
- [scripts/export-pdf.ps1](file:///d:/Projects/skills/skills/webapp-user-manual-pdf/scripts/export-pdf.ps1): สคริปต์ PowerShell สำหรับสั่ง Export HTML เป็น PDF อัตโนมัติผ่าน Edge/Chrome บน Windows
- [scripts/export-pdf.sh](file:///d:/Projects/skills/skills/webapp-user-manual-pdf/scripts/export-pdf.sh): สคริปต์ Bash สำหรับสั่ง Export HTML เป็น PDF อัตโนมัติผ่าน Chrome/Chromium บน macOS/Linux
- [references/pdf-styling-guide.md](file:///d:/Projects/skills/skills/webapp-user-manual-pdf/references/pdf-styling-guide.md): คู่มือเทคนิคการตั้งค่า CSS Paged Media และข้อผิดพลาดที่ต้องระวัง
