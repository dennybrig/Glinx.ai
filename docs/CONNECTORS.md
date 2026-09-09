# Configure authorized discovery

Start with one company-controlled endpoint. Use `glinx init` to produce a local configuration, then enable selected sources. No credentials belong in the JSON config; unknown config keys are rejected.

## Endpoint inventory

```bash
glinx scan --host --company "My company" --serve
```

No administrator elevation is requested. Windows reads accessible installation display names; macOS checks application-bundle names; Linux checks the available supported package manager. Run separately on other approved endpoints to broaden coverage. v0.1 does not aggregate scans across a fleet.

## Mail domain discovery

```bash
glinx scan --domain your-company.com
```

Only MX records are queried. This explicitly sends the domain to Cloudflare's public DNS-over-HTTPS resolver. It may reveal Microsoft 365, Google Workspace, or a gateway; it cannot prove mailbox activity or inventory an organization's SaaS. At most 20 explicit domains per scan; wildcard domains and CIDR ranges are rejected. See [Cloudflare's JSON DNS API](https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/make-api-requests/dns-json/).

## Microsoft 365 / Entra enterprise applications

The tenant administrator registers a single-tenant application and grants the Microsoft Graph **application** permission `Application.Read.All` with administrator consent. No `Mail.Read`, file, user, or write permission is required by this connector. It reads `/v1.0/servicePrincipals` using a restricted field selection and filters application registrations. See [Microsoft's endpoint and permission documentation](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list?view=graph-rest-1.0).

For this prototype, either supply a short-lived Graph access token through `GLINX_M365_TOKEN`, or set these process environment variables through your company's normal secret-management process:

| Variable | Value |
|---|---|
| `GLINX_M365_TENANT_ID` | Directory tenant UUID |
| `GLINX_M365_CLIENT_ID` | Approved application client UUID |
| `GLINX_M365_CLIENT_SECRET` | Application secret value, not its identifier |

Then run:

```bash
glinx scan --m365 --company "My company" --output scan.json
```

The client-credential route gets a token from `login.microsoftonline.com` using the `https://graph.microsoft.com/.default` scope. Tokens are held in memory and are never written into reports or the configuration. Do not paste secrets into shell commands that are retained in history. This implementation does not store, rotate, refresh, or manage credentials; each run obtains a fresh token when using app credentials. An explicit `GLINX_M365_TOKEN` takes precedence over app credentials. See [Microsoft's client credentials flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow).

Only the Microsoft global cloud is supported. 401/403 errors become visible source failures; the report does not show fabricated successful results. Pagination is bounded at 100 pages. A mid-source failure discards that source's incomplete result, while preserving other completed sources. App registration presence does not prove a paid license, configured SSO, active users, or an integration.

## Known ERP and application endpoints

```bash
glinx scan --endpoint https://erp.your-company.com
```

This sends one bounded HTTPS GET to an explicitly supplied URL and checks its page title/server headers for known product names. It does not crawl links, log in, ignore TLS errors, or follow redirects. Approved ports are 443 and 8443. URLs with credentials, query strings, or fragments are rejected. A login redirect or self-signed certificate may yield an error requiring administrator review. No page body is retained. Add native authenticated ERP metadata connectors in subsequent releases.

## Owner inventory

Start with `examples/inventory.csv` as a format example; its content is illustrative. Use a separate file for company data:

```csv
name,category,owner,connects_to,relationship
Epicor,ERP,Operations,Microsoft SQL Server,Reported production database
Microsoft SQL Server,Data,IT,,
```

```bash
glinx scan --inventory your-inventory.csv --company "My company"
```

Allowed categories: ERP, Email, Finance, CRM, People, Collaboration, Data, Infrastructure, Unclassified. Only `name` is required. `connects_to` must identify another row by original or canonical product name. Each row can state one connection; repeat the source row for additional connections. Unknown targets fail explicitly. The file is bounded to 2 MB and 5,000 rows. All imported statements and links are marked **reported**.

## Status and output

- Exit `0`: every enabled collector completed.
- Exit `1`: invalid input, scope, configuration, or local output failure.
- Exit `2`: at least one source failed; the report was still written with other successful sources.

A scan timestamp indicates when evidence was collected, not how fresh the underlying source record is. Source completion is not whole-company coverage. Use `glinx serve --report scan.json` to reopen a saved report.
