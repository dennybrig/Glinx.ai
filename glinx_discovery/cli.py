"""Install with pip; invoke glinx or python -m glinx_discovery."""
import argparse
import json
import os
import sys
import tempfile
import urllib.error
from pathlib import Path

from . import __version__
from .collectors import collect_host, collect_dns, collect_m365, collect_endpoints, collect_csv, domain_name, endpoint_url
from .model import now, report

DEFAULT_CONFIG = {"company": "My company", "host": False, "domains": [], "m365": False, "endpoints": [], "inventory": ""}


def validate_config(config):
    if not isinstance(config, dict) or set(config) - set(DEFAULT_CONFIG):
        raise ValueError("Config contains unknown fields or is not an object")
    result = {**DEFAULT_CONFIG, **config}
    for key in ("host", "m365"):
        if type(result[key]) is not bool:
            raise ValueError(f"{key} must be true or false")
    for key in ("company", "inventory"):
        if not isinstance(result[key], str) or len(result[key]) > 500:
            raise ValueError(f"{key} must be a string of at most 500 characters")
    for key, validate in (("domains", domain_name), ("endpoints", endpoint_url)):
        values = result[key]
        if not isinstance(values, list) or len(values) > 20 or any(not isinstance(v, str) for v in values):
            raise ValueError(f"{key} must be a list of at most 20 explicit targets")
        result[key] = list(dict.fromkeys(validate(v) for v in values))
    return result


def save_json(path, payload):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".glinx-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)
            file.write("\n")
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def safe_error(error):
    if isinstance(error, urllib.error.HTTPError):
        return f"HTTP {error.code}: check source access and permissions. No response body retained."
    if isinstance(error, (ValueError, RuntimeError)):
        return str(error)[:240]
    return f"{type(error).__name__}: source unavailable. Check access, configuration, and connectivity."


def run_scan(config):
    config = validate_config(config)
    items, statuses, links = [], [], []
    jobs = [("endpoint", "Installed applications", config["host"], collect_host)]
    jobs += [("dns", "Mail DNS · " + d, True, lambda d=d: collect_dns([d])) for d in config["domains"]]
    if not config["domains"]:
        jobs.append(("dns", "Mail DNS", False, None))
    jobs.append(("m365", "Microsoft 365 applications", config["m365"], collect_m365))
    jobs += [("endpoints", "HTTPS · " + e, True, lambda e=e: collect_endpoints([e])) for e in config["endpoints"]]
    if not config["endpoints"]:
        jobs.append(("endpoints", "Approved web endpoints", False, None))
    jobs.append(("inventory", "Owner inventory", bool(config["inventory"]), lambda: collect_csv(config["inventory"])))
    for source, label, enabled, operation in jobs:
        status = {"id": source, "name": label, "status": "not_configured", "count": 0, "detail": "Not enabled; this source was not examined.", "finished_at": now()}
        if enabled:
            try:
                result = operation()
                found, detail = result[:2]
                items.extend(found)
                if len(result) > 2:
                    links.extend(result[2])
                status.update(status="complete", count=len(found), detail=detail)
            except Exception as error:
                status.update(status="error", detail=safe_error(error))
        status["finished_at"] = now()
        statuses.append(status)
    return report(config["company"], items, statuses, links)


def parser():
    root = argparse.ArgumentParser(description="Glinx discovery: a local, evidence-backed inventory of company systems.")
    root.add_argument("--version", action="version", version=__version__)
    sub = root.add_subparsers(dest="command", required=True)
    from glinx_company.cli import register_commands
    register_commands(sub)
    init = sub.add_parser("init", help="Write a config with all collectors disabled")
    init.add_argument("--output", default="glinx-config.json")
    scan = sub.add_parser("scan", help="Run only explicitly enabled collectors")
    scan.add_argument("--config")
    scan.add_argument("--company")
    scan.add_argument("--host", action="store_true", help="Read this endpoint's installation inventory")
    scan.add_argument("--domain", action="append", help="Query an approved domain's MX via Cloudflare DNS over HTTPS")
    scan.add_argument("--endpoint", action="append", help="Inspect one approved HTTPS landing page")
    scan.add_argument("--m365", action="store_true", help="Read enterprise app registrations using GLINX_M365_TOKEN")
    scan.add_argument("--inventory", help="Read an owner-supplied inventory CSV")
    scan.add_argument("--output", default="scan.json")
    scan.add_argument("--serve", action="store_true")
    scan.add_argument("--port", type=int, default=8765)
    demo = sub.add_parser("demo", help="Write a clearly labeled fictional company report")
    demo.add_argument("--output", default="scan-demo.json")
    demo.add_argument("--serve", action="store_true")
    demo.add_argument("--port", type=int, default=8765)
    serve = sub.add_parser("serve", help="Open the dashboard for an existing report or the sample company")
    serve.add_argument("--report")
    serve.add_argument("--port", type=int, default=8765)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "company":
            from glinx_company.cli import main as company_main
            return company_main(args)
        if args.command == "init":
            if Path(args.output).exists():
                raise ValueError("Config already exists; choose another --output path")
            save_json(args.output, DEFAULT_CONFIG)
            print(f"Created {args.output}. Enable only sources you are authorized to examine.")
            return 0
        if args.command == "serve":
            from .server import serve
            return serve(args.report, args.port)
        if args.command == "demo":
            from .server import web_dir
            payload = json.loads((web_dir() / "demo.json").read_text(encoding="utf-8"))
        else:
            config = dict(DEFAULT_CONFIG)
            if args.config:
                config.update(validate_config(json.loads(Path(args.config).read_text(encoding="utf-8"))))
            for key in ("company", "inventory"):
                if getattr(args, key) is not None:
                    config[key] = getattr(args, key)
            if args.host:
                config["host"] = True
            if args.m365:
                config["m365"] = True
            if args.domain is not None:
                config["domains"] = args.domain
            if args.endpoint is not None:
                config["endpoints"] = args.endpoint
            config = validate_config(config)
            if not any(config[k] for k in ("host", "domains", "m365", "endpoints", "inventory")):
                raise ValueError("No sources enabled. Use --host, --inventory, --domain, --endpoint, --m365, or --config")
            payload = run_scan(config)
        save_json(args.output, payload)
        errors = sum(c["status"] == "error" for c in payload["collectors"])
        print(f"{payload['mode'].upper()}: {len(payload['systems'])} systems; {errors} collector errors. Saved {args.output}")
        for collector in payload["collectors"]:
            print(f"  {collector['status']:16} {collector['name']}: {collector['detail']}")
        if args.serve:
            from .server import serve
            serve(args.output, args.port)
        return 2 if errors else 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("Glinx: " + safe_error(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
