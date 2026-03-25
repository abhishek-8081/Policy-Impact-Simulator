CLEWS_OUTPUT_FIELDS = ["energy_cost", "emissions", "energy_investment", "energy_consumption"]
OG_INPUT_FIELDS     = ["energy_cost", "govt_revenue", "tax_rate", "population_growth"]
OG_OUTPUT_FIELDS    = ["productivity", "wages", "savings", "capital", "gdp", "govt_revenue"]

PARAM_RANGES = {
    "carbon_tax":        (0,   200),
    "base_energy_cost":  (1,   300),
    "renewable_share":   (0,   1),
    "tax_rate":          (0,   0.6),
    "population_growth": (-0.05, 0.1),
}

PARAM_WARNINGS = [
    ("carbon_tax",        lambda v: v > 150,  "Carbon tax above $150/tCO2 is unrealistic for most economies (EU ETS peak ~$100)."),
    ("carbon_tax",        lambda v: v == 0,   "Zero carbon tax — no price signal for decarbonisation."),
    ("renewable_share",   lambda v: v > 0.85, "Renewable share above 85% requires significant grid storage investment not modelled here."),
    ("tax_rate",          lambda v: v > 0.5,  "Tax rate above 50% is above most OECD countries' effective rates."),
    ("population_growth", lambda v: v > 0.03, "Population growth above 3% is very high — typical only in sub-Saharan Africa."),
    ("base_energy_cost",  lambda v: v < 10,   "Base energy cost below $10/MWh is below global minimum — check units."),
]


def validate_parameters(params):
    warnings = []
    for key, (lo, hi) in PARAM_RANGES.items():
        if key not in params:
            continue
        v = float(params[key])
        if not (lo <= v <= hi):
            raise ValueError(f"Parameter '{key}' = {v} is out of valid range [{lo}, {hi}].")
    for key, test_fn, msg in PARAM_WARNINGS:
        if key in params and test_fn(float(params[key])):
            warnings.append(msg)
    return warnings


def _check_fields(data, required_fields, label):
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing field: '{field}' in {label}.")
        if not isinstance(data[field], (int, float)):
            raise ValueError(f"Non-numeric value for '{field}' in {label}: {data[field]!r}")


def _check_non_negative(data, fields, label):
    for field in fields:
        if field in data and data[field] < 0:
            raise ValueError(f"Unexpected negative value for '{field}' in {label}: {data[field]}")


def validate_clews_output(data):
    _check_fields(data, CLEWS_OUTPUT_FIELDS, "CLEWS output")
    _check_non_negative(data, CLEWS_OUTPUT_FIELDS, "CLEWS output")
    return True


def validate_og_inputs(data):
    _check_fields(data, OG_INPUT_FIELDS, "OG-Core inputs")
    _check_non_negative(data, OG_INPUT_FIELDS, "OG-Core inputs")
    if not (0 <= data["tax_rate"] <= 1):
        raise ValueError(f"tax_rate must be in [0, 1], got {data['tax_rate']}")
    return True


def validate_og_output(data):
    _check_fields(data, OG_OUTPUT_FIELDS, "OG-Core output")
    _check_non_negative(data, OG_OUTPUT_FIELDS, "OG-Core output")
    return True
