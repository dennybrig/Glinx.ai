"""One company per local SQLite file. Report imports are atomic and idempotent."""
import json
import os
import sqlite3
import uuid
from pathlib import Path

from .contracts import canonical, digest, now, text, timestamp, validate_report
from .projection import compare, project

SCHEMA = """
CREATE TABLE company (singleton INTEGER PRIMARY KEY CHECK(singleton=1), id TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL, purpose TEXT NOT NULL, mode TEXT CHECK(mode IN ('demo','live')));
CREATE TABLE scopes (id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0), description TEXT NOT NULL,
 PRIMARY KEY(id,revision));
CREATE TABLE runs (sequence INTEGER PRIMARY KEY, run_id TEXT NOT NULL UNIQUE, scope_id TEXT NOT NULL,
 scope_revision INTEGER NOT NULL, generated_at TEXT NOT NULL, imported_at TEXT NOT NULL,
 digest TEXT NOT NULL, legacy_scan_id TEXT NOT NULL, report_json TEXT NOT NULL,
 FOREIGN KEY(scope_id,scope_revision) REFERENCES scopes(id,revision), UNIQUE(scope_id,scope_revision,digest));
CREATE INDEX idx_runs_scope_time ON runs(scope_id,scope_revision,generated_at,sequence);
PRAGMA user_version=1;
"""


def database_path(path):
    path = Path(path).expanduser().resolve()
    from glinx_discovery.server import web_dir
    if path == web_dir().resolve() or web_dir().resolve() in path.parents:
        raise ValueError("Company databases must be outside the public dashboard directory")
    return path


def create_company(path, name, purpose="", company_id=None):
    text(name, "Company name", 200)
    text(purpose, "Company purpose", 1000, empty=True)
    path = database_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation never replaces an existing company database.
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    db = None
    try:
        db = sqlite3.connect(path)
        db.executescript(SCHEMA)
        db.execute("INSERT INTO company(singleton,id,name,purpose) VALUES(1,?,?,?)", (company_id or str(uuid.uuid4()), name, purpose))
        db.commit()
    except Exception:
        if db:
            db.close()
        path.unlink(missing_ok=True)
        raise
    finally:
        if db:
            db.close()
    return path


class CompanyStore:
    def __init__(self, path):
        path = database_path(path)
        if not path.is_file():
            raise ValueError("Company database does not exist; run glinx company init first")
        self.db = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=3, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        if self.db.execute("PRAGMA user_version").fetchone()[0] != 1:
            self.db.close()
            raise ValueError("Unsupported company database version")
        try:
            self.profile()
        except Exception:
            self.db.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()

    def profile(self):
        row = self.db.execute("SELECT id,name,purpose,mode FROM company WHERE singleton=1").fetchone()
        if row is None:
            raise ValueError("Company database has no profile")
        return dict(row)

    def import_report(self, report, scope_id, revision=1, description=None):
        validate_report(report)
        text(scope_id, "Scope ID", 100)
        if type(revision) is not int or not 1 <= revision <= 1000000:
            raise ValueError("Scope revision must be a positive integer")
        if description is not None:
            text(description, "Scope description", 1000)
        encoded, fingerprint = canonical(report), digest(report)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            profile = self.profile()
            if report["company"] != profile["name"]:
                raise ValueError("Report company label differs from this database; select the correct company database")
            if profile["mode"] and profile["mode"] != report["mode"]:
                raise ValueError("Demo and live evidence require separate company databases")
            scope = self.db.execute("SELECT description FROM scopes WHERE id=? AND revision=?", (scope_id, revision)).fetchone()
            if scope and description is not None and description != scope["description"]:
                raise ValueError("Scope description changed; use a new scope revision")
            self.db.execute("INSERT OR IGNORE INTO scopes(id,revision,description) VALUES(?,?,?)", (scope_id, revision, description or "User-designated collection boundary; original configuration is not authenticated by report 1.0."))
            existing = self.db.execute("SELECT run_id FROM runs WHERE scope_id=? AND scope_revision=? AND digest=?", (scope_id, revision, fingerprint)).fetchone()
            if existing:
                self.db.execute("COMMIT")
                return {"run_id": existing["run_id"], "created": False}
            run_id = str(uuid.uuid4())
            self.db.execute("INSERT INTO runs(run_id,scope_id,scope_revision,generated_at,imported_at,digest,legacy_scan_id,report_json) VALUES(?,?,?,?,?,?,?,?)",
                            (run_id, scope_id, revision, timestamp(report["generated_at"]), now(), fingerprint, report["scan_id"], encoded))
            self.db.execute("UPDATE company SET mode=? WHERE singleton=1", (report["mode"],))
            self.db.execute("COMMIT")
            return {"run_id": run_id, "created": True}
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def runs(self, scope_id, revision=1):
        rows = self.db.execute("SELECT run_id,generated_at,imported_at,legacy_scan_id,report_json FROM runs WHERE scope_id=? AND scope_revision=? ORDER BY generated_at,sequence", (scope_id, revision))
        return [{**{k: row[k] for k in ("run_id", "generated_at", "imported_at", "legacy_scan_id")}, "report": json.loads(row["report_json"])} for row in rows]

    def scopes(self):
        return [dict(row) for row in self.db.execute("SELECT id,revision,description FROM scopes ORDER BY id,revision")]

    def diff(self, scope_id, revision=1, before=None, after=None):
        runs = self.runs(scope_id, revision)
        if len(runs) < 2:
            raise ValueError("Import at least two reports into the same scope revision to compare")
        return compare(runs, before or runs[-2]["run_id"], after or runs[-1]["run_id"])

    def export(self, scope_id, revision=1):
        runs = self.runs(scope_id, revision)
        if not runs:
            raise ValueError("No saved reports exist for this scope revision")
        if len(runs) > 20:
            raise ValueError("Browser history export is limited to 20 snapshots; use company diff for this larger history")
        scope = self.db.execute("SELECT id,revision,description FROM scopes WHERE id=? AND revision=?", (scope_id, revision)).fetchone()
        result = {"company_memory_version": "1.0", "company": self.profile(), "scope": dict(scope), "runs": runs,
                  "views": [project(runs[:i + 1]) for i in range(len(runs))],
                  "comparisons": [compare(runs, runs[a]["run_id"], runs[b]["run_id"]) for b in range(len(runs)) for a in range(b)]}
        if any(len(view["systems"]) > 5000 or len(view["relationships"]) > 10000 for view in result["views"]):
            raise ValueError("Browser history is limited to 5,000 remembered systems and 10,000 connections; use company diff")
        if len(canonical(result).encode("utf-8")) > 15_000_000:
            raise ValueError("Browser history export exceeds 15 MB; use company diff")
        return result
