from flask import Flask, request, jsonify, render_template_string
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

app = Flask(__name__)

# Historical HVAC telemetry logs
telemetry_logs = [
    {"time": "09:00", "temp": 27.5, "hum": 58, "occ": 1, "power": 1850.0, "mode": "ACTIVE_COOLING"},
    {"time": "09:15", "temp": 25.0, "hum": 54, "occ": 1, "power": 1420.0, "mode": "OPTIMIZED_NORMAL"},
    {"time": "09:30", "temp": 24.2, "hum": 51, "occ": 0, "power": 210.0, "mode": "ECO_STANDBY"},
]

BASELINE_POWER_WATTS = 2200.0  # Unoptimized traditional HVAC load

def predict_energy_usage(logs):
    if len(logs) < 3:
        return logs[-1]["power"]
    X = np.arange(len(logs)).reshape(-1, 1)
    y = np.array([row["power"] for row in logs])
    model = LinearRegression()
    model.fit(X, y)
    return round(max(100.0, float(model.predict([[len(logs) + 1]])[0])), 1)

@app.route('/api/hvac-data', methods=['POST'])
def receive_hvac_data():
    data = request.json
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "temp": data.get("temperature", 24.0),
        "hum": data.get("humidity", 50.0),
        "occ": data.get("occupancy", 0),
        "power": data.get("power_watts", 0.0),
        "mode": data.get("mode", "OPTIMIZED_NORMAL")
    }
    telemetry_logs.append(entry)
    if len(telemetry_logs) > 25:
        telemetry_logs.pop(0)

    savings_pct = round(((BASELINE_POWER_WATTS - entry["power"]) / BASELINE_POWER_WATTS) * 100, 1)
    return jsonify({
        "status": "success",
        "energy_savings_percent": max(0.0, savings_pct),
        "predicted_next_power_watts": predict_energy_usage(telemetry_logs)
    })

@app.route('/')
def dashboard():
    latest = telemetry_logs[-1]
    predicted_power = predict_energy_usage(telemetry_logs)
    savings_pct = max(0.0, round(((BASELINE_POWER_WATTS - latest["power"]) / BASELINE_POWER_WATTS) * 100, 1))

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>HVAC Energy Optimization Analytics</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding: 20px; }
            .card { background: #1e293b; padding: 20px; margin: 12px; width: 260px; border-radius: 10px; display: inline-block; border: 1px solid #334155; }
            .metric { font-size: 28px; font-weight: bold; color: #38bdf8; margin: 10px 0; }
            .save { color: #4ade80; }
            table { margin: 20px auto; border-collapse: collapse; width: 85%; background: #1e293b; }
            th, td { padding: 10px; border: 1px solid #334155; }
            th { background: #0284c7; color: white; }
        </style>
    </head>
    <body>
        <h1>⚡ HVAC Energy Optimization Using IoT Analytics</h1>
        <div class="card">
            <h3>Current HVAC Power</h3>
            <div class="metric">{{ latest.power }} W</div>
            <p>Mode: <b>{{ latest.mode }}</b></p>
        </div>
        <div class="card">
            <h3>Energy Saved vs Baseline</h3>
            <div class="metric save">{{ savings }}%</div>
            <p>Baseline: 2200 W | Temp: {{ latest.temp }}°C</p>
        </div>
        <div class="card">
            <h3>AI Forecast (Next Interval)</h3>
            <div class="metric">{{ predicted }} W</div>
            <p>Occupancy: {{ 'Detected' if latest.occ == 1 else 'Vacant' }}</p>
        </div>
        <table>
            <tr><th>Time</th><th>Temp (°C)</th><th>Humidity (%)</th><th>Occupancy</th><th>Power (W)</th><th>Mode</th></tr>
            {% for row in logs[::-1] %}
            <tr>
                <td>{{ row.time }}</td><td>{{ row.temp }}</td><td>{{ row.hum }}</td>
                <td>{{ 'Yes' if row.occ == 1 else 'No' }}</td><td>{{ row.power }}</td><td>{{ row.mode }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html, latest=latest, savings=savings_pct, predicted=predicted_power, logs=telemetry_logs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
