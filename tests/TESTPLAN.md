# Test Plan — ComfyUI-LM-Studio (API mode, WireMock)

## Scope

Covers `LMStudioNode._get_response_api` in `node.py`. The SDK path
(`_get_response_sdk`) is out of scope for WireMock since it bypasses HTTP;
cover it separately with `unittest.mock` against the `lmstudio` module.

## Tooling

No Docker. The mock server is a **jbang Kotlin (Clikt) facade** that embeds
WireMock and seeds stubs from the **LM Studio official OpenAPI** document.
Runtime is **GraalVM 25 + Kotlin 2.3.2** pinned via `.sdkmanrc`, and the
script can be AOT-compiled to a native binary.

- **Toolchain**: `sdk env` (reads `.sdkmanrc`) → `java=25-graal`,
  `kotlin=2.3.2`.
- **Facade**: `tests/wiremock-lms.kt` (jbang header declares deps:
  `org.wiremock:wiremock:3.9.1`, `com.github.ajalt.clikt:clikt:4.4.0`,
  `io.swagger.parser.v3:swagger-parser:2.1.22`).
- **Stub source**: default `https://lmstudio.ai/docs/openapi.yaml`, override
  with `--spec` (path or URL). Response examples from the spec become stub
  bodies; paths without examples get a `{"stubbed": true, "path": ...}`
  placeholder you can override per-test from Python.
- **Test runner**: `pytest`; bound to whatever URL the facade prints.
- **Fixtures**: session-scoped skip if WireMock isn't reachable; per-test
  reset of mappings + request log via the admin API.

Install & run:

```
curl -s "https://get.sdkman.io" | bash  # one-time
sdk env install                         # picks up .sdkmanrc
curl -Ls https://sh.jbang.dev | bash    # one-time
jbang tests/wiremock-lms.kt start       # listens on 127.0.0.1:8089

# (optional) AOT native binary:
jbang --native tests/wiremock-lms.kt
./wiremock-lms start

pip install pytest wiremock requests
pytest tests/ -q
```

## Endpoint under test

`POST {server_address}/api/v0/chat/completions`

Expected request payload keys: `model`, `messages`, `temperature`, `stream`.
Expected response shape (from the node's parser):

```json
{
  "choices": [{"message": {"content": "<str>"}}],
  "usage":   {"prompt_tokens": 0, "completion_tokens": 0},
  "stats":   {"tokens_per_second": 0.0}
}
```

## Test cases

| # | Name | Stub | Assert |
|---|------|------|--------|
| 1 | happy_path | 200 with valid completion, usage, stats | returns `(content, formatted stats)`; payload echoes inputs |
| 2 | strips_thinking_tokens | 200 with `<think>secret</think>visible` | with `thinking_tokens=False`, only `visible` remains |
| 3 | keeps_thinking_tokens | same body | with `thinking_tokens=True`, full content kept |
| 4 | missing_usage_and_stats | 200, `choices` only, no `usage`/`stats` | returns default zero stats, no crash |
| 5 | malformed_choices | 200, `{}` | catches KeyError, returns `Error: ...` string and default stats |
| 6 | http_500 | 500 status | `raise_for_status` triggers, returns `Error: ...` and default stats |
| 7 | connection_refused | WireMock off / unused port | returns `Connection error - is LM Studio running at ...?` |
| 8 | timeout | WireMock `fixedDelay` > 120_000 ms, or a short-override fixture | returns `Request timed out ...` |
| 9 | request_shape | 200 | verifies payload: model, messages roles/content, temperature, stream=false |
| 10 | content_type_header | 200 | verifies `Content-Type: application/json` on the request |
| 11 | server_address_trailing_slash (bug candidate) | 200 at `/api/v0/chat/completions` | document behavior when user passes `http://host:1234/` |
| 12 | max_tokens_ignored (known bug) | 200, record request | confirms `max_tokens` is absent from payload — failing test that pins current behavior until fix |

## Out-of-scope but recommended

- **SDK path**: patch `lmstudio.llm`, `lmstudio.Chat`, `lmstudio.prepare_image`
  and assert call sequence + tempfile cleanup.
- **Image preprocessing**: unit-test `_prepare_image` with a synthetic
  ndarray; verify uint8 clamp and RGB conversion once fixed.
- **Regex**: unit-test `_clean_thinking_tokens` on nested/variant tags.

## File layout

```
.sdkmanrc                # java=25-graal, kotlin=2.3.2
tests/
  TESTPLAN.md            # this file
  wiremock-lms.kt        # jbang Kotlin/Clikt facade seeding from LMS OpenAPI
  conftest.py            # wiremock fixtures (skip if server absent)
  test_api_mode.py       # cases 1–12
  stubs/                 # reusable stub builders (optional)
```

## CI hook

Provision SDKMAN + jbang in the job, `sdk env`, launch the facade in the
background (`jbang tests/wiremock-lms.kt start &`), wait for
`127.0.0.1:8089`, then run `pytest -q`. A `WIREMOCK_URL` env var lets the
same tests target a locally- or CI-started server.

For cold-start speed in CI, prefer the native binary: build once with
`jbang --native` and cache `./wiremock-lms`.
