package al.clk.api

// Spring JdbcTemplate facade — discovers the DB through DatabaseMetaData
// and exposes /jdbc/<table> + /jdbc/<table>/{id} via Ktor so the Python
// JDBC executor (protocols/jdbc.py) can use the same HTTP codepath.
//
// Consumed by api/api.mock.jbang.kt via //SOURCES.
//
// Two modes (see api/jdbc/README.md):
//   Local  — `--jdbc-url jdbc:sqlite::memory:` boots an in-memory
//            SQLite via `org.xerial:sqlite-jdbc`. `--sql-file` runs
//            DDL (plain `.sql` or the SQLDelight `.sq` at
//            api/jdbc/spec/sample-tables.sq) before serving so every
//            table shows up in `DatabaseMetaData` immediately.
//            SQLDelight (`app.cash.sqldelight:jdbc-driver:2.0.2`) is
//            on the classpath so typed fixtures compile; the runtime
//            discovery path still goes through DatabaseMetaData.
//   Real   — `--jdbc-url jdbc:postgresql://host:5432/db` plus
//            `postgresql` + `postgis-jdbc`. Same pipeline.
//
// Auth header surface (all optional, honoured per-request):
//   X-JDBC-User          JDBC user. Can be a URI-template-style string
//                        like `apikey:<key>` or `jwt:<sub>` that the
//                        driver / DB will recognise.
//   X-JDBC-Password      One of:
//                          • plain password
//                          • bearer access-token (Cloud SQL IAM etc.)
//                          • full signed JWT
//                          • shared secret — the Kotlin side mints a
//                            JWT from X-JDBC-User + X-JDBC-Audience
//                            using this as HMAC secret.
//   X-JDBC-Auth          basic | bearer | jwt | oauth2 | passthrough
//                        — picks the credential-minting path.
//   X-JDBC-Audience      JWT `aud` / OAuth2 audience
//   X-JDBC-Scope         OAuth2 scope (space-separated)
//   X-JDBC-TokenURL      OAuth2 client_credentials endpoint
//   X-JDBC-ClientId      OAuth2 client_id
//   X-JDBC-ClientSecret  OAuth2 client_secret
//
// The combined token (whatever the auth path produced) becomes the JDBC
// password for a HikariDataSource rebuilt per-request (or reused from a
// per-credential-hash cache if long-lived enough).

import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.core.Context
import com.github.ajalt.clikt.parameters.options.default
import com.github.ajalt.clikt.parameters.options.option
import com.github.ajalt.clikt.parameters.types.int

private val jdbcLog = org.slf4j.LoggerFactory.getLogger("jdbc")

class JdbcGroup : CliktCommand(name = "jdbc") {
    override fun help(context: Context) =
        "Spring JdbcTemplate facade — schema discovery + CRUD routes."
    override fun run() = Unit
}

class JdbcServe : CliktCommand(name = "serve") {
    override fun help(context: Context) =
        "Start the Ktor REST front-end over Spring JdbcTemplate."
    val port    by option("-p", "--port").int().default(8095)
    val host    by option("--host").default("127.0.0.1")
    val jdbcUrl by option("--jdbc-url",
        help = "Local: jdbc:sqlite::memory:  |  Real: jdbc:postgresql://host:5432/db"
    ).default("")
    val user    by option("--user",
        help = "JDBC user; may be overridden per-request via X-JDBC-User.").default("")
    val pass    by option("--pass",
        help = "JDBC password / token; may be overridden per-request via X-JDBC-Password.").default("")
    val sqlFile by option("--sql-file",
        help = "Bootstrap SQL / SQLDelight .sq to run after connecting (local mode)."
    ).default("")

    override fun run() {
        jdbcLog.info("jdbc mock on http://{}:{}  (url={}, user={}, sql={})",
            host, port,
            if (jdbcUrl.isBlank()) "<per-request>" else jdbcUrl,
            if (user.isBlank())    "<per-request>" else user,
            if (sqlFile.isBlank()) "<none>"        else sqlFile)
        // Discovery-first flow (follow-up impl):
        //
        //   1. Resolve connection:
        //        • read X-JDBC-* headers (fall back to CLI defaults)
        //        • derive password per X-JDBC-Auth:
        //            basic        → password as-is
        //            bearer       → password as bearer token
        //            jwt          → password as a full signed JWT
        //            jwt-mint     → HMAC-sign a JWT from User + Audience
        //                           using password as the secret
        //            oauth2       → POST token_url, use access_token
        //            passthrough  → don't touch
        //        • HikariCP pool keyed by (jdbcUrl, user, derived-pw).
        //
        //   2. `GET /jdbc/__schema` — **discovery endpoint**.
        //      Uses DatabaseMetaData:
        //        getCatalogs / getSchemas / getTables / getColumns /
        //        getPrimaryKeys / getImportedKeys / getIndexInfo
        //      → emits the same table-descriptor shape our Python
        //         to_jsonschema/jdbc.py converter already consumes
        //         (columns[].sql_type + pg_type + nullable + size +
        //         precision/scale + geotype). Postgres 18 specifics:
        //          • `pg_type.typname` from pg_type join so jsonb /
        //            ltree / inet / …  keep their refined type.
        //          • PostGIS columns: geometry_columns + geography_columns
        //            views → geotype (Point, Polygon, MultiPolygon, …).
        //          • JSON tables (PG 18 SQL/JSON): we expose them with
        //            a single `row` column typed as `format: json`
        //            until there's a stable way to discover their
        //            schema (JSON_TABLE columns are query-scoped).
        //
        //   3. `GET /jdbc/<table>` / `/jdbc/<table>/{id}` → Spring
        //      JdbcTemplate with a per-table RowMapper generated from
        //      the discovered metadata. No per-table code anywhere —
        //      one generic SELECT / INSERT / UPDATE / DELETE handler
        //      driven entirely by DatabaseMetaData.
        //
        //   4. PostGIS geometry columns round-trip as GeoJSON via
        //      net.postgis:postgis-jdbc + a small adapter so the
        //      client sees the `format: geojson` the Python binding
        //      promised.
        //
        // The Python side (comfyui_openapi_node) feeds the Canonical
        // form straight from /jdbc/__schema at import time, so dropping
        // a new DB into the JDBC URL is the only step to surface every
        // table as typed ComfyUI nodes — zero repo changes.
        println("JDBC Spring skeleton ready on $host:$port (deps declared).")
    }
}
