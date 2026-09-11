"""Small, explicit CLI workflows for company memory."""
import json
import sqlite3
from pathlib import Path

from glinx_discovery.cli import save_json
from .contracts import read_report
from .demo import SCOPE, create_demo
from .store import CompanyStore, create_company


def write_export(path, payload, database):
    from glinx_discovery.server import web_dir
    destination = Path(path).expanduser().resolve()
    if destination == Path(database).expanduser().resolve():
        raise ValueError("An export cannot overwrite its company database")
    if payload["company"]["mode"] == "live" and web_dir().resolve() in destination.parents:
        raise ValueError("Live company exports must stay outside the public dashboard directory")
    save_json(destination, payload)


def register_commands(sub):
    root = sub.add_parser("company", help="Persist and compare company discovery history")
    commands = root.add_subparsers(dest="company_command", required=True)
    init = commands.add_parser("init", help="Create a new company database")
    init.add_argument("--db", required=True)
    init.add_argument("--name", required=True)
    init.add_argument("--purpose", default="")
    demo = commands.add_parser("demo", help="Store Alder Forge's three fictional reports and open its memory")
    demo.add_argument("--db", default="company-demo.db")
    demo.add_argument("--output")
    demo.add_argument("--serve", action="store_true")
    demo.add_argument("--port", type=int, default=8765)
    for name, help_text in (("import", "Import a supplied report into an explicit collection scope"), ("history", "List saved snapshots"), ("diff", "Compare snapshots in a scope revision"), ("export", "Export history for the browser viewer"), ("serve", "View saved company memory locally")):
        p = commands.add_parser(name, help=help_text)
        p.add_argument("--db", required=True)
        p.add_argument("--scope-id", required=True)
        p.add_argument("--scope-revision", type=int, default=1)
        if name == "import":
            p.add_argument("report")
            p.add_argument("--scope-description")
        if name == "diff":
            p.add_argument("--before", help="Internal run ID; defaults to the penultimate snapshot")
            p.add_argument("--after", help="Internal run ID; defaults to the latest snapshot")
        if name == "export":
            p.add_argument("--output", default="company-memory.json")
        if name == "serve":
            p.add_argument("--port", type=int, default=8765)


def serve_memory(payload, port):
    from http.server import ThreadingHTTPServer
    from glinx_discovery.server import handler_for
    if not 1024 <= port <= 65535:
        raise ValueError("Choose a port from 1024 to 65535")
    with ThreadingHTTPServer(("127.0.0.1", port), handler_for(payload["runs"][-1]["report"], port, memory_payload=payload)) as server:
        print(f"Glinx company memory: http://127.0.0.1:{port}/memory.html (Ctrl+C to stop)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


def main(args):
    try:
        command = args.company_command
        if command == "init":
            create_company(args.db, args.name, args.purpose)
            print("Created company memory for " + args.name)
            return 0
        if command == "demo":
            payload = create_demo(args.db)
            print(f"Alder Forge: {len(payload['runs'])} saved snapshots; {payload['views'][-1]['counts']['remembered']} remembered systems.")
            if args.output:
                write_export(args.output, payload, args.db)
            return serve_memory(payload, args.port) if args.serve else 0
        with CompanyStore(args.db) as store:
            if command == "import":
                result = store.import_report(read_report(args.report), args.scope_id, args.scope_revision, args.scope_description)
                print(("Imported" if result["created"] else "Already stored") + " snapshot " + result["run_id"])
                return 0
            if command == "history":
                runs = store.runs(args.scope_id, args.scope_revision)
                for run in runs:
                    print(f"{run['run_id']}  {run['generated_at']}  {len(run['report']['systems'])} systems in scan")
                print(f"{len(runs)} snapshots in scope {args.scope_id}, revision {args.scope_revision}")
                return 0
            if command == "diff":
                print(json.dumps(store.diff(args.scope_id, args.scope_revision, args.before, args.after), indent=2, ensure_ascii=False))
                return 0
            payload = store.export(args.scope_id, args.scope_revision)
        if command == "export":
            write_export(args.output, payload, args.db)
            print(f"Saved {len(payload['runs'])} snapshots to {args.output}")
            return 0
        return serve_memory(payload, args.port)
    except sqlite3.Error as error:
        # Do not print SQL, raw records, or database contents on failure.
        raise ValueError(f"Company database unavailable ({type(error).__name__}); check the file and retry when it is not locked") from None
