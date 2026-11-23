# Fourteen Screenshot Study: Morphology, Variants and Preset Routing

This study is a direct visual inspection of all 14 supplied PNG screenshots. Each original was opened at full resolution; a contact sheet was used only to compare the set. The machine-readable companion is [`reference-catalog.json`](../assets/reference-catalog.json), which records original filenames, SHA-256 hashes, pixel dimensions, metadata, observations, uncertainties and qualitative parameters. Screenshots are not redistributed in the Skill.

## Provenance and evidence limits

The completed report **Thai Krathong 3D Builder — Deep Research Upgrade** is research provenance. Its document ID is `DeepResearchRecentReport_4c1e9a838c908191a4530d375d7ac631`; backing conversation `6b045683-f268-83ec-b4c7-4bb5b7e3705c`; report message `bcd23164-52b9-4fd5-bd6b-ff6fc858c693`. The report-linked original `skill.zip` was not available in the inspected runtime. These records are a **new direct integration** of the report and supplied screenshots, not a recovered copy of that archive.

This document establishes observed target morphology. It does **not** validate the report's earlier generated meshes, triangle counts, renders or package tests, and it supplies **no rendered similarity scores**. Current implementation and image-match checks must be run separately. A preset mapping selects a structural starting point; variant gaps below remain requirements until implemented and visually verified.

All references show one elevated perspective view. Use qualitative proportions and visible overlap cues; do not invent physical dimensions, hidden counts or backside geometry. Pixel sizes and PNG DPI identify the source image only. Material names describe the rendered appearance, with uncertain physical composition stated explicitly.

## Most consequential differences

- **White lotus centres differ.** R05 has a large smooth pale dome; R06 has an open nested cup and a slim unlit candle-like cylinder. Outer whorls are broad and nearly horizontal, while inner whorls stand upright.
- **Petal bowls need volume and lips.** R04 has broad thick rounded front lobes and pointed rear crests. R02 needs a cream-to-pink tip gradient and cupped petals. A thin pointed blade cannot reproduce either silhouette.
- **Banana-leaf designs are multiple subtypes.** R07 has low angular overlapping bands; R08 has rounded/clipped tabs; R09 is a shallow sawtooth border; R13 has a tall broad pointed crown. R01/R03 are brighter compact bowls, with R03 adding bead-like trim and a rolled front V.
- **R11 is noncircular throughout.** Its pointed-front heart/diamond-like deck, base and border must share the outline. **R12 has three raised decks**, not merely extra leaf rows on one deck.
- **R14 is bread slices.** Flat porous crumb faces, substantial crust sides and cylindrical centre pieces require different geometry/material regions from petals. **R10 is a continuous concave basin** with a rounded thick lip.

## Routing index

| ID | Original screenshot | Starting preset | Essential subtype / gap |
| --- | --- | --- | --- |
| R01 | `2026-11-23_214537.png` | `ref-banana-classic` | Compact lime-green folded-leaf bowl with unobstructed round deck |
| R02 | `2026-11-23_214555.png` | `ref-pink-lotus` | Pink-tip lotus-petal bowl on a green base |
| R03 | `2026-11-23_214613.png` | `ref-banana-classic` | Pale lime pointed-fold bowl with bead-like inner trim and rolled V band |
| R04 | `2026-11-23_214625.png` | `ref-orange-bowl` | Thick orange petal bowl with rounded rolled front lips |
| R05 | `2026-11-23_214638.png` | `ref-white-lotus` | Open white lotus with large smooth central dome |
| R06 | `2026-11-23_214701.png` | `ref-white-lotus` | Open white lotus with nested open centre and slim pale candle |
| R07 | `2026-11-23_215736.png` | `ref-banana-classic` | Dark-green angular multilayer wreath with broad leaf-covered deck |
| R08 | `2026-11-23_215754.png` | `ref-banana-classic` | Rounded/clipped folded-tab wreath with low scalloped edge |
| R09 | `2026-11-23_215807.png` | `ref-banana-classic` | Minimal low sawtooth leaf border with large flat deck |
| R10 | `2026-11-23_215820.png` | `ref-clay-bowl` | Plain terracotta-like shallow bowl with thick rounded lip |
| R11 | `2026-11-23_215833.png` | `ref-diamond-leaf` | Pointed-front heart/diamond-like leaf construction |
| R12 | `2026-11-23_215846.png` | `ref-tiered-leaf` | Three visibly stepped leaf-covered decks with pointed crowns |
| R13 | `2026-11-23_215901.png` | `ref-banana-classic` | Tall broad pointed leaf crown with lower folded band |
| R14 | `2026-11-23_215912.png` | `ref-bread-flower` | Radial bread-slice flower with cylindrical centre and small round slices |

## Lighting groups

**R01–R06:** Dark rippling water with orange reflections, strongest behind and to image right; the object is brightly and broadly lit. Surface colour includes this warm illumination and cannot be sampled as an intrinsic material value without correction.

**R07–R14:** Blue-to-charcoal background with soft pale bokeh; a warm vertical reflection appears below the object. Broad front/upper-left lighting and a candle flame accompany a directional accessory shadow toward image upper right. Match object lighting separately from background.

Match the object mask and camera before judging material colour. The warm water field and blue bokeh field are scene context, not part of the exported krathong geometry. For banana-leaf materials, central deck veins are predominantly parallel; grain must rotate with each folded panel rather than use one world-space direction everywhere.

## Per-image evidence

### R01 — Compact lime-green folded-leaf bowl with unobstructed round deck

**Source:** `2026-11-23_214537.png` · 645 × 556 px · recommended family `ref-banana-classic`.

**Mapping:** Family-level starting point; requires a compact low bowl variant, not the tall dark-green crown used by R13.

**Silhouette and layers:** Shallow circular body seen as an ellipse; many pointed crests make a dense compact perimeter. The front edge remains broad and low rather than forming long narrow spikes. At least two distinguishable staggered bands of folded green motifs are visible. Exact whole-ring count and hidden rear construction are not established.

**Petal/fold profile:** Width — Broad triangular/diamond-like faces relative to their visible height; pinched lower corners. Tip — Pointed angular peaks, with small bevels and slight surface rounding. Curl — Low transverse cupping and folded front side flaps; no large smooth spoon curl. Overlap — Staggered faces overlap side to side; a low front band crosses the taller inner crests, with V-shaped seams.

**Centre and base:** A large, nearly flat lime-green circular deck fills most of the opening. Faint radial seams converge near its centre; no central flowers or accessories are visible. A continuous low yellow-green cylindrical side band is exposed below the leaf folds; the underside is hidden.

**Materials and accessories:** Green and yellow-green waxy/satin appearance, with subtle mottling and radial surface traces on the centre; this is a rendered appearance, not proof of real banana-leaf construction. No candle, incense or flame is visible.

**Lighting:** Dark rippling water with orange reflections, strongest behind and to image right; the object is brightly and broadly lit. Surface colour includes this warm illumination and cannot be sampled as an intrinsic material value without correction.

**Qualitative target parameters:** footprint: circular; wall profile: low compact bowl; fold width: broad; fold rise: low to moderate; fold tip: pointed; fold curl: slight; layering: staggered overlapping bands; center mode: large flat green deck; palette: lime and yellow-green.

**Confidence:** family: high; silhouette: high; fold construction: medium; material identity: low; hidden geometry: low.

**Occluded / inferred:** A single elevated view hides the bottom, rear fastenings and exact fold thickness. Radial centre seams are visible; whether they represent separate leaf pieces or texture is uncertain.

**Required variant differences:** Preserve the large empty centre and compact wall height. Use broad folded facets and a continuous low base band; omit flowers and ceremonial accessories.

### R02 — Pink-tip lotus-petal bowl on a green base

**Source:** `2026-11-23_214555.png` · 635 × 563 px · recommended family `ref-pink-lotus`.

**Mapping:** Strong family match; needs a wide open deck and tall pointed bowl walls rather than an open flat blossom.

**Silhouette and layers:** Circular bowl with a wide opening and a jagged pointed rear crest. The lower front forms a broad overlapping scalloped band. Multiple nested petal bands are visible with increasing rise toward the inner/back crest. Perspective and occlusion prevent a reliable exact whole-ring count.

**Petal/fold profile:** Width — Broad tapered petals, widest through the middle and narrowing toward the point and attachment. Tip — Distinct pink/red pointed tips, some slightly hooked outward. Curl — Concave spoon-like transverse cup; front outer petals turn outward into a low lip. Overlap — Several staggered rows overlap strongly; inner petals rise above lower outer petals, leaving a wide unobstructed opening.

**Centre and base:** Large pale cream/yellow-pink flat circular deck with faint radial wedges. It is not a dense flower centre. Low green/yellow cylindrical band beneath the petal body; flat underside not shown.

**Materials and accessories:** Cream/yellow petal bases transition toward pink and red tips/edges; subtle surface texture, pale edge highlights and shadowed overlaps. Pink is a positional gradient, not a uniform material colour. No candle, incense or flame is visible.

**Lighting:** Dark rippling water with orange reflections, strongest behind and to image right; the object is brightly and broadly lit. Surface colour includes this warm illumination and cannot be sampled as an intrinsic material value without correction.

**Qualitative target parameters:** footprint: circular; wall profile: open petal bowl; petal width: broad; petal rise: moderate to high; tip: pointed; transverse cup: moderate; outer lip: outward; layering: nested staggered whorls; center mode: large flat pale deck; palette: cream bases to pink/red tips, green base.

**Confidence:** family: high; silhouette: high; petal profile: high; material identity: low; hidden geometry: low.

**Occluded / inferred:** Backside petal attachments and exact hidden petal counts are unknown. The image does not establish real thickness, dimensions or whether the material is natural petal, wax or a stylized substitute.

**Required variant differences:** Keep the pale exposed centre instead of filling it with stamens or marigolds. Model petal cupping, outward lower lip and pink tip gradient separately.

### R03 — Pale lime pointed-fold bowl with bead-like inner trim and rolled V band

**Source:** `2026-11-23_214613.png` · 617 × 568 px · recommended family `ref-banana-classic`.

**Mapping:** Partial family match only; the beaded trim and rolled lower band are distinct features that the ordinary banana preset may not contain.

**Silhouette and layers:** Compact circular bowl with a repetitive pointed crown. The front has a large descending V/chevron rather than a plain straight rim. A pointed outer crown and a lower decorative folded band surround one continuous inner ring of pale ovoid bead-like forms; exact trim count is not established.

**Petal/fold profile:** Width — Broad triangular folded panels; side flaps spread laterally. Tip — Sharp lime/yellow pointed peaks along the upper perimeter. Curl — Raised rounded/rolled strips follow the front chevron; leaf panels are faceted with mild cupping. Overlap — Upper pointed panels overlap; lower diagonal strips cross in a prominent front V. The pale bead-like trim overlays the inner rim.

**Centre and base:** Wide flat pale-yellow circular deck with visible radial wedges, bounded by rounded pale-yellow ovoids. These rounded forms should not automatically be labelled marigolds. Pale green wall continues to the bottom edge; no separate exposed stem band is clearly visible.

**Materials and accessories:** Bright pale yellow-green surfaces, smooth rounded trim and mild waxy highlights; the image does not identify the physical material of the beads or deck. No candle, incense or flame is visible.

**Lighting:** Dark rippling water with orange reflections, strongest behind and to image right; the object is brightly and broadly lit. Surface colour includes this warm illumination and cannot be sampled as an intrinsic material value without correction.

**Qualitative target parameters:** footprint: circular; wall profile: compact pointed bowl; fold width: broad; fold tip: pointed; lower band: rolled chevron/V; inner trim: continuous ovoid bead-like ring; center mode: flat pale-yellow deck; palette: pale lime and yellow.

**Confidence:** family: high; silhouette: high; decorative trim: high; material identity: low; hidden geometry: low.

**Occluded / inferred:** The back of the crossing lower strips and their fastening are occluded. Bead-like trim is visible, but its botanical or craft identity is unverified. Do not infer a full bead count or real-world size from this perspective.

**Required variant differences:** Add an inner ovoid trim ring and the front rolled V band as separate geometry. Use pale materials and a broad empty deck; a dark-green triangular wreath is insufficient.

### R04 — Thick orange petal bowl with rounded rolled front lips

**Source:** `2026-11-23_214625.png` · 614 × 543 px · recommended family `ref-orange-bowl`.

**Mapping:** Strong family match if broad lips and petal volume are retained.

**Silhouette and layers:** Low circular orange bowl with a broad flat centre; the rear has pointed overlapping peaks while the front has rounded thick scalloped lobes. Multiple staggered petal rows are visible; the exact hidden whole-ring counts are uncertain.

**Petal/fold profile:** Width — Wide substantial petals/lobes with visible volume, not thin strips. Tip — Rear crests are pointed; front outer lobes have rounded tops and broad corners. Curl — Pronounced inward/outward lip rounding at the front, with thick amber-highlighted rims and recessed cupped middles. Overlap — Staggered petal layers wrap the wall; front rounded lobes overlap a taller inner row and a narrow continuous base band.

**Centre and base:** Large nearly flat orange disk with mottled texture and faint radial divisions; no floral cluster occupies the opening. Low continuous orange side band under the petal lobes.

**Materials and accessories:** Saturated orange/yellow with darker amber/toasted-looking lip edges and mottled centre. The wax-, cake- or bread-like impression is ambiguous; do not assert composition from colour alone. No candle, incense or flame is visible.

**Lighting:** Dark rippling water with orange reflections, strongest behind and to image right; the object is brightly and broadly lit. Surface colour includes this warm illumination and cannot be sampled as an intrinsic material value without correction.

**Qualitative target parameters:** footprint: circular; wall profile: thick lobed bowl; petal width: very broad; lip thickness: visually substantial; front tip: rounded; rear tip: pointed; curl: strong rolled lip; center mode: flat mottled orange deck; palette: orange with amber rims.

**Confidence:** family: high; silhouette: high; lip profile: high; material identity: low; hidden geometry: low.

**Occluded / inferred:** Only the elevated front view is available; lip cross-sections and underside thickness require further views. Exact whole-ring petal counts and physical material remain unknown.

**Required variant differences:** Make front lips rounded and thick, with differentiated inner and outer surfaces. Preserve the orange central disk and avoid narrow lotus blades or flower clusters.

### R05 — Open white lotus with large smooth central dome

**Source:** `2026-11-23_214638.png` · 482 × 451 px · recommended family `ref-white-lotus`.

**Mapping:** Same family as R06 but requires a different centre; do not merge the two subtypes.

**Silhouette and layers:** Open radial blossom with broad near-horizontal outer petals and a taller nested inner cup; no obvious cylindrical base is exposed. Several visible whorls change pitch from low outer petals to upright inner petals. Exact hidden whorl and petal counts are not recoverable.

**Petal/fold profile:** Width — Broad spoon-shaped petals, pinched near attachment and fuller toward the distal half. Tip — Mostly tapered rounded points, with small notches or hooks on some visible edges. Curl — Transverse cupping, raised pale rims and curled/notched tips; outer petals spread flat while inner petals stand upright. Overlap — Nested offset whorls overlap; outer petals remain individually readable around the full visible contour.

**Centre and base:** A large smooth pale rounded dome/volume protrudes within the inner cup. Its lower attachment is hidden. It must not be replaced silently by a small flower core or candle. Petals conceal the underside and attachment; no separate base shape can be verified.

**Materials and accessories:** Ivory-white surface, soft cream shading, pale edge highlights and weak fine texture. Rendering may suggest soft or waxy petals but does not prove a physical material. No candle, incense or flame is visible; the centre is the smooth pale volume.

**Lighting:** Dark rippling water with orange reflections, strongest behind and to image right; the object is brightly and broadly lit. Surface colour includes this warm illumination and cannot be sampled as an intrinsic material value without correction.

**Qualitative target parameters:** footprint: open radial blossom; outer petals: broad low spoons; inner petals: upright nested cup; tip: soft tapered, occasionally notched; edge curl: visible; center mode: large smooth dome; base visibility: hidden; palette: ivory.

**Confidence:** family: high; silhouette: high; center presence: high; center identity: low; hidden geometry: low.

**Occluded / inferred:** The identity and full geometry of the central dome are unverified. The bottom and rear petal attachments are hidden. Lighting and screenshot scale differ from R06, so direct pixel dimensions are not object dimensions.

**Required variant differences:** Add an explicit dome centre option while retaining the broad outer whorls. Do not enable the R06 candle or assume the dome is a real lotus seedpod.

### R06 — Open white lotus with nested open centre and slim pale candle

**Source:** `2026-11-23_214701.png` · 408 × 379 px · recommended family `ref-white-lotus`.

**Mapping:** Strong family match; default centre must stay open around the slim candle, unlike R05.

**Silhouette and layers:** Wide white lotus with nearly horizontal outer petals, an upright rear crown and a visibly open nested inner cup. Several nested whorls vary in radius, rise and pitch independently. Exact hidden counts are not established.

**Petal/fold profile:** Width — Broad outer spoons and progressively smaller inner petals, with narrow attachments. Tip — Tapered soft points; some curled or notched edge details. Curl — Clear transverse cup and lifted margins, with the outer front petal almost horizontal and curling upward at its rim. Overlap — Offset nested whorls reveal small inner petals around the accessory; outer petal gaps remain visible.

**Centre and base:** An open small petal cup surrounds one visible slender pale vertical candle-like cylinder. There is no large smooth dome. No exposed cylindrical stem band; attachment and underside are hidden by petals.

**Materials and accessories:** Ivory-white petals with cream highlights and soft grey-green shaded folds; the slim centre cylinder is pale yellow/cream. One slender pale candle-like cylinder is visible. No flame or incense is visible.

**Lighting:** Dark rippling water with orange reflections, strongest behind and to image right; the object is brightly and broadly lit. Surface colour includes this warm illumination and cannot be sampled as an intrinsic material value without correction.

**Qualitative target parameters:** footprint: open radial blossom; outer petals: broad low spoons; inner petals: small open cup; edge curl: visible; center mode: open with slim unlit candle; palette: ivory with pale cream centre accessory.

**Confidence:** family: high; silhouette: high; center openness: high; accessory identity: medium; hidden geometry: low.

**Occluded / inferred:** The small pale cylinder is visually consistent with a candle; wick detail is not clear enough to establish more. Hidden attachments, exact counts and real dimensions remain unknown.

**Required variant differences:** Select open/candle centre instead of the R05 dome. Keep independent whorl pitch and the broad front outer petal.

### R07 — Dark-green angular multilayer wreath with broad leaf-covered deck

**Source:** `2026-11-23_215736.png` · 805 × 563 px · recommended family `ref-banana-classic`.

**Mapping:** Strong banana family match; requires several low overlapping perimeter bands rather than a flower-filled centre.

**Silhouette and layers:** Wide circular disk with a strongly jagged leaf contour and multiple low staggered angular bands visible at the front. Multiple low concentric perimeter bands surround one broad continuous central deck. The screenshot does not show three separately elevated interior decks.

**Petal/fold profile:** Width — Broad triangular/diamond folded panels; large side flaps. Tip — Sharp angular points with central facet ridges. Curl — Mostly planar folded facets, not smooth blade curvature; slight bends at overlaps. Overlap — Several perimeter bands overlap with dark gaps. Small brown fastening-like marks are visible at some front seams.

**Centre and base:** Large near-flat green leaf-covered deck with long parallel veins, unobstructed apart from the central candle/incense. Pale porous-looking cylindrical band exposed below the dark green folds; material identity is unconfirmed.

**Materials and accessories:** Dark/medium green directional leaf veins; grain rotates with different folded panels. Deep seam shadows separate bands; base is pale cream with irregular yellow-brown flecks. One visible lit white candle and three visible incense sticks stand together near the centre.

**Lighting:** Blue-to-charcoal background with soft pale bokeh; a warm vertical reflection appears below the object. Broad front/upper-left lighting and a candle flame accompany a directional accessory shadow toward image upper right. Match object lighting separately from background.

**Qualitative target parameters:** footprint: circular; rim profile: multi-band angular wreath; fold width: broad; fold tip: sharp; fold construction: planar facets with ridge and flaps; center mode: large flat leaf deck; base band: exposed pale flecked; palette: dark green.

**Confidence:** family: high; silhouette: high; fold facets: high; material identity: medium; hidden geometry: low.

**Occluded / inferred:** Small brown marks resemble fasteners, but their exact type and hidden arrangement cannot be determined. The visible pale base cannot be positively identified as banana stem from this render. Exact hidden leaf counts are not established.

**Required variant differences:** Keep the deck open and use a few broad faceted overlapping bands. Preserve rotated leaf grain and dark inter-layer seams; do not add flowers.

### R08 — Rounded/clipped folded-tab wreath with low scalloped edge

**Source:** `2026-11-23_215754.png` · 716 × 556 px · recommended family `ref-banana-classic`.

**Mapping:** Family-level only; the pointed-leaf classic preset needs a rounded/clipped-tab variant.

**Silhouette and layers:** Circular broad deck with a soft scalloped perimeter; the rear contour is formed by broad rounded or clipped polygonal tabs rather than tall points. Low concentric rim bands around a single dominant central deck. Precise full ring counts are not proven.

**Petal/fold profile:** Width — Wide short tabs with broad shoulders. Tip — Rounded or clipped/faceted ends; not spear points. Curl — Bent planar faces with mild rounding; little long longitudinal curl. Overlap — Low overlapping edge bands create a dark ring at the front; outer tabs are offset relative to inner tabs.

**Centre and base:** Nearly flat green circular deck with long parallel veins and a clear open area around the candle. Visible pale cream flecked circular band beneath green trim.

**Materials and accessories:** Directional dark-green leaf texture with medium-green ridges; lower overlaps are almost black in shade. The base has pale porous/flecked appearance. One visible lit white candle and three visible incense sticks.

**Lighting:** Blue-to-charcoal background with soft pale bokeh; a warm vertical reflection appears below the object. Broad front/upper-left lighting and a candle flame accompany a directional accessory shadow toward image upper right. Match object lighting separately from background.

**Qualitative target parameters:** footprint: circular; rim profile: low scalloped tabs; fold width: wide short; tip: rounded/clipped; fold rise: low; center mode: large flat leaf deck; palette: dark green.

**Confidence:** family: high; silhouette: high; tab tip profile: high; material identity: medium; hidden geometry: low.

**Occluded / inferred:** Backside tab profiles and exact fold thickness are hidden. The screenshot cannot establish total tab counts or substrate composition.

**Required variant differences:** Replace sharp triangular tips with broad rounded/clipped ends. Keep the rim low, the centre large and the exposed base band visible.

### R09 — Minimal low sawtooth leaf border with large flat deck

**Source:** `2026-11-23_215807.png` · 708 × 533 px · recommended family `ref-banana-classic`.

**Mapping:** Family-level only; requires a shallow single-border treatment rather than a tall or multi-tier crown.

**Silhouette and layers:** Flat circular platter-like body with short outward triangular points around the rim. The central deck occupies most of the visible object. A single main low border is apparent around one broad continuous deck; do not invent extra raised tiers.

**Petal/fold profile:** Width — Broad shallow triangular folded pieces; limited visible height. Tip — Short sharp sawtooth points directed outward. Curl — Minimal visible curl; mainly folded planar facets. Overlap — One dominant low sawtooth perimeter band; any additional bands are hidden or cannot be separated confidently.

**Centre and base:** Very large near-flat green leaf-covered deck with long parallel veins and no flowers. Prominent pale cream flecked cylindrical band under the shallow green top.

**Materials and accessories:** Parallel green leaf grain on the deck; grain turns across the small outer facets. Pale base has irregular pores/flecks. One visible lit white candle and three visible incense sticks.

**Lighting:** Blue-to-charcoal background with soft pale bokeh; a warm vertical reflection appears below the object. Broad front/upper-left lighting and a candle flame accompany a directional accessory shadow toward image upper right. Match object lighting separately from background.

**Qualitative target parameters:** footprint: circular; rim profile: low sawtooth; fold width: broad shallow; fold rise: minimal; layering: one dominant visible border; center mode: very large flat leaf deck; base band: prominent pale flecked.

**Confidence:** family: high; silhouette: high; low profile: high; material identity: medium; hidden geometry: low.

**Occluded / inferred:** Hidden rim layers and exact leaf counts are unknown. Deck curvature appears slight, but one perspective cannot prove perfect planarity.

**Required variant differences:** Reduce wall and fold height substantially relative to R13. Keep one dominant low border and a wide uncluttered deck.

### R10 — Plain terracotta-like shallow bowl with thick rounded lip

**Source:** `2026-11-23_215820.png` · 736 × 544 px · recommended family `ref-clay-bowl`.

**Mapping:** Strong family match; the bowl must be genuinely concave with a continuous inner wall and thick lip.

**Silhouette and layers:** Round broad shallow basin with smooth elliptical rim, thick rounded lip and a continuous curved outer side wall; no petal points. One continuous bowl wall around a concave interior; no concentric leaf or flower rings.

**Petal/fold profile:** Width — No petals or leaf folds. Tip — Continuous rounded rim, no tips. Curl — Smooth inward basin curvature and rounded lip cross-section. Overlap — None; the basin is visually continuous.

**Centre and base:** Reddish-brown interior slopes smoothly toward the lower central floor, occupied only by the candle/incense. It must not be modeled as a raised flat disk covering the opening. Dark brown exterior wall; bottom and foot are occluded.

**Materials and accessories:** Terracotta-like matte reddish-brown surface with small dark speckles, a lighter warm rim and a much darker outer side. Material appearance is strong evidence, but actual physical clay is not verified. One visible lit white candle and three visible incense sticks.

**Lighting:** Blue-to-charcoal background with soft pale bokeh; a warm vertical reflection appears below the object. Broad front/upper-left lighting and a candle flame accompany a directional accessory shadow toward image upper right. Match object lighting separately from background.

**Qualitative target parameters:** footprint: circular; body: continuous concave basin; rim: thick rounded; wall: smooth curved; center mode: concave clay interior; palette: warm reddish brown, lighter rim, dark exterior.

**Confidence:** family: high; silhouette: high; concavity: high; material identity: medium; hidden geometry: low.

**Occluded / inferred:** The underside, foot shape and physical wall thickness are not observable. Absolute bowl depth and scale cannot be recovered reliably from this single view.

**Required variant differences:** Use a concave bowl mesh with distinct inner wall, rounded lip and outer side. Add restrained speckle variation; do not attach petals or a green base band.

### R11 — Pointed-front heart/diamond-like leaf construction

**Source:** `2026-11-23_215833.png` · 774 × 573 px · recommended family `ref-diamond-leaf`.

**Mapping:** Strong noncircular family match; the deck, border and base all need the same bilateral outline.

**Silhouette and layers:** Bilaterally symmetric heart/diamond-like planform with a pronounced sharp front apex and broad left/right shoulders. It is not a circular krathong seen in perspective. Nested noncircular outline bands surround a matching pointed-front central deck. Rear contour is partly obscured by crests and the central accessories.

**Petal/fold profile:** Width — Broad faceted pointed leaves along the sides; folded bands converge at the front point. Tip — Sharp outward tips and a very distinct long front apex. Curl — Angular ridges and panel bends, with little smooth spoon curvature. Overlap — Several perimeter bands follow the noncircular contour and overlap in a nested V at the front. Small brown fastening-like marks occur at seams.

**Centre and base:** Broad green vein-textured deck with a pointed front and rounded shoulders; it must share the perimeter shape rather than remain a circular disk. Pale flecked base follows the same pointed-front outline, exposed along both sides and at the apex.

**Materials and accessories:** Directional green grain, dark facet overlaps and pale flecked substrate; grain and folds follow local panel orientation. One visible lit white candle and three visible incense sticks.

**Lighting:** Blue-to-charcoal background with soft pale bokeh; a warm vertical reflection appears below the object. Broad front/upper-left lighting and a candle flame accompany a directional accessory shadow toward image upper right. Match object lighting separately from background.

**Qualitative target parameters:** footprint: bilateral heart/diamond-like; front: sharp elongated apex; shoulders: broad; rim: nested faceted V bands; center mode: matching noncircular leaf deck; base shape: same pointed outline.

**Confidence:** family: high; noncircular footprint: high; exact rear outline: medium; material identity: medium; hidden geometry: low.

**Occluded / inferred:** The exact top-view outline, especially any rear cleft, is partly occluded. Heart versus diamond is a descriptive subtype, not a claimed traditional craft name. Hidden fold counts and underside construction are not established.

**Required variant differences:** Apply the noncircular outline to centre, base and every perimeter band. Preserve the front V/apex and bilateral symmetry; do not approximate with circular rings.

### R12 — Three visibly stepped leaf-covered decks with pointed crowns

**Source:** `2026-11-23_215846.png` · 806 × 634 px · recommended family `ref-tiered-leaf`.

**Mapping:** Strong tiered family match; requires discrete raised decks, not simply extra leaf rows on one deck.

**Silhouette and layers:** Tall stepped radial composition with three visible levels: broad lower platform, smaller elevated middle platform and compact upper platform. Three distinct elevated leaf-covered decks are visibly separated in height and radius, each with its own pointed border. Rear leaf overlaps obscure exact per-tier counts.

**Petal/fold profile:** Width — Broad triangular folded panels on each tier; large outer leaves spread diagonally. Tip — Sharp tall points with strong centre ridges. Curl — Mostly faceted bends; tier borders curl upward around each deck but individual panels are angular. Overlap — Each tier has its own overlapping crown/border; lower tiers remain visible as broad annular decks. Brown fastening-like marks punctuate some seams.

**Centre and base:** Small top circular leaf deck carries the candle; broad middle and lower annuli are exposed around it. Pale flecked circular substrate visible beneath the broad bottom tier.

**Materials and accessories:** Directional green veins across each deck, rotated grain on folded leaves, dark seams and pale substrate. Tier separation produces substantial occlusion shadows. One visible lit white candle and three visible incense sticks on the upper deck.

**Lighting:** Blue-to-charcoal background with soft pale bokeh; a warm vertical reflection appears below the object. Broad front/upper-left lighting and a candle flame accompany a directional accessory shadow toward image upper right. Match object lighting separately from background.

**Qualitative target parameters:** footprint: concentric circular; visible tiers: 3; tier radius: decreases upward; tier elevation: discrete raised steps; fold width: broad; fold tip: sharp; center mode: small upper deck plus exposed lower annuli.

**Confidence:** family: high; visible tier count: high; fold facets: high; material identity: medium; hidden geometry: low.

**Occluded / inferred:** Exact heights, radius ratios and hidden support volumes are not established. Per-tier leaf counts and hidden rear overlaps are unknown.

**Required variant differences:** Create three separate raised deck surfaces with decreasing radii. Place candle/incense on the top deck and keep lower annular areas visible.

### R13 — Tall broad pointed leaf crown with lower folded band

**Source:** `2026-11-23_215901.png` · 820 × 637 px · recommended family `ref-banana-classic`.

**Mapping:** Strong banana classic match for a tall-crown variant; not interchangeable with the low rims in R08/R09.

**Silhouette and layers:** Circular bowl-like wreath with a tall broad pointed rear crown and outward-spreading lower perimeter leaves; the centre remains open. One dominant tall crown plus a lower overlapping perimeter band; this is not the three raised deck architecture of R12.

**Petal/fold profile:** Width — Wide triangular panels with broad bases and prominent central ridges. Tip — Tall sharp tapered points, visibly much higher than R09. Curl — Angular folded facets with a slightly cupped V section; no thin continuous blade strips. Overlap — Tall pointed panels overlap around the central deck; a lower staggered band crosses the front, with visible dark seams and brown fastening-like marks.

**Centre and base:** Broad near-flat circular green deck with parallel leaf veins and a clear area around the candle. Pale cream flecked circular band exposed beneath the folded border.

**Materials and accessories:** Dark-green leaf grain follows each panel; overlap shadows are deep and front fold edges catch lighter green highlights. One visible lit white candle and three visible incense sticks.

**Lighting:** Blue-to-charcoal background with soft pale bokeh; a warm vertical reflection appears below the object. Broad front/upper-left lighting and a candle flame accompany a directional accessory shadow toward image upper right. Match object lighting separately from background.

**Qualitative target parameters:** footprint: circular; rim profile: tall pointed crown; fold width: broad; fold rise: high; fold tip: sharp; layering: tall crown plus lower band; center mode: large flat leaf deck.

**Confidence:** family: high; silhouette: high; tall crown: high; material identity: medium; hidden geometry: low.

**Occluded / inferred:** Rear fold attachments and exact crown counts are occluded. The apparent leaf thickness and physical substrate material are not measurable.

**Required variant differences:** Use broad, high triangular folded panels with readable ridges and flaps. Preserve a single main deck and lower overlap band; do not turn it into a stepped tower.

### R14 — Radial bread-slice flower with cylindrical centre and small round slices

**Source:** `2026-11-23_215912.png` · 733 × 578 px · recommended family `ref-bread-flower`.

**Mapping:** Strong bread family match if flat crumb faces and crust thickness are modeled distinctly.

**Silhouette and layers:** Open radial flower made from eight clearly visible broad elongated oval bread slices. Rounded petal tips and gaps produce a lobed contour, without a surrounding bowl wall. Eight visible outer slices in one radial ring. Seven smaller round slice tops are clearly visible around the main central cylinder; the rear is occluded, so seven is a visible count rather than a total-count claim.

**Petal/fold profile:** Width — Very broad flat elongated oval slices with narrower inner attachments. Tip — Rounded bread-slice ends; no sharp leaf points. Curl — Little to no visible petal cup; pieces resemble thick planar cut slices. Overlap — Outer slices converge around the centre and slightly overlap near their roots; small cylindrical pieces are arranged around a larger central cylinder.

**Centre and base:** Large upright bread-like cylindrical pedestal supports the candle. A surrounding ring of shorter cylinders has pale circular cut faces and browned rims. An orange/brown underlying support is partly visible between front slice roots; complete underside is hidden.

**Materials and accessories:** Cream/yellow porous crumb on broad top faces, toasted brown crust around slice edges and vertical sides, and fine vertical banding on cylinders. Crumb and crust need distinct material regions. One visible lit white candle and three visible incense sticks stand on the central pedestal.

**Lighting:** Blue-to-charcoal background with soft pale bokeh; a warm vertical reflection appears below the object. Broad front/upper-left lighting and a candle flame accompany a directional accessory shadow toward image upper right. Match object lighting separately from background.

**Qualitative target parameters:** footprint: eight-lobed radial slices; outer slices visible: 8; outer slice profile: flat thick elongated oval; center mode: large cylindrical pedestal; small round tops visible: 7; small round total: unknown due to occlusion; material regions: porous pale cut face and brown crust sides.

**Confidence:** family: high; outer visible count: high; bread appearance: high; small piece total: low; hidden geometry: low.

**Occluded / inferred:** A rear small cylinder may be hidden by the central pedestal/candle; do not set total small-piece count solely from the seven visible tops. The hidden supporting base and underside are not established. Rendered bread appearance does not verify recipe, physical buoyancy or actual material dimensions.

**Required variant differences:** Use thick flat oval slices rather than cupped lotus petals. Separate crumb top faces from crust sidewalls, and include central and small cylindrical forms.

## How to use the study

1. Select the exact screenshot ID, then choose its recommended family. Record the listed subtype and missing features before generation.
2. Match the footprint, exposed centre, layer architecture and petal/fold silhouette first. Keep centre options explicit, especially R05 versus R06 and R09 versus R13.
3. Render an elevated comparison view with similar camera framing; request or obtain top/side evidence when hidden structure matters. Keep all inferred geometry labelled.
4. Run numerical geometry QA, then separately review the camera-aligned silhouette, overlap, material regions and accessories. Record current results in new output reports. Do not copy prior research claims or introduce a similarity percentage without its measured method and limitations.
5. Update the catalog only with evidence that was actually observed or measured. Do not convert a qualitative target into a claimed real-world dimension.
