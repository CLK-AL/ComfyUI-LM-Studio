// KMP-safe enum mirror of java.sql.Types.
//
// `code` matches java.sql.Types numerically — on JVM you can cross-
// compare `SqlTypes.INTEGER.code == java.sql.Types.INTEGER`. In KMP
// commonMain (Android / iOS / Wasm) we can't import java.sql, but the
// constants stay identical.
//
// Use cases:
//   FormatType.INT32.mapping.sqlType == SqlTypes.INTEGER   // real enum
//   SqlTypes.INTEGER.code                                  // 4
//   SqlTypes.INTEGER.name                                  // "INTEGER"
//   SqlTypes.fromCode(-5)                                  // BIGINT
//   SqlTypes.fromName("BIGINT")                            // BIGINT

enum class SqlTypes(val code: Int) {
    BIT(-7),
    TINYINT(-6),
    SMALLINT(5),
    INTEGER(4),
    BIGINT(-5),
    FLOAT(6),
    REAL(7),
    DOUBLE(8),
    NUMERIC(2),
    DECIMAL(3),
    CHAR(1),
    VARCHAR(12),
    LONGVARCHAR(-1),
    DATE(91),
    TIME(92),
    TIMESTAMP(93),
    TIMESTAMP_WITH_TIMEZONE(2014),
    TIME_WITH_TIMEZONE(2013),
    BINARY(-2),
    VARBINARY(-3),
    LONGVARBINARY(-4),
    NULL(0),
    OTHER(1111),
    JAVA_OBJECT(2000),
    BLOB(2004),
    CLOB(2005),
    NCHAR(-15),
    NVARCHAR(-9),
    LONGNVARCHAR(-16),
    NCLOB(2011),
    BOOLEAN(16),
    ROWID(-8),
    SQLXML(2009),
    REF_CURSOR(2012),
    ARRAY(2003),
    STRUCT(2002),
    REF(2006),
    DATALINK(70);

    companion object {
        fun fromCode(code: Int): SqlTypes =
            entries.firstOrNull { it.code == code }
                ?: throw IllegalArgumentException("unknown sql type code: $code")

        fun fromName(name: String): SqlTypes =
            try { valueOf(name.uppercase()) }
            catch (e: IllegalArgumentException) {
                throw IllegalArgumentException("unknown sql type: $name", e)
            }
    }
}
