"""Small, portable evidence contract; no business content or credentials."""
import hashlib
import re
from datetime import datetime, timezone

SCHEMA_VERSION = "1.0"
CATEGORIES = {"ERP", "Email", "Finance", "CRM", "People", "Collaboration", "Data", "Infrastructure", "Unclassified"}
STATES = {"observed", "reported", "inferred"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stable_id(*parts):
    return hashlib.sha256("|".join(str(p).strip().lower() for p in parts).encode()).hexdigest()[:16]


def clean(value, limit=200):
    return re.sub(r"[\x00-\x1f\x7f]", " ", str(value or "")).strip()[:limit]


def finding(name, category, source, summary, status="observed", confidence=90, owner="", locator="", attributes=None, identity=None):
    name = clean(name)
    asset_id = stable_id("asset", identity or name)
    return {
        "id": asset_id, "name": name, "category": category if category in CATEGORIES else "Unclassified",
        "status": status, "confidence": confidence, "owner": clean(owner),
        "evidence": [{"id": stable_id(source, asset_id, summary), "source": source,
                      "summary": clean(summary, 600), "observed_at": now(), "locator": clean(locator),
                      "status": status, "confidence": confidence}],
        "attributes": attributes or {},
    }


def merge_findings(items):
    assets = {}
    rank = {"inferred": 0, "reported": 1, "observed": 2}
    for item in items:
        if item["id"] not in assets:
            assets[item["id"]] = {**item, "evidence": list(item["evidence"]), "attributes": dict(item["attributes"])}
            continue
        target = assets[item["id"]]
        known = {e["id"] for e in target["evidence"]}
        target["evidence"].extend(e for e in item["evidence"] if e["id"] not in known)
        target["confidence"] = max(target["confidence"], item["confidence"])
        if rank[item["status"]] > rank[target["status"]]:
            target["status"] = item["status"]
        if not target["owner"]:
            target["owner"] = item["owner"]
        target["attributes"].update(item["attributes"])
    return sorted(assets.values(), key=lambda a: (a["category"], a["name"].lower()))


def report(company, assets, collectors, relationships=None, demo=False):
    return {
        "schema_version": SCHEMA_VERSION, "scan_id": stable_id(now(), company, len(assets)),
        "generated_at": now(), "mode": "demo" if demo else "live",
        "company": clean(company) or "My company", "agent_version": "0.1.0",
        "scope": "Sample company" if demo else "Only the endpoint and sources explicitly enabled for this run",
        "systems": merge_findings(assets), "relationships": relationships or [], "collectors": collectors,
        "limitations": [
            "This inventory is bounded by configured sources. Total company coverage is unknown.",
            "Installed software and identity registrations do not establish active business use.",
            "DNS and web fingerprints are clues. Business integrations require independent evidence.",
        ],
    }
