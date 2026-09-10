# Part B - Orchestration And Sequencing

## Q1 - First fortnight

> What do you build, mock, or wait for? What is frozen by the end of week one?

**Answer:** I start with the authenticated shell, tenant context, queue, and evidence-review workspace. Those surfaces can use representative contract fixtures while ingest matures, but they do not simulate a screening outcome. The adapter, TypeScript transport types, and UI state stay separate so a stable API replaces fixtures without rewriting components.

By the end of week one, I freeze token and `/me` behavior, tenant scoping, product-bundle and PATCH shapes, screening run states, labelled grade semantics, usage, and error payloads. Ingest breadth, visual refinement, and non-blocking fields remain draft. The first stakeholder review is an evidence-review flow on staging, not a claim that an unfinished engine is ready.

## Q2 - Auth before IdP selection

> How do you sequence the app shell and identity decision without wasting the architect's time?

**Answer:** Authentication sits behind a small session boundary: obtain a token, retain it for the session, fetch `/me`, attach bearer headers, clear state on expiry, and sign out. Components consume tenant and permissions rather than provider-specific claims.

The mock passwordless endpoint exercises authorization and isolation while the cloud architect focuses on OIDC claims, redirect URLs, environments, secrets, and the identity ADR. The later change is limited to token acquisition; the permission checks, API client, and tenant tests stay in place.

## Q3 - Incomplete ingest

> What is the analyst and AI/ML handshake, and what does the day-one wizard refuse to fake?

**Answer:** The contract represents each field with value, tier, source, retrieval date, defaulted state, and gap state. The analyst owns source quality and exception reporting; AI/ML preserves uncertainty; the app turns gaps into source-backed work. The first screen is a pre-populated review, not an empty form.

I do not turn missing evidence into an empty declaration, infer safety from silence, or hide uncertainty behind a synthetic progress score. The extraction path follows the same rule: a pending spec remains unresolved, and a model proposal is filtered and presented for human review rather than silently applied.

## Q4 - Unlabelled number

> What happens before tomorrow's demo, and who agrees before a new score ships?

**Answer:** I do not add a client-calculated risk score. The demo uses the deterministic API's labelled grade, labelled Tier A recipe-weight coverage, gaps, and evidence-tiered matrix. A number without a method or owner looks precise while making the decision less defensible.

A new score needs a defined calculation, data lineage, evaluation criteria, and agreement from product, AI/ML, the domain or compliance owner, and the CTO. Its semantics belong in the versioned API contract, not in presentation code.

## Q5 - Contract change mid-sprint

> How do you handle a breaking rename in staging and prevent a repeat?

**Answer:** I treat it as an incident: restore the additive field or pin the client to the compatible version, assess the affected beta flow, and keep workarounds out of scattered components. Transport models and a single API adapter contain the immediate blast radius.

The durable control is a versioned contract, additive-only sprint changes, CI compatibility checks, explicit deprecation windows, and a named approver for breaking changes. Product terminology changes only after the API meaning is resolved.

## Q6 - 429 during a walkthrough

> What happens on the call, and how is quota policy separated from UX?

**Answer:** I explain that deterministic screening remains separate from metered LLM features and continue with an existing completed labelled pack. I do not retry a `429` in a loop. The product shows used, budget, remaining units, operation costs, and the server's detail so the operator understands what happened.

AI/ML and product own tenant quotas, reservations, and observability. UX owns a clear blocked state and a non-destructive path back to completed evidence. Retry policy is explicit user action, not an invisible client behavior.

## Q7 - Isolation bug

> What freezes, who investigates, and what proves the release is safe?

**Answer:** A cross-tenant exposure blocks release. Promotion and tenancy-related changes freeze while platform checks claims and data scoping, the application team checks session replacement and tenant-qualified query keys, and QA captures the exact account sequence, requests, storage state, and timestamps.

Release resumes only after API evidence and same-browser Maya/Ina regression tests show the root cause and its removal. The beta update states that the isolation gate is holding the release and gives a revised date without describing exposed tenant data.

## Q8 - Fractional designer

> How do you use two days of design time without creating two component sources of truth?

**Answer:** I use those sessions for workflow observation, hierarchy, accessibility, empty and failure states, and acceptance review. Engineering continues on known API and authorization paths between sessions.

The design file captures intent and decisions; coded components and tokens are the runtime source of truth. The useful measure is whether an operations lead can complete a source-backed review unaided, not the amount of cosmetic refinement completed.

## Q9 - One gate, three workstreams

> What is in the first gate, what is out, and what evidence supports the cut?

**Answer:** I separate the gate. The first one proves that an existing-tenant user can review evidence, produce a labelled pack, and print it. Completion observations, screening logs, output review, and support notes provide the evidence. Browser print CSS is enough for this stage.

Tenant provisioning, Stripe, payment recovery, and email delivery remain separate until ownership, failure handling, and support are designed. Bundling them into the same gate hides risk and delays the core workflow without proving it.

## Q10 - False peanut-free proposal

> How does agent output differ from engine output, and what release rule applies?

**Answer:** Agent and extraction output are untrusted proposals, never labelled conclusions. A peanut-free claim that conflicts with shared-line evidence is a warning and unresolved review work, not an accepted product claim. The UI keeps the assistant outside the pack, shows extraction provenance, and requires a source-backed human PATCH for Tier A evidence.

The model-output safety rule is enforced at more than one layer: prompts limit unsupported claims, the extractor filters invalid fields and inferred empty arrays, and the deterministic screening engine remains the only source of labelled grades. Evaluation includes conflicts between supplier evidence and facility shared-line evidence before any agent behavior is released.
