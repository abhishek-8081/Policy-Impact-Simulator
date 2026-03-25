def run_og(params):
    energy_cost = float(params["energy_cost"])
    govt_revenue_external = float(params.get("govt_revenue", 0))
    tax_rate = float(params.get("tax_rate", 0.2))
    pop_growth = float(params.get("population_growth", 0.02))

    productivity = max(0.5, 1.0 - energy_cost * 0.003)
    wages = productivity * 60
    savings = wages * (1 - tax_rate) * 0.35
    capital = savings * (1 + pop_growth) * 10
    labor = 50 * (1 + pop_growth)

    alpha = 0.33
    gdp = 100 * (capital ** alpha) * (labor ** (1 - alpha))
    govt_revenue_total = gdp * tax_rate + govt_revenue_external

    return {
        "productivity": round(productivity, 4),
        "wages": round(wages, 2),
        "savings": round(savings, 2),
        "capital": round(capital, 2),
        "gdp": round(gdp, 2),
        "govt_revenue": round(govt_revenue_total, 2),
    }
