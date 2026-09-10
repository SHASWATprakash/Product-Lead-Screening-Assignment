# Part B — Orchestration & Sequencing

## Q1 — First fortnight

Build the authenticated app shell, navigation, static profile-review layout, and API adapter against a versioned draft by mid-week. Use representative API fixtures rather than waiting for ingest completeness. By Friday, freeze auth token/me, tenant-scoped list and profile bundle shapes, PATCH fields, screening run lifecycle, grade labels, and error payloads. The designer can review a working shell in week three; the analyst owns coverage exceptions; AI/ML owns the frozen contract. The founder checkpoint gets staging navigation and a profile-review wizard, not a simulated screening claim.

**[ADD YOUR EXPERIENCE: a deadline where you staged a usable shell around an unfinished platform dependency.]**

## Q2 — Auth before IdP selection

Place authentication behind a small client session interface: exchange credentials, store a token, fetch the current principal, and attach bearer headers. Use the mock passwordless endpoint for tenant/isolation testing, while the cloud architect spends their limited time deciding identity boundaries, redirect URLs, environments, secrets, and OIDC claims. Replace only the token-acquisition adapter after the ADR; retain session, authorization, and tenant tests.

**[ADD YOUR EXPERIENCE: an auth or identity migration where an abstraction avoided client rewrites.]**

## Q3 — Incomplete ingest

Agree on a field-level contract: every field is a value with tier, source, retrieval date, gap and defaulted status. The analyst reports source exceptions and coverage by tenant; AI/ML preserves gaps as gaps; the app makes missing evidence actionable. On day one, the wizard starts from existing evidence and asks for source-backed completion. Do not turn missing values into empty strings, infer safety, or manufacture a progress score that hides uncertainty.

**[ADD YOUR EXPERIENCE: a data-quality issue where visible uncertainty changed the product decision.]**

## Q4 — Unlabelled number

Decline to calculate a client-side risk score for the demo. Show the server-provided labelled grade, coverage and gap breakdown instead, with a short explanation of how they work. After the demo, record the request as a product/clinical-policy decision and require CTO, AI/ML, domain/compliance ownership, and an evaluation plan before a new score enters the API contract.

**[ADD YOUR EXPERIENCE: resisting a misleading metric or risk score under presentation pressure.]**

## Q5 — Breaking contract change

Treat the staging failure as an incident: pin the app to the last compatible API version or immediately restore the additive field, assess beta impact, and update the designer’s terminology only after the API meaning is resolved. Establish contract ownership: versioned OpenAPI, additive-only changes during a sprint, CI compatibility checks, written deprecation windows, and a named approver for breaking changes.

**[ADD YOUR EXPERIENCE: a breaking dependency change and the control you introduced afterward.]**

## Q6 — 429 during walkthrough

On the call, explain that the inference budget is a deliberate control, keep the labelled pack separate from LLM features, and continue with the existing completed screening rather than retrying. This week, show remaining units and operation costs before submission, preserve the API detail on 429, and add a non-destructive path back to completed evidence. Agree with AI/ML on tenant quotas, reservation policy, and observability; product owns clear human messaging.

**[ADD YOUR EXPERIENCE: a cost, quota, or rate-limit constraint you designed around.]**

## Q7 — Isolation bug

Freeze beta promotion and all tenancy-related changes. Split investigation: platform checks tenant scoping and claims; app checks token replacement, cache invalidation, and tenant-qualified client storage; QA captures reproducible requests, responses, storage state, and timestamps. Release only after automated same-browser Maya/Ina tests and backend evidence prove the root cause. Tell the beta cohort the isolation gate is non-negotiable, explain the revised date, and avoid exposing any affected data details.

**[ADD YOUR EXPERIENCE: an authorization or data-isolation incident and how you coordinated its containment.]**

## Q8 — Fractional designer

Use the designer’s two days for workflow observation, information hierarchy, edge-state critique, and acceptance review of a maintained component inventory. Continue implementing known flows between sessions. The frontend owns coded components and tokens; the design file expresses intent and review decisions, not a competing source of runtime truth. Prioritize unaided activation tests over cosmetic revision.

**[ADD YOUR EXPERIENCE: working effectively with a fractional design partner.]**

## Q9 — One gate, three workstreams

Split the overloaded gate. First prove five unaided users can produce a labelled, printable pack from an existing tenant; print CSS is sufficient evidence for the export path. Keep Stripe provisioning and email delivery explicitly out until tenant creation and delivery ownership are designed and staffed. Report the cut with evidence: completion recordings, support observations, screening logs, and labelled-pack review rather than a single aspirational launch metric.

**[ADD YOUR EXPERIENCE: reducing an over-combined launch gate to protect a critical outcome.]**

## Q10 — False peanut-free proposal

Treat agent output as an untrusted proposal channel. Display its warning and provenance, require human source-backed PATCH confirmation, and prohibit it from appearing in the labelled pack or being framed as a facility/product claim. Add an evaluation case for supplier-specific evidence versus facility shared-line evidence, and block release of any agent feature until it passes that case and review by AI/ML, product, and the labelled-output policy owner.

**[ADD YOUR EXPERIENCE: a model or automation overclaim and the release control it led to.]**
