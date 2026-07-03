# Ramanujan's Interface — project root
Deterministic UI-development platform (ICL). Engine: Ramanujan Engine™. Patent: ICL-1.

## Layout
- `engine/`   — spec-core: spec_parser, component_mapper, pattern_library (the deterministic core)
- `libs/`     — design-tokens, emitters (web/html/native), ingest adapters (figma/canva/vision), quality-gates, commercial-core
- `agents/`   — spec-author, ingest, token-extract, spec-repair, verify, orchestrator (author the SPEC, never the code)
- `api/`      — hosted API layer (POST design|spec -> code)
- `specs/`    — YAML specifications
- `build/`    — build outputs
- `scripts/`  — dev/deploy tooling
- `assets/`   — static assets

Moat rule: the pattern library / generators stay server-side, never shipped to clients.
