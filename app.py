
# Import Flask to create our web application.
from flask import Flask, render_template

# Import SQLite to read the project's database.
import sqlite3

# Import Path to locate the database reliably.
from pathlib import Path

# Create the Flask application instance.
app = Flask(__name__)

# Locate the database in the same directory as this file.
DATABASE_PATH = Path(__file__).resolve().parent / "network.db"

# Identify the Windows test VM we are monitoring.
MONITORED_DEVICE_IP = "192.168.50.10"


# Retrieve traffic statistics for the monitored Windows VM.
def get_dashboard_stats():

    # Open the SQLite database in read-only mode.
    connection = sqlite3.connect(
        f"file:{DATABASE_PATH}?mode=ro",
        uri=True
    )

    # Return query results using their column names.
    connection.row_factory = sqlite3.Row

    try:
        # Create a cursor to execute SQL queries.
        cursor = connection.cursor()

        # Retrieve the Windows VM's aggregated traffic statistics.
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

        # Retrieve the query result.
        traffic = cursor.fetchone()

        # Prepare the statistics for the dashboard.
        stats = {
            "monitored_devices": 1,
            "total_packets": traffic["total_packets"],
            "total_bytes": traffic["total_bytes"],
            "total_mb": round(traffic["total_bytes"] / (1024 * 1024), 2),
            "tcp_packets": traffic["tcp_packets"],
            "udp_packets": traffic["udp_packets"],
            "dns_packets": traffic["dns_packets"],
            "feature_records": traffic["feature_records"],
            "detected_anomalies": 0
        }

        # Return the collected statistics.
        return stats

    finally:
        # Close the database connection even if a query fails.
        connection.close()


# Retrieve packet counts over time for the monitored Windows VM.
def get_traffic_chart_data():

    # Open the existing SQLite database in read-only mode.
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

        # Return the chart data to the dashboard.
        return chart_data

    finally:
        # Close the database connection.
        connection.close()



# Define the dashboard homepage.
@app.route("/")
def home():

    # Retrieve the dashboard summary statistics.
    stats = get_dashboard_stats()

    # Retrieve packet activity for the traffic chart.
    chart_data = get_traffic_chart_data()

    # Render the dashboard with both sets of data.
    return render_template(
        "index.html",
        stats=stats,
        chart_data=chart_data
    )



# Start the Flask development server.
if __name__ == "__main__":

    # Listen on port 5000 during development.
    app.run(host="0.0.0.0", port=5000, debug=True)
