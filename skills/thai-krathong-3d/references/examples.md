# Example Thai Workflows

**Prompt A — default ceremonial krathong**

> ปั้นกระทง 3D ใบตองพับสองชั้น ดอกดาวเรืองสีส้ม ดอกบานไม่รู้โรยสีม่วง พร้อมธูป 3 ดอกและเทียน 1 เล่ม ส่งออก GLB ไปใช้กับ Three.js

Use `assets/traditional.json` → generate complete → run QA → render three views → deliver GLB, PNG and metadata. Preserve leaf-ring nodes for further editing.

**Prompt B — pink lotus**

> สร้างกระทงดอกบัวสีชมพู โทนสมจริง หน้าตาเหมือนกระทงประดิษฐ์ด้วยมือ มีเทียนจุดไฟ

Use `assets/lotus.json` to block out the layered lotus. For photorealism, inspect petals and hand-refine their cupping in Blender. Emissive flame alone does not light the scene.

**Prompt C — user reference**

> สร้างกระทง 3D จากภาพนี้ให้ใกล้เคียงที่สุด ทำทีละส่วนและเช็คกับต้นฉบับก่อนขั้นต่อไป

First create `reference_analysis.json` of evidenced geometry, then pass base → banana folds → flowers → candle/incense → finish gates. Compare same views, document each mismatch; do not claim photo match from a procedural seed alone.

**Prompt D — web simulation**

> สร้างกระทง Low Poly พร้อมแอนิเมชันลอยน้ำบน Three.js และปรับ texture ให้เป็น matte

Use `assets/stylized.json`, GLB QA and `references/web-integration.md`. Implement bobbing animation in the **website runtime**. The GLB does not contain real buoyancy/physics.

**Parameter changes:** Copy a preset JSON and change `diameter_m`, `flower_style` (`marigold`, `lotus`, `mixed`, `none`), `flower_count`, `amaranth_count`, `outer_leaf_count`, `inner_leaf_count`, `candle`, `candle_lit`, `incense_count`, `quality` (`low`, `medium`, `high`) or `seed`. Colors are controlled in `scripts/generate_krathong.py` `PALETTE` until a palette override is implemented.
