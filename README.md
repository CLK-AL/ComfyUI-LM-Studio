# ComfyUI LM Studio Node

A powerful ComfyUI custom node that seamlessly integrates LM Studio's local language models into your ComfyUI workflows. This node supports both text-only and multimodal (text + image) inputs, making it perfect for complex AI-driven creative workflows.

![ComfyUI LM Studio Example](./example.png)

## Features

- **Unified Interface**: Single node for both text-only and text+image inputs
- **Dual Mode Support**: Works with both LM Studio SDK (recommended) and REST API
- **Vision Model Support**: Process images alongside text prompts with compatible models
- **Real-time Statistics**: Monitor tokens per second, input/output token counts
- **Thinking Tokens**: Optional support for models that use thinking tokens
- **Flexible Configuration**: Adjust temperature, max tokens, and server settings
- **Debug Mode**: Built-in debugging for troubleshooting

## Installation

### Prerequisites

1. **ComfyUI**: Make sure you have ComfyUI installed and running
2. **LM Studio**: Download and install [LM Studio](https://lmstudio.ai/) (free)
3. **Python**: Python 3.8 or higher
4. **Show Text Node**: Install [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts) for the Show Text node used in the example workflow (any other text display node will also work)

### Installation Steps

1. Navigate to your ComfyUI custom nodes directory:
   ```bash
   cd ComfyUI/custom_nodes/
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/gabe-init/ComfyUI-LM-Studio
   ```

3. Install the required dependencies:
   ```bash
   cd ComfyUI-LM-Studio
   pip install -r requirements.txt
   ```

4. Restart ComfyUI to load the new node

### LM Studio Setup

1. Open LM Studio and download a model (e.g., Mistral 7B Instruct)
2. Start the local server in LM Studio (default port: 1234)
3. Note the model ID from LM Studio for use in the node

## Usage

### Basic Text Generation

1. Add the "LM Studio Chat Interface" node to your workflow
2. Configure the following inputs:
   - **System Prompt**: Set the assistant's behavior
   - **User Message**: Your input prompt
   - **Model ID**: The exact model ID from LM Studio
   - **Server Address**: Usually `http://127.0.0.1:1234`
   - **Temperature**: Control randomness (0.0-1.0)
   - **Max Tokens**: Maximum response length

### Vision Model Usage

For models that support vision (like LLaVA):

1. Connect an image output to the node's image input
2. The node will automatically process both text and image
3. Make sure you're using the SDK mode for image support

### Configuration Options

- **Use SDK**: Enable for better performance and image support (requires `lmstudio` package)
- **Include Thinking Tokens**: For models that support chain-of-thought reasoning
- **Debug Mode**: Enable to see detailed processing information

## Example Workflow

An example workflow is included in `example_workflow/Example_Workflow.json`. This demonstrates:
- Basic text generation setup
- Parameter configuration
- Integration with other ComfyUI nodes

## Troubleshooting

### Connection Issues
- Ensure LM Studio server is running
- Check the server address matches LM Studio's settings
- Verify firewall isn't blocking local connections

### Performance Tips
- Use SDK mode when possible for better performance
- Adjust max tokens based on your needs
- For vision models, use reasonable image sizes

### Common Errors
- "Model not found": Verify the model ID matches exactly what's shown in LM Studio
- "Connection refused": Make sure LM Studio server is started
- Image processing issues: Install the SDK with `pip install lmstudio`

## Advanced Features

### SDK vs API Mode
- **SDK Mode**: Direct integration, supports images, better performance
- **API Mode**: REST-based fallback, text-only, works without SDK

### Debug Output
Enable debug mode to see:
- Model loading times
- Image processing status
- Token generation statistics
- Detailed error messages

## Requirements

- Python 3.8+
- ComfyUI
- LM Studio (running locally)
- See `requirements.txt` for Python packages

## API ComfyUI — concept

The node is a generic **API ComfyUI** surface: pick a spec kind
(OpenAPI today; AsyncAPI / GraphQL / MCP / gRPC / RSocket slots wired
through `spec_kinds.py`), load the spec from path / URL / raw JSON /
raw YAML / bytes, and the binding layer translates each operation's
JSON Schema into a ComfyUI node spec — `INPUT_TYPES`, `RETURN_TYPES`,
`RETURN_NAMES` — with typed slots (`STRING` / `INT` / `FLOAT` /
`BOOLEAN` / enum dropdowns). LM Studio is the first bundled preset.

### The full picture — no real DB, no real server

Individual API files (`.yaml` / `.json` / `.proto` / `.graphql` / `.sq`)
stay as independent contracts. **SQLite JSON1 is the unified logic**:

- **`SchemaRegistry`** — thin index over on-disk `*.schema.json` files;
  answers "which APIs have an `isbn` property?" via `json_extract` in
  one query. `resolve_ref()` handles both JSON Pointers and
  `registry://<kind>/<api>/<category>/<name>` URIs; `unified_component()`
  folds similar components (Google Books / Amazon / Audible `Book`)
  into one merged JSON Schema.
- **`EntityStore`** — two JSON1-validated tables that simulate an app
  holding N API projections of one JDBC entity. `store.project(type,
  id, schema)` returns only the fields a given API cares about;
  `store.patch(..., api=…)` applies RFC 7396 merge via SQL `json_patch()`,
  with every property diff recorded in an append-only audit log and
  streamable as **SSE frames** for realtime consumers.
- **`api/api.mock.jbang.kt`** — one Kotlin process with nested Clikt
  subcommands that mocks every protocol (HTTP / WebDAV / REST / HTTPS /
  WSS / SSE / gRPC / MCP / JDBC) against the same registry + entity
  store. No real API server, no real database.

![unified architecture](./puml/api-comfyui-unified.png)

![concept](./puml/api-comfyui-concept.png)

![binding sequence](./puml/api-comfyui-binding.png)

![node UI](./puml/api-comfyui-node-ui.png)

Sources: [`puml/api-comfyui-concept.puml`](./puml/api-comfyui-concept.puml),
[`puml/api-comfyui-binding.puml`](./puml/api-comfyui-binding.puml),
[`puml/api-comfyui-node-ui.puml`](./puml/api-comfyui-node-ui.puml).

Why the JSON Schema spine matters: **AsyncAPI shares OpenAPI's
`components.schemas` vocabulary**, so the binding layer built for
OpenAPI becomes AsyncAPI the moment you add an adapter that hands
`binding.py` an `(operation-like dict, components-like dict)` pair.
GraphQL, MCP tool manifests and gRPC plug in the same way.

## Repository layout

Kotlin, Python and Proto all share a single KMP-style source tree
rooted at `src/`, with the `al.clk.api` package reused across every
language. `api/api.mock.jbang.kt` is a thin Clikt shell that hands
control to `al.clk.api.apiMockMain` in `commonMain/`.

```
.
├── api.env                           ← shared env (dotenv-kotlin + python-dotenv)
├── __init__.py, node.py              ← upstream LMStudioNode (root-level, for drift check)
├── comfyui_openapi_node/             ← ComfyUI custom-node entry (thin re-export shell)
│   ├── __init__.py                   →  from al.clk.api import NODE_CLASS_MAPPINGS
│   └── node.py                       →  from al.clk.api.node import OpenAPINode
├── api/
│   ├── openapi/spec/…                ← YAML/JSON specs (LM Studio etc.)
│   ├── asyncapi/spec/…
│   ├── jdbc/spec/…
│   └── src/
│       ├── proto/al/clk/api/types.proto         (package al.clk.api)
│       ├── commonMain/kotlin/al/clk/api/        KMP-portable Kotlin
│       │   ├── APIMock.kt             Clikt root + `apiMockMain`
│       │   ├── FormatType.kt          one-hop mapper (KClass↔JClass↔PyClass)
│       │   ├── SqlTypes.kt, Naming.kt, ComponentTables.kt, FakeProvider.kt
│       ├── commonTest/kotlin/al/clk/api/        KMP parity tests
│       │   ├── FormatTypeCommonTest.kt, NamingCommonTest.kt
│       ├── jvmMain/kotlin/al/clk/api/           JVM-only (java.*, Jackson, Spring, Ktor, ical4j)
│       │   ├── JClassKClass.kt        java.*, Jackson refs live here
│       │   ├── JdbcExposed.kt, IcsVcfParser.kt, DatafakerProvider.kt
│       │   └── {openapi,asyncapi,mcp,rsocket,jdbc}/…Server.kt
│       ├── jvmTest/kotlin/al/clk/api/           JVM tests
│       │   ├── JClassKClassTest.kt, IcsVcfParserTest.kt
│       └── jbangMain/
│           └── ApiMock.jbang.kt       jbang launcher — //DEPS + //SOURCES + `main → apiMockMain`
└── src/
    ├── pyMain/py/al/clk/api/         Python mirror (package al.clk.api)
    │   ├── format_type.py, naming.py, registry.py, node.py
    │   ├── entity_store.py, schema_registry.py, schema_patch.py
    │   └── {presets,protocols,to_jsonschema}/…
    └── pyTest/py/al/clk/api/         pytest suite (259 cases)
        ├── conftest.py, bootstrap.py, fixtures/
        └── test_*.py                 (includes test_vcard_ical_api.py)
```

Design goal: **push as much logic as possible into `commonMain`** so a
future KMP publication (Android / iOS / JS) gets the same bridge. JVM
stays for things that genuinely need a JVM library — Jackson JSON
tree, Spring JDBC, WireMock, Ktor server, ical4j / ez-vcard,
datafaker, and the Apache Commons / libphonenumber / libpostal /
GeoIP integrations that `jvmMain` is the natural home for.

`jbangMain` is only the jbang launcher — the single
`ApiMock.jbang.kt` file that declares `//DEPS` + `//SOURCES` and
hands control to `apiMockMain(args)` in `commonMain/APIMock.kt`. A
Gradle `build.gradle.kts` pointed at the same source sets turns the
tree into a standard KMP publication without a line of code moving.

`api.env` is the shared configuration file — `python-dotenv` in
`conftest.py` and `dotenv-kotlin` in `APIMock.kt` both read the same
keys (`API_ROOT`, `PY_MAIN`, `WIREMOCK_PORT`, `JBANG_HOME`,
`KOTLIN_HOME`, `GRADLE_HOME`, …), so switching venvs or SDKMAN
layouts is a one-file change.

![folders](./puml/folders.png)

Full diagram source: [`puml/folders.puml`](./puml/folders.puml).

## Testing

The node is the unit under test: a ComfyUI node's public surface is just
`INPUT_TYPES` + `get_response(...)`, so the suite drives that contract
directly. The tricky part is that neither of the node's external
dependencies is required at test time:

- **ComfyUI runtime is not needed.** `node.py` is imported as a plain
  Python module. `pytest.ini` uses `--import-mode=importlib` and
  `--ignore=__init__.py` so the ComfyUI-discovery `__init__.py` (with
  its relative import) is skipped.
- **LM Studio is not needed.** An embedded [WireMock](https://wiremock.org/)
  server stands in for it. WireMock is launched from a jbang-backed
  Kotlin script (`api/api.mock.jbang.kt openapi start`) seeded from LM
  Studio's OpenAPI document (online first, with
  `api/openapi/spec/lm-studio.yaml` as offline fallback).

### What we test

`src/pyTest/py/al/clk/api/test_comfyui_mock.py` exercises
`LMStudioNode.get_response` with `use_sdk=False` (API path) against
the WireMock facade:

| Case                  | Checks                                                                      |
| --------------------- | ---------------------------------------------------------------------------- |
| `happy_path`          | Happy completion: content extracted, stats formatted with tokens/sec + I/O   |
| `thinking_stripped`   | With `thinking_tokens=False`, `<think>…</think>` is removed from the output  |
| `http_500`            | Server error → `"Error: …"` string, stats fall back to the node's default    |
| `request_shape`       | The HTTP request body carries model, temperature, stream=false, messages    |
| `connection_refused`  | Unreachable server → `"Connection error …"`, stats default                   |

The SDK path (`use_sdk=True`) is covered separately with `unittest.mock`
against the `lmstudio` package — it doesn't go through HTTP.

### How we test — architecture diagrams

Pre-rendered PNGs are checked into `puml/` alongside the sources.
Re-render with any of:

- **Browser (no install):** [plantuml-wasm](https://github.com/plantuml/plantuml-wasm)
  — pure-JS viewer. Paste a `.puml` file.
- **Server URL:** https://www.plantuml.com/plantuml/uml/
- **VS Code:** the *PlantUML* extension renders `.puml` inline.
- **CLI:** `java -jar plantuml.jar -tpng puml/*.puml` (requires `graphviz`
  for component diagrams).

**Component view** — what's wired to what, and what's explicitly *absent*
(ComfyUI runtime, LM Studio server):

![Test components](./puml/test-components.png)

**Sequence view** — one cold-start pytest session, end to end:

![Test sequence](./puml/test-sequence.png)

Sources: [`puml/test-components.puml`](./puml/test-components.puml),
[`puml/test-sequence.puml`](./puml/test-sequence.puml).

### How to run

Both launchers discover the ComfyUI virtualenv in `./venv`, `./.venv`,
`../venv`, `../.venv`, `../../venv`, or `../../.venv`. Override with
`COMFYUI_VENV=/path/to/venv`.

```bash
./run-tests.sh                                                         # Linux / macOS
./run-tests.sh src/pyTest/py/al/clk/api/test_comfyui_mock.py -v        # forward flags
```

```powershell
.\run-tests.ps1                                  # Windows
.\run-tests.ps1 -- -v                            # forward flags
```

First run bootstraps SDKMAN + jbang (pins in `.sdkmanrc`) and fetches the
OpenAPI spec. Subsequent runs skip the install. `SKIP_BOOTSTRAP=1`
requires a pre-running WireMock at `$WIREMOCK_URL` (default
`http://127.0.0.1:8089`).

### CI

`.github/workflows/tests.yml` runs the same `./run-tests.sh` on every
push and PR. It caches `~/.sdkman`, `~/.jbang`, and `~/.m2/repository`
so the first run installs everything (~3 min) and subsequent runs
reuse the cache (~20 s).

### Manual facade launch

```bash
source ~/.sdkman/bin/sdkman-init.sh && sdk env
jbang api/src/jbangMain/ApiMock.jbang.kt openapi start \
      --spec api/openapi/spec/lm-studio.yaml
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
