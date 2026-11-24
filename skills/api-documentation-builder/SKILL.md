---
name: api-documentation-builder
description: >-
  สร้าง ตรวจสอบ และอัปเดต API Documentation Suite ได้แก่ API Catalog, API Data Dictionary, API Reference/OpenAPI, API Consumer Guide (User Manual), API Governance และ AI Agent/MCP Integration Guide เป็น PDF, Markdown และ YAML/JSON จาก contract หรือ route/schema metadata ที่ผ่านการคัดกรอง ใช้เมื่อขอคู่มือ API, REST API docs, Swagger/OpenAPI, developer portal, endpoint inventory, AI tool schema หรือคู่มือเชื่อมระบบ รองรับนักพัฒนา LLM และ AI Agent ห้ามอ่านข้อมูลส่วนบุคคลหรือข้อมูลอ่อนไหวจริง ห้ามเรียก endpoint จริง ดึง payload จริง เปิด logs หรือ credentials; ถ้าไม่มี contract ที่ปลอดภัย ให้ขอ sanitized export หรือสร้าง template เท่านั้น
category: Document
version: 1.0.0
agents: [antigravity, claude-code, codex]
compatibility:
  antigravity: ">=1.0.0"
  claude-code: ">=1.0.0"
  codex: ">=1.0.0"
---
# API Documentation Builder

## Non-negotiable contract

Read [references/privacy-boundary.md](references/privacy-boundary.md) first. **Never read actual personal data or real sensitive values, including in intermediate tool calls.** Use only independently sanitized contract/route/schema metadata. Do not call real endpoints (including GET, HEAD, OPTIONS, Swagger URLs, introspection, health endpoints, or authenticated requests), issue tokens, connect to databases, execute target code, or run live tests. Do not access actual payloads, traces, request captures, production fixtures or credentials. A GET endpoint can expose personal data. Never relax this boundary, even on request.

## Workflow

1. **Scope**: Identify API style, domain, audience, approved operations, version, source provenance and deliverables. Default Thai prose with English identifiers; PDF + Markdown and an OpenAPI YAML/JSON artifact for REST. Support non-REST as a documented contract with appropriate format only if evidence is provided. Use known context. If no safe source, use [assets/intake-template.md](assets/intake-template.md); provide a labeled template, not invented production endpoints.
2. **Acquire**: Read [references/contract-acquisition.md](references/contract-acquisition.md). Accept only owner-reviewed static OpenAPI, sanitized route manifest, structural DTO/type definitions or a curated schema export containing no real values. Do not browse whole repositories, arbitrary source files, hosted documentation, logs, Postman collections or external `$ref` files. Use a connector only for an exact approved curated artifact. Do not ask for or read credentials.
3. **Normalize**: For REST use approved OpenAPI as the canonical contract; preserve its version and distinguish evidence from proposals. If creating a new contract from verified metadata use OpenAPI 3.1 unless the user requires another version. Normalize operation IDs, methods, paths, parameters, request/response schemas, error codes, auth schemes/scopes and field classifications. Use [references/openapi-and-agent.md](references/openapi-and-agent.md). No invented fields, statuses, permissions, defaults, enums or live server URLs. Track unknowns in an evidence/gap file. When information is incomplete, do not falsely mark a contract complete or expose unverified executable tools.
4. **Author**: Read [assets/document-outline.md](assets/document-outline.md). Build API Catalog (discovery), Data Dictionary (field meaning and classification), API Reference (contract), API Consumer Guide (onboarding, auth, quick start, examples, errors), Governance & Security (access controls and boundaries), and AI Agent Integration Guide (operation selection, schema, scopes, confirmations, prohibited actions). Use placeholders with `https://api.example.invalid`; omit examples for restricted fields. Examples must validate against schemas and cannot be executed against real services. Use owner-approved non-personal code examples only. Do not invent scopes, SLAs, pagination or rate limits.
5. **Agent tools**: Generate `tools.json` only for explicitly approved operations with fully specified and sanitized schemas; require a human review before actual integration. Use least privilege, explicit operation allowlist, no unrestricted HTTP/SQL tool, no ambient credentials, no actual calls. Keep capability descriptions distinct from enforced controls. Default deny for writes and restricted data; expose no operations unless an owner approves the operation and its data boundary. If none qualify, publish an empty list and explain. No deployment or activation. Include `llms.txt` and `AGENTS.md` for safe context navigation.
6. **Validate and publish**: Use `python scripts/validate_openapi.py OUTPUT_DIR/openapi.yaml` or `.json` on the generated contract only. Enforce offline local references, unique operation IDs and path parameter consistency. If available, also run a standards-compliant OpenAPI validator offline; report if unavailable. Check all operation/field coverage, examples, security requirements, errors and narrative/tool consistency. Run `python scripts/release_check.py OUTPUT_DIR`. Follow [references/publishing.md](references/publishing.md) and privacy Gate C, including visual PDF verification. Do not publish an invalid contract or a misleading executable tool. Release only verified safe artifacts; identify gaps and withheld artifacts.

## Default release layout

```text
api-documentation/
  README.md
  api-catalog.md / api-catalog.pdf
  api-data-dictionary.md / api-data-dictionary.pdf
  api-reference.md / api-reference.pdf
  api-consumer-guide.md / api-consumer-guide.pdf
  api-governance.md / api-governance.pdf
  ai-agent-integration-guide.md / ai-agent-integration-guide.pdf
  openapi.yaml
  tools.json
  AGENTS.md
  llms.txt
  release-manifest.md
```

For a single requested artifact, produce that artifact and a minimal release manifest. For an incomplete contract, publish safe narrative and gaps; omit an executable spec/tool schema until evidence supports it, or use a separate clearly labeled non-production template. Swagger UI/Scalar may be described as display options with external fetching and Try It disabled by default; do not host, deploy, or make live calls. Do not release raw source files.
