# พจนานุกรมข้อมูล API (API Data Dictionary)

**SYNTHETIC CONTRACT | TEMPLATE — NOT VERIFIED | NO LIVE CALLS**

ระบบ: Demo Department Directory · Contract v0.0.0 · Audience: Developer / AI Agent  
หลักฐาน: SRC_DEMO_API (สัญญา API สมมุติที่อยู่ในชุดนี้) · Metadata classification: Public demo  
เอกสารนี้อธิบายสัญญาสมมุติเท่านั้น ไม่ได้ยืนยันว่ามีระบบจริง ไม่ให้สิทธิ์เข้าถึงข้อมูล และไม่ได้ทดสอบ endpoint ใด

## Request fields

| Operation ID | Location / field | Type | Required | Nullable | Constraint | Class |
| --- | --- | --- | --- | --- | --- | --- |
| getDemoDepartment | path.code | string | Yes | No | 1–20 characters | Internal |

ไม่มี request body สำหรับทั้งสอง Operation

## Response fields

| Component / field | Type | Required | Nullable | Constraint / meaning | Class |
| --- | --- | --- | --- | --- | --- |
| DepartmentList.items | array of Department | Yes | No | รายการหน่วยงานสมมุติ | Internal |
| Department.code | string | Yes | No | 1–20 characters; รหัสหน่วยงานสมมุติ | Internal |
| Error.code | string | Yes | No | รหัสข้อผิดพลาดสำหรับโปรแกรม | Internal |

ทั้งสาม Component เป็น object ที่ไม่อนุญาต additional properties  
Format, Unit, Enum, Default: ไม่ระบุใน Contract; ไม่เติมค่าโดยการคาดเดา

## Mapping

| Operation | Status | Response component |
| --- | --- | --- |
| listDemoDepartments | 200 | DepartmentList |
| getDemoDepartment | 200 | Department |
| Both | 401, 403 | Error |
| getDemoDepartment | 404 | Error |

หลักฐาน: SRC_DEMO_API · [OpenAPI](openapi.yaml)
