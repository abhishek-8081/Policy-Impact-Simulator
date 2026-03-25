import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.mapping import clews_to_og, og_to_clews


CLEWS_OUT = {"energy_cost": 62.3, "emissions": 49.38, "energy_investment": 22.5, "energy_consumption": 81.31}
OG_OUT    = {"productivity": 0.81, "wages": 48.79, "savings": 12.81, "capital": 130.62, "gdp": 6956.01, "govt_revenue": 1763.4}
PARAMS    = {"carbon_tax": 30, "base_energy_cost": 50, "renewable_share": 0.3, "tax_rate": 0.25, "population_growth": 0.02}


def test_clews_to_og_output_keys():
    out = clews_to_og(CLEWS_OUT, PARAMS)
    assert set(out.keys()) == {"energy_cost", "govt_revenue", "tax_rate", "population_growth"}


def test_clews_to_og_energy_cost_passthrough():
    out = clews_to_og(CLEWS_OUT, PARAMS)
    assert out["energy_cost"] == CLEWS_OUT["energy_cost"]


def test_clews_to_og_govt_revenue_positive():
    out = clews_to_og(CLEWS_OUT, PARAMS)
    assert out["govt_revenue"] >= 0


def test_clews_to_og_zero_carbon_tax_zero_revenue():
    out = clews_to_og(CLEWS_OUT, {**PARAMS, "carbon_tax": 0})
    assert out["govt_revenue"] == 0.0


def test_og_to_clews_output_keys():
    out = og_to_clews(OG_OUT, PARAMS)
    assert set(out.keys()) == {"carbon_tax", "base_energy_cost", "renewable_share"}


def test_og_to_clews_higher_gdp_raises_base_cost():
    low  = og_to_clews({**OG_OUT, "gdp": 500},  PARAMS)
    high = og_to_clews({**OG_OUT, "gdp": 5000}, PARAMS)
    assert high["base_energy_cost"] > low["base_energy_cost"]


def test_og_to_clews_carbon_tax_unchanged():
    out = og_to_clews(OG_OUT, PARAMS)
    assert out["carbon_tax"] == PARAMS["carbon_tax"]
