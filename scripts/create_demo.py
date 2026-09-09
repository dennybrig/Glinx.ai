"""Generate the deterministic, explicitly fictional investor fixture."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-09-09T09:42:00Z"


def evidence(source, summary, status, score, locator):
    return {"id": "demo-" + source + "-" + locator.replace(" ", "-").lower(), "source": source, "summary": summary, "observed_at": DATE, "locator": "SAMPLE · " + locator, "status": status, "confidence": score}


def system(id, name, category, owner, source, summary, status="observed", score=90):
    return {"id": id, "name": name, "category": category, "owner": owner, "status": status, "confidence": score, "evidence": [evidence(source, summary, status, score, id)], "attributes": {}}


systems = [
    system("epicor", "Epicor Kinetic", "ERP", "Operations", "endpoint", "Sample endpoint inventory contains an Epicor Kinetic client. This is an installation record; active use has not been independently checked."),
    system("m365", "Microsoft 365", "Email", "IT", "dns", "Sample MX record points to alderforge-example.mail.protection.outlook.com. This suggests Microsoft mail routing; it does not prove active mailboxes.", "inferred", 60),
    system("salesforce", "Salesforce", "CRM", "Sales", "m365", "Sample Microsoft Entra enterprise application registration for Salesforce. Registration does not establish active use or a configured SSO connection."),
    system("adp", "ADP Workforce Now", "People", "People", "inventory", "Sample owner-provided inventory lists ADP Workforce Now for payroll and HR.", "reported", 75),
    system("quickbooks", "QuickBooks", "Finance", "Finance", "endpoint", "Sample installation inventory includes QuickBooks. Confirm its business purpose and whether it overlaps with ERP finance modules."),
    system("teams", "Microsoft Teams", "Collaboration", "IT", "endpoint", "Sample endpoint installation record for Microsoft Teams. No messages, meetings, or user accounts were read."),
    system("sharepoint", "SharePoint", "Collaboration", "IT", "m365", "Sample enterprise application registration for SharePoint. No site content, documents, or permissions were collected."),
    system("powerbi", "Power BI", "Data", "Finance", "endpoint", "Sample endpoint installation record for Power BI Desktop. No reports or datasets were read."),
    system("sql", "Microsoft SQL Server", "Data", "IT", "endpoint", "Sample installation record includes Microsoft SQL Server. Databases, tables, credentials, and business records were not examined."),
    system("dropbox", "Dropbox", "Collaboration", "", "endpoint", "Sample endpoint inventory contains Dropbox. No owner was supplied; an installation alone does not establish unauthorized use."),
    system("odoo", "Odoo", "ERP", "", "inventory", "Sample owner inventory lists an Odoo pilot with no assigned owner. Confirm whether it is active and what process it supports.", "reported", 75),
    system("maintenance", "Maintenance Tracker", "Unclassified", "", "inventory", "Sample inventory lists a local maintenance tracker with no business owner or system category.", "reported", 75),
]
systems[0]["evidence"].append(evidence("inventory", "Sample owner inventory identifies Epicor as the production planning system. Owner-reported context; not independently verified.", "reported", 75, "epicor-owner"))
systems[7]["evidence"].append(evidence("inventory", "Sample owner inventory describes a monthly CSV transfer from Epicor to Power BI. No live data flow was measured.", "reported", 75, "powerbi-owner"))
relationships = [
    {"id":"r-erp-db", "source":"epicor", "target":"sql", "label":"Production database", "status":"reported", "evidence":"SAMPLE · Operations owner reports that Epicor uses this SQL Server. The agent has not connected to either application to verify the relationship."},
    {"id":"r-erp-bi", "source":"epicor", "target":"powerbi", "label":"Monthly CSV transfer", "status":"reported", "evidence":"SAMPLE · Finance reports exporting an Epicor CSV monthly into Power BI. The transfer frequency and mechanism remain owner-reported."},
    {"id":"r-hr-fin", "source":"adp", "target":"quickbooks", "label":"Payroll journal export", "status":"reported", "evidence":"SAMPLE · Finance reports importing payroll journal exports into QuickBooks. No payroll data or integration configuration was accessed."},
]
collectors = [
    {"id":"endpoint", "name":"Installed applications", "status":"complete", "count":6, "detail":"SAMPLE · Application names from one fictional Windows workstation. Other company devices were not examined."},
    {"id":"dns", "name":"Mail domain", "status":"complete", "count":1, "detail":"SAMPLE · MX records suggest Microsoft mail routing. Email contents were not accessed."},
    {"id":"m365", "name":"Microsoft 365 applications", "status":"complete", "count":2, "detail":"SAMPLE · Two enterprise application registrations. Registration is not proof of active use or SSO configuration."},
    {"id":"inventory", "name":"Owner-provided inventory", "status":"complete", "count":5, "detail":"SAMPLE · Five system statements and three integrations reported by company owners. None were independently verified."},
    {"id":"endpoints", "name":"Approved ERP web endpoints", "status":"not_configured", "count":0, "detail":"SAMPLE · Direct ERP endpoint inspection has not been enabled. ERP findings come from endpoint and owner inventory evidence."},
]
payload = {"schema_version":"1.0", "scan_id":"demo-alder-forge-v1", "generated_at":DATE, "mode":"demo", "company":"Alder Forge", "agent_version":"0.1.0", "scope":"Fictional manufacturing company; all evidence is sample data", "systems":systems, "relationships":relationships, "collectors":collectors, "limitations":["All company names, evidence, owners, and integrations in this report are fictional demo data.","The map covers one sample endpoint and selected sample sources. Total company coverage is unknown.","Detection scores are rule-based signal strengths, not calibrated probabilities.","Integration links are owner-reported; no live data flow was measured."]}
for filename in ("demo.json", "initial.json"):
    (ROOT / "dist" / filename).write_text(json.dumps(payload, indent=2)+"\n", encoding="utf-8")
