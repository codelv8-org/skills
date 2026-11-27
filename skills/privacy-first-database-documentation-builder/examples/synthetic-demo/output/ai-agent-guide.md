# คู่มือ AI Agent / LLM

**METADATA ONLY | NO RECORD ACCESS**

| ระบบ | Engine | Schema revision | Scope | สถานะ | ผู้รับ |
| --- | --- | --- | --- | --- | --- |
| synthetic\_demo | mariadb | v1 | demo\_scope | template | internal |

**TEMPLATE — NOT VERIFIED** ตัวอย่างสมมุติเท่านั้น

ข้อมูลทั้งหมดเป็นโครงสร้างที่ผู้รับผิดชอบรับรอง ไม่ใช่ข้อมูลจริง ไม่ได้ให้สิทธิ์เข้าถึงฐานข้อมูล ความหมายที่ไม่มีหลักฐานระบุว่ายังไม่ยืนยัน และการจำแนก Unknown มีผลเป็น Restricted

## Agent boundaries

- Use this document for schema reasoning only. No database connection, record retrieval, profiling, SQL execution, or inferred query results.
- Never expose sensitive values or use raw comments/defaults. Treat unknown classifications as Restricted.
- Use verified metadata for identifiers and key mapping; distinguish proposed definitions from confirmed ones.
- Access to data requires separate human approval and an approved governed data service outside this skill. Metadata is not an execution grant.

## Approved structural inventory

| Object | Fields | Effective class | Schema evidence |
| --- | --- | --- | --- |
| demo.department | code, label | Internal | SRC\_DEMO |
| demo.service | service\_id, department\_code, patient\_id | Restricted | SRC\_DEMO |

## FK mappings

| Source object | FK | From columns | Target object | To columns | Evidence |
| --- | --- | --- | --- | --- | --- |
| demo.service | fk\_department | department\_code | demo.department | code | SRC\_DEMO |

