import sys, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.validation import (
    validate_clews_output, validate_og_inputs, validate_og_output,
    validate_parameters,
)


# ── validate_parameters ───────────────────────────────────────────────────────

def test_valid_params_no_error():
    params = {"carbon_tax": 30, "base_energy_cost": 50, "renewable_share": 0.3,
              "tax_rate": 0.25, "population_growth": 0.02}
    warnings = validate_parameters(params)
    assert isinstance(warnings, list)


def test_renewable_share_above_1_raises():
    with pytest.raises(ValueError, match="renewable_share"):
        validate_parameters({"renewable_share": 1.5})


def test_negative_carbon_tax_raises():
    with pytest.raises(ValueError, match="carbon_tax"):
        validate_parameters({"carbon_tax": -10})


def test_tax_rate_above_06_raises():
    with pytest.raises(ValueError, match="tax_rate"):
        validate_parameters({"tax_rate": 0.8})


def test_high_carbon_tax_returns_warning():
    warnings = validate_parameters({"carbon_tax": 160})
    assert any("unrealistic" in w for w in warnings)


def test_zero_carbon_tax_returns_warning():
    warnings = validate_parameters({"carbon_tax": 0})
    assert any("Zero carbon" in w for w in warnings)


# ── validate_clews_output ─────────────────────────────────────────────────────

def test_valid_clews_output():
    data = {"energy_cost": 62.3, "emissions": 49.38, "energy_investment": 22.5, "energy_consumption": 81.31}
    assert validate_clews_output(data) is True


def test_missing_clews_field_raises():
    with pytest.raises(ValueError, match="Missing field"):
        validate_clews_output({"energy_cost": 62.3})


def test_negative_clews_field_raises():
    with pytest.raises(ValueError, match="negative"):
        validate_clews_output({"energy_cost": -5, "emissions": 10, "energy_investment": 5, "energy_consumption": 30})


def test_non_numeric_clews_field_raises():
    with pytest.raises(ValueError, match="Non-numeric"):
        validate_clews_output({"energy_cost": "high", "emissions": 10, "energy_investment": 5, "energy_consumption": 30})


# ── validate_og_inputs ────────────────────────────────────────────────────────

def test_valid_og_inputs():
    data = {"energy_cost": 62.3, "govt_revenue": 24.4, "tax_rate": 0.25, "population_growth": 0.02}
    assert validate_og_inputs(data) is True


def test_invalid_tax_rate_in_og_inputs():
    with pytest.raises(ValueError, match="tax_rate"):
        validate_og_inputs({"energy_cost": 60, "govt_revenue": 10, "tax_rate": 1.5, "population_growth": 0.02})


# ── validate_og_output ────────────────────────────────────────────────────────

def test_valid_og_output():
    data = {"productivity": 0.81, "wages": 48.79, "savings": 12.81,
            "capital": 130.62, "gdp": 6956.01, "govt_revenue": 1763.4}
    assert validate_og_output(data) is True


def test_missing_og_output_field_raises():
    with pytest.raises(ValueError, match="Missing field"):
        validate_og_output({"productivity": 0.81, "wages": 48.79})
