"""Rebuild views from retained reports. Missing evidence never means deletion."""
from copy import deepcopy

from .contracts import canonical


def visibility(record, latest):
    statuses = {}
    for source in latest["collectors"]:
        statuses.setdefault(source["id"], []).append(source["status"])
    sources = {e["source"] for e in record["evidence"]}
    unavailable = sorted(s for s in sources if not statuses.get(s) or any(v != "complete" for v in statuses[s]))
    return ("unavailable" if unavailable else "not_seen"), unavailable


def project(runs):
    if not runs:
        return {"run_id": None, "systems": [], "relationships": [], "counts": {"remembered": 0, "seen": 0, "unavailable": 0, "not_seen": 0}}
    systems, links = {}, {}
    for run in runs:
        for record in run["report"]["systems"]:
            item = systems.setdefault(record["id"], {
                "first_run_id": run["run_id"], "first_seen": run["generated_at"],
                "history": [], "owner_claims": [], "identity_resolution": "legacy_product_aggregate",
            })
            item.update(record=deepcopy(record), last_run_id=run["run_id"], last_seen=run["generated_at"])
            item["history"].append(run["run_id"])
            if record["owner"] and not any(c["owner"] == record["owner"] for c in item["owner_claims"]):
                item["owner_claims"].append({"owner": record["owner"], "run_id": run["run_id"], "status": "reported"})
        for record in run["report"]["relationships"]:
            item = links.setdefault(record["id"], {"first_run_id": run["run_id"], "history": []})
            item.update(record=deepcopy(record), last_run_id=run["run_id"])
            item["history"].append(run["run_id"])
    latest = runs[-1]
    seen_ids = {s["id"] for s in latest["report"]["systems"]}
    counts = {"remembered": len(systems), "seen": len(seen_ids), "unavailable": 0, "not_seen": 0}
    for ident, item in systems.items():
        item["visibility"], item["unavailable_sources"] = ("seen", []) if ident in seen_ids else visibility(item["record"], latest["report"])
        if item["visibility"] != "seen":
            counts[item["visibility"]] += 1
    for item in links.values():
        item["visibility"] = "seen" if item["last_run_id"] == latest["run_id"] else "not_seen"
    return {"run_id": latest["run_id"], "systems": sorted(systems.values(), key=lambda x: (x["record"]["category"], x["record"]["name"])),
            "relationships": list(links.values()), "counts": counts}


def evidence_signature(record):
    return sorted(canonical({k: e[k] for k in ("source", "summary", "locator", "status", "confidence")}) for e in record["evidence"])


def compare(runs, before_id, after_id):
    indexes = {r["run_id"]: i for i, r in enumerate(runs)}
    if before_id not in indexes or after_id not in indexes or indexes[before_id] >= indexes[after_id]:
        raise ValueError("Choose an earlier and a later snapshot in the same scope revision")
    before_index, after_index = indexes[before_id], indexes[after_id]
    before, after = project(runs[:before_index + 1]), project(runs[:after_index + 1])
    old = {s["record"]["id"]: s for s in before["systems"]}
    changes = []
    for item in after["systems"]:
        record, prior = item["record"], old.get(item["record"]["id"])
        base = {"id": record["id"], "name": record["name"], "before_run_id": prior["last_run_id"] if prior else None,
                "after_run_id": item["last_run_id"], "fields": []}
        if prior is None:
            changes.append({**base, "kind": "added"})
        else:
            if item["visibility"] != prior["visibility"]:
                changes.append({**base, "kind": "seen_again" if item["visibility"] == "seen" else item["visibility"]})
            fields = [{"field": k, "before": prior["record"].get(k, {} if k == "attributes" else ""), "after": record.get(k, {} if k == "attributes" else "")}
                      for k in ("name", "category", "owner", "status", "confidence", "attributes")
                      if prior["record"].get(k, {} if k == "attributes" else "") != record.get(k, {} if k == "attributes" else "")]
            if fields:
                changes.append({**base, "kind": "changed", "fields": fields})
            elif evidence_signature(prior["record"]) != evidence_signature(record):
                changes.append({**base, "kind": "evidence_changed"})
    old_links = {x["record"]["id"]: x for x in before["relationships"]}
    relationship_changes = []
    for link in after["relationships"]:
        prior = old_links.get(link["record"]["id"])
        kind = "added" if prior is None else "changed" if canonical(prior["record"]) != canonical(link["record"]) else "not_seen" if prior["visibility"] == "seen" and link["visibility"] == "not_seen" else "seen_again" if prior["visibility"] == "not_seen" and link["visibility"] == "seen" else None
        if kind:
            relationship_changes.append({"id": link["record"]["id"], "kind": kind, "before_run_id": prior["last_run_id"] if prior else None, "after_run_id": link["last_run_id"]})
    prior_sources = {(c["id"], c["name"]): c for c in runs[before_index]["report"]["collectors"]}
    current_sources = {(c["id"], c["name"]): c for c in runs[after_index]["report"]["collectors"]}
    source_changes = [{"id": key[0], "name": key[1], "before": prior_sources.get(key, {}).get("status", "absent"), "after": current_sources.get(key, {}).get("status", "absent")}
                      for key in sorted(set(prior_sources) | set(current_sources))
                      if prior_sources.get(key, {}).get("status", "absent") != current_sources.get(key, {}).get("status", "absent")]
    return {"before_run_id": before_id, "after_run_id": after_id, "system_changes": changes,
            "relationship_changes": relationship_changes, "source_changes": source_changes}
