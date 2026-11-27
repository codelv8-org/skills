# Usage and runtime

Run from the installed skill directory. Python 3.9+ and standard library for Markdown, optional `markdown-it-py` and `weasyprint` with Pango, installed Thai fonts (Noto Sans Thai or equivalent) for PDF. Poppler `pdftotext`, `pdfinfo`, `pdfdetach` required for PDF lint; render visually with available PDF skill. Never install dependencies or make external calls without permission; use the available local document/PDF capability if optional renderer unavailable. Do not output font files. No DB/network dependencies. Use synthetic data for tests only.

```bash
python scripts/test_dictionary.py
python scripts/validate_metadata.py assets/metadata-template.json
python scripts/build_dictionary.py assets/metadata-template.json --mode dictionary --pdf --out /tmp/demo-dictionary
python scripts/build_dictionary.py APPROVED.json --mode full --out /tmp/db-docs-review
python scripts/build_dictionary.py CURRENT.json --previous PREVIOUS.json --mode diff --out /tmp/db-diff-review
python scripts/release_check.py /tmp/db-docs-review
```

The output directory must not exist. Generator writes to a new staging directory and only moves it into place if validation and supplementary lint pass. A human must independently approve source and output, even on PASS. PDF is an optional local renderer; no fonts are bundled. If a renderer fails, regenerate Markdown without `--pdf` and use a verified offline PDF workflow; do not pretend PDF was delivered.

Modes automatically inferred from user prompt; do not force a long form. Use the exact approved source reference and explicit owner confirmation. The default end-user formats are PDF and Markdown; optional `--pdf` is chosen by the agent. All modes share validation, classification, and release checks. PDF ERD uses verified key mapping table; `.mmd` is the neutral edge diagram, render it offline for diagram PDF when requested. Never fetch Mermaid JS from CDN or render an untrusted source.

Migration: v1 Database Documentation Builder accepted a different normalized manifest; v1 Privacy-First Data Dictionary used a narrower structural contract. Ask owner to project into v2.0 using the template. Retain safe reviewed evidence and separate curated definitions, omit defaults/comments; do not claim approval for a new scope. This package reconstructs the specialist generator from confirmed v1 behavior, not byte-for-byte original specialist code.
