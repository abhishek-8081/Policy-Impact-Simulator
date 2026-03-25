def run_clews(params):
    carbon_tax = float(params["carbon_tax"])
    base_energy_cost = float(params["base_energy_cost"])
    renewable_share = float(params.get("renewable_share", 0.2))

    energy_cost = base_energy_cost + carbon_tax * 0.5 * (1 - renewable_share * 0.6)
    emissions = max(0.0, 100 * (1 - carbon_tax / 80) * (1 - renewable_share * 0.7))
    energy_investment = base_energy_cost * 0.15 + renewable_share * 50
    energy_consumption = max(20.0, 100 - energy_cost * 0.3)

    return {
        "energy_cost": round(energy_cost, 2),
        "emissions": round(emissions, 2),
        "energy_investment": round(energy_investment, 2),
        "energy_consumption": round(energy_consumption, 2),
    }
