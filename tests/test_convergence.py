import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.orchestrator import run_converging, run_coupled


BASE_SCENARIO = {
    "parameters": {
        "carbon_tax": 30, "base_energy_cost": 50,
        "renewable_share": 0.3, "tax_rate": 0.25, "population_growth": 0.02,
    },
    "run_config": {"tolerance": 0.5, "max_iterations": 30, "coupling_direction": "clews_to_og"},
}


def test_convergence_returns_required_keys():
    result = run_converging(BASE_SCENARIO)
    assert "converged" in result
    assert "iterations" in result
    assert "history" in result
    assert "final" in result


def test_convergence_history_structure():
    result = run_converging(BASE_SCENARIO)
    for entry in result["history"]:
        assert "iteration" in entry
        assert "gdp" in entry
        assert "energy_cost" in entry
        assert "emissions" in entry
        assert "delta_gdp" in entry


def test_convergence_iterations_within_max():
    result = run_converging(BASE_SCENARIO)
    assert result["iterations"] <= BASE_SCENARIO["run_config"]["max_iterations"]


def test_convergence_with_loose_tolerance():
    scenario = {**BASE_SCENARIO, "run_config": {**BASE_SCENARIO["run_config"], "tolerance": 1000}}
    result = run_converging(scenario)
    # Very loose tolerance → should converge in iteration 1 or 2
    assert result["converged"] is True
    assert result["iterations"] <= 3


def test_convergence_final_has_clews_and_og():
    result = run_converging(BASE_SCENARIO)
    assert "clews" in result["final"]
    assert "og" in result["final"]


def test_coupled_clews_to_og():
    result = run_coupled(BASE_SCENARIO)
    assert "clews" in result
    assert "og" in result
    assert "exchange" in result


def test_coupled_og_to_clews():
    scenario = {
        **BASE_SCENARIO,
        "run_config": {**BASE_SCENARIO["run_config"], "coupling_direction": "og_to_clews"},
    }
    result = run_coupled(scenario)
    assert "clews" in result
    assert "og" in result
    assert "exchange" in result


def test_coupled_timing_keys():
    result = run_coupled(BASE_SCENARIO)
    assert "timing" in result
    assert "total_ms" in result["timing"]
