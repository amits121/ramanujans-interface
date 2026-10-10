# Ramanujan's Interface productization plan

Goal 2 of two: productize the deterministic UI engine for sale through resellers in India, starting with the founder's own website as the first use case.

Owner: Amit Sarkar, Founder, Intelligent Cloud Lab Inc. Date: 2026-10-07. Status: draft for the founder's rulings. Updated 2026-10-08 after phases 1 and 2; updated 2026-10-10 with the web host ruling. Proprietary and confidential; internal only. Capability-level language throughout; no method or mathematics appears in this document or in any material derived from it.

## 1. Purpose and sequence

One engine, sequenced use cases (base plan note of 2026-08-26): the UI development tool first, then the merchant site engine, the agency channel and the enterprise UI channel.

Ruling of 2026-10-07: this goal starts first. The internal consumer platform joins later through the same API under the enterprise tier.

Ruling of 2026-10-08 (F-1 decided): site number one is the innovation movement site, a separate brand from the company, on the domain inovations.techinnovations.io as written by the founder. The company's main site stays exactly as it is.

Ruling of 2026-10-10: site number one is served from an EC2 web host in the company's AWS account, nginx serving the engine's pre-rendered static output, not from S3 and CloudFront. The web host is the first server and is set up before the site specification is authored. The domain is techinnovations.io, which the founder owns; the host label is decision F-7.

Reseller channel in India per Offer 3, extension A: one-to-five-person web agencies serving local MSMEs in local languages; a platform house as the anchor later. Every offer and conversation is from Intelligent Cloud Lab Inc, US only.

Nothing here changes the product decisions of July 2026: hosted delivery, no source export by default, server-side engine, founder-only core, Canva as the separate global track.

## 2. Where the engine stands (state check 2026-10-07)

The prototype. Parser, mapper, pattern library with 16 patterns (6 layouts, 10 components), the schema, two sample specifications and two generated screens, built 2025-12-15 and acid-tested on a test server. React output on the Amplify component base.

Not yet a product. The code is not in the product repository, which holds only the folder scaffold. The generated header still carries a timestamp, so step 1 of the determinism sequence is open. There are no design tokens, no CSS, no validation, API or complex-component patterns, no tests and no packaging.

Ready inputs. The design-token and component specification set of December 2025 (colors, typography, spacing, shadows and radii; 17 global component files; 13 screen files); the designer's section library (header, footer, hero, feature cards, authentication pages); the ICL-1 provisional filed in February 2026 with the 58-pattern taxonomy; the master to-do list; the hosted architecture and delivery decisions.

Clocks. The utility conversion of the February 2026 provisional falls due on 2027-03-01. Public material stays at capability level until the founder rules otherwise.

Update 2026-10-08, phase 1 complete. The engine is in the product repository under engine/ (commit 16c3699). Determinism steps 1 to 5 are done: version in the header instead of the clock, pure rendering, fixed section order, one pure generate call returning code, content hash and cache key, pattern library 1.0.0. Six golden tests pass, including two fresh processes giving identical bytes and the recorded golden hashes matching. The originals in the backup tree are untouched.

Update 2026-10-10. Pattern library 1.2.0: 96 registered patterns across six targets, the determinism gate, the quality gates, the preview with phone emulation, the local artifact cache and the library repository with its CI gate (commits ae7079c, fed24e3, 488b4b9). Engine and library suites: 31 tests green on 2026-10-10.

## 3. Product definition (unchanged, restated for execution)

A hosted deterministic UI service. The language model authors the specification; the engine authors the code; identical specifications give byte-identical output. Default delivery is a running hosted site. Source is returned only through the enterprise tier.

Hosted site: static files on S3 and CloudFront; contact form through Turnstile to API Gateway to one SMTP relay function using the reseller's own mail provider; chat widget calling the reseller's own model endpoint; custom domain by CNAME. All-in cost about one to two dollars per site per month. Site number one runs on the EC2 web host of section 6; the S3 and CloudFront layout is the design for reseller volume (F-10).

The engine runs server-side only. The API returns a rendered artifact, its content hash and a hash-chained log entry. Emitted code looks hand-authored. The core is founder-only. The hardware-isolated core comes when paying customers justify it; nothing is over-built before that.

## 4. Work plan, engine and first site (founder, core)

| Phase | Window | Work | Exit |
|---|---|---|---|
| 1 Determinism and packaging. DONE 2026-10-08 | 2026-10-08 | Engine files and specifications moved into the product repository; timestamp removed; rendering pure; ordering pinned; golden byte-equality test; one pure generate call behind pattern library 1.0.0 | Met: same specification twice, same and fresh process, identical bytes and a stable content hash; commit 16c3699 |
| 2 Site patterns and tokens. DONE 2026-10-08 | 2026-10-08 | Design-token library from the December 2025 token specification to CSS variables; the ten site patterns registered (image, text block, navigation bar, hero, feature grid, footer, contact form, call-to-action band, testimonial, FAQ) plus the page layout; static target with no component framework; shell and pre-render so a site is plain HTML and CSS with no script | Met: ten patterns with render and accessibility checks; sample site builds to 3.5 KB of HTML and 6 KB of CSS; a second build is byte-identical; 14 tests green; pattern library 1.1.0 |
| 2b Web host | 2026-10-10 to 10-12 | The EC2 web host in the company account per section 6: security group, instance role, sites bucket, instance launched with the bootstrap script, Elastic IP, DNS record, certificate; first deploy of the sample site through scripts/deploy_site.py | The sample site answers over HTTPS on its host name; a second deploy leaves the served bytes identical to the build (E-2a) |
| 3 The innovation movement site | 2026-10-13 to 11-05 | Specification authored from the movement's brand inputs (theme line, hierarchy, summit date) and the designer library; generated; deployed to the web host; Turnstile contact form; the host name on techinnovations.io by an A record to the Elastic IP; regeneration recorded with its content hash | Site live on its host name; demo-ready for the Pune summit (tentative 2026-11-14): design to live site in minutes |
| 4 API shell | 2026-11-12 to 11-30 | API Gateway and a front-door function to the private engine host; API keys; per-tenant metering; signed responses; hash-chain log to S3; rate limits; a minimal reseller console to submit a design or specification and receive a hosted URL | A second tenant generates a site with its own key; a metering row is written; the signature verifies |
| 5 Ingest and language | December | Structured ingest first (Figma and Canva exports) to a specification draft; the specification-author agent; token extraction; regional-language text and fonts through the specification | A Canva or Figma export becomes a live site without hand edits |
| 6 Reseller pilot | December to January | Three agencies in Pune, ten sites each, Rs-scale pricing test, case studies; platform-house conversations with live sites as proof; Vibrant Gujarat January 2027 | Thirty sites live; median design-to-live under one day; zero hand edits |

## 5. Hosting and tenancy for resellers

Reseller account, then sites, then versioned specifications, then artifacts keyed by content hash. Each site is an S3 prefix behind CloudFront with its own certificate for the custom domain; a single multi-tenant distribution with host routing is the cost option once sites number in the hundreds. Site number one runs on the EC2 web host; the layout above is the design for reseller volume.

Metering per generation and per site-month. Stripe for global billing. India invoicing through the platform house or the resellers; the company sells from the US entity, and any India structure remains internal planning until a signed deal requires it.

Pricing: the global anchor stays at 99 dollars; India at Rs 499 to 999 per site per year through platform and reseller channels, with the reseller's margin on top and the upsell ladder (store, multi-site, domain and mail, booking and forms, managed updates, white label).

Support: resellers own their customers; the company supports resellers; hosting carries the SLA.

## 6. Infrastructure in the company account

Engine host (phase 4): one small EC2 instance in a private subnet, no public IP, Session Manager only, founder access only, engine code encrypted at rest. Front door: API Gateway and a validation, authentication and metering function, through a VPC link to the engine. Logs to S3, not CloudWatch, at volume. Until phase 4 the engine stays on the founder's Mac and builds run there; the web host never carries the engine, the pattern library or the mathematics, it serves built files only.

Development in us-east-1 per the compute strategy; hosted sites are served worldwide by CloudFront, which has edge locations in India, so no second region is needed for the sites.

Later: the hardware-isolated core per the July 2026 design, when there are paying customers.

Web host for site number one (ruling 2026-10-10). What the account holds, read on 2026-10-10 under the founder's profile icl-2 (account 359428598413, us-east-1): the VPC ICL-2-vpc (10.0.0.0/16) with the public subnets ICL-2-subnet-public1-us-east-1a and public2-us-east-1b routed to the internet gateway, two private subnets routed only to an S3 endpoint, no NAT gateway; no instances, Elastic IPs, key pairs, custom security groups or roles; one bucket (icl-rag-staging). No hosted zones in this account. The founder runs the steps below on the console; the session supplies the values and the scripts and verifies read-only.

| Step | Console action | Values |
|---|---|---|
| 1 Security group | EC2, Security groups, create icl-web-sg in ICL-2-vpc | Inbound HTTP 80 and HTTPS 443 from 0.0.0.0/0 and ::/0; no port 22; outbound all |
| 2 Instance role | IAM, Roles, create icl-web-host for EC2 | Managed policy AmazonSSMManagedInstanceCore plus an inline policy allowing s3:ListBucket on the sites bucket and s3:GetObject on its objects |
| 3 Sites bucket | S3, create icl-sites-359428598413 in us-east-1 | Block all public access; versioning on; default encryption |
| 4 Instance | EC2, Launch instance, name icl-web-host | Amazon Linux 2023, arm64 (ami-065b1b834d2a83a7a on 2026-10-10); t4g.micro; proceed without a key pair; VPC ICL-2-vpc, subnet ICL-2-subnet-public1-us-east-1a, auto-assign public IP enabled; security group icl-web-sg; 20 GB gp3, encrypted; IAM instance profile icl-web-host; metadata version 2 required; user data: scripts/server/web-host-user-data.sh with HOST, SITE and BUCKET filled |
| 5 Elastic IP | EC2, Elastic IPs, allocate and associate with icl-web-host | The site's fixed address; survives stop and start |
| 6 DNS | Route 53 in the account that holds the techinnovations.io zone | A record, the F-7 label plus .techinnovations.io, to the Elastic IP, TTL 300 |
| 7 Certificate | Systems Manager, Session Manager, connect to icl-web-host | sudo site-cert <host> <email> once the name resolves; issues the Let's Encrypt certificate, turns on the HTTPS redirect; the renewal timer is already installed by the bootstrap |
| 8 First deploy | On the Mac, on the founder's word | python scripts/deploy_site.py engine/specs/sample-landing.yaml sample-landing --host <host> --profile icl-2: gated build, upload to the bucket, site-sync on the host by Run Command, byte-equal check of the served files against the build |
| 9 Alarms | CloudWatch and Budgets | StatusCheckFailed_System alarm with the recover action; a monthly budget alarm. The host costs about eight dollars a month (t4g.micro, 20 GB, the Elastic IP) |

Access rule for the web host: Session Manager only; no SSH server, no key pair. Deploy writes (the bucket upload and the Run Command) run under the founder's profile per F-8. A replacement host is one launch with the same bootstrap: the bucket holds the last build, so the site is back in minutes.

## 7. The tamper-evident API contract (shared by both goals)

Request: version, request id, operation generate, the specification (schema-valid), the pattern library version and the target.

Response: ok, output (artifact, content hash, pattern library version), log entry (sequence, previous hash, entry hash) and a signature over the whole response.

Determinism rules: request id and metadata never influence output; the same specification with the same pattern library version always yields the same hash.

Targets: hosted static site (the product default) and source (enterprise tier and internal consumers only).

Consumer-side verification before any use: signature, response schema, and recomputation of the content hash.

## 8. The India reseller channel (Offer 3, extension A)

Who. One-to-five-person web agencies and youth ventures serving local MSMEs in local languages, recruited through the Pune summit, the influencer program and, later, the platform house.

The offer to them. Engine access, hosting, templates and training: a two-person agency delivers like twenty. A fixed per-site cost to the reseller; the reseller prices to the MSME.

Readiness gates before the first reseller. The founder's site live as proof; ten site patterns; ingest from a Canva or Figma export; regional-language rendering; hosting with a custom domain; metering and invoicing; the reseller agreement (lawyers' lane); a support runbook.

Discipline. Capability-level disclosure only; no method or mathematics in any reseller material; the determinism challenge (make the engine disagree with itself) is offered only after the internal gates have passed.

## 9. Decisions needed from the founder

| Id | Decision | Recommendation |
|---|---|---|
| F-1 | Site number one | DECIDED 2026-10-08: the innovation movement site on techinnovations.io; the company site unchanged |
| F-2 | Emitter for hosted sites | IMPLEMENTED 2026-10-08 as a pre-rendered static build: the hosted output is plain HTML and CSS, no script. A dedicated emitter is deferred until page weight demands it |
| F-3 | Repository and CI for the engine | DONE 2026-10-08: private repository, founder-only, CI gate on every push |
| F-4 | Pricing for the Pune pilot | Rs 999 per site per year to the reseller for the pilot; revisit with the case studies |
| F-5 | Show the engine live at the summit | Yes, from the movement site: a specification change goes live on stage with its hash |
| F-6 | Push to the private repository | DONE 2026-10-08: all phases pushed |
| F-7 | Host label and hosted-zone account | FINDINGS 2026-10-10: techinnovation.io, as written on 2026-10-10, is parked by a third party and is not the founder's; techinnovations.io is the founder's, on Route 53, in neither the company account nor the other profile on the founder's Mac, so a third account holds the zone; inovations.techinnovations.io does not resolve yet. DECIDE: the label (inovations, innovations, invent, or the apex) and whether the zone moves or delegates to the company account |
| F-8 | AWS rights for the session | Read-only commands under the company profile from the session (in use since 2026-10-10); every write run by the founder with the read-back pasted |
| F-9 | Content inputs for the movement site | PARTLY IN 2026-10-08: the Kaydence Media Ventures letter of intent fixes the summit as 14 November 2026 (tentative), Pune, with C-DAC, and quotes the theme line "Invent in India. Then make it." (T-1 candidate a). Still open: the brand hierarchy (B-1) and the December 2027 summit (S-1) |
| F-10 | Certificate and edge for the web host | Let's Encrypt on the host now (one box, no extra service); CloudFront with an ACM certificate when sites number more than a handful |
| F-11 | Where builds run | On the founder's Mac with the gates until the engine host exists (phase 4); the web host receives built files only |

## 10. Risks and mitigations

Fidelity. A marketing site needs about ten patterns and tokens, and the acceptance test is visual fidelity. A visual-diff check runs before any reseller sees output.

Ingest quality. Design-to-specification from screenshots is the hardest piece. Start with structured exports; screenshots come last.

Clocks and disclosure. File the utility conversion before the public narrative deepens; keep every public statement at capability level.

One founder on the core. Keep the core stable and version-pinned; maintain the sealed continuity envelope.

One web host. No redundancy for site number one, which is acceptable at this stage: the recover alarm restarts a failed host, the bucket holds the last build, and a replacement host is one launch with the same bootstrap.

## 11. Acceptance checks

E-1 Golden test: the same specification twice, in the same and in a fresh process, gives identical bytes and a stable content hash. Met on 2026-10-08.

E-2 The movement site is live on its host name on techinnovations.io, generated from a specification, the contact form delivers mail through Turnstile, and the accessibility score is 95 or higher.

E-2a The web host serves the sample site over HTTPS on its host name, and a second deploy leaves the served bytes identical to the build (the hash check in scripts/deploy_site.py).

E-3 A second tenant generates a site with its own key; a metering row is written; the signature verifies.

E-4 Reseller pilot: three agencies, thirty sites, median design-to-live under one day, zero hand edits.

## 12. Progress log

| Date | Entry |
|---|---|
| 2026-10-07 | Plan drafted. Ruling: goal 2 first, with the founder's own website as the first use case. |
| 2026-10-08 | F-1 decided: the innovation movement site on inovations.techinnovations.io; company site unchanged. Phase 1 complete: engine imported into engine/, determinism steps 1 to 5 done, six golden tests green, pattern library 1.0.0, local commit 16c3699. Master to-do steps 1 to 5 ticked. |
| 2026-10-08 | Phase 1 pushed. Phase 2 complete the same day: ten site patterns and the page layout registered without touching the core, design tokens to CSS variables, static target, shell with pre-render; the sample site is plain HTML and CSS and rebuilds byte-identical; 14 tests green; pattern library 1.1.0; committed locally. Open: F-7 domain spelling and hosted zone, F-8 AWS rights, F-9 content inputs. Next: phase 3, the movement site, as soon as F-9 arrives. |
| 2026-10-08 | Master to-do sections 1 and 1a continued: the determinism gate (step 6) with andon stop, the quality gates (accessibility and size budget on built output), the preview capture with true phone emulation and visual diff, and the local artifact cache (step 7, local tier). The sample site passes every gate: 3.5 KB of HTML, 6.3 KB of CSS, no script, identical on rebuild; phone and desktop captures reviewed. Pushed. Open in list order: ingest (section 2), agents (4), API (5), hosting (6, needs F-7 and F-8). |
| 2026-10-08 | Ruling: an exhaustive, black-box library repository in the private repository, never shared, pulled by the engine host through the pipeline; deterministic generation only. Built the same evening: catalogs from the installed packages (453 entries, 182 core) on the 58-slot taxonomy; packs for Amplify UI, Next.js, Material Web, Firebase and React Native with Expo (69 generators, 96 registered patterns); patterns now declare imports, handler bodies, effects and module code; six targets with golden samples; unknown types refused; CI gate on push. Pattern library 1.2.0. Pushed. |
| 2026-10-10 | Ruling: site number one on an EC2 web host in the company account; the server first, then the site. Read-only check of the account under profile icl-2: VPC ICL-2-vpc with public and private subnets and an internet gateway, no instances yet. DNS: techinnovation.io is parked by a third party; techinnovations.io is the founder's, on Route 53 in a third account (F-7 reopened). Written: the console recipe (section 6), the host bootstrap scripts/server/web-host-user-data.sh (nginx, site-sync from the bucket, certificate tooling, no SSH), scripts/deploy_site.py (gated build, upload, Run Command sync, byte-equal check), this plan's markdown source and the document builder scripts/build_techdocs.py. The Word save of 2026-10-09, which had reverted this document to its phase 1 state, is superseded by this rebuild. Next: the founder runs recipe steps 1 to 7; then the first deploy on his word; then the movement site specification. |
