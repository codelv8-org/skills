# Photoreal Head — Projection & Benchmark Lab v3.1.1

ตัวอย่างเส้นทาง **Existing scan → Clay / UV QA → Calibrated projection → Robust fusion → Holdout benchmark → Browser** ของ `photoreal-head-web v3.1.1` โดยเก็บไฟล์ GLB สแกนรุ่นเดิมเป็น Baseline ไม่อ้างว่าเป็นโมเดลที่ปั้นขึ้นใหม่

## Projection Lab (v3.1.1)

GitHub Pages build สร้างผลใหม่จากสำเนา `model/projection-head.glb` ซึ่งสืบทอดรูปทรงและสีจากสแกน `model/head.glb` ที่มีสิทธิ์เผยแพร่ CC BY 3.0 เท่านั้น รัน `scripts/build-photoreal-example.py` ผ่าน Projection Engine จริง สร้าง 9 โหมดและรายงาน `reports/projection_lab.json` พร้อมภาพ Overview ใหม่ที่อ้างอิงผลจาก run เดียวกัน:

- Front-only, 8-view, weighted mean ที่มี synthetic tint, robust consensus และ reviewed quarantine
- Coverage, Ambiguity, UV anisotropy, UV density; สีเทาคือพื้นที่ไม่มีข้อมูล
- ตัวเลข common-support MAE และ Coverage จาก holdout แยกจาก training

```bash
python -m pip install -r skills/photoreal-head-web/scripts/requirements-projection.txt
python scripts/build-photoreal-example.py --strict
```

ผลคือ B1 rendered-asset diagnostic แม้ geometry มาจากสแกนจริง ไม่ใช่ benchmark จากภาพถ่ายอิสระหรือ photorealism score ไม่ได้อนุมัติ final GLB หรือสร้าง intrinsic albedo ใหม่ หาก build ไม่สำเร็จ manifest แสดง BLOCKED และ viewer คง Baseline; ไม่เผยแพร่ผลเก่าหรือผลที่แต่งขึ้น ภาพ clay และรายงาน build เดิมด้านล่างเป็นหลักฐาน Baseline เท่านั้น

### เหตุที่ใช้ Atlas แยกสำหรับ Projection

UV ต้นฉบับมีส่วนซ้อนกัน สามเหลี่ยมกลับทิศ และ UV ที่ยุบตัว จึงไม่ผ่าน numeric UV gate แม้เปิด GLB ดูได้ตามปกติ เก็บ `model/head.glb` และ color/normal maps เดิมไว้เป็น Baseline พร้อมแสดงผลตรวจจริงใน `projection-lab/baseline_uv_report.json`.

สำเนา `model/projection-head.glb` เก็บรูปทรงและสามเหลี่ยมทั้งหมดเดิม แต่กาง UV ใหม่และถ่ายเฉพาะสีจากตำแหน่งบนผิวเดิม โดยแก้การกลับด้านแกน V ของภาพต้นฉบับก่อนถ่ายสี การตรวจภาพจริงพบว่าสีปากและตาเดิมอยู่ผิดตำแหน่ง จึงไม่ใช้ความคลาดเคลื่อนเทียบต้นฉบับที่กลับด้านเป็นหลักฐานคุณภาพ ใช้สำหรับ **unlit B1 diagnostic** เท่านั้น ไม่ย้าย tangent normal เดิมไปบน UV ใหม่ และไม่อ้างว่า automatic atlas เป็น anatomical atlas สำหรับ production. วิธีสร้าง hashes และผลเปรียบเทียบสีกับต้นฉบับที่จัดทิศภาพแล้วอยู่ใน `reports/atlas_preparation.json`; สคริปต์ที่สร้างซ้ำได้คือ `scripts/prepare-photoreal-atlas.py` จากราก repository.

ก่อนสร้างผลทุกครั้ง builder ตรวจ hash ของต้นฉบับและสำเนากับ preparation report แล้วบังคับ `PASS_UV_ONLY` ที่ไม่มี overlap, degenerate, wrong winding หรือ out-of-bounds รวมถึงเกณฑ์ distortion/density เดิม การทดสอบล้มจะเก็บ UV report และ heatmaps ไว้ให้ตรวจสาเหตุ ทั้ง PR และ Deploy ใช้ `--strict`.

Viewer ตรวจ SHA-256 ของโมเดลจริงก่อนเปิดโหมด Projection, สลับไปใช้รูปทรงสำเนากับ UV ที่ตรงกับผลทดสอบ และกลับไปยังโมเดล Baseline เมื่อเลือกพื้นผิว / Clay / Wireframe. สำหรับ Baseline SHA ที่ระบุในโค้ดเท่านั้น Viewer ตั้ง `flipY=true` ให้ Color / Normal เพื่อจัดทิศภาพให้ตรงรูปทรง โดยไม่แก้ bytes ของ GLB หรือเปลี่ยน normal scale. เป็นการแก้การแสดงผล ไม่ใช่การรับรอง PBR. สีเทาในผล Projection คือพื้นที่ไม่มีข้อมูลที่สังเกตได้ ไม่ใช่สีผิวที่เติมขึ้น.

สร้าง Atlas ซ้ำจากราก repository (ขั้นตอน authoring; CI ตรวจ artifact ที่ผูก hash แล้ว):

```bash
python -m pip install xatlas==0.0.11 -r skills/photoreal-head-web/scripts/requirements-projection.txt
python scripts/prepare-photoreal-atlas.py
python scripts/build-photoreal-example.py --strict
```

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
