# Stage 2A: company memory and the Alder Forge demo

Stage two now has a working local memory engine and an interactive history viewer. It builds on the unchanged stage-one Alder Forge report. This increment implements persistent report history, comparisons, and evidence continuity. Native installation identities, operational ERP access, and action agents remain subsequent increments.

## Explore the hosted demo

Open [Alder Forge company memory](https://glinx-discovery.dennybrig.chatgpt.site/memory.html). Stage one remains available at the root URL and from the sidebar.

Select **Replay the story**, or choose snapshots directly. The page initially opens on the second snapshot, showing three system/connection changes. Use **Compare with** to change the baseline, **Remembered systems** to search the accumulated inventory, and **See evidence** to inspect a system's history. **Source visibility** explains what each collector could examine.

| Snapshot | Seen in scan | Remembered | What to inspect |
| --- | --- | --- | --- |
| September 9 | 12 | 12 | The original stage-one baseline, with its evidence and three reported connections |
| September 10 | 13 | 13 | Fiix CMMS is disclosed; Dropbox gets a reported owner; a Fiix–Epicor connection is reported |
| September 11 | 10 | 13 | Microsoft 365 app discovery is unavailable for Salesforce/SharePoint; Odoo is absent from the successfully read owner inventory |

The third snapshot distinguishes **source unavailable** from **not seen in this scan**. Neither establishes removal. Previous observations and owner/connection claims remain inspectable. Fiix's discovery does not establish its installation date, and the new integration remains owner-reported.

The hosted page is a read-only demonstration using an export produced by the real memory engine. It does not run Python or write a hosted database. Replay changes which saved snapshot is viewed. Real persistence runs locally in SQLite. Opening an exported history in the browser is tab-local and does not modify its database or upload it.

## Run the working local demo

Until the implementation PR is merged, obtain its feature branch:

```bash
git clone --branch feature/stage-2-memory-demo --single-branch https://github.com/dennybrig/Glinx.ai.git
cd Glinx.ai
python -m glinx_discovery company demo --db company-demo.db --serve
```

Open **http://127.0.0.1:8765/memory.html**. On Windows, use `py -3` if `python` is unavailable. No third-party runtime packages or external services are required on Python installations that include SQLite.

Stop and restart the same command: the three saved imports retain their identity. Rerunning the demo never replaces a different company database. The viewer serves a snapshot of the database taken at startup; restart it after additional CLI imports.

## Use your own discovery reports

```bash
python -m glinx_discovery company init --db company.db --name "My company" --purpose "Our operating purpose"
python -m glinx_discovery company import --db company.db --scope-id workstation-a scan-a.json
python -m glinx_discovery company import --db company.db --scope-id workstation-a scan-b.json
python -m glinx_discovery company history --db company.db --scope-id workstation-a
python -m glinx_discovery company diff --db company.db --scope-id workstation-a
python -m glinx_discovery company serve --db company.db --scope-id workstation-a
python -m glinx_discovery company export --db company.db --scope-id workstation-a --output company-memory.json
```

The report company label must match the selected database. A database holds one company and one mode; demo and live reports require separate files. The database's internal company ID is independent of the display name. Scope IDs and revisions are explicit user assertions, not proof that source settings match. Use `--scope-description` to record the boundary and a new `--scope-revision` when that boundary changes. Different scopes or revisions cannot be compared.

`diff` defaults to the latest two reports by collection time. Optional `--before` and `--after` accept internal run IDs from `history`. Ties use import order. Backdated imports rebuild the historical view. Identical JSON content, including reordered object keys or different formatting, is imported once per scope revision. Different content is retained even if the legacy scan ID collides.

Exports support up to 20 snapshots, 5,000 remembered systems, 10,000 remembered connections, and 15 MB. The database/CLI can retain larger histories; the browser export is deliberately bounded. Current source scope, collection time, and evidence limitations remain visible. Conflicting claims stay in retained reports; the latest supplied claim is a display convention, not an adjudication.

Keep databases and live exports outside the public dashboard and Git. Files created on Unix use restrictive permissions; SQLite is not an encrypted or multi-user authorization service. Reports/exports are not signed. This local increment adds no business-system writes, unattended scanning, or LLM calls.

## Implementation and validation

`glinx_company` contains validation, transactional storage, projections, comparisons, the CLI, and the fictional scenario. `dist/memory.html` adds the history viewer alongside discovery. The existing local server exposes only fixed assets and the selected memory export; it accepts no upload or scan requests.

Run the Python and dashboard suites:

```bash
python -m unittest discover -s tests -v
node --test tests/model.test.mjs tests/memory.test.mjs
node --check dist/memory.js
```

The tests cover restart persistence, duplicate imports, scan-ID collisions, scope/company/mode isolation, transaction rollback, out-of-order imports, source loss/recovery, retained evidence semantics, import validation, output protection, and local server boundaries. The dashboard tests compare the committed demo's views and comparisons with fresh Python engine calculations.

`python scripts/create_memory_demo.py` regenerates only the fictional hosted fixture from a temporary SQLite database. The installable wheel includes both dashboard stages and the memory package.
