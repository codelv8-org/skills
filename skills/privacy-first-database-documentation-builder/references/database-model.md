# Canonical model and document rules

Use `assets/metadata-template.json` as the model. Keep each table/view identified by `schema.name` and columns by table + column. Preserve order. `source_id` is an opaque safe evidence label, not a server URI. `null` means unverified/unknown (not false), and unknown descriptions should explicitly say `ยังไม่ยืนยัน`. Distinguish storage type from business format and units. Use the owner's reviewed domain definitions; names alone do not prove semantics. Avoid invented example values for any person-linked field.

## Data Catalog

One row per object: stable ID, domain, schema, table/view, approved purpose, grain (if verified), owner role, classification, verification status, source ID, dictionary link. Indicate source/refresh date only if verified; do not infer frequency, freshness, size, number of rows, usage statistics or data lineage. Structural counts are fine. Add discovery index by domain. Table classifications should be at least as restrictive as their fields; Unknown is effective Restricted; use the maximum effective field classification.

## Data Dictionary

For each object: purpose, PK, known relationships, classification and scope. For each column: ordinal, exact name, data type, size/precision/scale, nullable, PK/unique/FK memberships (including composite order), approved definition, format/unit, validation rule description, classification, evidence/verification. Use `Unknown` or `null` when evidence is absent; classification defaults to Restricted. Omit all defaults, enumerations and raw expressions. Definitions come only from the separately reviewed definitions array. Treat pseudonymous HN/AN and linked medical attributes as Restricted. Do not label keys unique unless the relevant key or constraint is verified. Do not infer 1:1 from an FK without uniqueness evidence; FK existence is not proof of every row having a target if nullable or constraints disabled/unknown.

## ER diagram

Use only explicit approved FK column mappings (including ordered composite keys). Include PK/UK/FK labels, nullable when verified, table aliases safe for Mermaid and a mapping to exact IDs. Prefer a neutral edge/label if exact cardinality or enforcement is unknown. A verified FK generally constrains source to target with uniqueness/nullability determining cardinality; do not assert participation minimum on reverse side. Separate proposed conceptual diagrams from verified physical ERDs. Do not infer from matching names. Exclude out-of-scope targets rather than invent nodes. Split by domain for readability.

## Classification and agent guidance

Record per-field classification, reason category, allowed metadata disclosure, required approval (only if known), restrictions and unknowns. Default deny actual data access. Do not represent suggested safeguards as existing controls. Explain approved keys, grains, relationships, time semantics and units for an AI agent, plus where to find definitions. Include instructions: use metadata for reasoning only; do not query records or invent SQL results; access to data requires separate authorization and tooling outside this skill. Never include actual record samples, computed counts or identifiers.

## Lineage and schema diff
Only directed owner-approved mappings in the lineage array are evidence. No mapping means unknown, not absence of lineage. Compare independently reviewed snapshots with the same scope, engine, system and audience; describe additions/removals as snapshot differences, not verified deployment or DDL operations. Do not infer renames or breaking compatibility without evidence.
