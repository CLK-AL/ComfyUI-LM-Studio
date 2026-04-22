package al.clk.api

// Abstract fake-data provider + factory.
//
// Callers ask a `FakeProvider.generate(FormatType)` for a realistic
// string value; the provider implementation picks its source. The
// built-in `KotlinFakerProvider` uses io.github.serpro69:kotlin-faker;
// downstream consumers can plug their own (LLM-driven, domain-specific
// fixture replay, etc.) without changing the call site.

import java.util.concurrent.atomic.AtomicLong

/** Minimal abstraction — everyone who wants to hand the mock server
 *  realistic rows implements this. */
interface FakeProvider {
    /** Monotonic id used for INT64 columns and template placeholders. */
    fun nextId(): Long

    /** Reset the counter. Seeded randomness is provider-specific. */
    fun reset()

    /** Pick a realistic value for `fmt`. Return a String that will be
     *  spliced into a JSON body (downstream wraps it per FormatType's
     *  `jsonType`). */
    fun generate(fmt: FormatType): String
}

/** Provider factory — pick an implementation by name. Defaults to
 *  the datafaker-backed provider; register alternatives (e.g. a
 *  kotlin-faker or LLM-driven one) via `register()`. The Clikt
 *  `--faker` option on applicable subcommands surfaces the name
 *  to the user. */
object FakeProviderFactory {
    private val builders: MutableMap<String, (Long) -> FakeProvider> =
        mutableMapOf("datafaker" to { seed -> DatafakerProvider(seed) })

    fun register(name: String, build: (Long) -> FakeProvider) {
        builders[name] = build
    }

    fun create(name: String = "datafaker", seed: Long = 0): FakeProvider =
        (builders[name] ?: builders["datafaker"]!!)(seed)

    fun names(): List<String> = builders.keys.sorted()
}

/** Shared counter base-class — subclasses just override `generate`. */
abstract class BaseFakeProvider : FakeProvider {
    private val counter = AtomicLong(0)
    override fun nextId(): Long = counter.incrementAndGet()
    override fun reset() { counter.set(0) }
}
