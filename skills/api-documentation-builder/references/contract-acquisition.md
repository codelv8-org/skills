# Contract acquisition

Only retrieve an exact owner-reviewed artifact containing structure and non-sensitive descriptions. The skill cannot verify absence of private data by opening a raw source: sanitization must happen upstream. Obtain source ID, contract version or safe revision label, review confirmation, approved operations and publication scope. Never request API keys or auth tokens.

Accept sanitized OpenAPI 3.x JSON/YAML with local references, sanitized endpoint manifest, owner-curated request/response schema, or explicit structural definitions. If a repository is supplied, request a dedicated reviewed export (e.g. `docs/approved-contract.json`), not raw repo analysis. A user may ask their developer to export framework route metadata and DTO shape offline from a clean environment; do not run app boot, routes list, migrations, generators or arbitrary source in this skill. No application execution, dependency install, network calls or credential loading. Do not fetch a deployed Swagger JSON URL, GraphQL introspection, gRPC reflection or actual service endpoint; ask the owner to export and review offline.

## Owner-side projection checklist

- Keep HTTP method, path template, operation ID, domain/tag, description, version, lifecycle, auth scheme type, reviewed scope names, parameter names/location/type/required, request/response media type, response status, schema property names/types/constraints/required/nullability, approved relationships, format and classification.
- Remove examples, default values, enum literals and free text unless separately reviewed as non-personal structural constants. Replace hosts with `https://api.example.invalid`; remove URLs containing internal service locations, credentials or query tokens. Sanitize dynamic paths, headers, extension values, descriptions and component names. Use role-based owner labels only. Do not copy captured responses, stack traces or real identifiers.
- Bundle only vetted local schema references; flatten or convert external refs upstream. Do not follow links or resolve network resources. Confirm whether any endpoint or response shape is restricted or approved for agent use. Record unknowns without exposing payloads.
- For REST retain confirmed HTTP behavior; for GraphQL/gRPC/event-driven interfaces retain only reviewed SDL/proto/event schema, produce suitable reference/consumer guides; do not falsely translate to OpenAPI. Do not issue introspection, reflection, subscriptions or calls.

If metadata is incomplete, label evidence coverage and list missing fields. A path name alone does not prove auth, input, output, effect or classification. Avoid creating executable contract/tool definitions from guesses.
