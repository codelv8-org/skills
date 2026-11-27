# Synthetic Database Documentation Example

ใช้ fixture [metadata-template.json](../../assets/metadata-template.json) และ generator จริงของ Skill ในโหมด full; fixture เป็น template ไม่ใช่ข้อมูล production. ไม่มีการเชื่อมต่อฐานข้อมูล ไม่มี record values. ตัวอย่างประกอบด้วย 2 objects, 5 columns, 1 FK mapping และ 7 main documents. Unknown classification มีผลเป็น Restricted.

- [Interactive overview](index.html)
- [Generated Markdown index](output/README.md)
- [Data Dictionary](output/data-dictionary.md)
- [ERD Mermaid](output/er-diagram.mmd)
- [Release manifest](output/release-manifest.md)

สร้าง PDF จากชุด Markdown นี้โดยรัน `python scripts/build-documentation-examples.py` ที่ root ของ repository. GitHub Pages workflow สร้าง PDF ก่อนแพ็ก ZIP. ผลลัพธ์เป็น candidate จากข้อมูลสมมุติเท่านั้น ไม่ถือเป็นการรับรองระบบจริงหรือการอนุญาตเข้าถึงข้อมูล.
