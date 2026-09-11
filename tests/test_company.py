import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from glinx_company.cli import write_export
from glinx_company.contracts import read_report, validate_report
from glinx_company.demo import COMPANY_ID, SCOPE, create_demo, reports
from glinx_company.store import CompanyStore, create_company
from glinx_discovery.server import handler_for

ROOT = Path(__file__).resolve().parents[1]


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "company.db"
        create_company(self.path, "Alder Forge")
        self.baseline, self.followup, self.outage = reports()

    def test_restart_and_formatting_only_reimport_preserve_one_run(self):
        with CompanyStore(self.path) as store:
            first = store.import_report(self.baseline, "workstation")
        with CompanyStore(self.path) as reopened:
            duplicate = reopened.import_report(json.loads(json.dumps(self.baseline, sort_keys=True)), "workstation")
            self.assertEqual(duplicate, {"run_id": first["run_id"], "created": False})
            self.assertEqual(reopened.runs("workstation")[0]["report"], self.baseline)

    def test_legacy_scan_id_collision_keeps_different_content(self):
        changed = deepcopy(self.baseline)
        changed["systems"][0]["owner"] = "New owner claim"
        with CompanyStore(self.path) as store:
            a = store.import_report(self.baseline, "pilot")
            b = store.import_report(changed, "pilot")
            self.assertNotEqual(a["run_id"], b["run_id"])
            self.assertEqual(len(store.runs("pilot")), 2)
            self.assertEqual(store.diff("pilot")["system_changes"][0]["fields"][0]["field"], "owner")

    def test_timestamp_refresh_is_not_a_semantic_change(self):
        refreshed = deepcopy(self.baseline)
        refreshed["generated_at"] = "2026-09-10T09:42:00Z"
        for item in refreshed["systems"]:
            for e in item["evidence"]:
                e["observed_at"] = refreshed["generated_at"]
        with CompanyStore(self.path) as store:
            store.import_report(self.baseline, "pilot")
            store.import_report(refreshed, "pilot")
            diff = store.diff("pilot")
            self.assertFalse(diff["system_changes"] or diff["relationship_changes"] or diff["source_changes"])

    def test_failed_and_successful_sources_have_distinct_absence_states(self):
        with CompanyStore(self.path) as store:
            for report in reports():
                store.import_report(report, "pilot")
            export = store.export("pilot")
        view = export["views"][-1]
        systems = {s["record"]["id"]: s for s in view["systems"]}
        self.assertEqual(view["counts"], {"remembered": 13, "seen": 10, "unavailable": 2, "not_seen": 1})
        self.assertEqual(systems["salesforce"]["visibility"], "unavailable")
        self.assertEqual(systems["odoo"]["visibility"], "not_seen")
        self.assertEqual(systems["salesforce"]["record"], next(s for s in self.followup["systems"] if s["id"] == "salesforce"))
        self.assertTrue(all(s["identity_resolution"] == "legacy_product_aggregate" for s in systems.values()))

    def test_recovery_reuses_history_instead_of_discovering_a_new_system(self):
        restored = deepcopy(self.followup)
        restored["generated_at"] = "2026-09-12T09:42:00Z"
        with CompanyStore(self.path) as store:
            for report in [self.baseline, self.followup, self.outage, restored]:
                store.import_report(report, "pilot")
            changes = store.diff("pilot")["system_changes"]
        self.assertEqual({c["id"] for c in changes if c["kind"] == "seen_again"}, {"salesforce", "sharepoint", "odoo"})
        self.assertFalse(any(c["kind"] == "added" for c in changes))

    def test_out_of_order_import_and_no_future_knowledge(self):
        with CompanyStore(self.path) as store:
            for report in [self.outage, self.baseline, self.followup]:
                store.import_report(report, "pilot")
            payload = store.export("pilot")
        self.assertEqual(payload["runs"][0]["legacy_scan_id"], self.baseline["scan_id"])
        self.assertEqual(payload["views"][0]["counts"]["remembered"], 12)
        self.assertFalse(any(s["record"]["id"] == "fiix" for s in payload["views"][0]["systems"]))

    def test_scope_and_revision_boundaries_cannot_be_compared(self):
        with CompanyStore(self.path) as store:
            a = store.import_report(self.baseline, "A", description="First workstation")
            b = store.import_report(self.followup, "B")
            c = store.import_report(self.followup, "A", revision=2)
            store.import_report(self.outage, "A")
            for other in (b, c):
                with self.assertRaises(ValueError):
                    store.diff("A", before=a["run_id"], after=other["run_id"])
            with self.assertRaisesRegex(ValueError, "new scope revision"):
                store.import_report(self.followup, "A", description="Different workstation")

    def test_company_names_and_modes_do_not_cross_boundaries(self):
        foreign = deepcopy(self.followup)
        foreign["company"] = "Another company"
        live = deepcopy(self.followup)
        live["mode"] = "live"
        with CompanyStore(self.path) as store:
            store.import_report(self.baseline, "pilot")
            for report in (foreign, live):
                with self.assertRaises(ValueError):
                    store.import_report(report, "new-scope")
            self.assertEqual(len(store.scopes()), 1)
            self.assertEqual(len(store.runs("pilot")), 1)
        other = Path(self.temp.name) / "other.db"
        create_company(other, "Alder Forge")
        with CompanyStore(other) as store:
            self.assertEqual(store.runs("pilot"), [])

    def test_invalid_report_and_mid_import_failure_are_atomic(self):
        invalid = deepcopy(self.baseline)
        invalid["relationships"][0]["target"] = "unknown"
        with CompanyStore(self.path) as store:
            with self.assertRaises(ValueError):
                store.import_report(invalid, "pilot")
            store.db.execute("CREATE TEMP TRIGGER fail_import BEFORE INSERT ON runs BEGIN SELECT RAISE(ABORT,'simulated failure'); END")
            with self.assertRaises(sqlite3.IntegrityError):
                store.import_report(self.baseline, "pilot")
            self.assertEqual(store.scopes(), [])
            self.assertIsNone(store.profile()["mode"])
            self.assertEqual(store.runs("pilot"), [])

    def test_invalid_timestamp_score_and_oversized_file_fail(self):
        for update in ({"generated_at": "2026-09-10"}, {"generated_at": "not a date"}):
            with self.assertRaises(ValueError):
                validate_report({**self.baseline, **update})
        bad = deepcopy(self.baseline)
        bad["systems"][0]["confidence"] = float("nan")
        with self.assertRaises(ValueError):
            validate_report(bad)
        path = Path(self.temp.name) / "too-big.json"
        path.write_bytes(b" " * 5_000_001)
        with self.assertRaisesRegex(ValueError, "5 MB"):
            read_report(path)

    def test_existing_database_and_live_public_export_are_protected(self):
        original = self.path.read_bytes()
        with self.assertRaises(FileExistsError):
            create_company(self.path, "Replacement")
        self.assertEqual(self.path.read_bytes(), original)
        with self.assertRaisesRegex(ValueError, "overwrite"):
            write_export(self.path, {"company": {"mode": "demo"}}, self.path)
        with self.assertRaisesRegex(ValueError, "public"):
            write_export(ROOT / "dist" / "test-live.json", {"company": {"mode": "live"}}, self.path)

    def test_owner_and_relationship_evidence_is_retained_without_promotion(self):
        with CompanyStore(self.path) as store:
            for report in (self.baseline, self.followup):
                store.import_report(report, "pilot")
            view = store.export("pilot")["views"][-1]
        dropbox = next(s for s in view["systems"] if s["record"]["id"] == "dropbox")
        self.assertEqual(dropbox["owner_claims"][0]["status"], "reported")
        self.assertEqual(len(dropbox["history"]), 2)
        self.assertTrue(all(r["record"]["status"] == "reported" for r in view["relationships"]))

    def test_demo_is_repeatable_and_does_not_overwrite_other_company(self):
        demo_path = Path(self.temp.name) / "demo.db"
        first, second = create_demo(demo_path), create_demo(demo_path)
        self.assertEqual([r["run_id"] for r in first["runs"]], [r["run_id"] for r in second["runs"]])
        self.assertEqual(second["company"]["id"], COMPANY_ID)
        with self.assertRaises(ValueError):
            create_demo(self.path)

    def test_cli_restart_export_and_diff(self):
        path = Path(self.temp.name) / "cli.db"
        output = Path(self.temp.name) / "history.json"
        result = subprocess.run([sys.executable, "-m", "glinx_discovery", "company", "demo", "--db", str(path)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, "-m", "glinx_discovery", "company", "export", "--db", str(path), "--scope-id", SCOPE, "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text())["views"][-1]["counts"]["remembered"], 13)
        result = subprocess.run([sys.executable, "-m", "glinx_discovery", "company", "diff", "--db", str(path), "--scope-id", SCOPE], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["system_changes"]), 3)

    def test_selected_history_server_has_no_arbitrary_file_or_write_route(self):
        payload = create_demo(Path(self.temp.name) / "demo.db")

        class Connection:
            def __init__(self, request):
                self.request = io.BytesIO(request)
                self.output = b""
            def makefile(self, *args, **kwargs):
                return self.request
            def sendall(self, data):
                self.output += data

        def request(path, host="127.0.0.1:8765", method="GET"):
            connection = Connection(f"{method} {path} HTTP/1.0\r\nHost: {host}\r\n\r\n".encode())
            handler_for(self.baseline, 8765, memory_payload=payload)(connection, ("127.0.0.1", 1), object())
            return connection.output

        self.assertIn(b"200 OK", request("/memory-demo.json"))
        self.assertIn(COMPANY_ID.encode(), request("/memory-demo.json"))
        self.assertIn(b"404", request("/../company.db"))
        self.assertIn(b"403", request("/memory-demo.json", host="attacker.invalid"))
        self.assertIn(b"501", request("/memory-demo.json", method="POST"))


if __name__ == "__main__":
    unittest.main()
