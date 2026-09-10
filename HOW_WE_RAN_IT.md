# How We Ran It

## What Is Included

Lotwise is a React and TypeScript desktop app over the supplied `/v1` API. It supports demo sign-in, tenant-scoped work queues, evidence review and source-backed edits, asynchronous screening, visible usage, extract review, a bounded SKU assistant, and a print-friendly labelled pack.

The app does not use client-side fixture data for tenant records, profiles, screenings, usage, extraction results, or assistant answers. The only pre-filled text is the API-provided `honey_and_oil_switch` sample note.

## Run Without Docker

This is the path used when Docker Desktop is unavailable.

```bash
ollama pull qwen3.5:4b
ollama serve
```

If `ollama serve` reports that port `11434` is already in use, Ollama is already running and does not need a second process.

In a second terminal:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In a third terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`. The frontend defaults to `http://localhost:8000`; set `VITE_API_BASE_URL` to use another API host.

Docker Compose remains supported when Docker Desktop is running:

```bash
docker compose up --build
```

## Verification

```bash
cd frontend
npm test
npm run build

cd ../backend
source .venv/bin/activate
python -m unittest discover -s tests -v
```

The frontend tests cover API error handling, permissions, tenant-qualified cache keys, aborted navigation requests, idempotency-key reuse, and the SKU-assistant request payload. Backend tests cover screening idempotency and extraction safety: review-only extraction, JSON-mode request settings, malformed field filtering, and rejection of empty evidence inferred from a pending or absent source.

The idempotency test sends the same `Idempotency-Key` twice. It verifies that the API returns one `run_id`, writes one screening meter event, and adds one usage unit.

No Playwright browser suite is included. The reviewer paths below are the manual smoke test.

## Reviewer Paths

- **Maya** (`maya@northwind.example`): Open Cocoa Trail Bar. Use the trail hint to complete Wildflower honey's `declared_allergens` and `cross_contact_allergens` as explicit empty Tier A arrays with a dated primary source. Generate another screening and inspect the labelled pack.
- **Priya** (`priya@northwind.example`): The queue and product workspaces remain readable. Editing, extraction, SKU assistant, and screening generation are disabled. A forged protected request still surfaces the Core API's `403` detail.
- **Ina** (`ina@harbor.example`): Sign in in a separate session. The queue is populated from Harbor-scoped API responses only; Northwind products do not appear.
- **Extraction**: On Cocoa Trail Bar, select **Extract notes**. The drawer loads `honey_and_oil_switch` from `GET /v1/meta/sample-notes`, then sends `POST /v1/extract` with `apply: false`. Review the summary, warnings, unresolved evidence, and proposals. **Review for Tier A** opens a fresh human source-backed PATCH flow for that field. **Apply reviewed proposals as Tier B** asks for confirmation, then PATCHes only the proposals currently visible; it does not invoke the model again.
- **SKU assistant**: On an Ops Lead or QA workspace, select **Ask about SKU**. The panel sends the selected product ID and bounded question to `POST /v1/agent:ask`. The tool trace is collapsed and the panel is explicitly not a labelled pack.
- **Pack**: Generate or open a completed screening, choose **Inspect pack**, then **Print pack**. The browser print stylesheet retains the labelled grade, coverage, matrix, gaps, and provenance.

## Evidence And Safety Decisions

- The API is the source of truth for tenant data. Login clears the query cache; query keys include the tenant ID; sign-out also clears client state.
- A manual PATCH requires a source and offers Tier A or Tier B. The UI does not offer manual Tier C.
- Extraction never auto-applies. The extractor requests bounded JSON from Ollama, limits output to four patches, and filters fields against target-specific allowlists before proposals reach the UI. Unsupported fields and empty arrays inferred from pending or unmentioned evidence are discarded.
- The local model is kept warm for ten minutes after use. Extraction has a 120-second timeout and reports an actionable model error instead of waiting indefinitely. `OLLAMA_MODEL`, `LLM_EXTRACTION_TIMEOUT_SECONDS`, and `LLM_EXTRACTION_MAX_TOKENS` are available for local tuning.
- Screening is deterministic and asynchronous. The client polls only queued or running runs. It never automatically retries `429`; the API detail remains visible.
- `unknown` is rendered as a non-conclusion. Coverage and allergen outputs retain their labels and evidence tiers. Assistant and extraction output are not labelled screening conclusions.

## Known Limits

- The mock API persists mutations, usage, runs, and idempotency keys in memory. Restarting the API resets them.
- Local extract and assistant latency depend on Ollama and the machine. `ollama ps` confirms whether `qwen3.5:4b` is resident.
- The extractor is a proposal channel. It can return warnings and unresolved evidence, but a human source-backed PATCH is required for Tier A evidence.
- Spec-card search is not exposed as a standalone frontend feature.
