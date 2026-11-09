
# ============================================================
# Network Anomaly Detector - Flask Dashboard
# ============================================================

# Import Flask tools for rendering pages and returning JSON data.
from flask import Flask, render_template, jsonify

# Import SQLite for accessing the project's database.
import sqlite3

# Import Path to locate project files reliably.
from pathlib import Path

# Import pandas for preparing traffic records for the ML model.
import pandas as pd

# Import joblib for loading the trained Isolation Forest model.
import joblib

# Import the Telegram notification function.
from alerts import send_telegram_alert


# ============================================================
# Step 1: Initialize the Flask application and file paths
# ============================================================

# Create the Flask application instance.
app = Flask(__name__)

# Locate the project directory.
PROJECT_DIRECTORY = Path(__file__).resolve().parent

# Locate the SQLite database.
DATABASE_PATH = PROJECT_DIRECTORY / "network.db"

# Locate the saved machine-learning model.
MODEL_PATH = PROJECT_DIRECTORY / "isolation_forest_model.joblib"

# Identify the Windows test VM being monitored.
MONITORED_DEVICE_IP = "192.168.50.10"


# ============================================================
# Step 2: Load the trained anomaly detection model
# ============================================================

# Load the model bundle containing the trained model and feature list.
model_bundle = joblib.load(MODEL_PATH)

# Retrieve the trained Isolation Forest model.
model = model_bundle["model"]

# Retrieve the numerical features in their original training order.
feature_columns = model_bundle["feature_columns"]




# ============================================================
# Step 3: Process new traffic records and send Telegram alerts
# ============================================================

def process_new_records():

    # Open the SQLite database with write access.
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)

    # Store newly detected anomalies for Telegram notifications.
    new_alerts = []

    # Count successfully inserted detection records.
    processed_count = 0

    try:
        # Create a cursor for executing SQL statements.
        cursor = connection.cursor()

        # Retrieve traffic records that do not yet have predictions.
        cursor.execute("""
            SELECT
                minute,
                device_ip,
                packet_count,
                total_bytes,
                average_packet_size,
                tcp_count,
                udp_count,
                unique_destinations,
                unique_ports,
                dns_count
            FROM device_traffic_features
            WHERE device_ip = ?
            AND NOT EXISTS (
                SELECT 1
                FROM anomaly_detections
                WHERE anomaly_detections.minute =
                      device_traffic_features.minute
                AND anomaly_detections.device_ip =
                    device_traffic_features.device_ip
            )
            AND packet_count IS NOT NULL
            AND total_bytes IS NOT NULL
            AND average_packet_size IS NOT NULL
            AND tcp_count IS NOT NULL
            AND udp_count IS NOT NULL
            AND unique_destinations IS NOT NULL
            AND unique_ports IS NOT NULL
            AND dns_count IS NOT NULL
            ORDER BY minute ASC
        """, (MONITORED_DEVICE_IP,))

        # Retrieve all records that need to be analyzed.
        records = cursor.fetchall()

        # Stop if there are no new records.
        if not records:
            return 0

        # Convert the records into a pandas DataFrame.
        df = pd.DataFrame(
            records,
            columns=[
                "minute",
                "device_ip",
                "packet_count",
                "total_bytes",
                "average_packet_size",
                "tcp_count",
                "udp_count",
                "unique_destinations",
                "unique_ports",
                "dns_count"
            ]
        )

        # Select numerical features in the original training order.
        X = df[feature_columns]

        # Generate predictions using the Isolation Forest model.
        predictions = model.predict(X)

        # Calculate anomaly scores.
        anomaly_scores = model.decision_function(X)

        # Process each traffic record individually.
        for index, record in df.iterrows():

            # Retrieve the prediction and anomaly score.
            prediction = int(predictions[index])
            anomaly_score = float(anomaly_scores[index])

            # Insert the prediction into the database.
            cursor.execute("""
                INSERT OR IGNORE INTO anomaly_detections (
                    minute,
                    device_ip,
                    prediction,
                    anomaly_score
                )
                VALUES (?, ?, ?, ?)
            """, (
                record["minute"],
                record["device_ip"],
                prediction,
                anomaly_score
            ))

            # Check whether a new database record was inserted.
            if cursor.rowcount == 1:

                # Increase the successfully processed record count.
                processed_count += 1

                # Only collect newly inserted potential anomalies.
                if prediction == -1:

                    new_alerts.append({
                        "minute": record["minute"],
                        "device_ip": record["device_ip"],
                        "packet_count": int(record["packet_count"]),
                        "total_bytes": int(record["total_bytes"]),
                        "anomaly_score": anomaly_score
                    })

        # Save all detection records before contacting Telegram.
        connection.commit()

    finally:
        # Close the database connection.
        connection.close()

    # Send notifications after the database transaction is complete.
    for alert in new_alerts:

        send_telegram_alert(
            minute=alert["minute"],
            device_ip=alert["device_ip"],
            packet_count=alert["packet_count"],
            total_bytes=alert["total_bytes"],
            anomaly_score=alert["anomaly_score"]
        )

    # Return the number of newly inserted detection records.
    return processed_count




# ============================================================
# Step 4: Retrieve dashboard traffic statistics
# ============================================================

def get_dashboard_stats():

    # Open the database in read-only mode.
    connection = sqlite3.connect(
        f"file:{DATABASE_PATH}?mode=ro",
        uri=True
    )

    # Return query results using their column names.
    connection.row_factory = sqlite3.Row

    try:
        # Create a cursor for executing SQL queries.
        cursor = connection.cursor()

        # Retrieve aggregated traffic statistics for the monitored VM.
        cursor.execute("""
            SELECT
                COUNT(*) AS feature_records,
                COALESCE(SUM(packet_count), 0) AS total_packets,
                COALESCE(SUM(total_bytes), 0) AS total_bytes,
                COALESCE(SUM(tcp_count), 0) AS tcp_packets,
                COALESCE(SUM(udp_count), 0) AS udp_packets,
                COALESCE(SUM(dns_count), 0) AS dns_packets
            FROM device_traffic_features
            WHERE device_ip = ?
        """, (MONITORED_DEVICE_IP,))

        # Retrieve the traffic statistics.
        traffic = cursor.fetchone()

        # Count the potential anomalies stored by the ML model.
        cursor.execute("""
            SELECT COUNT(*)
            FROM anomaly_detections
            WHERE device_ip = ?
            AND prediction = -1
        """, (MONITORED_DEVICE_IP,))

        # Retrieve the anomaly count.
        anomaly_count = cursor.fetchone()[0]

        # Prepare the statistics for the dashboard.
        stats = {
            "monitored_devices": 1,
            "total_packets": traffic["total_packets"],
            "total_bytes": traffic["total_bytes"],
            "total_mb": round(
                traffic["total_bytes"] / (1024 * 1024), 2
            ),
            "tcp_packets": traffic["tcp_packets"],
            "udp_packets": traffic["udp_packets"],
            "dns_packets": traffic["dns_packets"],
            "feature_records": traffic["feature_records"],
            "detected_anomalies": anomaly_count
        }

        # Return the collected dashboard statistics.
        return stats

    finally:
        # Close the database connection.
        connection.close()


# ============================================================
# Step 5: Retrieve traffic chart data
# ============================================================

def get_traffic_chart_data():

    # Open the existing database in read-only mode.
    connection = sqlite3.connect(
        f"file:{DATABASE_PATH}?mode=ro",
        uri=True
    )

    try:
        # Create a cursor for executing SQL queries.
        cursor = connection.cursor()

        # Retrieve packet counts in chronological order.
        cursor.execute("""
            SELECT
                minute,
                packet_count
            FROM device_traffic_features
            WHERE device_ip = ?
            ORDER BY minute ASC
        """, (MONITORED_DEVICE_IP,))

        # Fetch all matching traffic records.
        records = cursor.fetchall()

        # Separate timestamps and packet counts for the chart.
        chart_data = {
            "labels": [row[0] for row in records],
            "packets": [row[1] for row in records]
        }

        # Return the chart data.
        return chart_data

    finally:
        # Close the database connection.
        connection.close()


# ============================================================
# Step 6: Retrieve recent anomaly alerts
# ============================================================

def get_recent_anomalies():

    # Open the database in read-only mode.
    connection = sqlite3.connect(
        f"file:{DATABASE_PATH}?mode=ro",
        uri=True
    )

    # Return query results using their column names.
    connection.row_factory = sqlite3.Row

    try:
        # Create a cursor for executing SQL queries.
        cursor = connection.cursor()

        # Retrieve the ten most recent potential anomalies.
        cursor.execute("""
            SELECT
                minute,
                device_ip,
                anomaly_score,
                detected_at
            FROM anomaly_detections
            WHERE device_ip = ?
            AND prediction = -1
            ORDER BY minute DESC
            LIMIT 10
        """, (MONITORED_DEVICE_IP,))

        # Retrieve the matching anomaly records.
        records = cursor.fetchall()

        # Convert database rows into dictionaries for JSON responses.
        anomalies = [dict(record) for record in records]

        # Return the recent anomaly records.
        return anomalies

    finally:
        # Close the database connection.
        connection.close()


# ============================================================
# Step 7: Define the dashboard homepage
# ============================================================

@app.route("/")
def home():

    # Process any new traffic records before displaying the dashboard.
    process_new_records()

    # Retrieve the dashboard summary statistics.
    stats = get_dashboard_stats()

    # Retrieve packet activity for the traffic chart.
    chart_data = get_traffic_chart_data()

    # Retrieve recent potential anomaly alerts.
    recent_anomalies = get_recent_anomalies()

    # Render the dashboard with all retrieved information.
    return render_template(
        "index.html",
        stats=stats,
        chart_data=chart_data,
        recent_anomalies=recent_anomalies
    )


# ============================================================
# Step 8: Provide dashboard information through the API
# ============================================================

@app.route("/api/dashboard-data")
def dashboard_data():

    # Process any new traffic records before updating the dashboard.
    process_new_records()

    # Retrieve the latest dashboard statistics.
    stats = get_dashboard_stats()

    # Retrieve the latest traffic chart data.
    chart_data = get_traffic_chart_data()

    # Retrieve the latest potential anomaly alerts.
    recent_anomalies = get_recent_anomalies()

    # Return all dashboard information as JSON.
    return jsonify({
        "stats": stats,
        "chart_data": chart_data,
        "recent_anomalies": recent_anomalies
    })


# ============================================================
# Step 9: Start the Flask development server
# ============================================================

if __name__ == "__main__":

    # Listen on port 5000 during development.
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

