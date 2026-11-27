# พจนานุกรมข้อมูล (Data Dictionary)

**METADATA ONLY | NO RECORD ACCESS**

| ระบบ | Engine | Schema revision | Scope | สถานะ | ผู้รับ |
| --- | --- | --- | --- | --- | --- |
| synthetic\_demo | mariadb | v1 | demo\_scope | template | internal |

**TEMPLATE — NOT VERIFIED** ตัวอย่างสมมุติเท่านั้น

ข้อมูลทั้งหมดเป็นโครงสร้างที่ผู้รับผิดชอบรับรอง ไม่ใช่ข้อมูลจริง ไม่ได้ให้สิทธิ์เข้าถึงฐานข้อมูล ความหมายที่ไม่มีหลักฐานระบุว่ายังไม่ยืนยัน และการจำแนก Unknown มีผลเป็น Restricted

จำนวนวัตถุ: 2 | จำนวนคอลัมน์: 5

## demo.department

| ชนิด | คำอธิบาย | Grain | Classification | หลักฐาน |
| --- | --- | --- | --- | --- |
| table | โครงสร้างสมมุติสำหรับหน่วยงาน | หนึ่งรายการต่อรหัสหน่วยงาน | Internal | SRC\_DEMO |

### โครงสร้างและคีย์

| ลำดับ | Field | Data type / dimension | Nullable | Key membership | Schema source |
| --- | --- | --- | --- | --- | --- |
| 1 | code | varchar (length=20) | No | PK pk\_department 1 | SRC\_DEMO |
| 2 | label | varchar (length=80) | Yes | — | SRC\_DEMO |

### ความหมายและความอ่อนไหว

| Field | ความหมาย | Format | Unit | Class → Effective | Definition status | Definition source |
| --- | --- | --- | --- | --- | --- | --- |
| code | รหัสหน่วยงานในโครงสร้างสมมุติ | ยังไม่ยืนยัน | ยังไม่ยืนยัน | Internal | verified | SRC\_DEMO |
| label | ยังไม่ยืนยัน | ยังไม่ยืนยัน | ยังไม่ยืนยัน | Internal | ยังไม่ยืนยัน | ยังไม่ยืนยัน |

### คีย์ (ตามลำดับคอลัมน์)

| Key | Kind | Ordered columns | Source |
| --- | --- | --- | --- |
| pk\_department | primary | code | SRC\_DEMO |

## demo.service

| ชนิด | คำอธิบาย | Grain | Classification | หลักฐาน |
| --- | --- | --- | --- | --- |
| table | ยังไม่ยืนยัน | ยังไม่ยืนยัน | Internal → Restricted | SRC\_DEMO |

### โครงสร้างและคีย์

| ลำดับ | Field | Data type / dimension | Nullable | Key membership | Schema source |
| --- | --- | --- | --- | --- | --- |
| 1 | service\_id | integer (precision=10, scale=0) | No | PK pk\_service 1 | SRC\_DEMO |
| 2 | department\_code | varchar (length=20) | No | FK fk\_department 1 | SRC\_DEMO |
| 3 | patient\_id | varchar (length=24) | Unknown | — | SRC\_DEMO |

### ความหมายและความอ่อนไหว

| Field | ความหมาย | Format | Unit | Class → Effective | Definition status | Definition source |
| --- | --- | --- | --- | --- | --- | --- |
| service\_id | ยังไม่ยืนยัน | ยังไม่ยืนยัน | ยังไม่ยืนยัน | Internal | ยังไม่ยืนยัน | ยังไม่ยืนยัน |
| department\_code | ยังไม่ยืนยัน | ยังไม่ยืนยัน | ยังไม่ยืนยัน | Internal | ยังไม่ยืนยัน | ยังไม่ยืนยัน |
| patient\_id | ยังไม่ยืนยัน | ยังไม่ยืนยัน | ยังไม่ยืนยัน | Unknown → Restricted | ยังไม่ยืนยัน | ยังไม่ยืนยัน |

### คีย์ (ตามลำดับคอลัมน์)

| Key | Kind | Ordered columns | Source |
| --- | --- | --- | --- |
| pk\_service | primary | service\_id | SRC\_DEMO |

### FK mappings

| Source object | FK | From columns | Target object | To columns | Source |
| --- | --- | --- | --- | --- | --- |
| demo.service | fk\_department | department\_code | demo.department | code | SRC\_DEMO |

## ข้อจำกัด

ไม่แสดงค่า default, raw comments, enum values, expressions, ตัวอย่างข้อมูลจริง หรือสถิติจาก records
