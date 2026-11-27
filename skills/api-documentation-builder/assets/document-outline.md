# Output outlines (Thai by default)

Begin each document with system/version/audience/classification/scope/status and safe evidence IDs.

## API Catalog
Overview, domain index, inventory (operation ID, method, path, purpose, lifecycle/version, classification, scope, owner role, evidence/status), links to reference, gaps.

## API Data Dictionary
Naming/format conventions; request/response field dictionary (operation ID, location/status, media type, stable field path, type, required, nullable, constraint, meaning, unit, classification, evidence); reusable component definitions; gaps. Wide PDF tables may be split into basic and semantic panels.

## API Reference
Contract conventions; authentication; one section per operation (method, path, purpose, path/query/header parameters, request schema, response statuses and schemas, errors, scopes, classification, verified pagination/rate limits, safe examples); spec link; unresolved contract details. Never include live server URL.

## API Consumer Guide (User Manual)
Audience and use cases; prerequisites and approved access process; authentication concepts; placeholder-based quick start; request/response structure; common errors and troubleshooting; retries/pagination if verified; versioning; contact role and restrictions. Add safe cURL/JS/Python examples only as useful and verified against contract, no actual calls. Do not imply unknown auth or route.

## API Governance
Owner roles; classification; documented access controls vs proposals; scope management; auditing; data minimization; incident handling; versioning and deprecation; limitations and review.

## AI Agent Integration Guide
Safe operation discovery; allowlist; tool input/output contracts; authorization; human approval; side-effect and privacy policies; deny-by-default; integration steps without execution; tool manifest evidence/coverage; unavailable operations. `AGENTS.md` is operational guidance; `llms.txt` is a safe navigation index. Do not grant access by documentation.
