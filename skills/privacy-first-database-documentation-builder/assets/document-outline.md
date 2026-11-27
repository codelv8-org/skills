# Output outlines (Thai by default)

Every document begins with system/version/audience/classification/scope/status and approved evidence IDs. Adapt headings, not required content. Use only verified safe information.

## Catalog
1. Overview and scope; 2. domain index; 3. object inventory (schema, object, type, purpose, grain, owner role, classification, source/status); 4. links to dictionary and ERD; 5. unknowns.

## Dictionary
1. Conventions; 2. per-object summary; 3. per-field table (ordinal, field, type/length, nullable, key membership, definition, format/unit, classification, evidence/status); 4. approved constraints; 5. relationships and gaps. For wide PDFs split columns into basic and semantic panels, keeping field ID.

## ERD
1. Scope and legend; 2. verified diagram or key mapping list; 3. composite FK mapping and nullability/uniqueness notes; 4. unverified relationships excluded.

## Classification
1. Classification vocabulary; 2. field/object classification matrix; 3. personal-data risk and metadata publication rules; 4. verified safeguards vs recommendations; 5. unknowns and review owners (roles only).

## Consumer Guide
1. Quick start using documentation; 2. how to interpret tables/keys/types/grain; 3. join relationship explanation without real queries or records; 4. restrictions and separate access approval; 5. AI agent instructions and document navigation.

## Data Lineage and Schema Diff
List only approved directed mappings and their sources. If no mapping is provided, say lineage is unknown. For schema diff, compare same-scope snapshots and describe changes without claiming deployment or renames.

## llms.txt
Provide a short summary and relative links to reviewed docs, no raw source, no credentials, no query permission. Label the coverage and version. Use `README.md` as the human index and `release-manifest.md` for QA and gaps.
