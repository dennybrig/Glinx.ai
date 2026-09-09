"""Conservative product fingerprints. No claim of exhaustive coverage."""
import re

CATALOG = [
    (r"\b(epicor|kinetic erp)\b", "Epicor", "ERP"),
    (r"\bsap\b|\bsap business one\b", "SAP", "ERP"),
    (r"\bnetsuite\b", "Oracle NetSuite", "ERP"),
    (r"\b(odoo|openerp)\b", "Odoo", "ERP"),
    (r"\b(dynamics 365|business central|dynamics nav|dynamics ax)\b", "Microsoft Dynamics", "ERP"),
    (r"\b(syteline|infor)\b", "Infor", "ERP"),
    (r"\b(quickbooks|intuit quickbooks)\b", "QuickBooks", "Finance"),
    (r"\bsage (50|100|200|300|intacct)\b", "Sage", "Finance"),
    (r"\bxero\b", "Xero", "Finance"),
    (r"\bsalesforce\b", "Salesforce", "CRM"),
    (r"\bhubspot\b", "HubSpot", "CRM"),
    (r"\bworkday\b", "Workday", "People"),
    (r"\b(adp workforce|adp)\b", "ADP", "People"),
    (r"\bbamboohr\b", "BambooHR", "People"),
    (r"\b(microsoft 365|office 365|exchange online)\b", "Microsoft 365", "Email"),
    (r"\boutlook\b", "Microsoft Outlook", "Email"),
    (r"\b(google workspace|g suite)\b", "Google Workspace", "Email"),
    (r"\bslack\b", "Slack", "Collaboration"),
    (r"\b(microsoft teams|teams)\b", "Microsoft Teams", "Collaboration"),
    (r"\bsharepoint\b", "SharePoint", "Collaboration"),
    (r"\bdropbox\b", "Dropbox", "Collaboration"),
    (r"\b(power bi|powerbi)\b", "Power BI", "Data"),
    (r"\btableau\b", "Tableau", "Data"),
    (r"\bpostgres(?:ql)?(?:[-\d.]*|\.service)\b", "PostgreSQL", "Data"),
    (r"\b(mysql|mariadb)\b", "MySQL / MariaDB", "Data"),
    (r"\b(mssql|sql server)\b", "Microsoft SQL Server", "Data"),
    (r"\bdocker\b", "Docker", "Infrastructure"),
]


def identify(text):
    for pattern, name, category in CATALOG:
        if re.search(pattern, text, re.I):
            return name, category
    return None
