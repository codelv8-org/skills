# คู่มือการใช้งาน API (API Consumer Guide)

**SYNTHETIC CONTRACT | TEMPLATE — NOT VERIFIED | NO LIVE CALLS**

ระบบ: Demo Department Directory · Contract v0.0.0 · Audience: Developer / AI Agent  
หลักฐาน: SRC_DEMO_API (สัญญา API สมมุติที่อยู่ในชุดนี้) · Metadata classification: Public demo  
เอกสารนี้อธิบายสัญญาสมมุติเท่านั้น ไม่ได้ยืนยันว่ามีระบบจริง ไม่ให้สิทธิ์เข้าถึงข้อมูล และไม่ได้ทดสอบ endpoint ใด

## 1. เริ่มต้นใช้งาน

คู่มือนี้ใช้สาธิตการอ่าน Contract และจัดเตรียม Request เท่านั้น โดยไม่มี API จริงรองรับ

1. ตรวจสอบชื่อ Operation และ Schema จาก [API Catalog](api-catalog.md) และ [OpenAPI](openapi.yaml)
2. หากนำแนวทางไปใช้กับระบบจริง ให้ขอ URL, สิทธิ์ และวิธียืนยันตัวตนจากผู้รับผิดชอบ API ผ่านช่องทางที่ได้รับอนุมัติแยกต่างหาก
3. อ่านตัวอย่าง Request ด้านล่างโดยไม่รันคำสั่ง ใช้ placeholder เท่านั้น

## 2. Authentication

Contract สมมุติกำหนด HTTP Bearer ใน header Authorization ไม่ได้กำหนด token issuer, scopes หรือกระบวนการออก token จริง  
ใช้ YOUR_ACCESS_TOKEN เป็น placeholder ห้ามใช้ token จริงในเอกสาร

## 3. ตัวอย่าง Request และ Response

### Step 1 — อ่านรายการหน่วยงานสมมุติ

```bash
curl --request GET 'https://api.example.invalid/demo/departments' \
  --header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  --header 'Accept: application/json'
```

ตัวอย่าง Response 200 สมมุติ (ไม่ได้มาจากการเรียก API):

```json
{"items":[{"code":"DEMO_DEPT"}]}
```

### Step 2 — อ่านข้อมูลตามรหัสหน่วยงานสมมุติ

```bash
curl --request GET 'https://api.example.invalid/demo/departments/DEMO_DEPT' \
  --header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  --header 'Accept: application/json'
```

ตัวอย่าง Response 200 สมมุติ:

```json
{"code":"DEMO_DEPT"}
```

## 4. การจัดการข้อผิดพลาด

| Status | ความหมายตาม Contract | แนวทางในระบบจริง (ข้อเสนอแนะ) |
| --- | --- | --- |
| 401 | Authentication missing / invalid | ตรวจวิธีขอสิทธิ์และสถานะ token โดยไม่บันทึกค่า token |
| 403 | Access not permitted | ตรวจนโยบายสิทธิ์กับผู้ดูแล ไม่เพิ่มสิทธิ์เอง |
| 404 | ไม่พบรหัส (getDemoDepartment) | ตรวจ path parameter ตาม Schema |

Contract กำหนด Error.code เป็น string แต่ไม่กำหนดชุดรหัส error ที่แน่นอน

## 5. ข้อจำกัดและความปลอดภัย

- ไม่ใช้ข้อมูลส่วนบุคคลจริง ไม่ส่ง payload หรือ credentials เข้า Agent
- ไม่รันคำสั่งตัวอย่างกับ endpoint จริงหรือ URL ภายนอก
- ไม่คาดเดา pagination, rate limit, retry policy หรือ SLA
- เอกสารนี้ไม่ให้สิทธิ์หรืออนุญาตการเชื่อมต่อ API จริง
