from flask import Blueprint, request, jsonify, Response
from pathlib import Path
import json, uuid, time, csv, io
from datetime import datetime

from pipeline.orchestrator import run_clews_only, run_og_only, run_coupled, run_converging
from pipeline.validation import validate_parameters
from utils.logger import log_run

simulate_bp = Blueprint("simulate", __name__)

BASE_DIR      = Path(__file__).parent.parent
SCENARIOS_DIR = BASE_DIR / "data" / "scenarios"
RESULTS_DIR   = BASE_DIR / "data" / "results"


def _load_scenario(scenario_id):
    path = SCENARIOS_DIR / f"{scenario_id}.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_run(run_id, files):
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        path = run_dir / filename
        if filename.endswith(".txt"):
            with path.open("w", encoding="utf-8") as f:
                f.write(content)
        else:
            with path.open("w", encoding="utf-8") as f:
                json.dump(content, f, indent=2)


@simulate_bp.route("/run/<scenario_id>", methods=["POST"])
def run_scenario(scenario_id):
    scenario = _load_scenario(scenario_id)
    if scenario is None:
        return jsonify({"error": "Scenario not found"}), 404

    run_id     = "run_" + uuid.uuid4().hex[:10]
    start_time = time.time()
    log_lines  = [
        f"[{datetime.utcnow().isoformat()}] Run started: {run_id}",
        f"[{datetime.utcnow().isoformat()}] Scenario: {scenario['name']} ({scenario_id})",
        f"[{datetime.utcnow().isoformat()}] Mode: {scenario['model']}",
    ]

    params   = scenario["parameters"]
    warnings = []
    try:
        warnings = validate_parameters(params)
    except ValueError as exc:
        return jsonify({"error": str(exc), "type": "validation_error"}), 422

    try:
        model  = scenario["model"]
        files  = {}
        result_payload = {}
        timing     = {}

        if model == "clews":
            log_lines.append(f"[{datetime.utcnow().isoformat()}] Running CLEWS model...")
            t0     = time.perf_counter()
            output = run_clews_only(params)
            timing = {"clews_ms": round((time.perf_counter() - t0) * 1000, 1), "total_ms": 0}
            timing["total_ms"] = timing["clews_ms"]
            files["clews_output.json"] = output
            result_payload = {"clews": output}
            log_lines.append(f"[{datetime.utcnow().isoformat()}] CLEWS done in {timing['clews_ms']}ms")

        elif model == "og":
            log_lines.append(f"[{datetime.utcnow().isoformat()}] Running OG-Core model...")
            og_params = {
                "energy_cost":       params.get("base_energy_cost", 50),
                "tax_rate":          params.get("tax_rate", 0.2),
                "population_growth": params.get("population_growth", 0.02),
                "govt_revenue":      0,
            }
            t0     = time.perf_counter()
            output = run_og_only(og_params)
            timing = {"og_ms": round((time.perf_counter() - t0) * 1000, 1), "total_ms": 0}
            timing["total_ms"] = timing["og_ms"]
            files["og_output.json"] = output
            result_payload = {"og": output}
            log_lines.append(f"[{datetime.utcnow().isoformat()}] OG-Core done in {timing['og_ms']}ms")

        elif model == "coupled":
            log_lines.append(f"[{datetime.utcnow().isoformat()}] Running coupled pipeline...")
            output = run_coupled(scenario, log_lines)
            timing = output.pop("timing", {})
            files["clews_output.json"]  = output.get("clews", {})
            files["og_output.json"]     = output.get("og", {})
            files["exchange_data.json"] = output.get("exchange", {})
            result_payload = output

        elif model == "converging":
            log_lines.append(f"[{datetime.utcnow().isoformat()}] Running converging pipeline...")
            output = run_converging(scenario, log_lines)
            timing = output.pop("timing", {})
            files["clews_output.json"]      = output.get("final", {}).get("clews", {})
            files["og_output.json"]         = output.get("final", {}).get("og", {})
            files["convergence_log.json"]   = output.get("history", [])
            result_payload = output
            log_lines.append(
                f"[{datetime.utcnow().isoformat()}] Converged={output.get('converged')}, "
                f"iterations={output.get('iterations')}"
            )
        else:
            return jsonify({"error": f"Unknown model type: {model}"}), 400

        duration = round(time.time() - start_time, 3)
        log_lines.append(f"[{datetime.utcnow().isoformat()}] Run finished in {duration}s.")

        metadata = {
            "run_id":           run_id,
            "scenario_id":      scenario_id,
            "scenario_name":    scenario["name"],
            "model":            model,
            "timestamp":        datetime.utcnow().isoformat(),
            "duration_seconds": duration,
            "status":           "success",
            "timing":           timing,
            "warnings":         warnings,
        }
        files["metadata.json"] = metadata
        files["run_log.txt"]   = "\n".join(log_lines)
        _save_run(run_id, files)

        results_summary = {k: v for k, v in result_payload.items() if k != "history"}
        log_run(run_id, scenario_id, scenario["name"], model, params, results_summary, timing, "success")

        return jsonify({
            "run_id":   run_id,
            "metadata": metadata,
            "results":  result_payload,
            "warnings": warnings,
        })

    except ValueError as exc:
        duration = round(time.time() - start_time, 3)
        log_lines.append(f"[{datetime.utcnow().isoformat()}] ERROR: {exc}")
        metadata = {
            "run_id": run_id, "scenario_id": scenario_id,
            "scenario_name": scenario["name"], "model": scenario["model"],
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": duration, "status": "error", "error": str(exc),
        }
        _save_run(run_id, {"metadata.json": metadata, "run_log.txt": "\n".join(log_lines)})
        log_run(run_id, scenario_id, scenario["name"], scenario["model"], params, {}, {}, "error")
        return jsonify({"error": str(exc), "run_id": run_id}), 422


@simulate_bp.route("/sweep", methods=["POST"])
def parameter_sweep():
    body        = request.get_json(silent=True) or {}
    base_params = body.get("parameters", {
        "carbon_tax": 30, "base_energy_cost": 50, "renewable_share": 0.3,
        "tax_rate": 0.25, "population_growth": 0.02,
    })
    sweep_param = body.get("sweep_param", "carbon_tax")
    sweep_min   = float(body.get("min", 0))
    sweep_max   = float(body.get("max", 100))
    steps       = int(body.get("steps", 20))
    model       = body.get("model", "clews")

    step_size = (sweep_max - sweep_min) / max(steps - 1, 1)
    results   = []

    for i in range(steps):
        value  = round(sweep_min + i * step_size, 4)
        p      = {**base_params, sweep_param: value}
        if model == "clews":
            out = run_clews_only(p)
        else:
            og_p = {
                "energy_cost":       p.get("base_energy_cost", 50),
                "tax_rate":          p.get("tax_rate", 0.2),
                "population_growth": p.get("population_growth", 0.02),
                "govt_revenue":      0,
            }
            out = run_og_only(og_p)
        results.append({"param_value": value, **out})

    return jsonify({"sweep_param": sweep_param, "model": model, "results": results})


@simulate_bp.route("/results/<run_id>/export/json", methods=["GET"])
def export_json(run_id):
    run_dir = RESULTS_DIR / run_id
    if not run_dir.exists():
        return jsonify({"error": "Run not found"}), 404
    data = {}
    for path in run_dir.iterdir():
        if path.suffix == ".json":
            with path.open("r", encoding="utf-8") as f:
                data[path.stem] = json.load(f)
    return Response(
        json.dumps(data, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{run_id}.json"'},
    )


@simulate_bp.route("/results/<run_id>/export/csv", methods=["GET"])
def export_csv(run_id):
    run_dir = RESULTS_DIR / run_id
    if not run_dir.exists():
        return jsonify({"error": "Run not found"}), 404

    rows = []
    for path in run_dir.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as f:
                obj = json.load(f)
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, (int, float, str, bool)):
                        rows.append({"file": path.stem, "key": k, "value": v})
        except (json.JSONDecodeError, OSError):
            continue

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["file", "key", "value"])
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{run_id}.csv"'},
    )


@simulate_bp.route("/scenarios/<scenario_id>/export", methods=["GET"])
def export_scenario(scenario_id):
    path = SCENARIOS_DIR / f"{scenario_id}.json"
    if not path.exists():
        return jsonify({"error": "Scenario not found"}), 404
    with path.open("r", encoding="utf-8") as f:
        data = f.read()
    return Response(
        data,
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{scenario_id}.json"'},
    )
