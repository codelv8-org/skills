# CSS Paged Media & Print Styling Guide for Web App Manuals

คู่มือข้อแนะนำทางเทคนิคสำหรับการออกแบบและจัดหน้าเอกสารสิ่งพิมพ์ขนาด A4 ด้วย CSS Paged Media สำหรับส่งออกเป็นไฟล์ PDF คุณภาพสูง

---

## 1. ขนาดกระดาษและระยะขอบ A4 (A4 Paper Dimensions)

กระดาษขนาด **A4** ตามมาตรฐาน ISO 216:
- ความกว้าง: `210 mm` (8.27 นิ้ว หรือ 794 px ที่ 96 DPI)
- ความสูง: `297 mm` (11.69 นิ้ว หรือ 1123 px ที่ 96 DPI)

### การตั้งค่าระยะขอบแนะนำ (Recommended Margins):
```css
@page {
  size: A4 portrait;
  margin-top: 22mm;
  margin-bottom: 22mm;
  margin-left: 18mm;
  margin-right: 18mm;
}
```

---

## 2. การควบคุมการแบ่งหน้า (Page Breaks Control)

ปัญหาที่พบบ่อยที่สุดเมื่อแปลง HTML เป็น PDF คือข้อความหรือตารางถูกตัดแบ่งครึ่งหน้าอย่างไม่สวยงาม:

### 2.1 บังคับขึ้นหน้าใหม่ (Force Break Before)
ใช้สำหรับเริ่มต้นบทใหม่ (Chapter) หรือเอกสารส่วนสำคัญ:
```css
.chapter-start {
  break-before: page;
  page-break-before: always;
}
```

### 2.2 ป้องกันการตัดขาดกลางวัตถุ (Avoid Break Inside)
ใช้กับการ์ดขั้นตอน (Step Card), ตาราง (Table), แถวในตาราง (TR), รูปภาพ และกล่องแจ้งเตือน (Callout):
```css
.avoid-break, table, tr, .step-box, .callout-box, .figure-box {
  break-inside: avoid;
  page-break-inside: avoid;
}
```

### 2.3 ป้องกันหัวข้อลอยค้างท้ายหน้า (Orphaned Headings)
ป้องกันไม่ให้ `<h1>`, `<h2>`, `<h3>` ไปอยู่ที่บรรทัดสุดท้ายของหน้า โดยไม่มีเนื้อหาตามมา:
```css
h1, h2, h3, h4 {
  break-after: avoid;
  page-break-after: avoid;
}
```

---

## 3. หัวกระดาษและท้ายกระดาษ (Running Headers & Footers)

ใน CSS Paged Media สามารถกำหนดเนื้อหาหัวกระดาษและท้ายกระดาษผ่าน Margin Box:

```css
@page {
  /* หัวกระดาษซ้าย: ชื่อระบบ */
  @top-left {
    content: "SmartHR Portal - คู่มือการใช้งาน";
    font-size: 8pt;
    color: #64748b;
  }

  /* หัวกระดาษขวา: รหัสเอกสาร */
  @top-right {
    content: "DOC-2026-V1";
    font-size: 8pt;
    color: #64748b;
  }

  /* ท้ายกระดาษขวา: หมายเลขหน้าอัตโนมัติ */
  @bottom-right {
    content: "หน้าที่ " counter(page);
    font-size: 8pt;
    font-weight: bold;
  }
}
```

---

## 4. ข้อควรระวังในการพิมพ์สีและพื้นหลัง (Background Graphics)

เบราว์เซอร์โดยปกติจะปิดการพิมพ์สีพื้นหลัง (`background-color`) ไว้โดยปริยาย เพื่อประหยัดหมึกพิมพ์
ในการทำคู่มือ PDF ที่ต้องการแบนเนอร์สีและการ์ดสวยงาม **จำเป็นต้องใส่คำสั่งนี้ใน body**:

```css
body {
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
```
และในการสั่งพิมพ์จากหน้าต่างเบราว์เซอร์ ต้องติ๊กเครื่องหมายถูกที่ **"Background graphics" (กราฟิกพื้นหลัง)** เสมอ
