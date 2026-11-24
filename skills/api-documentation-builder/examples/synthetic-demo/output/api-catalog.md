# บัญชี API (API Catalog)

**SYNTHETIC CONTRACT | TEMPLATE — NOT VERIFIED | NO LIVE CALLS**

ระบบ: Demo Department Directory · Contract v0.0.0 · Audience: Developer / AI Agent  
หลักฐาน: SRC_DEMO_API (สัญญา API สมมุติที่อยู่ในชุดนี้) · Metadata classification: Public demo  
เอกสารนี้อธิบายสัญญาสมมุติเท่านั้น ไม่ได้ยืนยันว่ามีระบบจริง ไม่ให้สิทธิ์เข้าถึงข้อมูล และไม่ได้ทดสอบ endpoint ใด

## API inventory

| Method | Path | Operation ID | Purpose | Auth | Data class |
| --- | --- | --- | --- | --- | --- |
| GET | /demo/departments | listDemoDepartments | ค้นหารายการรหัสหน่วยงานสมมุติ | DemoBearer | Internal |
| GET | /demo/departments/{code} | getDemoDepartment | ดูรหัสหน่วยงานสมมุติตาม code | DemoBearer | Internal |

ทั้งสอง Operation มีสถานะ Template และไม่มีสิทธิ์เรียกใช้งานจริง  
Scope, Owner role, Rate limit, Pagination, SLA: ยังไม่ยืนยันและไม่ใช่ข้อกำหนดของตัวอย่าง

หลักฐาน: SRC_DEMO_API · [OpenAPI](openapi.yaml)
