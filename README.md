# Product Lead screening — Lotwise take-home

This is a **take-home screening** for the Product Lead role: a hands-on product engineer who owns app-side delivery (React, auth, business flows) **and** orchestrates the other technical contributors against a frozen API seam.

It has two parts. Both are required.

| Part | What | Timebox (guideline) |
|---|---|---|
| **A — Build** | A React app that consumes the Lotwise Core API we provide | **5–7 hours**. |
| **B — Orchestration** | Written answers to 10 delivery / sequencing scenarios | **60–90 minutes** |

Submit a repo (or zip) with the app, a short `HOW_WE_RAN_IT.md`, and `PART_B.md`.

---

## Responsibilities of a Product Lead Engineer

1. Turns product/business requirements into a shippable self-serve surface.
2. Integrates that surface with a versioned backend API owned by someone else (the “brain” / platform side).
3. Sequences work across AI/ML, cloud/auth, data, and a fractional designer — without owning those functions.
4. Develops the React-based self-serve client-side flow (and the auth/SSO glue).

Lotwise is a **stand-in product** in an adjacent domain (food co-manufacturing allergen / spec-gap screening). It is **not** the product you would work on, it is merely a mock simulation of tasks similar to what you may encounter on the job. The *shape* is the same: ingested profiles with gaps, a deterministic labelled engine behind a REST API, an improve-loop, tenant-scoped auth, metering, and a small agentic layer that must not be allowed to mint labelled claims.

Please do not try to reverse-engineer a real product from this. Treat Lotwise as the spec.

---

## The product you are building on

**Lotwise** helps a food **co-manufacturer** (contract packer) produce a **screening-grade Allergen & Spec-Gap Pack** they can send to a brand owner before a production slot is released.

A separate (already-run) ingest job has pre-populated facilities, products, and ingredients from public filings, websites, and old spec sheets. Coverage is uneven. Some fields are Tier A (primary spec), some Tier B (public/website), some Tier C (sector default), some are **gaps**.

The Core API:

- Validates and stores those provenanced fields.
- Runs a **deterministic** screening engine (no LLM on this path) that always returns a **labelled** grade: `screening-ready` or `indicative`. It never returns an unlabelled number or an unlabelled allergen conclusion.
- Exposes an **agentic** layer (local Ollama, `qwen3.5:4b`) for unstructured-note extraction and “ask the spec brain” questions. Extraction proposes patches; a human has to confirm them as primary data before they count as Tier A.

Your job is the **self-serve app**: sign-in, onboarding / gap-fill wizard, screening dashboard, improve-loop, and the extract review flow.

### Demo tenant (your primary world)

**Northwind Co-Packing** — two sites, three SKUs. Log in as Maya.

| SKU | Why it is in the seed |
|---|---|
| Maple Pecan Granola (`prd_granola`) | Mostly complete, Vermont dedicated line. Should come back **screening-ready** (oats + pecans are ≥80% at Tier A). Sunflower oil is still gapped, so several allergen rows stay **`unknown`** — that is correct, not a bug. Happy-path dashboard + honest unknowns. |
| Cocoa Trail Bar (`prd_trail_bar`) | Boston shared peanut line, honey + oil specs missing. Starts **indicative** at 70% Tier-A weight. **Hero improve-loop:** confirm a honey spec as Tier A and the grade should flip to screening-ready (80% rule). |
| Kids Apple Oat Pouch (`prd_kids_pouch`) | Onboarding mess. Kids SKUs **block** on missing `label_claims` / `intended_market` even if recipe coverage is later fixed. |

A second tenant (**Harbor Pack**) exists so you can prove isolation. Maya must never see Rotterdam / tahini data. Ina is the Harbor user.

### Confidence tiers

| Tier | Meaning | Typical source |
|---|---|---|
| **A** | Primary | Dated supplier spec, controlled QMS SOP, lab report |
| **B** | Secondary | Website, inspection summary, unverified scan |
| **C** | Defaulted / inferred | Sector-default card. Always `defaulted: true` |
| *(gap)* | Unknown | Engine must show `unknown` / a gap — **never** a bare “safe” / “0” |

Grade rule (server-side, frozen): **screening-ready** iff Tier-A recipe-weight coverage ≥ 80% **and** there are no blocking gaps. Otherwise **indicative**.

Important: `POST /v1/extract` with `apply: true` stamps fields as **Tier B**. That will **not** by itself flip the trail bar to screening-ready. A human confirming a primary spec via `PATCH` (Tier A) will. Design the UI so that distinction is obvious. It is a feature, not a bug.

---

## What we provide vs what you build

We provide this folder: a runnable **Lotwise Core API** (FastAPI), seed data, Docker Compose (API + Ollama + `qwen3.5:4b`), and this brief.

You build a **greenfield React app**. TypeScript + Vite is the expected stack. You may use a component library (MUI, shadcn, Chakra, etc.). You may not submit a no-code prototype or a Figma-only file as Part A.

**Do not modify the screening engine or tenant isolation.** Treat `/v1` as a frozen contract you integrate with. If you genuinely cannot complete a flow without an additive endpoint, put the request in `CONTRACT_CHANGE.md` (name, payload, why) and work around it in the UI. Silent forks of the engine are an auto-fail for Part A.

Auth in the mock is passwordless: `POST /v1/auth/token` with an email from `GET /v1/meta/demo-users`. That stands in for magic-link / SSO. We still want the **app** to feel like a B2B product (session, tenant context, 401/403, sign-out), not a curl wrapper.

---

## Part A — product you should ship

A reviewer will log in as Maya and try to complete the following without reading your code. If a flow is incomplete, say so in `HOW_WE_RAN_IT.md` rather than hiding it.

### Must-have (the thin slice)

1. **Sign-in.** Email of a demo user → JWT in memory or localStorage → subsequent calls send `Authorization: Bearer`. Sign out. Show tenant name + role.
2. **Home / work queue.** Northwind’s facilities and products, with a visible hint of completeness (gap counts or status). Harbor SKUs must not appear.
3. **Product workspace.** For a selected SKU: pre-populated profile (facility + recipe + per-field tier/provenance/gap). This is the onboarding wizard’s first screen — the data is already there; the user is reviewing and completing it, not typing a blank form.
4. **Improve-loop.** `PATCH` a gapped field (ingredient, facility, or product) with a `source` string. Re-run screening. The trail-bar honey path above should be completable in the UI.
5. **Screening run.** `POST /v1/screenings:generate` is **async** (202 + `run_id`). Poll `GET /v1/screenings/{run_id}` until `completed` / `failed`. Show grade, weight coverage, allergen matrix (status **and** tier), gaps, lineage/source. **Never** display an allergen conclusion or a coverage number without its label/tier. `unknown` is a first-class state.
6. **Async + error states.** Queued/running, 401, 403 (Priya is a `viewer` — mutations must fail clearly), 404, 429 (budget), 502 (Ollama down — extract/ask only). Do not swallow the API `detail`.
7. **Metering visible.** Budget used / remaining from `GET /v1/usage`. A 429 should tell the human what happened, not retry in a loop.

### Should-have (strongly preferred if time remains)

8. **Extract review flow.** Paste sample notes from `GET /v1/meta/sample-notes` (key `honey_and_oil_switch`) → `POST /v1/extract` with `apply: false` → show proposals, warnings, unresolved → human confirms selected patches via `PATCH` as Tier A **or** apply-as-B with the consequences explained. Do not auto-apply in the background.
9. **Role-aware UI.** Priya (`viewer`) can look but cannot generate or patch. Hide or disable primary actions; still handle 403 if they deep-link.
10. **Pack view.** A print-friendly / export-preview of the latest completed run (the artefact the co-man would send the brand). It must repeat the grade label and the “indicative — verify before disclosure” idea. You do not need a real PDF library.

### Nice-to-have (only after 1–7)

11. `POST /v1/agent:ask` as a bounded “ask about this SKU” panel, with the tool trace collapsible. Keep it obviously **not** the labelled pack.
12. Isolation demo: a switcher is **not** required; signing in as Ina in a second session and seeing only Harbor is enough. A short note in `HOW_WE_RAN_IT.md` is fine.
13. Idempotency: send `Idempotency-Key` on generate and show that a retry does not double-charge.

### Out of scope

- Real SSO / Auth0 / Azure AD B2C (describe it in Part B).
- Stripe, dunning, plan upgrade (Part B).
- Building your own LLM, retraining, or replacing the engine.
- Pixel-perfect brand system. Clear hierarchy, readable provenance, and honest empty states beat decoration.
- Mobile-first. Desktop is enough.
- Persistence beyond what the API holds. API state resets when the API process restarts.

### What “good” looks like (Part A)

1. The business flow is complete and honest (gaps, tiers, async, 403/429).
2. Integration is correct (JWT, polling, tenant scoping, no labelled claims from the agent).
3. The UI is something an ops lead could use unaided for the trail-bar loop.
4. Code is structured like you would maintain it (components, types from the contract, error helper). We will not nitpick folder names.

AI-assisted coding is allowed. You still need to be able to walk us through every flow in a follow-up conversation.

---

## Running the API

### Prerequisites

- Docker + Docker Compose, **or** Python 3.12 + [Ollama](https://ollama.com) for local-dev.
- First Compose up pulls `qwen3.5:4b` (~3.4 GB). Screening itself does **not** need the model; extract / specs synthesize / agent:ask do.

### Docker Compose (preferred)

```bash
cd Product-Lead-Screening-Assignment
docker compose up --build
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/v1/openapi.json

Override the model with `OLLAMA_MODEL=qwen3.5:4b docker compose up --build` (that is already the default).

### Local, no Docker

```bash
ollama pull qwen3.5:4b
cd Product-Lead-Screening-Assignment/backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Ollama must be on `http://localhost:11434`. Env vars are in `.env.example`.

### Smoke the engine without the LLM

```bash
cd backend
python scripts/smoke_screening.py
```

Expected: granola `screening-ready` (~0.85, with some `unknown` rows because oil is gapped), trail bar `indicative` (~0.7 Tier A, peanut Tier-C cross-contact), kids pouch `indicative` with blocking gaps, Harbor tahini `screening-ready` (sesame present; only when run as that tenant).

### Quick curl

```bash
# 1. Token
curl -s http://localhost:8000/v1/auth/token \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"maya@northwind.example\"}"

# 2. Use the access_token as TOKEN
curl -s http://localhost:8000/v1/me -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:8000/v1/products -H "Authorization: Bearer $TOKEN"

# 3. Generate + poll
curl -s http://localhost:8000/v1/screenings:generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: trail-bar-1" \
  -d "{\"product_id\":\"prd_trail_bar\"}"
```

### Demo accounts

| Email | Tenant | Role | Can PATCH / generate / extract? |
|---|---|---|---|
| `maya@northwind.example` | Northwind | `ops_lead` | Yes |
| `julian@northwind.example` | Northwind | `qa` | Yes |
| `priya@northwind.example` | Northwind | `viewer` | **No** (403) |
| `ina@harbor.example` | Harbor Pack | `ops_lead` | Yes, Harbor data only |

There are no passwords. `GET /v1/meta/demo-users` lists them (take-home only — a real IdP would never do this).

### Metering costs (budget units)

| Call | Cost |
|---|---|
| `POST /v1/screenings:generate` | 1 |
| `POST /v1/specs:query` with `synthesize: true` | 2 |
| `POST /v1/extract` | 3 |
| `POST /v1/agent:ask` | 4 |
| Reads, patches, `specs:query` with `synthesize: false` | 0 |

Northwind starts at 6 / 40 used. Over-budget returns **429**. Do not retry 429 without a user action.

CPU-only Ollama is slow. Extract/ask can take tens of seconds. Show a real in-flight state; do not time the UI out at 10s.

---

## API contract (app-side view)

Interactive spec: http://localhost:8000/docs after the API is up. Summary:

| Method | Path | Perm | Notes |
|---|---|---|---|
| POST | `/v1/auth/token` | public | `{ "email" }` → JWT + user |
| GET | `/v1/me` | any authed | User, tenant, permissions |
| GET | `/v1/usage` | `profiles:read` | Budget + recent meter events |
| GET | `/v1/facilities` | `profiles:read` | Tenant-scoped |
| GET | `/v1/facilities/{id}` | `profiles:read` | Per-field provenance |
| PATCH | `/v1/facilities/{id}` | `profiles:write` | `{ "fields": { "name": { "value", "source", "tier?" } } }` |
| GET | `/v1/products` | `profiles:read` | |
| GET | `/v1/products/{id}` | `profiles:read` | Bundle: product + facility + ingredients |
| PATCH | `/v1/products/{id}` | `profiles:write` | |
| GET | `/v1/ingredients` | `profiles:read` | |
| GET | `/v1/ingredients/{id}` | `profiles:read` | |
| PATCH | `/v1/ingredients/{id}` | `profiles:write` | Default tier if omitted: **A** (human primary) |
| POST | `/v1/screenings:generate` | `screenings:run` | 202, optional `Idempotency-Key` |
| GET | `/v1/screenings` | `profiles:read` | `?product_id=` |
| GET | `/v1/screenings/{run_id}` | `profiles:read` | Poll until `completed` |
| POST | `/v1/extract` | `extract:run` | LLM. `apply: true` also needs `profiles:write`, stamps **B** |
| POST | `/v1/specs:query` | `profiles:read` | Card search; `synthesize: true` is metered + LLM |
| POST | `/v1/agent:ask` | `agent:ask` | Tool-using LLM. Not a labelled pack |
| GET | `/v1/health` `/v1/version` | public | |
| GET | `/v1/meta/demo-users` `/v1/meta/sample-notes` | public | Take-home fixtures |

Provenanced field shape (every profile field):

```json
{
  "value": ["peanut"],
  "tier": "B",
  "source": "Massachusetts inspection summary 2025-11",
  "retrieved_at": "2025-11-02",
  "gap": false,
  "defaulted": false
}
```

PATCH body:

```json
{
  "fields": {
    "declared_allergens": {
      "value": [],
      "source": "Meadowbrook Apiaries spec sheet 2026-07-02",
      "tier": "A"
    }
  }
}
```

Allergen matrix row: `allergen`, `status` (`present` | `possible_cross_contact` | `not_detected` | `unknown`), `tier` (null when unknown), `why`, `lineage`.

CORS is open for localhost. Point Vite at `http://localhost:8000`.

---

## Suggested trail-bar script (reviewer path)

Use this as your own QA checklist:

1. Sign in as Maya. Confirm three Northwind SKUs, no tahini.
2. Open Cocoa Trail Bar. See honey + sunflower oil gaps; Boston `validated_changeover_sop_id` gapped; peanut likely `possible_cross_contact` at Tier C after a run.
3. Generate screening. Grade `indicative`, coverage 0.7.
4. PATCH `ing_honey` `declared_allergens` + `cross_contact_allergens` to `[]` at Tier A with a dated source, and `spec_sheet_date`. Re-run. Grade should become `screening-ready`.
5. Optional: paste `honey_and_oil_switch` notes into extract; show that a “no peanuts” brand request is a **warning**, not a claim you print.
6. Sign in as Priya. Generate is forbidden.
7. Sign in as Ina. Only Harbor.

---

## Part B — orchestration & sequencing

Answer in `PART_B.md`. For each question: **what you would do**, **in what order**, **who you pull in**, and **one concrete experience** that informs it (product, your role, what happened). A page per question is too much; a tight half-page is enough. Bullet lists are fine. “It depends” without a recommended default is not.

You are the Product Lead for Lotwise. Counterparts:

| Role | What they own | Constraint |
|---|---|---|
| You (Product Lead) | App-side: web app, auth integration, billing/metering UX, export/pack, improve-loop. All front-end engineering. | You are the only FE engineer. |
| AI/ML Platform Engineer | Ingest pipeline, Core API, screening engine, agent/LLM abstraction, eval. | On the critical path for the engine; API contract is the seam. |
| Cloud architect | Azure tenancy, SSO/OIDC, environments, secrets. | ~4 hours/week. |
| Data analyst | Operates ingest, source exceptions, coverage. | Does not write app code. |
| Product designer | Fractional. UX review + visual quality. **Does not build front-end.** | Onboards after you have already started. |
| CTO | Architecture, labelled-output policy, gates. | Signs the “never unlabelled” rule. |

The Core API is supposed to freeze before both sides build in parallel. Ingest quality is best-effort. Screening-grade output is a gate; unaided activation (ops lead gets to a sendable pack without you on a call) is a later gate. LLM spend is metered because it is the margin line.

### Q1 — First fortnight

You start Monday. The API OpenAPI is a draft, not frozen. Designer starts in two weeks. Cloud architect is available Thursday this week and Thursday next week only. AI/ML is mid-build on the engine and does not want interrupt-driven contract churn. Data analyst is loading the first 40 facilities with messy public sources. Leadership wants “app shell + wizard on staging” at the end of next week because a founder checkpoint is booked.

Sequence the fortnight. What do you personally build vs. mock vs. wait for? What do you need frozen by Friday of week 1, and what can stay draft?

### Q2 — Auth when the IdP is not chosen

ADR for OIDC vs. passwordless vs. vendor (Auth0-style vs. Azure AD B2C) is still `[CONFIRM]`. You need authenticated tenants to test isolation and the wizard. Cloud architect has four hours this week and wants that time spent on environments, not a throwaway IdP.

How do you sequence WS-auth vs. the app shell so you do not paint yourself into a corner, and so you do not burn the architect’s hours on a prototype login?

### Q3 — Pre-populate vs. ingest reality

The wizard is supposed to open on a pre-populated profile. The analyst says 30% of fields will still be gapped at beta, and two source portals change HTML without notice. AI/ML wants you to treat missing as empty strings in the UI “for now.”

What is the handshake between you, the analyst, and AI/ML for “incomplete ingest”? What does the wizard do on day one vs. what you refuse to fake in the client?

### Q4 — Unlabelled number

A stakeholder demo is tomorrow. They ask you to show a single “allergen risk score /100” on the dashboard because buyers will not read tiers. The engine will not return that number. They suggest you compute it in the React app from the matrix.

What do you do between now and tomorrow, and what do you do after? Who has to agree before any score ships?

### Q5 — Contract change mid-sprint

You are mid-wizard. AI/ML adds a breaking rename (`grade` → `output_label`) on `/v1` “for clarity” and mentions it in Slack after merging. Your staging app is red. Designer mockups still say “grade.” A beta date does not move.

How do you handle the incident this afternoon, and what process do you put on the seam so this is not the culture?

### Q6 — 429 in a live walkthrough

During a recorded walkthrough with a brand owner, extract + three agent questions trip 429. Maya (ops) is on the call. The brand owner laughs and says “so it just… stops?”

What do you do on the call, what do you change in the product this week, and how do you work with AI/ML on budget policy vs. UX? Cite a time you had a cost/rate-limit constraint in a product.

### Q7 — Isolation bug, seven days before beta

QA logs in as Maya, then Ina, in the same browser, and sees one Harbor SKU in the Northwind list. You cannot tell yet if it is an API RLS miss, a cached JWT, or your client storing the last product id in `localStorage` without a tenant key.

Release sequencing: what do you freeze, who investigates what, what evidence you want before you call it “app” vs. “platform,” and what you tell the beta cohort if the window slips a week.

### Q8 — Fractional designer

Designer onboards for two days a week starting week 3. You have already shipped an app shell they will hate. They will not write React. You need unaided activation later, which you believe is mostly information architecture, not palette.

Working agreement: how you use those days, what you will not wait on them for, and how you avoid two sources of truth for components.

### Q9 — One gate, three workstreams

The same gate now claims: (a) Stripe test transaction provisions a tenant, (b) pack export lands in the brand’s inbox as PDF, (c) five unaided packs. You have one of you. AI/ML is still on engine accuracy. Billing vendor is chosen but not integrated. Export is “standards-based later; for now a print stylesheet.”

Cut or sequence. What is in, what is explicitly out, what evidence you will actually put on the gate, and how you say no.

### Q10 — Agent proposes a false “peanut-free”

Extract returns a patch `declared_allergens: []` on the Boston trail bar and a summary that “Northwind can support a peanut-free claim.” The notes only said the *pecan supplier* has no peanut. Facility shared-line peanut is still gapped SOP.

How should the product treat agent output vs. engine output? What UX and what release rule would you add? What similar failure have you seen when a model was allowed to speak in a labelled channel?

---

## How we review

Part A is a working app against this API, not a slide deck. Part B is how you will actually run a programme with four other specialists and a frozen seam.

We will look at the trail-bar improve-loop, honesty of labels, 403/429, and whether the agent is fenced off from the pack. Then we will read Part B for sequencing, defaults under ambiguity, and whether your experience is specific.

If something is unfinished, list it. Ghosted requirements score worse than a named cut.

---

## Questions

If the brief is ambiguous, document the assumption in `HOW_WE_RAN_IT.md` and proceed. That is closer to the job than waiting for a perfect spec.
