from flask import Blueprint, jsonify
from pathlib import Path
import json

results_bp = Blueprint("results", __name__)

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "data" / "results"


def _load_run(run_id):
    run_dir = RESULTS_DIR / run_id
    if not run_dir.exists():
        return None
    data = {}
    for path in run_dir.iterdir():
        if path.suffix == ".json":
            try:
                with path.open("r", encoding="utf-8") as f:
                    data[path.stem] = json.load(f)
            except (json.JSONDecodeError, OSError):
                data[path.stem] = None
        elif path.suffix == ".txt":
            try:
                with path.open("r", encoding="utf-8") as f:
                    data[path.stem] = f.read()
            except OSError:
                data[path.stem] = None
    return data


@results_bp.route("/results", methods=["GET"])
def list_results():
    runs = []
    if not RESULTS_DIR.exists():
        return jsonify([])
    for run_dir in sorted(RESULTS_DIR.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        meta_path = run_dir / "metadata.json"
        if meta_path.exists():
            try:
                with meta_path.open("r", encoding="utf-8") as f:
                    runs.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue
    return jsonify(runs)


@results_bp.route("/results/<run_id>", methods=["GET"])
def get_result(run_id):
    data = _load_run(run_id)
    if data is None:
        return jsonify({"error": "Run not found"}), 404
    return jsonify(data)


@results_bp.route("/results/<run_id_a>/compare/<run_id_b>", methods=["GET"])
def compare_results(run_id_a, run_id_b):
    run_a = _load_run(run_id_a)
    run_b = _load_run(run_id_b)
    if run_a is None:
        return jsonify({"error": f"Run {run_id_a} not found"}), 404
    if run_b is None:
        return jsonify({"error": f"Run {run_id_b} not found"}), 404
    return jsonify({"run_a": run_a, "run_b": run_b})
