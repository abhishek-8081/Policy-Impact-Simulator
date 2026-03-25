from flask import Blueprint, jsonify
from pathlib import Path
import json

presets_bp = Blueprint("presets", __name__)

PRESETS_DIR = Path(__file__).parent.parent / "presets"


@presets_bp.route("/presets", methods=["GET"])
def list_presets():
    presets = []
    for path in sorted(PRESETS_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                # Return lightweight summary — full data loaded per-country
                presets.append({
                    "id":          data["id"],
                    "name":        data["name"],
                    "flag":        data["flag"],
                    "description": data["description"],
                })
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return jsonify(presets)


@presets_bp.route("/presets/<country_id>", methods=["GET"])
def get_preset(country_id):
    path = PRESETS_DIR / f"{country_id}.json"
    if not path.exists():
        return jsonify({"error": f"Preset '{country_id}' not found"}), 404
    with path.open("r", encoding="utf-8") as f:
        return jsonify(json.load(f))
