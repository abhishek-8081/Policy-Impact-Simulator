def clews_to_og(clews_output, user_params):
    carbon_tax = float(user_params.get("carbon_tax", 0))
    energy_consumption = float(clews_output["energy_consumption"])

    return {
        "energy_cost": clews_output["energy_cost"],
        "govt_revenue": carbon_tax * energy_consumption * 0.01,
        "tax_rate": float(user_params.get("tax_rate", 0.2)),
        "population_growth": float(user_params.get("population_growth", 0.02)),
    }


def og_to_clews(og_output, user_params):
    gdp_factor = og_output["gdp"] / 1000

    return {
        "carbon_tax": float(user_params.get("carbon_tax", 0)),
        "base_energy_cost": float(user_params["base_energy_cost"]) * (0.8 + 0.2 * gdp_factor),
        "renewable_share": float(user_params.get("renewable_share", 0.2)),
    }
