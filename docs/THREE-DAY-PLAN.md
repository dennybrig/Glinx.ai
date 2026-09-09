# Three days to a credible demonstration

Use this as a preparation plan, not a claim that untested integrations are already proven.

| Day | Work | Exit criterion |
|---|---|---|
| 1 — Establish the baseline | Clone the repo; run the local sample; test the host collector on Denny's intended demonstration computer; review the output for appropriate disclosure. | The demo opens offline, and one real endpoint report imports correctly. |
| 2 — Add company evidence | With the company's authorization, have its administrator configure Microsoft 365 app-read access or prepare an inventory CSV; add the company mail domain if appropriate; confirm system owners. | At least one real company source beyond the endpoint produces traceable evidence, or its access limitation is explicitly documented. |
| 3 — Rehearse and freeze | Rehearse the five-minute walkthrough; retain the packaged sample as fallback; check the presentation machine and screen-sharing session; avoid last-minute connector work. | A repeatable five-minute story, a clear distinction between sample and real results, and a specific pilot request. |

## Immediate pilot backlog

1. Validate endpoint enumeration on the company's Windows/macOS machines and address missed application sources.
2. Validate the Microsoft connector against an approved tenant, including permissions, expired credentials, and throttling.
3. Build one native ERP metadata connector for the pilot company's actual ERP.
4. Add Google Workspace/identity-provider or MDM inventory as dictated by the pilot's systems.
5. Add tenant/installation identities, controlled credential storage, scheduled incremental scans, and signed reports.
6. Add an authenticated ingestion service, multi-tenant isolation, audit history, and a managed installer.

The strongest investor claim is that a first evidence-backed sensing loop runs end to end and has a clear route into a real pilot. The present prototype does not substantiate a claim of company-wide autonomous intelligence.
