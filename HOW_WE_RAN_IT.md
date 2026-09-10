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

## Reviewer paths

- **Maya** (`maya@northwind.example`): Open Cocoa Trail Bar, generate its first screening, then use the trail hint to complete Wildflower honey `declared_allergens` and `cross_contact_allergens` as empty Tier-A arrays with a dated primary source. Generate again: the result should become `screening-ready` at 80% Tier-A recipe-weight coverage.
- **Priya** (`priya@northwind.example`): The workspace remains readable, while evidence edits, extraction, and generation are unavailable. The client still surfaces API `403` details for forbidden deep-link calls.
- **Ina** (`ina@harbor.example`): The work queue is populated entirely by tenant-scoped API responses, so only Harbor data is shown.
- **Extract review**: On Cocoa Trail Bar, choose **Extract notes**. The supplied `honey_and_oil_switch` fixture is loaded from the API. Review warnings and proposals, then either confirm an individual proposal as Tier A or deliberately apply all proposals as Tier B.
- **Pack**: Open the latest completed run from the workspace and use **Print pack**. The print stylesheet preserves the grade, coverage label, matrix, evidence and gaps.

## Product decisions

- All client state comes from the Core API. The only pre-filled text comes from `GET /v1/meta/sample-notes`, an API fixture explicitly supplied for the take-home.
- A source is mandatory for a manual patch. Manual confirmation defaults to Tier A; extract apply is visibly Tier B and never presented as a labelled conclusion.
- `unknown` is displayed as an explicit non-conclusion. Grade and coverage are always shown with their labels.
- The client sends a unique idempotency key for every screening generation and polls only while the run is queued or running. It never retries `429` responses automatically.

## Known cuts

- `agent:ask` and spec-card search are intentionally excluded. They are nice-to-have flows and must not share a visual channel with the labelled pack.
- The mock API owns persistence. Restarting it resets profile edits, runs, and usage state.
