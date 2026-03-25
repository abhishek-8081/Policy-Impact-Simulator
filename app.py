from flask import Flask, render_template
from pathlib import Path
import os

from routes.scenarios import scenarios_bp
from routes.simulate import simulate_bp
from routes.results import results_bp
from routes.presets import presets_bp
from routes.analysis import analysis_bp

BASE_DIR = Path(__file__).parent

for subdir in ["scenarios", "results", "exchange", "logs"]:
    (BASE_DIR / "data" / subdir).mkdir(parents=True, exist_ok=True)

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

app.register_blueprint(scenarios_bp)
app.register_blueprint(simulate_bp)
app.register_blueprint(results_bp)
app.register_blueprint(presets_bp)
app.register_blueprint(analysis_bp)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8888))
    app.run(host="0.0.0.0", port=port, debug=True)
