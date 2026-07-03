# Ramanujan's Interface - Master To-Do List

_Intelligent Cloud Lab | print-and-tick checklist | 2026-07-02_

## 0. Project setup, IP & infrastructure

- [ ] Initialize git repo in Ramanujn's-Interface/ (product root)
- [ ] Configure separate ICL AWS profile (aws configure --profile icl) — new account, never cross-billed
- [ ] Migrate domain intelligentcloud.guru from old AWS account to new ICL account
- [ ] Keep pattern library / generators server-side only (no client SDK, never open-source) — moat rule
- [ ] Build the commercial shell fresh in ICL - use no third-party product code
- [ ] Convert ICL-1 provisional patent -> utility filing (keep IFS/Banach equations filed, not published)
- [ ] Founder-only: complete marketplace / seller registrations (legal entity, tax, banking)

## 1. Deterministic engine - spec-core (LIBRARIES: author the CODE)

- [ ] Package existing spec-engine (spec_parser.py, component_mapper.py, pattern_library.py, spec-schema.json) into engine/
- [ ] Prove f(spec)=code running in the new ICL home (parse sample YAML -> emit React)
- [ ] pattern-lib-web: package the 16 live patterns (L-01..L-06, C-01..C-10)
- [ ] Add complex component patterns: image, heading/text, nav bar, hero section, feature grid
- [ ] Expand pattern library from 16 -> 58 patterns (D/E/S/V/A/F/I/X categories) as demand dictates
- [ ] quality-gates library: accessibility (WCAG) + performance checks, guaranteed by construction
- [ ] verify-preview library: headless-Chrome render + visual diff (reuse existing pipeline)
- [ ] commercial-core: build ICL's own auth / api / turnstile / bot-protection

## 2. Design fidelity & ingest libraries

- [ ] design-tokens library: extract colors / fonts / spacing -> CSS (so output LOOKS like the design)
- [ ] ingest-figma: Figma REST/MCP -> normalized design tree
- [ ] ingest-canva: Canva Connect export -> normalized (lower priority; autofill is Enterprise-gated)
- [ ] ingest-vision: any custom graphic (PNG/JPG) -> layout structure (hardest; the 'any graphic' unlock)

## 3. Multi-target emitters (framework-agnostic + mobile)

- [ ] pattern-lib-html: deterministic HTML/CSS emitter
- [ ] pattern-lib-native: React Native / Expo emitter (the 'mobile app' output)
- [ ] (reference only) study Builder.io Mitosis for one-IR -> many-frameworks (do NOT put in the engine)

## 4. Agents (author the SPEC, never the code)

- [ ] ingest-agent (vision): Figma / Canva / graphic -> structured design description
- [ ] spec-author-agent (CORE): design or prompt -> valid YAML spec (schema-constrained, few-shot from reference specs)
- [ ] token-extract-agent: design -> theme tokens (feeds design-tokens)
- [ ] spec-repair-agent: validate + auto-fix spec against schema
- [ ] verify-agent: render vs source visual diff -> feedback loop
- [ ] orchestrator-agent: MCP tool running ingest -> spec -> generate -> verify
- [ ] pattern-proposal-agent: unmapped element -> propose new pattern (human-reviewed) [later]

## 5. API & commercial layer

- [ ] API layer: POST design|spec -> code (the a-UI-01 / hosted endpoint)
- [ ] API-key authentication + rate limiting
- [ ] Usage metering
- [ ] Stripe metered / subscription billing
- [ ] Landing page + docs + self-serve signup (build ICL's own UI core)
- [ ] Pricing tiers: indie $29-49 / Pro $99 / Agency $199+ (protects the $99 blended ARPU)
- [ ] (Phase 2) subscription hosted model (multi-tenant hosting + per-customer deploy) - DEFER

## 6. Hosting & deploy

- [ ] Stand up ICL EC2 / Lambda + API Gateway
- [ ] nginx config for static React sites
- [ ] Deploy pipeline (build -> server -> CDN/CloudFront invalidate)
- [ ] Monitoring / alarms

## 7. Cloud marketplaces (OUR side by Aug 15; approval time is external)

- [ ] Research + pick a marketplace-enablement layer (Tackle / Suger / Clazar / Labra) - one integration, not three
- [ ] FILE GCP Marketplace partner application FIRST (approval-gated even to start building)
- [ ] AWS Marketplace: seller registration + metering integration + listing content
- [ ] Azure Marketplace: Partner Center + SaaS fulfillment API + listing content
- [ ] GCP Marketplace: procurement API integration + listing content (after partner approval)
- [ ] Submit all three (our side) by Aug 15

## 8. WP -> React migration (first use cases = dogfood + case studies + alpha)

- [ ] Restart one WordPress instance briefly OR locate DB/XML backups (content access)
- [ ] Confirm each site type: brochure/marketing (easy) vs dynamic (forms / WooCommerce / membership)
- [ ] Site #1 (semi-manual): build & validate spec-core + ingest + design-tokens against it
- [ ] Per site x6: extract content (WP REST /wp-json or XML export)
- [ ] Per site x6: capture design -> screenshot -> vision-ingest -> SPEC (or map to L/C patterns)
- [ ] Per site x6: extract theme tokens (colors / fonts) -> design-tokens
- [ ] Per site x6: generate React via engine + populate content
- [ ] Per site x6: deploy to nginx on ICL EC2
- [ ] Write case studies: migration speed, cost savings (WP servers -> static), perf/SEO gains
- [ ] Capture the speed-up curve (Site 1 days -> Site 6 hours) as the headline metric

## 9. Launch milestones

- [ ] Aug 1, 2026 - ALPHA on Product Hunt + similar (lean metered API: YAML->code + Stripe + landing; NO Figma/hosted/mobile in alpha)
- [ ] Aug 15, 2026 - our side of AWS/Azure/GCP marketplace listings submitted
- [ ] Sept 1, 2026 - full marketing launch (Pune agency)
- [ ] Mar 31, 2027 - reach 10,000 subscribers (1/3 of target; 30k x $99/mo = ~$3M/mo target)

## 10. Moat & IP protection

- [ ] Legal lock: ICL-1 utility conversion; keep equations filed not published
- [ ] Technical lock: pattern library 100% server-side; no client SDK; never open-source
- [ ] Compounding lock: data flywheel - log every ingested design to improve agents + grow token/spec corpus

## 11. Team, offshore & personal

- [ ] Final interviews of ~10 developers (HR does strict vetting first)
- [ ] Plan & prepare short-term family relocation to Pune

## 12. Marketing (SEPARATE TRACK - not built here)

- [ ] Handled by marketing firm + Google tools, own plan & budget
- [ ] Reference only in this project; do not build marketing assets in the engineering lane

## 13. Delivery model - no source export (current plan)

- [ ] Default delivery = hosted running result via API; NEVER return source code (except vetted Enterprise export tier)
- [ ] Position as deterministic math-based UI API that replaces the probabilistic LLM call
- [ ] Reject client-side DRM/encryption; protect by keeping engine server-side

## 14. Hosted site architecture (hybrid serverless)

- [ ] Static site served from S3 + CloudFront (on-demand build container, torn down when idle)
- [ ] Contact form: static form + Cloudflare Turnstile -> API Gateway -> one generic SMTP-relay Lambda
- [ ] Email offloaded to reseller's own SMTP; write setup docs for ~12 providers (SendGrid, SES, GoDaddy, etc.)
- [ ] "Post to your own endpoint" mode, automated by an agent
- [ ] Chat widget calls reseller's own LLM endpoint directly (zero chat cost/liability)
- [ ] Reseller connects own domain (CNAME to CloudFront); managed DNS = paid add-on
- [ ] Confirm target ~$1-2/site all-in, ~90% gross margin at $99

## 15. Canva Premium App - the beachhead (Canva sells it)

- [ ] Build narrow, delightful in-editor app: "turn your Canva design into a real website" (one-click)
- [ ] Ingest via Canva Design Editing API (structured design -> high fidelity)
- [ ] Keep export/upload fallback (non-dependent; serves non-Canva users too)
- [ ] List via Canva Premium Apps Program (Canva markets, bills, revenue-shares)
- [ ] Design flow ADDITIVE - output stays in Canva ecosystem (Canva keeps user + hosting + upsell)
- [ ] Free-to-try -> premium funnel to drive installs + ratings
- [ ] Seed reviews/installs from WP case studies + first creator-resellers
- [ ] Keep non-Canva channels live so slow approval can't stall launch
- [ ] (Earned, later) OEM/embed deal for native my.canva.site output

## 16. Pricing & upsell ladder (Macy's, not dollar store)

- [ ] Anchor tier: $99 premium; NOT a race to the bottom vs Canva free Websites
- [ ] Build upsells from day one: e-commerce/store, multi-site, custom domain + pro email
- [ ] Advanced functionality: booking, memberships, CRM/forms, analytics
- [ ] AI features add-on (chat/agent, content, SEO)
- [ ] Traffic/bandwidth tiers; priority support/SLA; managed "keep it fresh" updates
- [ ] Agency/team seats + white-label (highest ACV)
- [ ] Target NRR > 100% (grow MRR, not just logos)

## 17. Internal moat & agent hardening

- [ ] Class A (core algorithm, pattern library, IFS) = FOUNDER-ONLY; no engineer touches it
- [ ] All engineers (trainee or senior) operate through hardened agents (on-call, scaling, features)
- [ ] Wall Class A off from the trainee/senior repo entirely
- [ ] Red-team the agents themselves (what can they see/log/return about Class A?)
- [ ] Break-glass succession envelope for Class A (sealed/encrypted access; bus-factor mitigation)
- [ ] API-surface defenses: rate limits, enumeration/anomaly detection (IDS/IPS agent), per-tenant sets, output fingerprinting

## 18. Go-to-market & business plan (current)

- [ ] Canva Premium App launch: first week of August
- [ ] Full product (APIs + features) complete by mid-August (excl. marketplace approval)
- [ ] Relocate to India mid-August
- [ ] Sign India web-design/marketing firm as first reseller + marketing arm (barter or paid)
- [ ] Stand up YouTube channel + ads (studied YouTube/Google algorithm approach)
- [ ] 4-person offsite marketing team (~$2k/mo) + ~$3k ads; ~$5k initial push
- [ ] Recruit Canva-ecosystem creators (educators, VAs, template sellers, small agencies) as resellers
- [ ] Hold M/E ratio ~6 (product built -> distribution is the bottleneck); reinvest all margin

## 19. Validation gate & reliability (first 1,000)

- [ ] Instrument from customer #1: conversion by channel, churn/retention, NRR/expansion, CAC by channel
- [ ] First 1,000 paying at $99 = validation gate; scale what converts
- [ ] Target ~$1M/month combined within 6 months of hitting 1,000 (target, not forecast until validated)
- [ ] Senior anchor (founder + AI review) for reliability/security/incident response (hosted = critical infra)
- [ ] India trainee hiring: walk-in interviews; ~$10k for 4 trainees / 6 months for feature work via agents

