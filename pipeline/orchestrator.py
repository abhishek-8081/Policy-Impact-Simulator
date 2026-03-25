from pathlib import Path
import json
import time
from datetime import datetime

from models.clews_lite import run_clews
from models.og_lite import run_og
from pipeline.mapping import clews_to_og, og_to_clews
from pipeline.validation import (
    validate_clews_output, validate_og_inputs, validate_og_output,
)

BASE_DIR    = Path(__file__).parent.parent
EXCHANGE_DIR = BASE_DIR / "data" / "exchange"


def _ms(t0):
    return round((time.perf_counter() - t0) * 1000, 1)


def _save_exchange(filename, data):
    EXCHANGE_DIR.mkdir(parents=True, exist_ok=True)
    path = EXCHANGE_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _log(log_lines, msg):
    log_lines.append(f"[{datetime.utcnow().isoformat()}] {msg}")


def run_clews_only(params):
    return run_clews(params)


def run_og_only(params):
    return run_og(params)


def run_coupled(scenario, log_lines=None):
    if log_lines is None:
        log_lines = []

    params    = scenario["parameters"]
    direction = scenario.get("run_config", {}).get("coupling_direction", "clews_to_og")
    timing    = {}

    if direction == "clews_to_og":
        _log(log_lines, "Step 1/3 — Running CLEWS model")
        t0 = time.perf_counter()
        clews_result = run_clews(params)
        timing["clews_ms"] = _ms(t0)
        _save_exchange("clews_output.json", clews_result)
        validate_clews_output(clews_result)
        _log(log_lines, f"  CLEWS done in {timing['clews_ms']}ms: {clews_result}")

        _log(log_lines, "Step 2/3 — Mapping CLEWS to OG-Core inputs")
        t0 = time.perf_counter()
        og_inputs = clews_to_og(clews_result, params)
        timing["mapping_ms"] = _ms(t0)
        _save_exchange("exchange_data.json", og_inputs)
        validate_og_inputs(og_inputs)
        _log(log_lines, f"  Mapping done in {timing['mapping_ms']}ms: {og_inputs}")

        _log(log_lines, "Step 3/3 — Running OG-Core model")
        t0 = time.perf_counter()
        og_result = run_og(og_inputs)
        timing["og_ms"] = _ms(t0)
        _save_exchange("og_output.json", og_result)
        validate_og_output(og_result)
        _log(log_lines, f"  OG-Core done in {timing['og_ms']}ms: {og_result}")

        timing["total_ms"] = round(sum(timing.values()), 1)
        return {"clews": clews_result, "exchange": og_inputs, "og": og_result, "timing": timing}

    elif direction == "og_to_clews":
        og_seed = {
            "energy_cost":       params.get("base_energy_cost", 50),
            "tax_rate":          params.get("tax_rate", 0.2),
            "population_growth": params.get("population_growth", 0.02),
            "govt_revenue":      0,
        }

        _log(log_lines, "Step 1/3 — Running OG-Core model")
        t0 = time.perf_counter()
        og_result = run_og(og_seed)
        timing["og_ms"] = _ms(t0)
        _save_exchange("og_output.json", og_result)
        validate_og_output(og_result)

        _log(log_lines, "Step 2/3 — Mapping OG-Core to CLEWS inputs")
        t0 = time.perf_counter()
        clews_inputs = og_to_clews(og_result, params)
        timing["mapping_ms"] = _ms(t0)
        _save_exchange("exchange_data.json", clews_inputs)
        _validate_clews_inputs(clews_inputs)

        _log(log_lines, "Step 3/3 — Running CLEWS model")
        t0 = time.perf_counter()
        clews_result = run_clews(clews_inputs)
        timing["clews_ms"] = _ms(t0)
        _save_exchange("clews_output.json", clews_result)
        validate_clews_output(clews_result)

        timing["total_ms"] = round(sum(timing.values()), 1)
        return {"og": og_result, "exchange": clews_inputs, "clews": clews_result, "timing": timing}

    else:
        raise ValueError(f"Unknown coupling direction: {direction}")


def _validate_clews_inputs(data):
    required = ["carbon_tax", "base_energy_cost", "renewable_share"]
    for field in required:
        if field not in data:
            raise ValueError(f"Missing field: '{field}' in mapped CLEWS inputs")


def run_converging(scenario, log_lines=None):
    if log_lines is None:
        log_lines = []

    params     = dict(scenario["parameters"])
    run_config = scenario.get("run_config", {})
    tolerance  = float(run_config.get("tolerance", 0.5))
    max_iter   = int(run_config.get("max_iterations", 20))

    _log(log_lines, f"Converging mode: tolerance={tolerance}, max_iterations={max_iter}")

    convergence_history = []
    prev_gdp            = None
    clews_result        = {}
    og_result           = {}
    total_t0            = time.perf_counter()

    for i in range(max_iter):
        _log(log_lines, f"Iteration {i + 1}/{max_iter}")

        clews_result = run_clews(params)
        validate_clews_output(clews_result)

        og_inputs = clews_to_og(clews_result, params)
        validate_og_inputs(og_inputs)

        og_result = run_og(og_inputs)
        validate_og_output(og_result)

        delta_gdp = abs(og_result["gdp"] - prev_gdp) if prev_gdp is not None else None

        convergence_history.append({
            "iteration":   i + 1,
            "gdp":         og_result["gdp"],
            "energy_cost": clews_result["energy_cost"],
            "emissions":   clews_result["emissions"],
            "delta_gdp":   round(delta_gdp, 4) if delta_gdp is not None else None,
        })

        _log(log_lines,
             f"  GDP={og_result['gdp']}, delta_gdp={delta_gdp}, "
             f"energy_cost={clews_result['energy_cost']}")

        if prev_gdp is not None and delta_gdp < tolerance:
            total_ms = _ms(total_t0)
            _log(log_lines, f"Converged after {i + 1} iterations ({total_ms}ms)")
            return {
                "converged":  True,
                "iterations": i + 1,
                "history":    convergence_history,
                "final":      {"clews": clews_result, "og": og_result},
                "timing":     {"total_ms": total_ms},
            }

        prev_gdp = og_result["gdp"]
        feedback = og_to_clews(og_result, params)
        params.update(feedback)

    total_ms = _ms(total_t0)
    _log(log_lines, f"Did not converge within {max_iter} iterations ({total_ms}ms).")
    return {
        "converged":  False,
        "iterations": max_iter,
        "history":    convergence_history,
        "final":      {"clews": clews_result, "og": og_result},
        "timing":     {"total_ms": total_ms},
    }
