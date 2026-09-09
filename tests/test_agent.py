import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from glinx_discovery.cli import main, run_scan, validate_config
from glinx_discovery.collectors import collect_csv, collect_m365, collect_host, domain_name, endpoint_url, graph_url, collect_dns, m365_token, NoRedirect
from glinx_discovery.model import finding, merge_findings


class AgentTests(unittest.TestCase):
    def test_merges_evidence_without_duplicate_records(self):
        first = finding("Epicor", "ERP", "endpoint", "Installation entry", confidence=90)
        second = finding("Epicor", "ERP", "inventory", "Owner reports planning system", "reported", 75, "Operations")
        result = merge_findings([first, second, first])
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]["evidence"]), 2)
        self.assertEqual(result[0]["owner"], "Operations")
        self.assertEqual(result[0]["status"], "observed")
        self.assertEqual(len(first["evidence"]), 1)

    def test_default_does_not_touch_network_or_endpoint(self):
        with patch("glinx_discovery.cli.collect_host") as host, patch("glinx_discovery.cli.collect_m365") as graph:
            data = run_scan({})
        host.assert_not_called()
        graph.assert_not_called()
        self.assertFalse(data["systems"])
        self.assertTrue(all(c["status"] == "not_configured" for c in data["collectors"]))

    def test_invalid_scope_rejected_before_collector_execution(self):
        for config in ({"domains": ["*.example.com"]}, {"host": "true"}, {"token": "secret"}, {"endpoints": ["https://u:p@erp.example.com"]}, {"domains": ["10.0.0.0/24"]}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                validate_config(config)

    def test_continuations_cannot_leak_bearer_token(self):
        for url in ("https://evil.example/v1.0/servicePrincipals", "https://graph.microsoft.com@evil.example/v1.0/servicePrincipals", "http://graph.microsoft.com/v1.0/servicePrincipals", "https://graph.microsoft.com/v1.0/users"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                graph_url(url)

    def test_m365_pagination_filters_managed_identities_and_never_serializes_token(self):
        page1 = {"value": [{"id":"a", "displayName":"Salesforce", "servicePrincipalType":"Application"}], "@odata.nextLink":"https://graph.microsoft.com/v1.0/servicePrincipals?$skiptoken=next"}
        page2 = {"value": [{"id":"b", "displayName":"Managed identity", "servicePrincipalType":"ManagedIdentity"}, {"id":"c", "displayName":"Odoo", "servicePrincipalType":"Application"}]}
        with patch.dict(os.environ, {"GLINX_M365_TOKEN":"private-test-token"}), patch("glinx_discovery.collectors.request", side_effect=[(json.dumps(page1).encode(), {}),(json.dumps(page2).encode(), {})]) as req:
            assets, detail = collect_m365()
        self.assertEqual(len(assets), 2)
        self.assertEqual(req.call_count, 2)
        self.assertNotIn("private-test-token", json.dumps(assets))
        self.assertFalse(any(a["category"] == "People" for a in assets))

    def test_m365_unsafe_next_page_is_rejected_before_request(self):
        page = {"value": [], "@odata.nextLink":"https://evil.example/steal"}
        with patch.dict(os.environ, {"GLINX_M365_TOKEN":"private-test-token"}), patch("glinx_discovery.collectors.request", return_value=(json.dumps(page).encode(), {})) as req:
            with self.assertRaises(ValueError):
                collect_m365()
        self.assertEqual(req.call_count, 1)

    def test_client_credentials_use_fixed_microsoft_origin_and_keep_secret_out_of_report(self):
        tenant = "11111111-1111-1111-1111-111111111111"
        client = "22222222-2222-2222-2222-222222222222"
        env = {"GLINX_M365_TOKEN":"", "GLINX_M365_TENANT_ID":tenant, "GLINX_M365_CLIENT_ID":client, "GLINX_M365_CLIENT_SECRET":"synthetic-secret"}
        with patch.dict(os.environ, env), patch("glinx_discovery.collectors.request", return_value=(b'{"access_token":"short-lived"}', {})) as req:
            self.assertEqual(m365_token(), "short-lived")
        self.assertEqual(req.call_args.args[0], f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token")
        self.assertIn(b"grant_type=client_credentials", req.call_args.kwargs["data"])

    def test_redirects_are_not_followed(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://evil.example"))

    def test_dns_lookalike_hostname_does_not_match_microsoft(self):
        response = {"Status":0,"Answer":[{"type":15,"data":"0 mail.protection.outlook.com.evil.example."}]}
        with patch("glinx_discovery.collectors.request", return_value=(json.dumps(response).encode(),{})):
            assets, _ = collect_dns(["example.com"])
        self.assertNotEqual(assets[0]["name"], "Microsoft 365")

    def test_one_failed_domain_does_not_erase_other_sources(self):
        good = finding("Microsoft 365", "Email", "dns", "MX clue", "inferred", 60)
        with patch("glinx_discovery.cli.collect_dns", side_effect=[([good], "Read approved domain"), OSError("sensitive private path")]):
            data = run_scan({"domains":["example.com", "example.org"]})
        self.assertEqual(len(data["systems"]), 1)
        self.assertEqual(sum(c["status"] == "error" for c in data["collectors"]), 1)
        self.assertNotIn("sensitive private path", json.dumps(data))

    def test_csv_relationships_are_reported_not_invented(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "inventory.csv"
            path.write_text("name,category,owner,connects_to,relationship\nEpicor,ERP,Operations,SQL Server,Reported database\nSQL Server,Data,IT,,\n", encoding="utf-8")
            assets, _, links = collect_csv(path)
        self.assertEqual(len(assets), 2)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["status"], "reported")
        self.assertEqual(links[0]["source"], assets[0]["id"])
        self.assertTrue(all(a["status"] == "reported" for a in assets))

    def test_csv_unknown_relationship_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "inventory.csv"
            path.write_text("name,connects_to\nEpicor,Missing system\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                collect_csv(path)

    def test_host_reads_names_and_produces_no_integration(self):
        with patch("glinx_discovery.collectors.local_inventory", return_value=["Epicor Kinetic", "SAP Business One", "unknown-library"]), patch("glinx_discovery.collectors.platform.system", return_value="Linux"):
            data = run_scan({"host":True})
        self.assertEqual(len(data["systems"]), 3)
        self.assertFalse(data["relationships"])
        self.assertTrue(all(a["evidence"] for a in data["systems"]))

    def test_dns_provider_is_only_inferred(self):
        response = {"Status":0,"Answer":[{"type":15,"data":"0 example-com.mail.protection.outlook.com."}]}
        with patch("glinx_discovery.collectors.request", return_value=(json.dumps(response).encode(),{})):
            assets, _ = collect_dns(["example.com"])
        self.assertEqual(assets[0]["name"], "Microsoft 365")
        self.assertEqual(assets[0]["status"], "inferred")

    def test_cli_partial_scan_returns_nonzero_and_preserves_report(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"GLINX_M365_TOKEN":""}), patch("sys.stdout", new_callable=io.StringIO):
            output = Path(folder) / "scan.json"
            code = main(["scan", "--m365", "--output", str(output)])
            data = json.loads(output.read_text())
            if os.name != "nt":
                self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        self.assertEqual(code, 2)
        self.assertEqual(data["mode"], "live")
        self.assertFalse(data["systems"])
        self.assertTrue(any(c["status"] == "error" for c in data["collectors"]))

    def test_cli_requires_scope(self):
        with patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(main(["scan"]), 1)

    def test_domains_and_endpoints_enforce_explicit_targets(self):
        self.assertEqual(domain_name("Example.COM."), "example.com")
        self.assertEqual(endpoint_url("https://erp.example.com:8443/"), "https://erp.example.com:8443/")
        for url in ("http://erp.example.com", "https://erp.example.com/?token=something", "https://erp.example.com:22"):
            with self.assertRaises(ValueError):
                endpoint_url(url)


if __name__ == "__main__":
    unittest.main()
