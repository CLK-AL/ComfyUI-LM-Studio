# Test Plan — ComfyUI-LM-Studio (API mode, WireMock)

## Scope

Covers `LMStudioNode._get_response_api` in `node.py`. The SDK path
(`_get_response_sdk`) is out of scope for WireMock since it bypasses HTTP;
cover it separately with `unittest.mock` against the `lmstudio` module.

## Tooling

- **WireMock**: run as a standalone server (Docker: `wiremock/wiremock:3.9.1`
  or the jar). Default bound to `http://127.0.0.1:8089`.
- **Python client**: `wiremock` PyPI package (>=2.6) to program stubs.
- **Test runner**: `pytest`.
- **Fixtures**: a session-scoped fixture starts WireMock (or assumes it's
  already running in CI), resets mappings between tests, and tears it down.

Install:

```
pip install pytest wiremock requests
docker run --rm -d -p 8089:8080 --name wiremock wiremock/wiremock:3.9.1
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
tests/
  TESTPLAN.md            # this file
  conftest.py            # wiremock fixtures
  test_api_mode.py       # cases 1–12
  stubs/                 # reusable stub builders
```

## CI hook

Add a job that boots WireMock in a service container and runs `pytest -q`.
Keep a `WIREMOCK_URL` env var so the same tests work locally against a
manually-started server.
