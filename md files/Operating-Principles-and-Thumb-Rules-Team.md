# Engineering operating principles and thumb rules - Ramanujan's Interface

_Owner: Amit Sarkar, CTO. Audience: ICL engineering team. Update Date: 2026-07-03. Status: V0-2._

These govern every change to Ramanujan's Interface. The three principles are the constitution; the thumb rules are their tactical instantiations. When a rule and a principle conflict, the principle wins.

## The three principles

**P1 - System thinking throughout.** Name the invariants each change touches:

- The moat boundary: AGENTS author the SPEC (probabilistic, LLM-driven); LIBRARIES author the CODE (deterministic). This line is never crossed.
- Determinism: f(spec)=code is a pure function - no randomness, no timestamps, no LLM inference, no side effects, no external state in the code-generation path (ICL-1).
- Proprietary core isolation: the pattern library and generators live server-side only - never shipped to a client, never open-sourced, no client SDK (the trade-secret moat).
- Extensibility: new patterns are REGISTERED, never added by modifying the engine or existing patterns (ICL-1 claim 3).
- Quality-by-construction: every pattern passes the five gates (Nielsen usability, WCAG 2.1 AAA, <50ms render, cross-browser, 100% tests) before registration.
- Clean IP wall: ICL is a standalone entity; only ICL-owned IP is used; no third-party product code enters ICL; the spec-engine is ICL-owned; separate AWS account, separate repo, never cross-billed.
- Control plane / data plane separation (configuration vs data).
- Everything inside the platform VPC. No credentials in code, ever.
- Blast radius bounded by pipeline-stage boundaries: ingest -> spec -> generate -> emit -> deploy.
- Class A founder-only: the core algorithm, pattern library, and IFS internals are touched by the founder alone. No engineer, trainee or senior, has access.
- Agent-mediated access: every other engineer operates only through hardened agents (on-call maintenance, scaling, some feature work). The agent boundary is the security perimeter.
- No source export: hosted, running output is the default delivery; source code is never returned except through a vetted Enterprise export tier. The engine is a server-side black box.
- Additive to host platforms: integrations keep the host (e.g., Canva) as beneficiary - the host keeps the user, the hosting, and an upsell. Never extractive.

If you cannot name which invariant a change touches, you do not understand it well enough to ship it.

**P2 - Pipeline/gear-assembly impact analysis (two-stage).** Named bounded flows: ingest->spec, spec->code, emit->target, deploy. Stage 1 within-assembly; Stage 2 cross-assembly black-box. Determinism must hold end to end.

**P3 - No over-engineering, fewer moving parts, serverless-first.** Four tests: absorb by existing component; new failure mode; new IAM/SG/route; new vendor/invoice.

## The thumb rules

1. The moat boundary is sacred - LLMs/agents produce the SPEC; the deterministic engine produces the CODE. Never inject an LLM into code generation.
2. Determinism preserved - no randomness, timestamps, unseeded IDs, or nondeterministic ordering in the generation path; imports sorted; identical spec -> byte-identical code.
3. Pattern library is server-side only - generators never ship to clients, never open-sourced, no client SDK.
4. New patterns are registered, not by editing the engine or existing patterns; each passes the five quality gates before registration.
5. Spec-driven development only - a complete spec and flow review before any code (this is literally the product).
6. Clean IP wall - only ICL-owned IP; no third-party product code; the spec-engine is ICL IP; separate account, separate repo, never cross-billed.
7. Use what is available first - minimum moving parts; reuse proven patterns (re-authored), no new dependency unless required.
8. Code line limits - about 300 lines per file (excluding comments/docstrings); up to 500 if necessary; do not split just to save ~100 lines.
9. No edit of production code without approval - new functionality goes in new code, not by modifying proven production code.
10. No credentials in code or on the command line - environment variables only.
11. No over-engineering - the smallest correct change that meets the spec.
12. Control plane / data plane separation; everything inside the VPC.
13. Simplest-fix-first - analyze the narrowest possible change first; escalate only when ruled out by evidence.
14. One task, one command, one question at a time - human in the loop at every step; no bundled multi-deliverable responses.
15. No confidential or proprietary references (IFS/Banach equations, pattern generators, patent internals) in code, comments, docstrings, generated output, or customer-facing documents.
16. No function or pattern-ID rename after deployment - modify in place; a rename cascades through every spec and integration.
17. No guess - read the context first and root-cause with the whys; verify names, schemas, and patterns from working source before writing code.
18. Modern stack only - Python 3.12+ and current React/TS idioms; no deprecated usage for new or edited code.
19. No secrets or infrastructure identifiers to LLMs - and never paste the pattern-library source, the IFS/Banach equations, or generator code into an external LLM; use placeholders and substitute real values yourself.
20. Class A is founder-only - nobody else touches the core algorithm, pattern library, or IFS internals; there is no exception for seniority.
21. Engineers work through hardened agents only - for maintenance, scaling, and feature work; direct access to the core is not granted.
22. No source export by default - the API returns hosted, running output; source is returned only through the vetted Enterprise export tier.
23. Additive to host platforms - build integrations so the host profits (keeps the user, hosting, and upsell); never extractive.
24. Red-team the agents - the agent boundary is the perimeter; test what an agent can see, log, or return about Class A, and harden agent outputs.
25. Break-glass succession for Class A - maintain a sealed/encrypted continuity path (trustee, co-founder, or estate) so founder-only access is not a single point of failure.

## How we use LLMs

LLMs author the SPEC (front half), never the deterministic CODE (the moat). No change ships unless a human can defend it without the LLM. Never expose the pattern generators, IFS/Banach equations, or engine internals to any external LLM.
