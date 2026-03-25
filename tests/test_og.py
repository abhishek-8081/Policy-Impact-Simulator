import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.og_lite import run_og


BASE = {"energy_cost": 60, "tax_rate": 0.25, "population_growth": 0.02, "govt_revenue": 0}


def test_output_keys():
    out = run_og(BASE)
    assert set(out.keys()) == {"productivity", "wages", "savings", "capital", "gdp", "govt_revenue"}


def test_values_non_negative():
    out = run_og(BASE)
    for k, v in out.items():
        assert v >= 0, f"{k} should be non-negative, got {v}"


def test_high_energy_cost_lowers_gdp():
    low  = run_og({**BASE, "energy_cost": 10})
    high = run_og({**BASE, "energy_cost": 200})
    assert high["gdp"] < low["gdp"]


def test_productivity_floor():
    # Productivity should never go below 0.5
    out = run_og({**BASE, "energy_cost": 10000})
    assert out["productivity"] >= 0.5


def test_higher_tax_rate_raises_govt_revenue():
    low  = run_og({**BASE, "tax_rate": 0.1})
    high = run_og({**BASE, "tax_rate": 0.5})
    assert high["govt_revenue"] > low["govt_revenue"]


def test_govt_revenue_external_passthrough():
    without = run_og({**BASE, "govt_revenue": 0})
    with_   = run_og({**BASE, "govt_revenue": 500})
    assert with_["govt_revenue"] == round(without["govt_revenue"] + 500, 2)


def test_cobb_douglas_positive_gdp():
    out = run_og(BASE)
    assert out["gdp"] > 0
