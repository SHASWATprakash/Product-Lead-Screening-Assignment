# Lotwise Self-Serve App

## Run locally

1. Start the supplied Core API from the repository root:

   ```bash
   docker compose up --build
   ```

2. In a second terminal, start the web app:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open the Vite URL (normally `http://localhost:5173`). The client calls `http://localhost:8000` by default. Set `VITE_API_BASE_URL` when the API is hosted elsewhere.

## Verification

Run the idempotency contract check from the backend virtual environment:

```bash
cd backend
source .venv/bin/activate
python -m unittest discover -s tests -v
```

The check sends two generation requests with the same `Idempotency-Key`. It asserts they return the same `run_id`, add one screening meter event, and increase usage by one unit only.

## Local model performance

Extraction and the SKU assistant depend on the local Ollama runtime. Extraction requests a bounded JSON response, keeps the model resident for ten minutes after use, and fails after 120 seconds with an actionable error rather than holding the UI indefinitely. On a machine under memory pressure, wait for the first model load to finish, then use `ollama ps` to confirm `qwen3.5:4b` is resident before retrying. `OLLAMA_MODEL`, `LLM_EXTRACTION_TIMEOUT_SECONDS`, and `LLM_EXTRACTION_MAX_TOKENS` can be set for local performance testing.

## Reviewer paths

- **Maya** (`maya@northwind.example`): Open Cocoa Trail Bar, generate its first screening, then use the trail hint to complete Wildflower honey `declared_allergens` and `cross_contact_allergens` as empty Tier-A arrays with a dated primary source. Generate again: the result should become `screening-ready` at 80% Tier-A recipe-weight coverage.
- **Priya** (`priya@northwind.example`): The workspace remains readable, while evidence edits, extraction, and generation are unavailable. The Core API returns its `403` detail for any forged or replayed mutation request; the client preserves that detail in its error handling. Product navigation remains readable because `profiles:read` is allowed.
- **Ina** (`ina@harbor.example`): The work queue is populated entirely by tenant-scoped API responses, so only Harbor data is shown.
- **Extract review**: On Cocoa Trail Bar, choose **Extract notes**. The supplied `honey_and_oil_switch` fixture is loaded from the API. Review warnings and proposals, then either confirm an individual proposal as Tier A or deliberately apply all proposals as Tier B.
- **SKU assistant**: On an Ops Lead or QA workspace, choose **Ask about SKU**. The panel submits the selected product id with the question to `POST /v1/agent:ask`; its tool trace remains collapsed by default. It is intentionally separate from the labelled screening pack.
- **Pack**: Open the latest completed run from the workspace and use **Print pack**. The print stylesheet preserves the grade, coverage label, matrix, evidence and gaps.

## Product decisions

- All client state comes from the Core API. The only pre-filled text comes from `GET /v1/meta/sample-notes`, an API fixture explicitly supplied for the take-home.
- A source is mandatory for a manual patch. Manual confirmation defaults to Tier A; extract apply is visibly Tier B and never presented as a labelled conclusion.
- `unknown` is displayed as an explicit non-conclusion. Grade and coverage are always shown with their labels.
- The client retains one idempotency key per tenant and product for a generation retry and polls only while the run is queued or running. It never retries `429` responses automatically. The backend contract test verifies duplicate requests return one run and one charge.

## Known cuts

- Spec-card search remains intentionally excluded from the first pass.
- The mock API owns persistence. Restarting it resets profile edits, runs, and usage state.
