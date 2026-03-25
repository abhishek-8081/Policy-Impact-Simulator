import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.clews_lite import run_clews


BASE = {"carbon_tax": 30, "base_energy_cost": 50, "renewable_share": 0.3}


def test_output_keys():
    out = run_clews(BASE)
    assert set(out.keys()) == {"energy_cost", "emissions", "energy_investment", "energy_consumption"}


def test_values_non_negative():
    out = run_clews(BASE)
    for k, v in out.items():
        assert v >= 0, f"{k} should be non-negative, got {v}"


def test_higher_carbon_tax_raises_energy_cost():
    low  = run_clews({**BASE, "carbon_tax": 0})
    high = run_clews({**BASE, "carbon_tax": 80})
    assert high["energy_cost"] > low["energy_cost"]


def test_higher_carbon_tax_lowers_emissions():
    low  = run_clews({**BASE, "carbon_tax": 0})
    high = run_clews({**BASE, "carbon_tax": 80})
    assert high["emissions"] < low["emissions"]


def test_higher_renewables_lower_emissions():
    low  = run_clews({**BASE, "renewable_share": 0.1})
    high = run_clews({**BASE, "renewable_share": 0.9})
    assert high["emissions"] < low["emissions"]


def test_energy_consumption_floor():
    # Very high energy cost should never push consumption below 20
    out = run_clews({"carbon_tax": 200, "base_energy_cost": 300, "renewable_share": 0.0})
    assert out["energy_consumption"] >= 20


def test_zero_carbon_tax():
    out = run_clews({"carbon_tax": 0, "base_energy_cost": 50, "renewable_share": 0.3})
    assert out["energy_cost"] == round(50 + 0, 2)


def test_full_renewables_near_zero_emissions():
    out = run_clews({"carbon_tax": 80, "base_energy_cost": 50, "renewable_share": 1.0})
    assert out["emissions"] == 0.0
