# Policy Impact Simulator

**CLEWS and OG-Core Integration**

A web-based modelling workbench for exploring how energy policy decisions interact with macroeconomic outcomes. It integrates a CLEWS energy model with an OG-Core overlapping-generations macroeconomic model through a bidirectional coupling and iterative convergence pipeline — entirely in the browser, with no command-line interaction required.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [Models](#models)
6. [Modes of Operation](#modes-of-operation)
7. [Parameters](#parameters)
8. [Getting Started](#getting-started)
9. [API Reference](#api-reference)
10. [Configuration](#configuration)
11. [Data Storage](#data-storage)
12. [Limitations](#limitations)
13. [References](#references)

---

## Overview

The Policy Impact Simulator demonstrates a complete integration pipeline between two complementary modelling frameworks:

- **CLEWS / OSeMOSYS** — a Climate, Land, Energy and Water Systems model used for national energy planning and resource optimisation
- **OG-Core** — an open-source overlapping-generations (OLG) macroeconomic model maintained by the Policy Simulation Library that captures how households save, work, and consume across their lifetimes

The simulator allows analysts and policymakers to run either model independently, chain them together in a coupled pipeline, or iterate them in a feedback loop until the system reaches economic equilibrium — all through a clean, no-code web interface.

---

## Features

**Minimalistic Interface**
Clean, uncluttered layout designed for analysts and policymakers. Every parameter is labelled, every output is explained with inline tooltips, and nothing competes for attention. Runs entirely in the browser.

**No-Code Policy Exploration**
Adjust carbon tax, renewable share, fiscal rates, and population growth with sliders or number inputs. Directional indicators show how each lever shifts outputs in real time. Country presets load real-world baseline values in one click.

**Independent Model Execution**
Run CLEWS or OG-Core individually with full scenario management. Create named scenarios, switch between them, save parameter sets, and reproduce any past run.

**Bidirectional Coupled Pipeline**
Chain both models together. Run CLEWS first and pass energy cost outputs to OG-Core as production cost shocks, or reverse the direction to study how GDP growth changes energy demand. A validated mapping layer handles the data exchange between models.

**Iterative Convergence Engine**
Run the coupled pipeline in a loop until GDP stabilises. Each iteration feeds OG-Core's macro output back into CLEWS as an updated energy demand signal. The loop stops when the absolute GDP change falls below the configured tolerance. A convergence chart visualises the stabilisation path across iterations.

**Sensitivity Analysis**
Perturbs each input parameter by 10% and measures how much each output changes. Returns an elasticity table identifying which lever has the largest influence on each output at the current parameter values.

**Parameter Sweep**
Sweeps any single parameter across its full range and charts all outputs simultaneously, showing the complete response curve without requiring manual re-runs.

**Scenario Management**
Full create, read, update, delete operations for named scenarios stored as JSON files. Scenarios can be exported individually.

**Run History and Comparison**
Every run is automatically saved with its full parameter set, model outputs, timing data, and status. Select any two runs to render a side-by-side bar chart and a table of absolute and percentage differences. Export results as CSV or JSON.

**Real-time Parameter Warnings**
Non-blocking advisory checks alert on economically unusual inputs before execution. Runs always complete; warnings are informational only.

**Light and Dark Mode**
Full theme support with a warm amber palette (Dark Forge). Charts, labels, and legends re-render immediately on theme toggle. IBM Plex Sans typography throughout.

---

## Architecture


<img width="5207" height="2085" alt="image" src="https://github.com/user-attachments/assets/cf961805-ec46-4bdb-9cda-cbfd1a88f08b" />



---

## Project Structure

```
policy-impact-simulator/
|
+-- app.py                      Flask application entry point
+-- requirements.txt
|
+-- routes/
|   +-- scenarios.py            Scenario CRUD endpoints
|   +-- simulate.py             Run execution endpoint
|   +-- results.py              Results and comparison endpoints
|   +-- presets.py              Country preset endpoints
|   +-- analysis.py             Sensitivity and sweep endpoints
|
+-- models/
|   +-- clews_lite.py           CLEWS energy model (analytical approximation)
|   +-- og_lite.py              OG-Core macro model (analytical approximation)
|
+-- pipeline/
|   +-- orchestrator.py         Coordinates model execution modes
|   +-- mapping.py              Maps CLEWS outputs to OG-Core inputs (and reverse)
|   +-- validation.py           Output validation checks
|
+-- utils/
|   +-- logger.py               JSONL run logger
|
+-- templates/
|   +-- index.html              Single-page application template
|
+-- static/
|   +-- css/main.css            All styles (Dark Forge theme, light/dark)
|   +-- js/app.js               UI logic, API calls, theme management
|   +-- js/charts.js            Plotly chart rendering functions
|   +-- js/scenarios.js         Scenario management UI
|   +-- img/architecture.png    Architecture diagram
|
+-- presets/
|   +-- india.json
|   +-- germany.json
|   +-- nigeria.json
|   +-- usa.json
|
+-- data/                       Created at runtime
|   +-- scenarios/
|   +-- results/
|   +-- exchange/
|   +-- logs/
|
+-- tests/
```

---

## Models

### CLEWS Lite

A closed-form analytical approximation of CLEWS / OSeMOSYS outputs.

**Inputs:** `carbon_tax`, `base_energy_cost`, `renewable_share`

**Outputs:**

| Output | Description |
|---|---|
| `energy_cost` | Effective cost of energy after carbon tax, dampened by renewable share |
| `emissions` | Total CO2 emissions, reduced by renewable penetration |
| `energy_investment` | Capital required for the energy mix |
| `energy_consumption` | Total energy demand |

**Note:** The real CLEWS/OSeMOSYS solves a full linear programming optimisation over an energy system with multiple technologies, time periods, and resource constraints. This approximation captures the correct directional relationships between parameters and outputs.

### OG-Core Lite

A Cobb-Douglas approximation of the OG-Core overlapping-generations model.

**Inputs:** `tax_rate`, `population_growth`, `energy_cost` (from CLEWS when coupled)

**Outputs:**

| Output | Description |
|---|---|
| `gdp` | Total output, penalised by tax rate and energy cost |
| `wages` | Labour share of output |
| `savings` | Household savings as a share of after-tax income |
| `capital` | Capital stock accumulated from savings |
| `govt_revenue` | Tax revenue collected |

**Note:** The real OG-Core solves an 80-period OLG lifecycle optimisation with heterogeneous households, firms, and a government sector using iterative numerical methods (time path iteration).

### Mapping Layer

`pipeline/mapping.py` transforms outputs between models:

- **CLEWS to OG-Core:** `energy_cost` is converted into a production cost shock that reduces effective capital productivity in the macro model
- **OG-Core to CLEWS:** `gdp` and `savings` are converted into updated energy demand and investment signals for the energy model

---

## Modes of Operation

### Models (Tab 1)

Run CLEWS or OG-Core independently. Select a model, configure parameters, and click Run. Results are displayed with computed outputs, directional change indicators versus the previous run, any parameter warnings, and full timing data. All runs are persisted to `data/results/`.

Additional tools available on this tab:
- **Sensitivity Analysis** — identify the most influential parameter for each output
- **Parameter Sweep** — chart any parameter across its full range

### Coupled (Tab 2)

Chains both models in sequence with a single data exchange. Choose a direction:

- **CLEWS to OG-Core** — energy cost and emissions from CLEWS are mapped to production cost inputs for OG-Core
- **OG-Core to CLEWS** — GDP and savings from OG-Core are mapped to energy demand adjustments for CLEWS

The UI shows a live step progress indicator (Model A / Transform / Model B), validation badges for each stage, and a data flow diagram showing intermediate exchange values and timing for each step.

### Converging (Tab 3)

Extends the coupled pipeline into an iterative feedback loop.

**Algorithm:**
1. Run CLEWS with current parameters
2. Map CLEWS outputs to OG-Core inputs
3. Run OG-Core; record GDP
4. Compute |delta GDP| from the previous iteration
5. If |delta GDP| < tolerance, stop. Otherwise map OG-Core outputs back to CLEWS energy demand parameters and go to step 1.
6. Stop unconditionally at max iterations to prevent infinite loops.

**Configuration:**
- `tolerance` — GDP convergence threshold (default 0.5)
- `max_iterations` — safety limit (default 20)

**Outputs:** Three charts showing GDP trajectory, emissions and energy cost over iterations, and the absolute GDP delta per iteration with the tolerance line. A full iteration history table is also rendered.

### Results (Tab 4)

Browses all past runs stored in `data/results/`. Each run shows its scenario name, model, mode, status, timing, and a summary of outputs. Features:

- Expand any run to see its full JSON output
- Select two runs in the Compare dropdowns to render a grouped bar chart and a percentage difference table
- Download any run as a CSV file

---

## Parameters

| Parameter | Range | Unit | Description |
|---|---|---|---|
| Carbon Tax | 0 - 200 | $/tCO2 | Tax per ton of CO2 emitted. Raises energy cost; reduces emissions and GDP. |
| Base Energy Cost | 10 - 150 | $/MWh | Baseline electricity cost before carbon tax. Floor cost for production. |
| Renewable Share | 0 - 1 | fraction | Share of energy from renewables. Dampens carbon tax impact and cuts emissions. |
| Tax Rate | 0 - 0.6 | fraction | Economy-wide income tax rate. Reduces household savings; raises government revenue. |
| Population Growth | 0 - 0.1 | annual rate | Labour force growth rate. Increases labour supply and GDP in the OLG model. |
| Tolerance | 0.01 - 5 | GDP units | Convergence threshold for the iterative pipeline. |
| Max Iterations | 1 - 100 | integer | Safety limit on the converging loop. |

### Country Presets

Approximate baseline values drawn from public sources (IEA energy statistics, World Bank carbon pricing databases, OECD fiscal data). Suitable for demonstrating relative differences between economies; not intended as precise policy simulations.

| Preset | Carbon Tax | Base Energy Cost | Renewable Share | Tax Rate | Population Growth |
|---|---|---|---|---|---|
| India | 5 | 40 | 0.24 | 0.17 | 0.009 |
| Germany | 55 | 90 | 0.46 | 0.39 | -0.001 |
| Nigeria | 2 | 25 | 0.20 | 0.06 | 0.026 |
| USA | 15 | 65 | 0.22 | 0.27 | 0.005 |

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip

### Installation

```bash
git clone <repository-url>
cd policy-impact-simulator
pip install -r requirements.txt
```

### Running Locally

```bash
python app.py
```

Open `http://localhost:8888` in a browser.

To use a different port:

```bash
PORT=5000 python app.py
```

### Running with a Production Server

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:8888 app:app
```

---

## API Reference

### Scenarios

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/scenarios` | Create a new scenario |
| `GET` | `/scenarios` | List all scenarios |
| `GET` | `/scenarios/<id>` | Get a single scenario |
| `PUT` | `/scenarios/<id>` | Update scenario parameters |
| `DELETE` | `/scenarios/<id>` | Delete a scenario |
| `GET` | `/scenarios/<id>/export` | Export scenario as JSON |

### Simulation

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/run/<scenario_id>` | Execute a scenario |

Request body (JSON):

```json
{
  "mode": "independent",
  "model": "clews",
  "parameters": {
    "carbon_tax": 30,
    "base_energy_cost": 50,
    "renewable_share": 0.3,
    "tax_rate": 0.25,
    "population_growth": 0.02
  }
}
```

Mode values: `independent`, `coupled`, `converging`

### Results

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/results` | List all past runs |
| `GET` | `/results/<run_id>` | Full result for a single run |
| `GET` | `/results/<a>/compare/<b>` | Compare two runs |
| `GET` | `/results/<run_id>/export/csv` | Export run as CSV |
| `GET` | `/results/<run_id>/export/json` | Export run as JSON |

### Analysis

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/sensitivity` | Run sensitivity analysis |
| `POST` | `/sweep` | Run parameter sweep |

### Presets

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/presets` | List available country presets |
| `GET` | `/presets/<name>` | Load a specific preset |

---

## Configuration

All configuration is handled through environment variables.

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8888` | Port the server listens on |

The `data/` directory and all subdirectories (`scenarios/`, `results/`, `exchange/`, `logs/`) are created automatically on startup if they do not exist.

---

## Data Storage

All data is stored as flat files on disk. There is no database dependency.

```
data/
+-- scenarios/          One JSON file per scenario
+-- results/            One directory per run, containing result.json
+-- exchange/           Intermediate coupling data saved per coupled/converging run
+-- logs/run_log.jsonl  Append-only log of all runs in JSONL format
```

A run result file contains:

```json
{
  "run_id": "...",
  "scenario_id": "...",
  "scenario_name": "...",
  "mode": "independent",
  "model": "clews",
  "status": "success",
  "parameters": { ... },
  "clews_output": { ... },
  "og_output": { ... },
  "warnings": [],
  "timing": { "total_ms": 12 },
  "metadata": { ... }
}
```

---

## Limitations

- **Simplified model formulas.** Both CLEWS and OG-Core are represented as closed-form analytical approximations. Real OG-Core solves an 80-period OLG lifecycle optimisation; real CLEWS/OSeMOSYS solves a full linear programme over an energy system with many technologies and time periods. The qualitative relationships between parameters and outputs are correct, but absolute values are illustrative only.

- **No authentication.** The application has no user accounts or access control. All scenarios and results are visible to anyone with access to the URL. Do not use this deployment for sensitive policy analysis without adding an authentication layer.

- **File-based storage.** Data is stored as JSON files on disk. This is not suitable for concurrent access by multiple users at scale. A database backend would be required for production use.

- **Illustrative mapping layer.** The data exchange between CLEWS and OG-Core uses simplified linear transformations. A production coupling would require careful dimensional alignment between OSeMOSYS output files (CSV format with technology and time-period dimensions) and OG-Core input parameters (age-structured demographic and fiscal data).

---

## References

- OSeMOSYS: https://github.com/OSeMOSYS/OSeMOSYS
- MUIO (existing OSeMOSYS UI): https://github.com/OSeMOSYS/MUIO
- OG-Core (Policy Simulation Library): https://github.com/PSLmodels/OG-Core
- CLEWS framework: https://www.sei.org/tools/clews/
- IEA World Energy Statistics: https://www.iea.org/data-and-statistics
- World Bank Carbon Pricing Dashboard: https://carbonpricingdashboard.worldbank.org
