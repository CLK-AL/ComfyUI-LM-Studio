# KMP migration plan — `/api/common` → Compose Multiplatform

`/api/common/*.kt` was written so the same code works three ways:

1. **JVM today**, pulled into `api/api.mock.jbang.kt` via `//SOURCES`.
2. **JVM + Spring** (JdbcTemplate path) — `api/jdbc/JdbcServer.kt`.
3. **KMP tomorrow** — lift the common files into a Compose
   Multiplatform module's `commonMain` with zero edits.

The only requirement enforced on `/api/common/*.kt`: **no `java.*`
imports, no Spring annotations, no JVM-only stdlib calls**. Today
every file sticks to `kotlin.*`, `kotlinx.serialization.*`, and
Exposed's multiplatform core.

## Library choice — two co-existing paths

| Path | Libraries | Good for |
| --- | --- | --- |
| **JVM (Spring)** | `spring-jdbc` + `HikariCP` + `postgresql` + `postgis-jdbc` | Existing ops muscle memory, production Postgres + PostGIS, the full `DatabaseMetaData` introspection path. |
| **KMP (SQLDelight + Exposed)** | `sqldelight` (driver + runtime) + `exposed-core/dao/jdbc/json/kotlin-datetime` | Compose Multiplatform frontends (Desktop / Android / iOS / Web). Same CRUD on every target. |

Both paths land in the same `api.mock.jbang.kt` today so a reviewer
can see them side by side. The Python side doesn't care which path
the Kotlin server chose — it only talks to `/jdbc/__schema` and the
per-table REST routes.

## Target module layout (Gradle multiplatform)

    compose-ui/
      build.gradle.kts                     # kotlin("multiplatform") + compose plugin
      src/
        commonMain/kotlin/
          api/common/Naming.kt              ← moved, unchanged
          api/common/ComponentTables.kt     ← moved, unchanged
          api/common/JdbcExposed.kt         ← moved, unchanged
          ui/ApiExplorer.kt                 ← Compose screens
        desktopMain/kotlin/                 (JVM)
          Main.kt                           → application { Window { ApiExplorer() } }
        androidMain/kotlin/                 (Android)
          MainActivity.kt                   → setContent { ApiExplorer() }
        iosMain/kotlin/                     (iOS, Native)
          MainViewController.kt             → ComposeUIViewController { ApiExplorer() }
        wasmJsMain/kotlin/                  (Compose for Web)
          Main.kt                           → ComposeViewport { ApiExplorer() }

Dependency list (per `commonMain`):

```kotlin
implementation(compose.runtime)
implementation(compose.material3)
implementation(compose.foundation)
implementation("org.jetbrains.exposed:exposed-core:0.54.0")
implementation("org.jetbrains.exposed:exposed-jdbc:0.54.0")   // JVM targets
implementation("app.cash.sqldelight:runtime:2.0.2")
```

## What Compose UI binds to

Every piece we need already exists:

- **`INPUT_TYPES`** from binding.py (Python) has an equivalent use on
  the Kotlin side: `ComponentTables.columnsFromSchema(schema)` plus
  `patch_op_to_sse` gives us the widget-generation contract.
- **`SchemaRegistry`** on disk + SQLite index — Compose for Web reads
  the JSON files over HTTP; Compose Desktop opens them directly.
- **`EntityStore` audit → SSE** — Compose listens on
  `/entities/__events` and re-renders the grid per patch op.

## Keep-it-portable checklist

- [x] `Naming.kt` uses only `kotlin.text.Regex`, no `java.util.regex`.
- [x] `ComponentTables.kt` uses `kotlinx.serialization.json.*`, not
      Jackson.
- [x] `JdbcExposed.kt` uses Exposed's multiplatform `exposed-core`
      API (select/insert DSL) — not `java.sql.*`.
- [ ] When the Compose module lands, swap `exposed-jdbc` → platform
      driver (`org.jetbrains.androidx.sqlite` on Android, `psql-wasm`
      on Wasm) — the DSL stays.

## Why this matters for the project

The Python `comfyui_openapi_node` package is a visual pipeline
scheduler plugin. The Kotlin mock is a multi-protocol simulator. A
Compose Multiplatform frontend on top makes the whole thing a
single-binary tool you can distribute standalone — **any spec,
anywhere, same UI, no real server, no real database**.
