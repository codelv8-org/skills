# Synthetic API Documentation Example

ตัวอย่างการใช้ Skill สร้างเอกสารครบ 6 หมวดจาก [OpenAPI contract สมมุติ](output/openapi.yaml) ที่มี 2 GET operations, 3 schemas, HTTP Bearer แบบสมมุติ และ 0 approved agent tools. Host ใช้โดเมน .invalid. ไม่มีการเรียก API จริงหรือใช้ข้อมูลจริง.

- [Interactive overview](index.html)
- [Markdown index](output/README.md)
- [API Consumer Guide](output/api-consumer-guide.md)
- [OpenAPI YAML](output/openapi.yaml)
- [Tool manifest](output/tools.json)
- [Release manifest](output/release-manifest.md)

สร้าง PDF จากชุด Markdown นี้โดยรัน `python scripts/build-documentation-examples.py` ที่ root ของ repository. GitHub Pages workflow สร้าง PDF ก่อนแพ็ก ZIP. ตัวอย่างไม่ใช่ Contract ของระบบจริงและไม่ให้สิทธิ์เข้าถึงระบบใด.
