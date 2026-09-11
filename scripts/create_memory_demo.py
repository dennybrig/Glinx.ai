"""Generate the hosted fictional history with the real SQLite memory engine."""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from glinx_company.demo import create_demo

with tempfile.TemporaryDirectory() as folder:
    payload = create_demo(Path(folder) / "alder.db")
    (ROOT / "dist" / "memory-demo.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Generated Alder Forge memory: " + str(payload["views"][-1]["counts"]))
