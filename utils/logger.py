from pathlib import Path
import json
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
LOG_FILE = BASE_DIR / "data" / "logs" / "run_log.jsonl"


def _ensure_log_dir():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def log_run(run_id, scenario_id, scenario_name, model, parameters, results_summary, timing, status):
    _ensure_log_dir()
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "run_id": run_id,
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "model": model,
        "status": status,
        "parameters": parameters,
        "results_summary": results_summary,
        "timing": timing,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def get_recent_logs(limit=50):
    _ensure_log_dir()
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    records = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(records))[-limit:]
