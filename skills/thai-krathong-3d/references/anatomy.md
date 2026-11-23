# Thai Krathong Anatomy and Silhouette Guide

## Component hierarchy

| Part | What the model must communicate | Common failure |
| --- | --- | --- |
| 01 Banana-stem slice (ฐานหยวกกล้วย) | Shallow round floating base, slightly organic perimeter; exposed cut stem only if the reference shows it | A tall solid pot or bowl shape |
| 01 Banana-leaf wrap (ใบตองหุ้มฐาน) | Wide long green strips, overlapping horizontal seam, often leaf cover over upper base | Floating petals unattached to base |
| 02 Folded banana-leaf ring (กลีบใบตองพับ) | Repeated folded green motifs along rim; visibly angular/V or pointed geometry and 2–3 staggered concentric layers where present | One smooth flower-shaped torus or uniformly thin spikes |
| 03 Marigolds (ดอกดาวเรือง) | Dense ruffled golden-orange spherical flower heads with many small florets | Smooth pumpkin-like or golf-ball spheres |
| 03 Globe amaranth (ดอกบานไม่รู้โรย) | Small purple pom-pom heads; granular surface | Larger purple marigolds that dominate the arrangement |
| 03 Lotus flower (ดอกบัว) | Layered tapered petals, cupped curvature, pale to vivid pink gradients; distinct center | Equilateral triangles instead of petals |
| 04 Candle (เทียน) | One slender vertical wax cylinder, often centered or just off-center | Oversized central pillar |
| 04 Incense (ธูป) | Usually three slender sticks in a small nearby cluster (unless user/reference specifies otherwise) | Thick rods that look like wooden posts |

## Dimensions and layout (starter estimates, not ceremonial rules)

- Default base diameter 0.26 m; acceptable personalization parameter 0.12–0.50 m.
- Base thickness ~0.04 m (15% of diameter).
- Leaf tips typically reach ~0.11–0.13 m above bottom in the bundled presets.
- Flower heads cluster inside the leaf ring, centered around ~0.065 m above bottom in the bundled presets.
- Incense tips may reach ~0.22 m above bottom; candle is deliberately shorter.
- Keep the centroid and footprint approximately circular. Ring counts and density are reference-dependent.

## Modeling techniques

**Banana leaf folds:** create a thin, two-sided ribbed mesh from crease profiles. Add thickness to avoid fragile one-sided rendering. Use varied dark/medium/light greens to make layers readable. A perfectly regular array looks synthetic; slight deterministic variations in height/width improve handcrafted appearance. Do not exaggerate noise when matching an orderly ceremonial pattern.

**Banana-stem material:** pale green cut plant fibers are distinct from the darker waxy leaf wrapping. Use high roughness and no metallic sheen. Banana-leaf surfaces can show longitudinal shading rather than isotropic marble noise.

**Marigolds:** represent many rounded-to-ruffled florets around a dense center. Increase petal density for high-detail assets but keep the whole head's silhouette rounded rather than spiky; for photo-realism, replace polygon flakes with Blender-curved petals / PBR alpha details.

**Lotus:** use overlapping rows with rounded/tapered petal silhouettes and inward cup. Real petals should not be straight planar triangles; use curvature and a nuanced pink gradient.

**Accessories:** present incense and candle as separate nodes, with sufficient physical clearance from blooms. Flames are stylized emissive decorative meshes; actual lighting/shadows must be implemented in the renderer.

## Cultural reference context

- Thailand Foundation, *Loy Krathong Festival – All You Need to Know*: https://thailandfoundation.or.th/loy-krathong-festival-all-you-need-to-know-v2/
- Thai government overview, *How Loy Krathong Is Celebrated*: https://www.thailand.go.th/useful-information-detail/how-loy-krathong-is-celebrated
- DLTV educational material: https://dltv.ac.th/utils/files/download/174876

Treat photography and cultural images as references to observe, not assets to copy into distributable materials without permission.
