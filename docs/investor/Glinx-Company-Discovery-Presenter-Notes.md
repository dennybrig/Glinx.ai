# Glinx Company Discovery

Investor presentation, September 2026.

## 1. Glinx Company Discovery

Opening: Glinx is building software that helps a company develop an evidence-backed understanding of itself. Company Discovery is the first product increment. It gives an owner a structured view of the systems the business runs on and the evidence behind that view. This presentation focuses on the current discovery prototype and the next pilot milestone.

The cover image is an AI-generated illustration of a fictional manufacturing floor. It does not depict a Glinx customer or a real installation. Glinx uses its own branding. This deck does not imply affiliation with Bain or PwC.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/README.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/ARCHITECTURE.md

## 2. Glinx starts with a practical first product

Use this slide as the full investment story in about 45 seconds. The problem is fragmented knowledge about operating systems. The product is a local sensing agent and an evidence viewer. The proof is engineering progress, including 17 agent tests and 7 dashboard-model tests, plus a real Linux scan and package installation checks. The next proof point is a customer-approved pilot. The available project evidence does not establish revenue, paying customers, measured savings or willingness to pay. Those remain questions for the pilot.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/README.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/VALIDATION.md

## 3. Leaders need a reliable map before they can automate

Describe this as Glinx's product thesis, rather than a quantified market study. A company may already have IT tools, spreadsheets or knowledgeable employees. Glinx aims to assemble a business-readable inventory with the source evidence and unresolved questions visible. This version records integration statements only when someone supplies separate evidence. It does not measure data flows or automatically prove how systems connect.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/ARCHITECTURE.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/REPORT-CONTRACT.md

## 4. The owner defines the scope of discovery

The agent is installable today as a Python package and can also run from a source checkout. The owner explicitly enables the sources for each run. Company administrators provide approval and credentials where a cloud service requires them. The agent then collects metadata, normalizes known product names and writes a local JSON report. The viewer presents the inventory, source outcomes and review questions. This is a manually invoked prototype, with fleet enrollment and managed deployment still ahead.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/README.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/glinx_discovery/cli.py
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/CONNECTORS.md

## 5. Five source types give the agent different views

The local collector supports Windows installation registry entries, macOS application-bundle names and Linux package names. Windows and macOS behavior still need live pilot validation. The mail-domain collector queries MX records using Cloudflare DNS over HTTPS. Microsoft 365 uses Graph application-read access to inspect enterprise application registrations. It does not read mailboxes. HTTPS discovery is limited to explicitly supplied landing pages and headers. Owner CSV data adds context and reported relationships. These collectors cannot guarantee whole-company coverage from one installation.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/CONNECTORS.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/glinx_discovery/collectors.py

## 6. The discovery report stays local by default

Be precise about what local means. The report remains local unless its owner chooses to share it. Enabled cloud connectors still contact their providers, and DNS lookup sends the approved domain name to Cloudflare. HTTPS inspection temporarily reads a landing page for a product fingerprint but does not retain the page content. Credentials stay in process memory and do not enter the report. Installation names and application identifiers can still be sensitive, so pilot teams should review any report before sharing. This slide describes implemented behavior, not a security certification.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/ARCHITECTURE.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/CONNECTORS.md

## 7. A fictional manufacturer makes the product concrete

This slide establishes the demonstration before any numbers appear to be customer results. Alder Forge is a fictional scenario with 12 systems, 7 business functions, 14 evidence records and 3 owner-reported integration statements. These counts come directly from the packaged sample report. The three integrations are Epicor to SQL Server, an Epicor CSV handoff to Power BI, and a payroll journal export from ADP to QuickBooks. None describes a measured live flow. During the demo, replay the sample and open an evidence panel.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/dist/demo.json
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/INVESTOR-DEMO.md

## 8. Every finding explains what Glinx knows

This is the core trust mechanism. Observed means a source returned a record, such as an installation entry or an enterprise application registration. Owner reported means a person supplied a statement. Inferred means a fingerprint suggests a product or provider. Glinx retains each evidence record's state and timestamp. A higher system-level state does not turn every underlying statement into an observation. Detection scores in the UI are rule strengths, not calibrated probabilities. The company map's membership lines do not imply an integration.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/REPORT-CONTRACT.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/glinx_discovery/model.py
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/dist/demo.json

## 9. Customer value is the next hypothesis to test

These are proposed customer benefits and a commercial hypothesis. No measured savings, price point, paying customer or recurring revenue is claimed. The first pilot should record time and owner effort rather than promise an unsupported productivity percentage. The fictional sample includes three unassigned systems and reported manual transfers that show the kind of question an owner can investigate. Manufacturing is a proposed initial customer focus consistent with the founder's operating background and the demo. The software's wider scope can expand to other businesses. Ongoing monitoring and subscription economics require further product and customer validation.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/THREE-DAY-PLAN.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/dist/model.js
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/dist/demo.json

## 10. The prototype works within a defined scope

Keep the proof precise. The implementation record reports 17 Python agent tests and 7 JavaScript model tests. A real Linux scan examined 693 package entries and returned one endpoint record in the development environment. That environment was not a representative company inventory and no network source was enabled. The built wheel installed into a fresh environment and served its packaged assets and report routes. Microsoft and DNS behavior used synthetic responses for validation. The original session did not execute Windows/macOS inventory against real machines or use a real Microsoft tenant. The original dashboard also needs a rehearsal in the presentation browser. These are engineering results, not customer traction.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/VALIDATION.md

## 11. Discovery is the first layer of the wider Glinx vision

Define self-awareness operationally. The long-term goal is a company model that can describe its identity, assess its condition and learn from history. The current increment implements the initial Sense stage. Understand, Decide, Act and Learn are a roadmap, not delivered features. The present inventory questions use deterministic rules and do not invoke an LLM. Future reasoning should preserve source-native evidence, permissions and provenance, with human authority governing actions.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/ARCHITECTURE.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/README.md

## 12. A focused pilot can establish accuracy and value

This is a proposed pilot design. It does not imply an existing customer commitment or an agreed delivery date. Select a company with a willing owner, an administrator and a clearly bounded set of systems. Compare discovery results against an owner-reviewed baseline. Add approved identity metadata and build a native ERP metadata connector chosen for that company. The present product can identify ERP presence through inventory and fingerprints but does not read ERP transactions. Conclude with an explicit customer decision on usefulness and a paid next phase.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/THREE-DAY-PLAN.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/CONNECTORS.md

## 13. The next milestone is a real company pilot

Close by asking for a design-partner introduction and clarity about what pilot evidence would support a next investment decision. No fundraising amount or valuation is proposed because neither has been defined. The demo and source links are private: Denny can present the demo through screen sharing, and collaborators need repository access. For the live demonstration, replay the fictional company, inspect Epicor, review evidence and gaps, then import a reviewed real report if one is available. Do not present sample results as a live company scan.

Demo: https://glinx-discovery.dennybrig.chatgpt.site
Repository: https://github.com/dennybrig/Glinx.ai

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/INVESTOR-DEMO.md

## 14. Investor questions

Use this appendix if the investor asks about scope, present capability or implementation credibility. Give the exact current answer before discussing the roadmap. Keep the distinction between sample data, implemented code and live-tenant validation clear. The repository includes CI configuration for multiple operating systems, but that configuration alone is not evidence that the original session validated real customer machines.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/INVESTOR-DEMO.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/VALIDATION.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/README.md

## 15. Proposed pilot acceptance criteria

Agree with the company on how to measure a successful pilot before beginning. Do not claim a percentage of whole-company coverage when the total is unknown. Assess discovery against a bounded owner-reviewed list and report both misses and false matches. Track setup effort and every required permission. Ask the company to identify a useful follow-up decision and whether it would pay for continued work. These criteria are proposals for evaluation, not existing pilot results.

Sources:
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/THREE-DAY-PLAN.md
- https://github.com/dennybrig/Glinx.ai/blob/8e49df99fe437d0452892e5034a3c0ca97e56a8c/docs/REPORT-CONTRACT.md
