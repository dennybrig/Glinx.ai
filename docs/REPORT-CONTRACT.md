# Report contract · 1.0

The Python agent writes UTF-8 JSON. `dist/model.js` validates imports before rendering them. The frontend accepts files up to 5 MB, 5,000 systems, 10,000 relationships, and 100 collector outcomes. Larger deployments need a paginated backend instead of increasing browser limits indefinitely.

| Field | Meaning |
|---|---|
| `schema_version` | Exact supported contract string: `1.0` |
| `mode` | `demo` for sample evidence, `live` for collector outputs |
| `company` | Owner-provided company label |
| `scan_id`, `generated_at`, `agent_version` | Scan metadata |
| `scope` | Description of the configured collection boundary |
| `systems` | Deduplicated systems with evidence |
| `relationships` | Independently supplied statements connecting system IDs |
| `collectors` | Outcomes: `complete`, `error`, or `not_configured` |
| `limitations` | Known scope and interpretation limits |

Each system contains `id`, `name`, `category`, `owner` (empty when unknown), `status`, `confidence`, `evidence`, and optional `attributes`. Each evidence item carries `id`, `source`, `summary`, `observed_at`, `locator`, `status`, and `confidence`. Every relationship carries `id`, `source`, `target`, `label`, `status`, and `evidence`.

Relationship endpoints must refer to distinct existing systems. Product IDs are deterministic hashes of normalized names in v0.1. This is intentionally a product-level inventory, not an installation/tenant identity graph. Evidence IDs also incorporate source and summary. Conflicting ownership and multiple tenants are not automatically reconciled.

Detection scores are deterministic rule strengths. The system-level state selects observed over reported over inferred; individual evidence retains its original state. The highest evidence score is shown at system level. Connections do not inherit system confidence.

Report import validates shape and references, not authenticity. Reports are not cryptographically signed. A manually altered file can change a displayed claim; treat imported evidence as supplied data and verify its source before operational use.

The system count is the inventory size. Business functions exclude Infrastructure and Unclassified. Source completion counts only configured collectors. No percentage of total company discovery is reported because its denominator is unknown.
