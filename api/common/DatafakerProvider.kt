// Default FakeProvider implementation backed by net.datafaker.
//
// Registered by name "datafaker" in the FakeProviderFactory. Stable
// Java API, fully callable from Kotlin; covers every FormatType the
// bridge defines.

import java.util.Locale
import net.datafaker.Faker

class DatafakerProvider(
    seed: Long = 0L,
    locale: Locale = Locale.US,
) : BaseFakeProvider() {

    private val faker: Faker = Faker(locale, java.util.Random(seed))
    private val rng = java.util.Random(seed)

    override fun generate(fmt: FormatType): String = when (fmt) {
        FormatType.TEXT               -> faker.lorem().sentence()
        FormatType.TEXTAREA,
        FormatType.MARKDOWN,
        FormatType.DYNAMIC_PROMPT     -> faker.lorem().paragraph()
        FormatType.PASSWORD           -> faker.internet().password()
        FormatType.EMAIL,
        FormatType.VCARD_EMAIL        -> faker.internet().emailAddress()
        FormatType.URL,
        FormatType.VCARD_URL          -> faker.internet().url()
        FormatType.SEARCH             -> faker.lorem().word()
        FormatType.TEL,
        FormatType.VCARD_TEL          -> faker.phoneNumber().phoneNumber()
        FormatType.UUID,
        FormatType.VCARD_UID,
        FormatType.ICAL_UID           -> java.util.UUID.randomUUID().toString()
        FormatType.COLOR              -> "#%06x".format(rng.nextInt(0x1_000_000))
        FormatType.DATE,
        FormatType.VCARD_BDAY,
        FormatType.VCARD_ANNIVERSARY  -> faker.timeAndDate().birthday().toString().substring(0, 10)
        FormatType.TIME               -> "%02d:%02d:%02d".format(
            rng.nextInt(24), rng.nextInt(60), rng.nextInt(60))
        FormatType.DATETIME,
        FormatType.VCARD_REV,
        FormatType.ICAL_DTSTART,
        FormatType.ICAL_DTEND,
        FormatType.ICAL_DTSTAMP,
        FormatType.ICAL_DUE,
        FormatType.ICAL_COMPLETED,
        FormatType.ICAL_RECUR_ID      -> faker.timeAndDate().birthday().toString()
        FormatType.MONTH              -> "%04d-%02d".format(2000 + rng.nextInt(30), 1 + rng.nextInt(12))
        FormatType.WEEK               -> "%04d-W%02d".format(2000 + rng.nextInt(30), 1 + rng.nextInt(53))
        FormatType.YEAR               -> (1900 + rng.nextInt(200)).toString()
        FormatType.QUARTER            -> (1 + rng.nextInt(4)).toString()
        FormatType.MONTH_OF_YEAR      -> (1 + rng.nextInt(12)).toString()
        FormatType.DAY                -> (1 + rng.nextInt(31)).toString()
        FormatType.DAY_OF_WEEK        -> (1 + rng.nextInt(7)).toString()
        FormatType.DAY_OF_YEAR        -> (1 + rng.nextInt(366)).toString()
        FormatType.ISO_WEEK_NUM       -> (1 + rng.nextInt(53)).toString()
        FormatType.HOUR               -> rng.nextInt(24).toString()
        FormatType.MINUTE,
        FormatType.SECOND             -> rng.nextInt(60).toString()
        FormatType.MILLISECOND        -> rng.nextInt(1000).toString()
        FormatType.TIMEZONE,
        FormatType.VCARD_TZ,
        FormatType.ICAL_TZID          -> "Europe/${faker.address().city().replace(" ", "_")}"
        FormatType.OFFSET             -> "+%02d:00".format(rng.nextInt(13))
        FormatType.DURATION,
        FormatType.ICAL_DURATION      -> "PT${1 + rng.nextInt(24)}H"
        FormatType.IPV4               -> faker.internet().ipV4Address()
        FormatType.IPV6               -> faker.internet().ipV6Address()
        FormatType.HOSTNAME           -> faker.internet().domainName()
        FormatType.REGEX              -> "^.*$"
        FormatType.JSON_POINTER       -> "/" + faker.lorem().word()
        FormatType.BYTE,
        FormatType.BINARY             -> "/tmp/${faker.file().fileName()}"
        FormatType.HIDDEN             -> "hidden:${nextId()}"
        FormatType.GEOJSON,
        FormatType.ICAL_GEO           -> """{"type":"Point","coordinates":[${faker.address().longitude()},${faker.address().latitude()}]}"""
        FormatType.VCARD_GEO          -> "geo:${faker.address().latitude()},${faker.address().longitude()}"
        FormatType.JSON_OBJECT        -> """{"id":${nextId()}}"""
        FormatType.JSON_ARRAY         -> "[]"
        FormatType.INT32              -> rng.nextInt(Int.MAX_VALUE).toString()
        FormatType.INT64              -> nextId().toString()
        FormatType.FLOAT_,
        FormatType.DOUBLE_,
        FormatType.RANGE,
        FormatType.KNOB,
        FormatType.NUMBER_FIELD       -> "%.4f".format(rng.nextDouble() * 100)
        FormatType.BOOL,
        FormatType.CHECKBOX           -> rng.nextBoolean().toString()
        FormatType.ENUM               -> "option_${1 + rng.nextInt(5)}"
        FormatType.RADIO              -> "radio_${1 + rng.nextInt(3)}"
        FormatType.MULTI_SELECT       -> """["a","b"]"""
        FormatType.IMAGE,
        FormatType.MASK,
        FormatType.WEBCAM             -> "/images/${faker.file().fileName()}"
        FormatType.AUDIO              -> "/audio/${faker.file().fileName()}"
        FormatType.VIDEO              -> "/video/${faker.file().fileName()}"
        FormatType.LATENT,
        FormatType.CONDITIONING,
        FormatType.CLIP_VISION_OUTPUT -> """{"shape":[1,4,64,64]}"""
        FormatType.MODEL,
        FormatType.CLIP,
        FormatType.VAE,
        FormatType.CONTROL_NET,
        FormatType.STYLE_MODEL,
        FormatType.CLIP_VISION,
        FormatType.UPSCALE_MODEL      -> "${faker.app().name().replace(" ", "_")}.safetensors"
        FormatType.VCARD_FN           -> faker.name().fullName()
        FormatType.VCARD_N            -> "${faker.name().lastName()};${faker.name().firstName()};;;"
        FormatType.VCARD_NICKNAME     -> faker.name().firstName()
        FormatType.VCARD_GENDER       -> listOf("M", "F", "O", "N", "U")[rng.nextInt(5)]
        FormatType.VCARD_ADR          -> ";;${faker.address().streetAddress()};${faker.address().city()};${faker.address().state()};${faker.address().zipCode()};${faker.address().country()}"
        FormatType.VCARD_TITLE,
        FormatType.VCARD_ROLE         -> faker.job().title()
        FormatType.VCARD_ORG          -> faker.company().name()
        FormatType.VCARD_NOTE         -> faker.lorem().sentence()
        FormatType.VCARD_CATEGORIES   -> List(3) { faker.lorem().word() }.joinToString(",")
        FormatType.ICAL_LOCATION      -> faker.address().fullAddress()
        FormatType.ICAL_SUMMARY       -> faker.lorem().sentence(5)
        FormatType.ICAL_DESCRIPTION,
        FormatType.ICAL_COMMENT       -> faker.lorem().paragraph()
        FormatType.ICAL_STATUS        -> "CONFIRMED"
        FormatType.ICAL_CLASS         -> "PUBLIC"
        FormatType.ICAL_TRANSP        -> "OPAQUE"
        FormatType.ICAL_PRIORITY      -> rng.nextInt(10).toString()
        FormatType.ICAL_SEQUENCE      -> nextId().toString()
        FormatType.ICAL_RRULE         -> "FREQ=WEEKLY;BYDAY=MO;COUNT=10"
        FormatType.ICAL_RDATE,
        FormatType.ICAL_EXDATE        -> faker.timeAndDate().birthday().toString()
        FormatType.ICAL_ATTENDEE,
        FormatType.ICAL_ORGANIZER     -> "mailto:${faker.internet().emailAddress()}"
        FormatType.ICAL_CATEGORIES    -> "BUSINESS,PERSONAL"
        FormatType.ICAL_METHOD        -> "PUBLISH"
        FormatType.ICAL_CALSCALE      -> "GREGORIAN"
        FormatType.ICAL_RELATED_TO    -> "uid-${nextId()}@example.com"
        FormatType.SEMI_DELIMITED     -> List(3) { faker.lorem().word() }.joinToString(";")
        FormatType.CSV_ROW            -> List(3) { faker.lorem().word() }.joinToString(",")
        FormatType.TSV_ROW            -> List(3) { faker.lorem().word() }.joinToString("\t")
        FormatType.LOCALE             -> "en-${faker.address().countryCode()}"
        FormatType.CALENDAR_SYSTEM    -> "gregorian"
        FormatType.PERSON_NAME        -> faker.name().fullName()
        FormatType.NUMBER_FMT         -> "%,.2f".format(rng.nextDouble() * 1_000_000)
        FormatType.DECIMAL            -> "%.2f".format(rng.nextDouble() * 1_000)
        FormatType.CURRENCY           -> "${faker.money().currencyCode()} %,.2f".format(rng.nextDouble() * 10_000)
        FormatType.MEASURE            -> "${1 + rng.nextInt(100)} kg"
        FormatType.UNIT               -> listOf(
            "length-meter", "length-kilometer", "mass-kilogram",
            "volume-liter", "temperature-celsius", "duration-hour",
            "speed-kilometer-per-hour", "digital-megabyte")[rng.nextInt(8)]
        FormatType.ORDINAL            -> (1 + rng.nextInt(100)).toString() + "th"
        FormatType.PLURAL             -> listOf(
            "zero", "one", "two", "few", "many", "other")[rng.nextInt(6)]
    }
}
