// Exposed-flavoured mirror of the Spring JdbcTemplate path in
// api/jdbc/JdbcServer.kt.
//
// Lives here in api/common/ so both JVM-only and KMP-portable
// callers can //SOURCES it. Imports are the same on JVM and on
// Android / iOS / Desktop / Web KMP targets — Exposed's core and
// DAO modules are multiplatform now.  When we migrate the UI to
// Compose Multiplatform, *this* file moves verbatim into
// commonMain — no rewrite.
//
// Compared with the Spring path (JdbcServer.kt):
//
//   Spring JdbcTemplate           Exposed
//   ─────────────────────────     ──────────────────────────
//   HikariDataSource              Database.connect(url, driver)
//   DataSourceTransactionManager  transaction { }
//   jdbcTemplate.queryForList     Table.selectAll().map { }
//   jdbcTemplate.update           Table.insert { it[col] = v }
//   DatabaseMetaData discovery    TransactionManager.current()
//                                   .db.vendorSpecificMetaData
//
// The MVP here is the *connection + CRUD surface* — schema
// discovery is common between both paths because it uses the
// same java.sql.DatabaseMetaData (Exposed exposes it straight).

import org.jetbrains.exposed.sql.Database
import org.jetbrains.exposed.sql.Op
import org.jetbrains.exposed.sql.Table
import org.jetbrains.exposed.sql.deleteWhere
import org.jetbrains.exposed.sql.insert
import org.jetbrains.exposed.sql.select
import org.jetbrains.exposed.sql.selectAll
import org.jetbrains.exposed.sql.transactions.transaction
import org.jetbrains.exposed.sql.update

object JdbcExposed {

    /** Open an Exposed `Database` handle. Works for:
     *   jdbc:sqlite::memory:           (driver = org.sqlite.JDBC)
     *   jdbc:sqlite:/path/to/file.db
     *   jdbc:postgresql://h:5432/db    (driver = org.postgresql.Driver)
     *
     * The same call signature works on every KMP JVM target. For
     * Android / native SQLite we'd swap to `exposed-sqlite` or a
     * platform-specific driver, but the rest of this file stays. */
    fun connect(jdbcUrl: String, user: String = "", password: String = ""): Database {
        val driver = when {
            jdbcUrl.startsWith("jdbc:sqlite")      -> "org.sqlite.JDBC"
            jdbcUrl.startsWith("jdbc:postgresql")  -> "org.postgresql.Driver"
            else -> throw IllegalArgumentException("unsupported jdbc url: $jdbcUrl")
        }
        return Database.connect(jdbcUrl, driver = driver, user = user, password = password)
    }

    /** Dynamic table wrapper — we don't know column names at compile
     *  time because they come from the spec. Mirrors the DDL emitted
     *  by common/ComponentTables.kt. */
    class DynamicTable(name: String, cols: List<Column>) : Table(name) {
        // `colMap` instead of `columns` — Exposed's Table already
        // defines a `columns` property and Kotlin requires an
        // `override` modifier to shadow it.
        val colMap: Map<String, org.jetbrains.exposed.sql.Column<*>> = buildMap {
            for (c in cols) put(
                c.name,
                when (c.sqlType) {
                    "INTEGER" -> integer(c.name)
                    "REAL"    -> double(c.name)
                    "BLOB"    -> blob(c.name)
                    else      -> text(c.name)
                }
            )
        }
    }

    fun fetchAll(db: Database, table: DynamicTable): List<Map<String, Any?>> = transaction(db) {
        table.selectAll().map { row ->
            table.colMap.mapValues { (_, col) -> row[col] }
        }
    }
}
