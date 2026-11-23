# Photo-Reference Analysis and Part-by-Part Quality Gates

Use this protocol whenever the user supplies an image or asks to match a picture. Image similarity can only be asserted after inspecting actual comparison renders. Do **not** manufacture confidence values or measured similarity scores.

## A. Analyze before building

1. **Inventory views:** list images, distinguish top/side/front/3-quarter views, note occlusions and perspective. Select the designated primary reference.
2. **Annotate visible assemblies:** diameter, thickness, leaf rings, count of visible leaves, floral types, approximate head counts, candle/incense quantity and placement, central negative space, motifs.
3. **Normalize ratios:** use base diameter as `D=1`. Record layer height/D, leaf-tip radius/D, flower radius/D, accessory height/D. Use approximate values and mark uncertainty due to perspective.
4. **Separate evidence:** `observed` vs `inferred` vs `unknown`. Never treat an occluded backside as verified.
5. **Capture visual direction:** photorealistic, stylized clay, low-poly, handcrafted realism; green/yellow/purple balance, roughness, edge translucency, symmetry.
6. **Create a reference plan:** compare real vs generated same views after each stage. Record no-reference defaults explicitly.

### Suggested reference_analysis.json

```json
{
  "primary_reference": "example_top_view.jpg",
  "views": ["three-quarter", "top"],
  "target_style": "handcrafted stylized PBR",
  "observed": {
    "base_shape": "shallow round disc",
    "folded_leaf_rings": 2,
    "visible_outer_leaves": 18,
    "flowers": ["marigold", "globe amaranth"],
    "candle_count": 1,
    "incense_count": 3
  },
  "inferred": {"unseen_back_leaf_pattern": "same staggered pattern"},
  "unknown": ["underside construction", "exact real-world diameter"],
  "top_priorities": ["leaf-fold silhouette", "flower placement", "rim height"]
}
```

**Important:** The values shown above are examples, not observations of the user's actual photo.

## B. Test each stage separately

| Gate | Compare | Fail examples | Next action |
| --- | --- | --- | --- |
| G1 Base | Top circularity, thickness, edge bands | Too thick/rectangular | Correct diameter and sleeve before continuing |
| G2 Banana leaves | Side silhouette, ring layers, count and overlap | Spikes, missing stagger, wrong petal curvature | Sculpt ring profile/reduce or increase angular folds |
| G3 Flowers | Color mass, head size/shape, negative space | Flower arrangement too sparse or dense | Shift flowers/add head geometry; keep accessories clear |
| G4 Candle/incense | Number, orientation, spacing and relative height | Candle collides with lotus or incense too thick | Adjust location, length and stem diameter |
| G5 Finish | Material light response, shading, triangle counts, scale | Plastic leaf gloss, dark inverted normals | Fix normals, roughness, budget and re-render |

Give each dimension a **human/vision assessment** from 0–5, with evidence from the actual comparison. Weights if a single decision score is needed: silhouette 25%, leaf morphology 25%, floral composition 20%, relative proportions 15%, palette/materials 10%, accessories 5%. A score is a review heuristic only, not a calibrated statistical similarity measure. Require 4/5 minimum for silhouette and leaf morphology; recommend overall 4.2/5 before approving photo-matched delivery. Otherwise revise the lowest-scoring shape-critical part.

## C. Repeatable comparison renders

- Keep camera view, subject scale and light direction as stable as possible.
- Render top view for radial placement, front for relative heights, and isometric for craft quality.
- Put side-by-side images on the same approximate crop. Overlay silhouettes only if geometry and perspective are aligned.
- Run automatic GLB QA separately; passing triangle/mesh QA does not imply photo fidelity.
- Record a concise change log: `part → mismatch → intended fix → new evidence`.

## D. When the reference cannot be matched faithfully

Explain the limitation clearly (hidden geometry, insufficient resolution, simplified procedural flower construction, unavailable Blender), deliver best verified result and list specific parts needing hand sculpting. Do not claim 100% identical to a photo or a high numerical likeness absent an actual measurement method.
