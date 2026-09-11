"""Alder Forge's fictional history, using the unchanged stage-one baseline."""
import json
from copy import deepcopy
from pathlib import Path

from glinx_discovery.server import web_dir
from .contracts import digest
from .store import CompanyStore, create_company

SCOPE = "alder-forge-pilot"
COMPANY_ID = "8044b4a0-dfe4-5e60-9f80-a1deff090001"
PURPOSE = "Deliver dependable forged components while protecting quality, delivery commitments, and working capital."


def reports():
    baseline = json.loads((web_dir() / "demo.json").read_text(encoding="utf-8"))
    followup = deepcopy(baseline)
    followup.update(scan_id="alder-followup", generated_at="2026-09-10T09:42:00Z")
    dropbox = next(s for s in followup["systems"] if s["id"] == "dropbox")
    dropbox["owner"] = "Maya Chen · IT"
    dropbox["evidence"].append({"id": "dropbox-owner", "source": "inventory", "summary": "SAMPLE · Maya Chen is reported as the Dropbox owner by IT. This ownership statement is not independently verified.", "observed_at": followup["generated_at"], "locator": "Owner inventory · Dropbox", "status": "reported", "confidence": 75})
    followup["systems"].append({"id": "fiix", "name": "Fiix CMMS", "category": "Unclassified", "owner": "Luis Ortega · Maintenance", "status": "reported", "confidence": 75,
        "attributes": {"business_function": "Maintenance"}, "evidence": [{"id": "fiix-inventory", "source": "inventory", "summary": "SAMPLE · The maintenance owner lists Fiix CMMS. It is newly disclosed to Glinx; its installation date and active use are unverified.", "observed_at": followup["generated_at"], "locator": "Owner inventory · Fiix", "status": "reported", "confidence": 75}]})
    followup["relationships"].append({"id": "r-fiix-epicor", "source": "fiix", "target": "epicor", "label": "Maintenance work order export", "status": "reported", "evidence": "SAMPLE · Maintenance reports exporting work orders from Fiix to Epicor. No application connection or data transfer was verified."})
    outage = deepcopy(followup)
    outage.update(scan_id="alder-visibility-gap", generated_at="2026-09-11T09:42:00Z")
    outage["systems"] = [s for s in outage["systems"] if s["id"] not in ("salesforce", "sharepoint", "odoo")]
    for r in (followup, outage):
        for s in r["systems"]:
            for e in s["evidence"]:
                e["observed_at"] = r["generated_at"]
        for c in r["collectors"]:
            c["count"] = sum(e["source"] == c["id"] for s in r["systems"] for e in s["evidence"])
            if c["id"] == "inventory":
                c["detail"] = "SAMPLE · Owner-reported inventory and connections. Statements are not independently verified."
    for c in outage["collectors"]:
        if c["id"] == "m365":
            c.update(status="error", count=0, detail="SAMPLE · Microsoft 365 application metadata could not be read. Salesforce and SharePoint were not assessed in this snapshot.")
        if c["id"] == "inventory":
            c["detail"] = "SAMPLE · Owner inventory was read successfully. Odoo is absent from this supplied inventory; removal has not been established."
    return [baseline, followup, outage]


def create_demo(path):
    if not Path(path).exists():
        create_company(path, "Alder Forge", PURPOSE, company_id=COMPANY_ID)
    with CompanyStore(path) as store:
        if store.profile()["id"] != COMPANY_ID or store.profile()["mode"] not in (None, "demo"):
            raise ValueError("This database is not the Alder Forge demo; choose a new --db path")
        for report in reports():
            store.import_report(report, SCOPE, description="The same fictional workstation, mail domain, enterprise-app source, and owner inventory. No scope expansion across these snapshots.")
        return demo_export(store)


def demo_export(store):
    result = store.export(SCOPE)
    story = [
        ("The starting point", "12 systems discovered. The company now has a first recorded view."),
        ("The company changes", "Fiix is disclosed, Dropbox gets an owner, and a connection is reported."),
        ("Visibility is interrupted", "An app source fails. Glinx retains what it knew and makes the gap visible."),
    ]
    known = {digest(r): story[i] for i, r in enumerate(reports())}
    for run in result["runs"]:
        if digest(run["report"]) in known:
            run["label"], run["narrative"] = known[digest(run["report"])]
    return result
