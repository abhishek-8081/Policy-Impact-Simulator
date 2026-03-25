from flask import Blueprint, request, jsonify
from pathlib import Path
import json
import uuid
from datetime import datetime

scenarios_bp = Blueprint("scenarios", __name__)

BASE_DIR = Path(__file__).parent.parent
SCENARIOS_DIR = BASE_DIR / "data" / "scenarios"

DEFAULT_PARAMETERS = {
    "carbon_tax": 30,
    "base_energy_cost": 50,
    "renewable_share": 0.3,
    "tax_rate": 0.25,
    "population_growth": 0.02,
}

DEFAULT_RUN_CONFIG = {
    "tolerance": 0.5,
    "max_iterations": 20,
    "coupling_direction": "clews_to_og",
}


def _load_scenario(scenario_id):
    path = SCENARIOS_DIR / f"{scenario_id}.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_scenario(scenario):
    path = SCENARIOS_DIR / f"{scenario['id']}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(scenario, f, indent=2)


@scenarios_bp.route("/scenarios", methods=["POST"])
def create_scenario():
    body = request.get_json(silent=True) or {}
    scenario_id = "scenario_" + uuid.uuid4().hex[:8]
    scenario = {
        "id": scenario_id,
        "name": body.get("name", "Unnamed Scenario"),
        "created_at": datetime.utcnow().isoformat(),
        "model": body.get("model", "clews"),
        "parameters": {**DEFAULT_PARAMETERS, **body.get("parameters", {})},
        "run_config": {**DEFAULT_RUN_CONFIG, **body.get("run_config", {})},
    }
    _save_scenario(scenario)
    return jsonify(scenario), 201


@scenarios_bp.route("/scenarios", methods=["GET"])
def list_scenarios():
    scenarios = []
    for path in sorted(SCENARIOS_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                scenarios.append(json.load(f))
        except (json.JSONDecodeError, OSError):
            continue
    return jsonify(scenarios)


@scenarios_bp.route("/scenarios/<scenario_id>", methods=["GET"])
def get_scenario(scenario_id):
    scenario = _load_scenario(scenario_id)
    if scenario is None:
        return jsonify({"error": "Scenario not found"}), 404
    return jsonify(scenario)


@scenarios_bp.route("/scenarios/<scenario_id>", methods=["PUT"])
def update_scenario(scenario_id):
    scenario = _load_scenario(scenario_id)
    if scenario is None:
        return jsonify({"error": "Scenario not found"}), 404
    body = request.get_json(silent=True) or {}
    if "name" in body:
        scenario["name"] = body["name"]
    if "model" in body:
        scenario["model"] = body["model"]
    if "parameters" in body:
        scenario["parameters"].update(body["parameters"])
    if "run_config" in body:
        scenario["run_config"].update(body["run_config"])
    scenario["updated_at"] = datetime.utcnow().isoformat()
    _save_scenario(scenario)
    return jsonify(scenario)


@scenarios_bp.route("/scenarios/<scenario_id>", methods=["DELETE"])
def delete_scenario(scenario_id):
    path = SCENARIOS_DIR / f"{scenario_id}.json"
    if not path.exists():
        return jsonify({"error": "Scenario not found"}), 404
    path.unlink()
    return jsonify({"deleted": scenario_id})
