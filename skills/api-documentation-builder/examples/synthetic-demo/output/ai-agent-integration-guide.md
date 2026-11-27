# AI Agent / MCP Integration Guide

**SYNTHETIC CONTRACT | TEMPLATE — NOT VERIFIED | NO LIVE CALLS**

ระบบ: Demo Department Directory · Contract v0.0.0 · Audience: Developer / AI Agent  
หลักฐาน: SRC_DEMO_API (สัญญา API สมมุติที่อยู่ในชุดนี้) · Metadata classification: Public demo  
เอกสารนี้อธิบายสัญญาสมมุติเท่านั้น ไม่ได้ยืนยันว่ามีระบบจริง ไม่ให้สิทธิ์เข้าถึงข้อมูล และไม่ได้ทดสอบ endpoint ใด

## Operation discovery

อ่าน API Catalog, API Data Dictionary และ OpenAPI เพื่อเรียนรู้ความหมายของ Operation และโครงสร้าง Input/Output เท่านั้น

| Operation ID | Intended data shape | Agent execution |
| --- | --- | --- |
| listDemoDepartments | DepartmentList | Denied |
| getDemoDepartment | Department | Denied |

## Tool boundary

- `tools.json` เป็น draft manifest ที่มี 0 approved tools ไม่ใช่ MCP server หรือเครื่องมือที่เปิดใช้งาน
- Contract สมมุติไม่ใช่การอนุมัติจาก Data Owner ห้าม Agent เรียก API
- ก่อนสร้าง Tool จริง ต้องมี operation-level approval, verified scopes, input/output validation, privacy review และ controls ฝั่ง application
- ห้ามสร้าง unrestricted HTTP/SQL tool ห้ามเข้าถึงข้อมูลผู้ป่วยหรือข้อมูลจริง
- ใช้ [AGENTS.md](AGENTS.md) และ [llms.txt](llms.txt) เพื่อกำหนดขอบเขตการอ่านเอกสาร

No live execution, credentials, deployment or tool activation.
