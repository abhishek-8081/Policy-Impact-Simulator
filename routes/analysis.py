from flask import Blueprint, request, jsonify
from pathlib import Path
import json

from models.clews_lite import run_clews
from models.og_lite import run_og
from pipeline.mapping import clews_to_og
from utils.logger import get_recent_logs

analysis_bp = Blueprint("analysis", __name__)

DELTA = 0.10


def _base_outputs(params):
    clews = run_clews(params)
    og_in = clews_to_og(clews, params)
    og    = run_og(og_in)
    return {**clews, **og}


def _elasticity(base_val, perturbed_val, param_delta_pct):
    if base_val == 0:
        return 0.0
    pct_change_output = (perturbed_val - base_val) / abs(base_val)
    return round(pct_change_output / param_delta_pct, 4)


@analysis_bp.route("/sensitivity", methods=["POST"])
def sensitivity_analysis():
    body   = request.get_json(silent=True) or {}
    params = body.get("parameters", {
        "carbon_tax": 30, "base_energy_cost": 50,
        "renewable_share": 0.3, "tax_rate": 0.25, "population_growth": 0.02,
    })

    sweep_params = ["carbon_tax", "base_energy_cost", "renewable_share", "tax_rate", "population_growth"]
    base_out     = _base_outputs(params)
    sensitivity  = {}

    for param in sweep_params:
        base_val = float(params.get(param, 0))
        if base_val == 0:
            delta = 0.1
            delta_pct = 1.0
        else:
            delta     = base_val * DELTA
            delta_pct = DELTA

        perturbed        = {**params, param: base_val + delta}
        perturbed_out    = _base_outputs(perturbed)

        for out_key, base_v in base_out.items():
            if out_key not in sensitivity:
                sensitivity[out_key] = {}
            sensitivity[out_key][param] = _elasticity(base_v, perturbed_out[out_key], delta_pct)

    result = {}
    for out_key, elasticities in sensitivity.items():
        most_sensitive = max(elasticities, key=lambda k: abs(elasticities[k]))
        result[out_key] = {
            "most_sensitive_to": most_sensitive,
            "elasticity":        elasticities[most_sensitive],
            "all_elasticities":  elasticities,
        }

    return jsonify({"base_outputs": base_out, "sensitivity": result})


@analysis_bp.route("/logs", methods=["GET"])
def get_logs():
    limit = int(request.args.get("limit", 50))
    return jsonify(get_recent_logs(limit))
