"""Read-only collectors. Network access happens only for explicitly enabled sources."""
import csv
import json
import os
import platform
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .catalog import identify
from .model import CATEGORIES, clean, finding, stable_id

MAX_BYTES = 2_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(url, headers=None, max_bytes=MAX_BYTES, data=None):
    """Bound response size/time; do not forward bearer tokens through redirects."""
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Glinx-Discovery/0.1", **(headers or {})})
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=12) as res:
        data = res.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError("Response exceeds the collector size limit")
        return data, res.headers


def command(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=25, check=True).stdout


def local_inventory():
    """Return only display names, never process args, files, users, or registry secrets."""
    system = platform.system()
    names = []
    if system == "Windows":
        import winreg
        opened_roots = 0
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for access in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
                try:
                    with winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0, winreg.KEY_READ | access) as key:
                        opened_roots += 1
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                with winreg.OpenKey(key, winreg.EnumKey(key, i)) as child:
                                    names.append(str(winreg.QueryValueEx(child, "DisplayName")[0]))
                            except OSError:
                                continue
                except OSError:
                    continue
        if not opened_roots:
            raise RuntimeError("No installation registry inventory could be opened with current permissions")
    elif system == "Darwin":
        for folder in (Path("/Applications"), Path.home() / "Applications"):
            if folder.exists():
                names.extend(p.stem for p in folder.glob("*.app"))
    elif system == "Linux":
        if shutil.which("dpkg-query"):
            names = command(["dpkg-query", "-W", "-f=${binary:Package}\n"]).splitlines()
        elif shutil.which("rpm"):
            names = command(["rpm", "-qa", "--qf", "%{NAME}\n"]).splitlines()
        else:
            raise RuntimeError("No supported package manager (dpkg-query or rpm)")
    else:
        raise RuntimeError("Unsupported endpoint operating system")
    return sorted(set(clean(n) for n in names if n))


def collect_host():
    names = local_inventory()
    host_id = stable_id("host", platform.node())
    results = [finding("This endpoint", "Infrastructure", "endpoint", f"{platform.system()} {platform.release()}; {len(names)} installation entries examined.", confidence=100, identity=host_id)]
    for name in names:
        product = identify(name)
        # Linux package sets contain OS libraries, not a usable company app inventory.
        if not product and platform.system() == "Linux":
            continue
        canonical, category = product or (name, "Unclassified")
        results.append(finding(canonical, category, "endpoint", f"Installation entry: {name}. Installation does not establish active use.", confidence=90 if product else 75, locator=host_id))
    return results, f"Examined {len(names)} installed entries on one endpoint. Linux returns catalog matches; Windows/macOS also return unclassified apps."


def domain_name(value):
    value = value.strip().lower().rstrip(".")
    if len(value) > 253 or not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", value):
        raise ValueError("Use an explicit DNS domain, such as example.com")
    return value


def collect_dns(domains):
    results = []
    for domain in domains:
        domain = domain_name(domain)
        query = urllib.parse.urlencode({"name": domain, "type": "MX"})
        body, _ = request("https://cloudflare-dns.com/dns-query?" + query, {"Accept": "application/dns-json"})
        payload = json.loads(body)
        if payload.get("Status") != 0:
            raise RuntimeError("DNS lookup failed; verify the domain and DNS access")
        records = [a.get("data", "") for a in payload.get("Answer", []) if a.get("type") == 15]
        for mx in records:
            value = mx.lower()
            mx_host = value.split()[-1].rstrip(".")
            if mx_host == "mail.protection.outlook.com" or mx_host.endswith(".mail.protection.outlook.com"):
                name, category = "Microsoft 365", "Email"
            elif re.search(r"(?:^|\.)(?:google|googlemail)\.com\.?$", value.split()[-1]):
                name, category = "Google Workspace", "Email"
            elif mx_host == "pphosted.com" or mx_host.endswith(".pphosted.com"):
                name, category = "Proofpoint mail gateway", "Email"
            elif mx_host == "mimecast.com" or mx_host.endswith(".mimecast.com"):
                name, category = "Mimecast mail gateway", "Email"
            else:
                name, category = "Mail routing · " + domain, "Email"
            results.append(finding(name, category, "dns", f"MX for {domain}: {mx}. Mail routing is a provider clue, not proof of a subscription or active mailbox.", "inferred", 60, locator=domain))
    return results, f"Queried MX records for {len(domains)} approved domains via Cloudflare DNS over HTTPS."


def graph_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "graph.microsoft.com" or parsed.path != "/v1.0/servicePrincipals" or parsed.fragment:
        raise ValueError("Rejected an unexpected Microsoft Graph continuation URL")
    return url


def m365_token():
    token = os.getenv("GLINX_M365_TOKEN", "").strip()
    if token:
        return token
    tenant = os.getenv("GLINX_M365_TENANT_ID", "").strip()
    client = os.getenv("GLINX_M365_CLIENT_ID", "").strip()
    secret = os.getenv("GLINX_M365_CLIENT_SECRET", "")
    guid = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    if not secret or not re.fullmatch(guid, tenant) or not re.fullmatch(guid, client):
        raise ValueError("Set GLINX_M365_TOKEN, or configure the administrator-approved tenant ID, client ID, and client secret environment variables")
    body = urllib.parse.urlencode({"client_id": client, "client_secret": secret, "scope": "https://graph.microsoft.com/.default", "grant_type": "client_credentials"}).encode()
    data, _ = request(f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token", {"Content-Type": "application/x-www-form-urlencoded"}, data=body)
    payload = json.loads(data)
    if not isinstance(payload.get("access_token"), str) or not payload["access_token"]:
        raise ValueError("Microsoft did not return an access token; check app consent and credential validity")
    return payload["access_token"]


def collect_m365():
    token = m365_token()
    url = "https://graph.microsoft.com/v1.0/servicePrincipals?$select=id,appId,displayName,servicePrincipalType&$top=100"
    results, seen = [], set()
    for _ in range(100):
        if url in seen:
            raise ValueError("Microsoft Graph returned a repeated page")
        seen.add(url)
        body, _ = request(graph_url(url), {"Authorization": "Bearer " + token, "Accept": "application/json"})
        payload = json.loads(body)
        if not isinstance(payload.get("value"), list):
            raise ValueError("Unexpected Microsoft Graph response")
        for item in payload["value"]:
            if item.get("servicePrincipalType") != "Application":
                continue
            display = clean(item.get("displayName"))
            if not display:
                continue
            product = identify(display)
            name, category = product or (display, "Unclassified")
            results.append(finding(name, category, "m365", f"Enterprise application registration: {display}. Registration does not establish active use, SSO configuration, or a paid license.", confidence=85, locator=clean(item.get("id"))))
        url = payload.get("@odata.nextLink")
        if not url:
            return results, f"Read {len(results)} application registrations from Microsoft Graph. No mail or user records requested."
    raise RuntimeError("Microsoft Graph exceeded the 100-page safety limit; this collector is incomplete")


def endpoint_url(value):
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Approved endpoints must be explicit HTTPS URLs without credentials, query strings, or fragments")
    if parsed.port not in (None, 443, 8443):
        raise ValueError("Approved endpoint ports are 443 and 8443")
    return value


def collect_endpoints(endpoints):
    results = []
    for value in endpoints:
        url = endpoint_url(value)
        body, headers = request(url, {"Accept": "text/html"}, max_bytes=262144)
        # Inspect only a bounded landing page, retain a product clue rather than content.
        text = body.decode("utf-8", errors="replace")
        title = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
        clue = title.group(1) if title else ""
        clue += " " + headers.get("Server", "") + " " + headers.get("X-Powered-By", "")
        product = identify(clue)
        name, category = product or ("Web service · " + urllib.parse.urlsplit(url).hostname, "Unclassified")
        results.append(finding(name, category, "endpoints", "Approved HTTPS endpoint responded. " + ("Page-title or server-header fingerprint matched " + name + ". Confirm product and use with its owner." if product else "No known product fingerprint matched."), "inferred", 65 if product else 40, locator=url))
    return results, f"Inspected {len(endpoints)} explicitly approved HTTPS endpoints. No network ranges scanned."


def collect_csv(filename):
    path = Path(filename)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Inventory CSV must be smaller than 2 MB")
    results, raw_links, names = [], [], {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "name" not in reader.fieldnames:
            raise ValueError("Inventory CSV requires a name column")
        for index, row in enumerate(reader, 2):
            if index > 5001:
                raise ValueError("Inventory CSV exceeds 5,000 rows")
            name = clean(row.get("name"))
            if not name:
                continue
            product = identify(name)
            canonical, detected = product or (name, "Unclassified")
            category = clean(row.get("category")) or detected
            if category not in CATEGORIES:
                raise ValueError(f"Invalid category at CSV row {index}")
            item = finding(canonical, category, "inventory", f"Owner-provided inventory row {index}: {name}. Reported metadata has not been independently verified.", "reported", 75, clean(row.get("owner")), locator=f"CSV row {index}")
            results.append(item)
            names[name.lower()] = item["id"]
            names[canonical.lower()] = item["id"]
            if row.get("connects_to"):
                raw_links.append((item["id"], clean(row["connects_to"]), clean(row.get("relationship")) or "Reported integration", index))
    links = []
    for source, target_name, label, row in raw_links:
        if target_name.lower() not in names:
            raise ValueError(f"Unknown connects_to system in CSV row {row}")
        target = names[target_name.lower()]
        if source != target:
            links.append({"id": stable_id(source, target, label), "source": source, "target": target, "label": label, "status": "reported", "evidence": f"Owner-provided inventory row {row}; integration not independently verified."})
    return results, f"Read {len(results)} owner-reported inventory entries.", links
