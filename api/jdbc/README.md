# /api/jdbc — local + real modes

The JDBC facade has two runtime modes, picked by `--jdbc-url`:

| Mode      | `--jdbc-url`                           | Backing driver            | When it fits |
| --------- | -------------------------------------- | ------------------------- | ------------ |
| **Local** | `jdbc:sqlite::memory:` or `jdbc:sqlite:/tmp/x.db` | `org.xerial:sqlite-jdbc` | Tests, demos, first-touch UX. Zero deps beyond the jbang jars. |
| **Real**  | `jdbc:postgresql://host:5432/db`       | `org.postgresql:postgresql` + `net.postgis:postgis-jdbc` | Real PG 18 + PostGIS workloads. |

Both modes go through **exactly the same Spring `JdbcTemplate`
pipeline and expose exactly the same REST surface** — the Python
`comfyui_openapi_node` code can't tell the difference.

## SQLDelight for the local path

`spec/sample-tables.sq` is the SQLDelight source for the two-table
sample schema (`users`, `places`). Two ways to use it:

1. **Runtime DDL only.** Read the `CREATE TABLE` statements and apply
   them to an in-memory SQLite. The discovery endpoint
   (`GET /jdbc/__schema`) then produces the same table descriptor as
   the YAML-driven path — DatabaseMetaData doesn't care how the schema
   got into the DB.

2. **Compile-time typed API.** Feed the `.sq` through the SQLDelight
   Gradle / Maven plugin (`app.cash.sqldelight:sqlite-dialect:2.0.2`)
   to get a generated Kotlin class per query. Useful when we want to
   ship curated fixtures with a typed façade.

The declared queries at the bottom of `sample-tables.sq`
(`selectAllUsers`, `insertUser`, `selectPlacesNear`) are the typed API
for path #2. They use `json_extract(..., '$.coordinates[0]')` — SQLite
understands JSON paths, so the PostGIS GeoJSON round-trip works
locally too, modulo the simplifying choices described in the `.sq`
file (no real GEOMETRY type).

## Discovery endpoint

Both modes speak the same `/jdbc/__schema` shape:

```json
{
  "tables": [
    { "name": "users",  "primary_key": ["id"], "columns": [...] },
    { "name": "places", "primary_key": ["id"], "columns": [...] }
  ]
}
```

The Python side (`to_jsonschema/jdbc.py`) already knows how to turn
that into ComfyUI nodes. Dropping a new DB URL is the only step
needed to surface every table as typed nodes — **zero repo changes**.
