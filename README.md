# Glinx Discovery

**The first sensing layer for a living model of the enterprise.**

Glinx Discovery identifies systems from authorized metadata sources, retains the evidence behind each finding, and presents a company map. This v0.1 prototype implements the **Sense** stage of Glinx's **Sense → Understand → Decide → Act → Learn** loop.

It contains a working local discovery agent and an investor demo. It does not claim to discover an entire company from one computer or to make autonomous business decisions.

## Try the investor demo

Requires Python 3.10 or newer. The source checkout demo has no third-party runtime dependencies.

```bash
git clone https://github.com/dennybrig/Glinx.ai.git
cd Glinx.ai
python -m glinx_discovery demo --serve
```

Open **http://127.0.0.1:8765** in your browser. On Windows, replace `python` with `py -3` if needed, or double-click `start-demo.cmd`. On macOS/Linux, run `sh start-demo.sh`.

The fictional **Alder Forge** scenario includes 12 systems, 7 business functions, 14 evidence records, and 3 explicitly owner-reported integrations. Click **Replay discovery**, inspect Epicor, review the connection evidence, then open **Evidence & gaps**. The replay never runs a network scan.

## Install the agent

From the cloned or extracted project:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install .
glinx --version
```

The wheel contains the local dashboard. Python packaging may download build tools during installation; the agent itself has no third-party runtime dependencies. For an offline demo, run directly from the checkout as shown above.

The downloadable source bundle also includes the built wheel in `release/`. To install that package without fetching dependencies:

```bash
python -m pip install --no-index release/glinx_discovery-0.1.0-py3-none-any.whl
```

## Run a real scan

```bash
glinx scan --host --company "My company" --output scan.json --serve
```

This reads installed application metadata on **this computer**. The local dashboard shows this report, with no automatic upload. To use the hosted demo interface, click **Import scan** and choose `scan.json`; parsing stays in your browser tab. Reloading the hosted demo resets to the sample company.

Expand the scan only to sources your company has authorized:

```bash
glinx scan --host --domain your-company.com --inventory your-inventory.csv --company "My company"
glinx scan --m365 --company "My company"
glinx scan --endpoint https://erp.your-company.com --company "My company"
glinx init
glinx scan --config glinx-config.json
```

Replace example domains and paths before running them. `glinx init` writes a configuration with **every source disabled**. A scan with no enabled source exits with an actionable error. Microsoft 365 requires administrator-approved credentials; see [connector setup](docs/CONNECTORS.md).

## What works in v0.1

| Source | Collected metadata | What the finding means |
|---|---|---|
| Windows endpoint | Installed application display names from accessible uninstall registry entries | An installation record exists on one endpoint |
| macOS endpoint | `.app` names in `/Applications` and the current user's `Applications` directory | An application bundle exists in those directories |
| Linux endpoint | Package names via `dpkg-query` or `rpm`; catalog matches surfaced | A matching package entry exists on one endpoint |
| Company mail domain | MX records via Cloudflare DNS over HTTPS | A mail-routing provider clue; confirmation needed |
| Microsoft 365 / Entra | Application registration IDs, display names, type | An enterprise app is registered; active use is unverified |
| Approved HTTPS endpoints | Product match from a bounded landing-page title and server headers | A product fingerprint; confirmation needed |
| Owner inventory CSV | System, category, owner, optional connection statement | Owner-reported context and relationships |

No mailbox bodies, documents, browser history, passwords, process arguments, business database rows, or payroll records are collected. HTTPS landing pages are read briefly for matching but their content is not retained. Installation names, endpoint URLs, and app IDs can still be sensitive; keep real reports private.

The UI offers a company map, searchable inventory, function/evidence filters, source status, evidence drilldowns, rule-based follow-up questions, JSON/CSV export, and browser-local report import. Dotted company-map lines represent inventory membership. Integration links require separate evidence and are not inferred merely from co-occurrence.

## Collaborate

The canonical project is [dennybrig/Glinx.ai](https://github.com/dennybrig/Glinx.ai). Work on a feature branch and open a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md), [the architecture](docs/ARCHITECTURE.md), and [the report contract](docs/REPORT-CONTRACT.md). GitHub Actions runs the agent suite on Windows/macOS/Linux and the dashboard model suite on Node 22.

```bash
python -m unittest discover -s tests -v
node --test tests/model.test.mjs
node --check dist/app.js
python -m pip wheel --no-deps . --wheel-dir release
```

The frontend is authored directly in `dist/`; it does not need a JavaScript dependency installation or compilation step. `scripts/create_demo.py` regenerates only the clearly fictional sample fixture. Native installer signing, fleet deployment, tenant-managed OAuth onboarding, continuous monitoring, a centralized ingestion API, and business-content connectors are future work.

## Demo preparation

- [Five-minute investor walkthrough](docs/INVESTOR-DEMO.md)
- [Three-day preparation plan](docs/THREE-DAY-PLAN.md)
- [Validation record and limitations](docs/VALIDATION.md)

This repository is a private prototype. No open-source license is granted by its publication to authorized collaborators.
