# ตัวอย่าง Photoreal head for web

ตัวอย่างเส้นทาง **Existing model → Clay review → Web material → GLB inspection → Browser** ของ `photoreal-head-web v2.0.0`

## เปิดดู

เปิด `preview.html` ผ่าน local HTTP server ของ repository เช่นวิธีใน README หลัก ไม่ใช่เปิดด้วย `file://` เพราะ browser ต้องโหลด JavaScript modules และ GLB

- พื้นผิว: color และ tangent-space normal จากสแกนต้นฉบับ
- Clay: ปิด texture เพื่อตรวจ cranial silhouette, เบ้าตา จมูก แก้ม หู และขากรรไกร
- Wireframe: ดูสามเหลี่ยมจริงของ mesh
- กล้อง: หน้า เฉียง ซ้าย ขวา พร้อมหมุน/ซูมด้วยเมาส์ สัมผัส และคีย์บอร์ด
- ดาวน์โหลด `model/head.glb` และอ่าน `reports/glb_qa.json`

## ตัวอย่าง prompt ที่ใช้ต่อได้

```text
ใช้ photoreal-head-web ตรวจโมเดลศีรษะสแกนที่มีสิทธิ์ใช้สำหรับเว็บ
เริ่มจาก clay ด้านหน้า เฉียง ซ้าย ขวา และมุมใต้จมูก
ตรวจ UV0 และพื้นผิว จากนั้นส่งออก GLB ที่ฝัง color/normal maps
สร้าง viewer ที่เปลี่ยนระหว่างพื้นผิว Clay และ Wireframe ได้
แยกผลตรวจโครงสร้างจาก anatomy และ likeness acceptance
ถ้าไม่มีข้อมูล landmark/photo-fit อิสระ ให้รายงาน REVIEW_REQUIRED
คงเครดิตและ license ของโมเดลต้นฉบับ และอย่าอ้างว่าเป็นโมเดลที่ปั้นใหม่
```

## ผลที่ทำจริง

- ปรับใช้ geometry สแกน ไม่ได้สร้าง geometry ใบหน้าขึ้นใหม่
- ตัดส่วนไหล่และคอด้านล่าง เหลือศีรษะกับช่วงคอ ขอบคอเปิดอยู่
- จัดวัสดุ glTF ใช้ color/normal maps ที่มีสิทธิ์ใช้และ roughness คงที่สำหรับสาธิต
- สร้างภาพ clay ห้ามุมและภาพพื้นผิวสองมุมด้วย Blender 5.2.2 LTS
- ส่งออก GLB จริงและตรวจด้วย `inspect_glb.py` ของ Skill
- สร้าง UV preview ด้วย `render_uv_layout_glb.py` ของ Skill
- จัดภาพ overview จากภาพ render ของโมเดลเดียวกัน ไม่มีภาพศีรษะจาก AI มาแทน mesh

ดูค่าที่ตรวจจริงใน `reports/build.json` และ `reports/glb_qa.json` แทนตัวเลขที่อาจล้าสมัยในเอกสาร

## ข้อจำกัด

G3 **REVIEW_REQUIRED**: ไม่มี landmarks ที่วัดอิสระหรือชุดภาพ subject-specific สำหรับ photo-fit จึงไม่รับรอง anatomy/likeness และไม่มีคะแนน photorealism ตัวเลขอัตโนมัติ

โมเดลต้นฉบับหลับตา ไม่มีลูกตา/ฟันแยกชิ้น ไม่มี rig หรือ eyebrow variants ความสูงหลังตัดคอประมาณ 0.205 เมตรเป็นสเกลสำหรับสาธิต ไม่ใช่ขนาดบุคคลที่วัดจริง เป็นตัวอย่างตรวจและส่งออกสำหรับเว็บ ไม่ใช่ final release หรือ watertight mesh สำหรับพิมพ์ 3D

## แหล่งที่มาและสิทธิ์

โมเดล **Infinite, 3D Head Scan by Lee Perry-Smith**, Infinite Realities / Triplegangers, **Creative Commons Attribution 3.0 Unported** นำมาจาก [Three.js r180](https://github.com/mrdoob/three.js/tree/r180/examples/models/gltf/LeePerrySmith) การปรับแก้และ source hashes อยู่ใน `reports/provenance.json`; ข้อความสิทธิ์ต้นฉบับอยู่ใน `LICENSE-head.txt`

Three.js r180 ใช้ MIT license อยู่ใน `vendor/LICENSE` เก็บไลบรารี local ทั้งหมดและปรับ relative import ของ GLTFLoader ให้ตรงกับโฟลเดอร์นี้

ฟอนต์ LINE Seed Sans TH จาก [LINE Seed](https://seed.line.me/) และ [ชุดดาวน์โหลดทางการ](https://seed.line.me/src/images/fonts/LINE_Seed_Sans_TH.zip) เก็บไฟล์ WOFF2 ไว้ local
