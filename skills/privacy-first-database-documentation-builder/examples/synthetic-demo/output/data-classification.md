# การจำแนกข้อมูล (Data Classification)

**METADATA ONLY | NO RECORD ACCESS**

| ระบบ | Engine | Schema revision | Scope | สถานะ | ผู้รับ |
| --- | --- | --- | --- | --- | --- |
| synthetic\_demo | mariadb | v1 | demo\_scope | template | internal |

**TEMPLATE — NOT VERIFIED** ตัวอย่างสมมุติเท่านั้น

ข้อมูลทั้งหมดเป็นโครงสร้างที่ผู้รับผิดชอบรับรอง ไม่ใช่ข้อมูลจริง ไม่ได้ให้สิทธิ์เข้าถึงฐานข้อมูล ความหมายที่ไม่มีหลักฐานระบุว่ายังไม่ยืนยัน และการจำแนก Unknown มีผลเป็น Restricted

การจำแนกเป็นความเสี่ยงของข้อมูลที่ฟิลด์อาจแทน ไม่ใช่สิทธิ์เผยแพร่ metadata

| Object | Effective class |
| --- | --- |
| demo.department | Internal |
| demo.service | Restricted |

| Object | Field | Declared | Effective | เหตุผล | Evidence |
| --- | --- | --- | --- | --- | --- |
| demo.department | code | Internal | Internal | Owner declaration / ต้องทบทวน | SRC\_DEMO |
| demo.department | label | Internal | Internal | Owner declaration / ต้องทบทวน | SRC\_DEMO |
| demo.service | service\_id | Internal | Internal | Owner declaration / ต้องทบทวน | SRC\_DEMO |
| demo.service | department\_code | Internal | Internal | Owner declaration / ต้องทบทวน | SRC\_DEMO |
| demo.service | patient\_id | Unknown | Restricted | Unknown / ไม่ยืนยัน | SRC\_DEMO |

ต้องให้เจ้าของข้อมูลตรวจทานข้อจำกัดตามบริบทจริง ห้ามตีความว่า lint หรือ classification รับรองความสอดคล้อง PDPA
