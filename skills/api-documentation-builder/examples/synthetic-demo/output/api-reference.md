# API Reference

**SYNTHETIC CONTRACT | TEMPLATE — NOT VERIFIED | NO LIVE CALLS**

ระบบ: Demo Department Directory · Contract v0.0.0 · Audience: Developer / AI Agent  
หลักฐาน: SRC_DEMO_API (สัญญา API สมมุติที่อยู่ในชุดนี้) · Metadata classification: Public demo  
เอกสารนี้อธิบายสัญญาสมมุติเท่านั้น ไม่ได้ยืนยันว่ามีระบบจริง ไม่ให้สิทธิ์เข้าถึงข้อมูล และไม่ได้ทดสอบ endpoint ใด

## Contract

- OpenAPI 3.1.0 · [openapi.yaml](openapi.yaml)
- Base URL: `https://api.example.invalid` (placeholder; ไม่มีบริการให้เรียก)
- Media type: application/json
- Security: HTTP Bearer ตาม Contract สมมุติ ไม่ได้ระบุ token issuer หรือ scopes

## GET /demo/departments

Operation ID: `listDemoDepartments`  
ไม่รับ path/query parameters หรือ request body ตาม Contract นี้

| Status | Response schema | Meaning |
| --- | --- | --- |
| 200 | DepartmentList | รายการรหัสหน่วยงานสมมุติ |
| 401 | Error | ไม่มีหรือยืนยันตัวตนไม่สำเร็จ |
| 403 | Error | ไม่มีสิทธิ์ |

ตัวอย่าง response สมมุติ 200:

```json
{"items":[{"code":"DEMO_DEPT"}]}
```

## GET /demo/departments/{code}

Operation ID: `getDemoDepartment`  
`code`: required path parameter, string 1–20 characters

| Status | Response schema | Meaning |
| --- | --- | --- |
| 200 | Department | รหัสหน่วยงานสมมุติ |
| 401 | Error | ไม่มีหรือยืนยันตัวตนไม่สำเร็จ |
| 403 | Error | ไม่มีสิทธิ์ |
| 404 | Error | ไม่พบรหัสหน่วยงานสมมุติ |

ตัวอย่าง response สมมุติ 200:

```json
{"code":"DEMO_DEPT"}
```

ข้อจำกัด: pagination, filters, sorting, rate limits, version lifecycle และ retry policy ไม่ได้ระบุไว้ ไม่ควรตีความว่าใช้งานได้จริง
