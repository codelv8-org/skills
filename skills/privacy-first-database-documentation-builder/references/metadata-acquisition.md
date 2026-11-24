# Metadata acquisition — owner-operated only

Never execute these queries as the skill. They are optional snippets for the authorized data owner to create an export outside the agent. Use a dedicated least-privilege metadata identity and approved schema/object scope. The owner must review the result and remove any personal identifiers encoded in object names before supplying it. Do not collect comments, defaults, expressions, check predicates, view definitions, routine bodies, statistics, sizes, row counts, values, or sample rows. Even schema dumps may contain literals, secrets, data statements or real names. Prefer an allowlisted JSON projection over a dump.

## MySQL / MariaDB

Use schema name as a bound parameter in the owner's client (the `:approved_schema` syntax is illustrative). For explicit table scope add an owner-managed allowlist of names, not dynamically interpolated input.

```sql
SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = :approved_schema;

SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, ORDINAL_POSITION,
       DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH,
       NUMERIC_PRECISION, NUMERIC_SCALE, DATETIME_PRECISION
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = :approved_schema
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SELECT tc.TABLE_SCHEMA, tc.TABLE_NAME, tc.CONSTRAINT_NAME,
       tc.CONSTRAINT_TYPE, k.COLUMN_NAME, k.ORDINAL_POSITION,
       k.REFERENCED_TABLE_SCHEMA, k.REFERENCED_TABLE_NAME,
       k.REFERENCED_COLUMN_NAME, k.POSITION_IN_UNIQUE_CONSTRAINT
FROM information_schema.TABLE_CONSTRAINTS tc
JOIN information_schema.KEY_COLUMN_USAGE k
  ON tc.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA
 AND tc.TABLE_SCHEMA = k.TABLE_SCHEMA
 AND tc.TABLE_NAME = k.TABLE_NAME
 AND tc.CONSTRAINT_NAME = k.CONSTRAINT_NAME
WHERE tc.TABLE_SCHEMA = :approved_schema
  AND tc.CONSTRAINT_TYPE IN ('PRIMARY KEY','UNIQUE','FOREIGN KEY');
```

`DATA_TYPE` avoids `COLUMN_TYPE` literal enum definitions. Use only supported structural fields in the v2.0 input contract; do not add code sets or raw type modifiers. Confirm FK targets are within disclosure scope. Do not query TABLE_ROWS or profiling views.

## PostgreSQL

Project `information_schema.tables` (table_catalog only if approved, table_schema, table_name, table_type) and `information_schema.columns` (table_schema, table_name, column_name, ordinal_position, data_type, is_nullable, character_maximum_length, numeric_precision, numeric_scale, datetime_precision), filtering exact approved schema. For keys use owner-reviewed projection of `pg_catalog.pg_constraint`, `pg_class`, `pg_namespace`, `pg_attribute`; pair `conkey` and `confkey` by ordinal for composite FKs. Never fetch `pg_stats`, `pg_stat*`, `pg_get_constraintdef`, defaults, comments or expression bodies. Information schema visibility depends on permissions; lack of rows is not proof of absent objects.

## SQL Server

Owner projects `sys.schemas`, `sys.tables`, `sys.views`, `sys.columns`, `sys.types` with exact schema filter; preserve `max_length` byte-vs-character distinction, precision and scale. Key mapping via `sys.key_constraints`, `sys.index_columns`, `sys.foreign_keys`, `sys.foreign_key_columns` with ordinal and source/target columns. Do not fetch `sys.sql_modules`, default definitions, extended properties or stats. Metadata visibility depends on permissions.

## SQLite and other engines

Do not give the agent a live SQLite database or database file. Owner can use version-supported schema-only metadata projections such as `pragma_table_xinfo` (select cid, name, type, notnull, pk, hidden; exclude dflt_value) and `pragma_foreign_key_list` with exact approved table name. Do not fetch `sqlite_schema.sql` unless sanitized upstream. For other engines request equivalent curated structural metadata. Never use an ORM migration file without prior source review; migrations may contain inserted rows and comments.

## Evidence quality

Request safe object type, schema-qualified identity, ordinal, type, length/precision, nullability, PK/unique/FK column order, approved business definitions and classification separately. Owner may supply independently curated definitions in the separate definitions array, not raw comments, defaults, enum values or constraint expressions. Use scope labels, export date and source ID; avoid actual server addresses, usernames, database credentials. If relationships point outside scope, omit target identity unless disclosure is approved; record unresolved edge count only. Use classification `Unknown` for uncertain data, with effective classification Restricted. Project into the v2.0 contract before transfer; never attach a raw query export to the agent.
