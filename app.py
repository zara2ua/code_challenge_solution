import json
import os
from flask import Flask, jsonify, render_template
from reconciler import reconcile_meetings


app = Flask(__name__)


# Base path pointing to /api/data/ directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_json_file(filename):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        app.logger.error(f"Error reading {filename}: {e}")
        return None


# --- NEW FRONTEND ENDPOINT ---
@app.route("/meetings", methods=["GET"])
def render_meetings_page():
    """Serves the Vue.js HTML dashboard."""
    return render_template("index.html")


# --- DATA API ENDPOINT ---
@app.route("/data", methods=["GET"])
@app.route("/api/data", methods=["GET"])
def get_unified_data():
    calendar_data = load_json_file("calendar_events.json")
    crm_data = load_json_file("crm_events.json")

    if calendar_data is None and crm_data is None:
        return jsonify({"error": "Data files missing or unreadable"}), 500

    unified_meetings = reconcile_meetings(calendar_data or [], crm_data or [])

    return jsonify({
        "status": "success",
        "count": len(unified_meetings),
        "data": unified_meetings
    }), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)