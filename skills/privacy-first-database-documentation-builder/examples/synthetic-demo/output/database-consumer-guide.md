# คู่มือโครงสร้างฐานข้อมูล (Database Consumer Guide)

**METADATA ONLY | NO RECORD ACCESS**

| ระบบ | Engine | Schema revision | Scope | สถานะ | ผู้รับ |
| --- | --- | --- | --- | --- | --- |
| synthetic\_demo | mariadb | v1 | demo\_scope | template | internal |

**TEMPLATE — NOT VERIFIED** ตัวอย่างสมมุติเท่านั้น

ข้อมูลทั้งหมดเป็นโครงสร้างที่ผู้รับผิดชอบรับรอง ไม่ใช่ข้อมูลจริง ไม่ได้ให้สิทธิ์เข้าถึงฐานข้อมูล ความหมายที่ไม่มีหลักฐานระบุว่ายังไม่ยืนยัน และการจำแนก Unknown มีผลเป็น Restricted

## การใช้งาน

1. ตรวจสอบ scope และ schema revision ก่อนใช้เอกสาร
2. ค้นหาวัตถุใน Data Catalog และอ่านประเภทข้อมูล/ความหมายจาก Data Dictionary
3. ใช้ FK mapping ที่ยืนยันแล้วเพื่อเข้าใจความสัมพันธ์ โดยรักษาลำดับ composite keys
4. ตรวจ Effective classification และขอสิทธิ์แยกจาก Data Owner ก่อนเข้าถึงข้อมูลผ่านช่องทางที่องค์กรอนุมัติ

## ข้อจำกัด

เอกสารนี้ไม่ใช่เครื่องมือ Query และไม่ให้สิทธิ์เข้าถึงข้อมูลจริง ไม่สรุป Cardinality, nullability หรือความหมายที่ไม่มีหลักฐาน

| Object | Grain | Classification |
| --- | --- | --- |
| demo.department | หนึ่งรายการต่อรหัสหน่วยงาน | Internal |
| demo.service | ยังไม่ยืนยัน | Restricted |

