
# ============================================================
# Live Feature Extraction
# ============================================================
# This script processes completed one-minute packet windows
# and stores device-specific traffic features in SQLite.
# ============================================================

# Import SQLite for database operations.
import sqlite3

# Import time so the script can run continuously.
import time

# Import datetime to identify completed one-minute windows.
from datetime import datetime, timedelta

# Import Path to locate the database reliably.
from pathlib import Path


# ------------------------------------------------------------
# 1. Database configuration
# ------------------------------------------------------------

# Locate the project directory (the parent of this folder).
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Build the absolute path to the existing database.
DATABASE_PATH = PROJECT_DIR / "network.db"

# Set how often the script checks for completed minutes.
CHECK_INTERVAL = 10


# ------------------------------------------------------------
# 2. Extract features for completed minutes
# ------------------------------------------------------------

def extract_completed_minutes():

    # Open a connection to the existing database.
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        # Determine the beginning of the current minute.
        current_minute = datetime.now().replace(
            second=0,
            microsecond=0
        )

        # Only process minutes that have fully ended.
        completed_minute = (
            current_minute - timedelta(minutes=1)
        ).strftime("%Y-%m-%d %H:%M")

        # Calculate traffic features separately for each source IP.
        cursor.execute("""
            SELECT
                strftime('%Y-%m-%d %H:%M', timestamp) AS minute,
                src_ip AS device_ip,
                COUNT(*) AS packet_count,
                SUM(packet_size) AS total_bytes,
                AVG(packet_size) AS average_packet_size,
                SUM(CASE WHEN LOWER(protocol) = 'tcp' THEN 1 ELSE 0 END),
                SUM(CASE WHEN LOWER(protocol) = 'udp' THEN 1 ELSE 0 END),
                COUNT(DISTINCT dst_ip) AS unique_destinations,
                COUNT(DISTINCT dst_port) AS unique_ports,
                SUM(CASE WHEN dst_port = 53 THEN 1 ELSE 0 END)
            FROM packets
            WHERE timestamp >= ?
              AND timestamp < ?
            GROUP BY minute, device_ip
        """, (
            completed_minute,
            current_minute.strftime("%Y-%m-%d %H:%M:%S")
        ))

        # Retrieve the calculated results.
        feature_records = cursor.fetchall()

        # Insert or update the device-specific feature records.
        for record in feature_records:

            cursor.execute("""
                INSERT INTO device_traffic_features (
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
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(minute, device_ip)
                DO UPDATE SET
                    packet_count = excluded.packet_count,
                    total_bytes = excluded.total_bytes,
                    average_packet_size = excluded.average_packet_size,
                    tcp_count = excluded.tcp_count,
                    udp_count = excluded.udp_count,
                    unique_destinations = excluded.unique_destinations,
                    unique_ports = excluded.unique_ports,
                    dns_count = excluded.dns_count
            """, record)

            print(
                f"Processed {record[0]} | "
                f"Device: {record[1]} | "
                f"Packets: {record[2]} | "
                f"Bytes: {record[3]}"
            )

        # Save all feature records.
        connection.commit()

        if not feature_records:
            print(
                f"No packets found for {completed_minute}"
            )

    finally:
        # Always close the database connection.
        connection.close()


# ------------------------------------------------------------
# 3. Run feature extraction continuously
# ------------------------------------------------------------

if __name__ == "__main__":

    print("Live feature extraction started.")
    print(f"Database: {DATABASE_PATH}")
    print(f"Checking every {CHECK_INTERVAL} seconds.")
    print("Press Ctrl+C to stop.")

    try:
        while True:

            extract_completed_minutes()

            # Wait before checking again.
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nLive feature extraction stopped.")
