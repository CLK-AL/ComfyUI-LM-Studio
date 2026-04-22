package al.clk.api

import kotlin.test.Test
import kotlin.test.assertEquals

// KMP parity tests for `Naming.kt`. Mirrors `test_naming_parity.py` on
// the Python side and shares the same `tests/fixtures/naming-cases.json`
// fixture at CI time — here we cover the identity / shape contract only.
class NamingCommonTest {

    @Test fun component_name_is_pascal() {
        assertEquals("Book",   Naming.componentName("book"))
        assertEquals("BookList", Naming.componentName("book_list"))
        assertEquals("BookList", Naming.componentName("book-list"))
        assertEquals("BookList", Naming.componentName("bookList"))
        assertEquals("BookList", Naming.componentName("BookList"))
    }

    @Test fun table_name_is_snake() {
        assertEquals("book",       Naming.tableName("Book"))
        assertEquals("book_list",  Naming.tableName("BookList"))
        assertEquals("book_list",  Naming.tableName("book-list"))
    }

    @Test fun patch_name_is_snake_patch_suffix() {
        assertEquals("book_patch",      Naming.patchName("Book"))
        assertEquals("book_list_patch", Naming.patchName("BookList"))
    }

    @Test fun sse_frame_is_stable_dot_separator() {
        // {component}.{op} — UI consumers split on the dot.
        val frame = Naming.sseFrame("Book", "patched")
        assertEquals("book.patched", frame)
    }
}
