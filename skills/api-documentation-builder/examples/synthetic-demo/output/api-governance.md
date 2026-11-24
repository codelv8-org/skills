# API Governance & Security

**SYNTHETIC CONTRACT | TEMPLATE — NOT VERIFIED | NO LIVE CALLS**

ระบบ: Demo Department Directory · Contract v0.0.0 · Audience: Developer / AI Agent  
หลักฐาน: SRC_DEMO_API (สัญญา API สมมุติที่อยู่ในชุดนี้) · Metadata classification: Public demo  
เอกสารนี้อธิบายสัญญาสมมุติเท่านั้น ไม่ได้ยืนยันว่ามีระบบจริง ไม่ให้สิทธิ์เข้าถึงข้อมูล และไม่ได้ทดสอบ endpoint ใด

## ขอบเขตและการอนุญาต

| Control | สถานะในตัวอย่าง |
| --- | --- |
| Authentication | HTTP Bearer ตามสัญญาสมมุติ |
| Operation data classification | Internal ทั้งสอง GET |
| Live access and real values | Denied |
| Scopes / owner / retention / audit / rate limit | Unknown; ต้องยืนยันแยก |
| Agent operations | None; deny by default |

## ข้อเสนอแนะสำหรับระบบจริง

เจ้าของ API ต้องตรวจขอบเขตและอนุมัติการเข้าถึงแยกจากเอกสาร ใช้ least privilege และ response validation; ไม่บันทึก token หรือ payload ที่มีข้อมูลอ่อนไหว  
การบังคับใช้ต้องอยู่ในระบบจริง ไม่ใช่ Prompt หรือเอกสารเพียงอย่างเดียว  
ไม่อ้างว่าระบบสมมุติมี Control ที่ยังไม่ได้ยืนยัน และไม่รับรอง PDPA compliance
