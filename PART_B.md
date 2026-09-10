# Part B — Orchestration & Sequencing

## Q1 — First fortnight

> Sequence the fortnight. What do you personally build vs. mock vs. wait for? What needs to be frozen by Friday of week 1, and what can stay draft?

**Answer:** I build the authenticated shell, navigation, and profile-review workflow against versioned fixtures rather than wait for ingest to be complete. On enterprise mobile projects with evolving backend services, I have used TypeScript interfaces and realistic API responses so frontend work, UX review, and testing continue independently. Once the contract stabilises, the adapter replaces those fixtures without a component rewrite.

By Friday of week one, I need auth token and `/me`, tenant-scoped list and product-bundle shapes, PATCH payloads, screening lifecycle, labelled-grade semantics, and error payloads frozen. Visual polish, non-blocking ingest fields, and the designer's refinements stay draft. The founder checkpoint gets a staging shell and profile-review wizard, not a simulated screening claim.

## Q2 — Auth when the IdP is not chosen

> How do you sequence WS-auth vs. the app shell so you do not paint yourself into a corner or burn the architect's hours on a prototype login?

**Answer:** Authentication sits behind a session service that owns token acquisition, storage, `/me`, logout, bearer-header injection, and expiry handling. I have used this separation where authentication and backend integration requirements changed during delivery. Components depend on current permissions and tenant context, not the identity provider.

The mock passwordless endpoint supports isolation and wizard testing now. The cloud architect's limited time stays focused on environments, secrets, redirect URLs, OIDC claims, and the ADR. When the IdP is selected, token acquisition changes inside the adapter; authorization UI, API interceptors, route guards, and tenant-isolation tests remain intact.

## Q3 — Pre-populate vs. ingest reality

> What is the handshake between you, the analyst, and AI/ML for incomplete ingest? What does the wizard do on day one, and what do you refuse to fake in the client?

**Answer:** Uncertainty belongs in the domain model, not as an implementation detail. In healthcare-oriented work, I have treated source, validation state, and data availability as meaningful because incomplete clinical information changes what the UI can safely communicate.

The analyst reports source exceptions and coverage by tenant. AI/ML preserves absent evidence as a gap. The app starts with available evidence and directs the user to source-backed completion. I do not convert missing values into empty strings, imply safety, or introduce a progress metric that hides uncertainty.

## Q4 — Unlabelled number

> What do you do between now and tomorrow, and what do you do after? Who has to agree before any score ships?

**Answer:** I do not calculate a client-side risk score for a demo. In AI and healthcare-oriented systems, I have preferred validated backend output, evidence, and confidence or coverage information over invented presentation-layer metrics. A number looks authoritative even when its method is undefined.

For the demo, the dashboard shows the labelled grade, Tier-A coverage, gaps, and the reason behind each matrix row. A future score requires agreement from the CTO, AI/ML, the domain or compliance owner, plus an explicit calculation, evaluation criteria, and API-level semantics.

## Q5 — Contract change mid-sprint

> How do you handle the incident this afternoon, and what process do you put on the seam so this is not the culture?

**Answer:** A staging break from a rename is an incident. The immediate response is to restore compatibility or pin the client to the last supported contract, not spread a workaround through the UI. I have worked with REST and GraphQL integrations where backend changes affected multiple clients; transport models behind adapters keep that blast radius contained.

The seam needs a versioned OpenAPI contract, additive-only changes during a sprint, compatibility checks in CI, deprecation windows, and a named approver for breaking changes. Designer terminology changes only after the API meaning is agreed.

## Q6 — 429 in a live walkthrough

> What do you do on the call, what do you change in the product this week, and how do you work with AI/ML on budget policy versus UX?

**Answer:** On the call, I explain that inference capacity is controlled separately from deterministic screening and continue with the completed labelled pack. I have designed around rate limits and expensive backend or AI operations using throttling, caching, queues, and controlled retries. Repeated retries are the wrong response to a quota signal.

The product shows remaining units and operation cost before submission, preserves the API's 429 detail, and offers a non-destructive route back to completed results. AI/ML and product agree tenant quotas, reservation policy, and usage telemetry. Exponential backoff can suit transient failures; a 429 requires a clear budget policy and explicit user action.

## Q7 — Isolation bug, seven days before beta

> What do you freeze, who investigates what, what evidence do you need before calling it app versus platform, and what do you tell the beta cohort if the window slips?

**Answer:** Cross-tenant exposure is a release blocker. In multi-tenant healthcare architecture work, I have focused on enforcing tenant context at authorization and data-access boundaries instead of relying on frontend filtering.

Promotion and tenancy-related changes freeze. Platform checks RLS, tenant claims, and API responses; the app team checks token replacement, cache keys, and client storage; QA captures the account sequence, requests, responses, storage state, and timestamps. Release resumes only after automated same-browser Maya/Ina tests and backend evidence demonstrate isolation and the root cause is understood. If beta slips, I state that the release is held at the tenant-isolation gate and share the revised date without exposing affected data.

## Q8 — Fractional designer

> How do you use the designer's two days, what do you not wait on, and how do you avoid two sources of truth for components?

**Answer:** I use limited design time for workflow validation, information hierarchy, accessibility, edge states, and acceptance review. I have worked in delivery environments where engineering continued while specialist availability was constrained. Between sessions, implementation moves forward through reusable components and established design tokens.

The design file captures intent and decisions. The coded component system remains the runtime source of truth. I do not wait for a designer to start API integration, authentication, or known error states. The measure is an operations lead completing the flow unaided, not a backlog of visual polish.

## Q9 — One gate, three workstreams

> Cut or sequence. What is in, what is explicitly out, what evidence goes on the gate, and how do you say no?

**Answer:** I split this into separate gates. On large enterprise applications, I have found that combining unrelated dependencies into one release gate increases risk without proving the core experience. The first gate proves that five users can complete the existing-tenant workflow and produce a correct labelled, printable pack. A print stylesheet is sufficient at this stage.

Stripe provisioning and email delivery stay out until tenant creation, payment failure handling, delivery ownership, and support are designed and staffed. The decision rests on completion evidence, output validation, logs, and user observation, rather than an all-or-nothing launch metric that hides where the product fails.

## Q10 — Agent proposes a false peanut-free claim

> How should the product treat agent output versus engine output? What UX and release rule do you add?

**Answer:** In my AI and RAG work, I treat model output as probabilistic rather than authoritative. A peanut-free claim cannot become labelled truth because an agent generated it. The product retains the proposal and provenance, shows it as unverified, and requires human confirmation against source evidence before a PATCH makes it authoritative.

Agent output stays outside the labelled pack. The supplier-specific versus facility-wide evidence conflict belongs in the evaluation suite. An agent feature does not enter release until it passes that evaluation and review by AI/ML, product, and the labelled-output policy owner. The release rule is simple: model output cannot enter a deterministic or compliance-sensitive report without source-backed confirmation.
