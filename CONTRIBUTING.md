# Working together on Glinx

Use feature branches such as `connector/google-workspace` or `agent/windows-inventory` and open pull requests to `main`. Keep each PR focused on one discovery capability or user outcome. The repository owner manages collaborator access and branch protection in GitHub settings.

Run the commands in the README before requesting review. CI is defined in `.github/workflows/ci.yml`; branch protection has not been automatically enabled.

## Add a collector

1. Implement a bounded, read-only function in `glinx_discovery/collectors.py` or a new provider module. Return findings plus a coverage description. Use the helpers in `model.py`.
2. Add explicit scope/configuration in `cli.py`. Leave new sources disabled by default. Preserve evidence from other successful sources when one source fails.
3. Give every finding a source, timestamp, locator, and factual summary. Use `inferred` for fingerprints and `reported` for human-provided inventory. State what the evidence cannot establish.
4. Add synthetic fixtures and tests for the actual risks: pagination, wrong-tenant endpoints, token leakage, partial failure, duplicates, ambiguous fingerprints, or missing permissions.
5. Update the report contract and connector instructions when behavior changes. Update the schema version for breaking report changes.

Use the GitHub issue template to define permissions, metadata, and evidence meaning before writing a new connector. Keep real tenant exports, credentials, customer hostnames, and business files out of issues, commits, and test fixtures.

## Ownership and identity

v0.1 deduplicates by normalized product name. Different installations or tenants of the same product may collapse into one record. A future identity model should include organization, provider tenant, installation ID, and source-native resource ID while keeping their provenance separate.

## Frontend

`dist/model.js` validates imported reports and computes inventory rules. `dist/app.js` renders the workspace. Imported values are escaped before HTML rendering. Keep external report data out of executable markup and URLs. Changes to import validation, CSV escaping, evidence state, and relationship semantics require meaningful tests.

Keep the fictional scenario clearly labeled. Never silently replace a failed real scan with sample data, convert a reported connection into an observed one, or present a detection score as a statistical probability.
