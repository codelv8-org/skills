# Ready-to-use Work agent briefs

> **v3:** Preserve the anatomy and general guidance below. For current mandatory UV, texture, candidate export and final promotion use [surface-release-gates.md](surface-release-gates.md) and [anatomical-uv-and-registration.md](anatomical-uv-and-registration.md); any earlier final export command is legacy.

## Generic realistic head

สร้างโมเดลศีรษะมนุษย์เสมือนจริงสำหรับแสดงบนเว็บไซต์ เฉพาะศีรษะ คอส่วนบน หู และดวงตา สไตล์ photorealistic ไม่ต้องสร้างร่างกาย ใบหน้าเป็นผู้ใหญ่ทั่วไป ไม่อ้างอิงคนจริง เน้น anatomy/skin roughness/normal map สมจริง ต้องมี UV0 ออกแบบเพื่อ texture painting และ bake high-to-low ส่งออก .blend, .glb, UV layout PNG, PBR maps, ภาพหน้า/เฉียง/ด้านข้าง, และรายงาน QA ทดสอบบน Three.js

## Brow-design showcase

สร้างศีรษะคนแบบสมจริงสำหรับ catalog ลายคิ้ว 3D ให้แยกคิ้วออกเป็น texture/overlay ที่เปลี่ยนได้ ไม่ฝังคิ้วถาวรลงบนผิว หน้าเกลี้ยงไม่ถูกผมบัง เน้น forehead, eyelid, brow bone anatomy ความละเอียดสูง ให้แปลงภาพลายคิ้วแต่ละแบบเป็น tapered strokes with transparency และแมปลง UV ให้เข้ากับรูปทรงที่สมจริง ตรวจภาพ close-up หน้า/เฉียง/ด้านข้าง ส่ง GLB optimized for web และ preview component

## Existing head mesh cleanup

ตรวจไฟล์ [head.blend/head.obj/head.glb] ปรับรูปทรงและ retopology ถ้าจำเป็น ตรวจ UV ทาสีหรือ bake PBR maps ให้เข้ากับ glTF ปรับลด polygon/texture เพื่อใช้บนเว็บ ส่ง source file + self-contained GLB พร้อมตาราง QA และ screenshot browser validation; ไม่เปลี่ยนลักษณะใบหน้าต้นทางมากเกินจำเป็น

## Rescue a head that still looks artificial (recommended upgraded workflow)

ใช้ skill `photoreal-head-web` เพื่อซ่อมโมเดลศีรษะคนเดิมที่ดูไม่สมจริง ห้ามเริ่มจาก texture หรือเพิ่ม polygon โดยทันที ให้ตรวจ Anatomy ก่อน: ขนาดกะโหลกด้านหน้าและด้านหลัง เบ้าตา ตำแหน่งตา หู สันจมูก ปลายจมูก ปีกจมูก จมูกจากด้านใต้ กระดูกโหนกแก้ม คาง และขากรรไกร เปรียบเทียบรูปด้านหน้า มุม 45 องศา และโปรไฟล์ทั้งสองด้านด้วยวัสดุสีเทาแบบ Clay ห้ามรักษารูปทรงเดิมที่ผิดเพียงเพื่อคง topology หากจำเป็นให้เริ่มด้วย Human Base Mesh ที่มีใบอนุญาตเหมาะสมแล้วปั้นใหม่ ทำ HEAD_LANDMARKS + nasal bridge (se/rh) + ear extents และรัน analyze_anatomy.py --high-fidelity พร้อมรายงานข้อผิดพลาดแยกพื้นที่ หากมีภาพอ้างอิงให้ทำ 2D overlay และตรวจความคลาดเคลื่อนตามจุด landmarks จากนั้นจึงเริ่ม retopology, UV0, PBR, GLB และ Three.js ตรวจด้วยภาพจริงจาก Blender/WebGL; ห้ามรับรองความสมจริงโดยไม่มีภาพและรายงานตรวจสอบ.

## Nose, eyes, and ear precision audit

Inspect the existing human-head scene under gray clay only. Identify the nasal root/sellion and nasal bone-to-cartilage transition; compare mid-dorsum/rhinion, pronasale, nasal ala, nostril openings in frontal, profile and subnasal renderings. Verify eye sockets and lids surrounding the globe; verify lateral/posterior position and relief of ear helix, antihelix, concha, tragus and lobule. Annotate `n,se,rh,prn,sn,en_l/r,ex_l/r,al_l/r,t_l/r,sa_l/r,sba_l/r`, validate measurement and image fit, and refuse PBR export until anatomical defects are corrected.
