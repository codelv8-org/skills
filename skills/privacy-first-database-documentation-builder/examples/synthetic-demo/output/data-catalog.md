# บัญชีข้อมูล (Data Catalog)

**METADATA ONLY | NO RECORD ACCESS**

| ระบบ | Engine | Schema revision | Scope | สถานะ | ผู้รับ |
| --- | --- | --- | --- | --- | --- |
| synthetic\_demo | mariadb | v1 | demo\_scope | template | internal |

**TEMPLATE — NOT VERIFIED** ตัวอย่างสมมุติเท่านั้น

ข้อมูลทั้งหมดเป็นโครงสร้างที่ผู้รับผิดชอบรับรอง ไม่ใช่ข้อมูลจริง ไม่ได้ให้สิทธิ์เข้าถึงฐานข้อมูล ความหมายที่ไม่มีหลักฐานระบุว่ายังไม่ยืนยัน และการจำแนก Unknown มีผลเป็น Restricted

จำนวนวัตถุในขอบเขต: 2 (จำนวนเชิงโครงสร้าง ไม่ใช่จำนวน Record)

| Object | ชนิด | วัตถุประสงค์ | Grain | Owner role | Effective class | Schema source | Definition source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| demo.department | table | โครงสร้างสมมุติสำหรับหน่วยงาน | หนึ่งรายการต่อรหัสหน่วยงาน | Data Steward | Internal | SRC\_DEMO | SRC\_DEMO |
| demo.service | table | ยังไม่ยืนยัน | ยังไม่ยืนยัน | ยังไม่ยืนยัน | Restricted | SRC\_DEMO | ยังไม่ยืนยัน |

ไม่สรุปความถี่การอัปเดตหรือจำนวนข้อมูลจาก Schema
