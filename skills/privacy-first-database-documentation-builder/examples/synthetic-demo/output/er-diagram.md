# ความสัมพันธ์ฐานข้อมูล (ERD)

**METADATA ONLY | NO RECORD ACCESS**

| ระบบ | Engine | Schema revision | Scope | สถานะ | ผู้รับ |
| --- | --- | --- | --- | --- | --- |
| synthetic\_demo | mariadb | v1 | demo\_scope | template | internal |

**TEMPLATE — NOT VERIFIED** ตัวอย่างสมมุติเท่านั้น

ข้อมูลทั้งหมดเป็นโครงสร้างที่ผู้รับผิดชอบรับรอง ไม่ใช่ข้อมูลจริง ไม่ได้ให้สิทธิ์เข้าถึงฐานข้อมูล ความหมายที่ไม่มีหลักฐานระบุว่ายังไม่ยืนยัน และการจำแนก Unknown มีผลเป็น Restricted

แสดงความสัมพันธ์ FK ที่รับรองแล้วเท่านั้น ไม่อนุมาน Cardinality หรือ enforcement จากชื่อฟิลด์

| Object | PK (ordered) | UK (ordered) |
| --- | --- | --- |
| demo.department | code | ยังไม่ยืนยัน |
| demo.service | service\_id | ยังไม่ยืนยัน |

| Source object | FK | From columns | Target object | To columns | Evidence |
| --- | --- | --- | --- | --- | --- |
| demo.service | fk\_department | department\_code | demo.department | code | SRC\_DEMO |

