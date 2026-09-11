"""Validate supplied reports before storing them; no source authenticity is implied."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from glinx_discovery.model import CATEGORIES, STATES

MAX_REPORT_BYTES = 5_000_000


def text(value, name, limit=600, empty=False):
    if not isinstance(value, str) or len(value) > limit or (not empty and not value.strip()):
        raise ValueError(f"{name} must be a {'possibly empty ' if empty else ''}string of at most {limit} characters")
    return value


def timestamp(value):
    text(value, "Timestamp", 60)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError()
        return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds")
    except (ValueError, OverflowError):
        raise ValueError("Timestamps must include a valid date, time, and UTC offset") from None


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (ValueError, TypeError, RecursionError):
        raise ValueError("Report contains unsupported JSON values or nesting") from None


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def collection(value, name, limit):
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError(f"{name} must be a list of at most {limit} records")
    return value


def score(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 100:
        raise ValueError("Detection score must be a finite number from 0 to 100")


def state(value):
    if not isinstance(value, str) or value not in STATES:
        raise ValueError("Evidence state must be observed, reported, or inferred")


def validate_report(report):
    if not isinstance(report, dict) or report.get("schema_version") != "1.0":
        raise ValueError("Company memory accepts Glinx report schema 1.0")
    if report.get("mode") not in ("demo", "live"):
        raise ValueError("Report must explicitly declare demo or live mode")
    text(report.get("company"), "Company", 200)
    text(report.get("scan_id"), "Scan ID", 100)
    timestamp(report.get("generated_at"))
    ids = set()
    for item in collection(report.get("systems"), "Systems", 5000):
        if not isinstance(item, dict):
            raise ValueError("System must be an object")
        ident = text(item.get("id"), "System ID", 100)
        if ident in ids:
            raise ValueError("System IDs must be unique within a report")
        ids.add(ident)
        text(item.get("name"), "System name", 200)
        text(item.get("owner"), "Owner", 200, empty=True)
        if item.get("category") not in tuple(CATEGORIES):
            raise ValueError("System category is unsupported")
        state(item.get("status"))
        score(item.get("confidence"))
        evidence = collection(item.get("evidence"), "Evidence", 1000)
        if not evidence:
            raise ValueError("Every system requires evidence")
        for e in evidence:
            if not isinstance(e, dict):
                raise ValueError("Evidence must be an object")
            for key, limit in (("id", 100), ("source", 100), ("summary", 600), ("locator", 500)):
                text(e.get(key), "Evidence " + key, limit, empty=key == "locator")
            timestamp(e.get("observed_at"))
            state(e.get("status"))
            score(e.get("confidence"))
        if not isinstance(item.get("attributes", {}), dict):
            raise ValueError("System attributes must be an object")
    link_ids = set()
    for link in collection(report.get("relationships"), "Relationships", 10000):
        if not isinstance(link, dict):
            raise ValueError("Relationship must be an object")
        ident = text(link.get("id"), "Relationship ID", 100)
        source = text(link.get("source"), "Relationship source", 100)
        target = text(link.get("target"), "Relationship target", 100)
        if ident in link_ids or source not in ids or target not in ids or source == target:
            raise ValueError("Relationship IDs and endpoints must be valid and unique")
        link_ids.add(ident)
        text(link.get("label"), "Relationship label", 200)
        text(link.get("evidence"), "Relationship evidence", 600)
        state(link.get("status"))
    for source in collection(report.get("collectors"), "Collectors", 100):
        if not isinstance(source, dict):
            raise ValueError("Collector must be an object")
        text(source.get("id"), "Collector ID", 100)
        text(source.get("name"), "Collector name", 500)
        text(source.get("detail"), "Collector detail", 600, empty=True)
        if source.get("status") not in ("complete", "error", "not_configured"):
            raise ValueError("Invalid collector status")
        if type(source.get("count")) is not int or source["count"] < 0:
            raise ValueError("Collector count must be a nonnegative integer")
    for limit in collection(report.get("limitations", []), "Limitations", 20):
        text(limit, "Limitation", 600)
    if len(canonical(report).encode("utf-8")) > MAX_REPORT_BYTES:
        raise ValueError("Report exceeds 5 MB")
    return report


def read_report(path):
    with Path(path).open("rb") as handle:
        raw = handle.read(MAX_REPORT_BYTES + 1)
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError("Report exceeds 5 MB")
    try:
        return validate_report(json.loads(raw))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("The file is not a valid UTF-8 JSON report") from None
