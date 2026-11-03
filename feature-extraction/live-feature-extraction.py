
# ============================================================
# Live Feature Extraction
# ============================================================
# Processes completed one-minute packet windows and stores
# device-specific traffic features in SQLite.
#
# Supports multiple monitored LAN devices.
# ============================================================

# Import SQLite for database operations.
import sqlite3

# Import time for continuous execution.
import time

# Import datetime for minute-based processing.
from datetime import datetime

# Import Path to locate the database.
from pathlib import Path


# ------------------------------------------------------------
# 1. Database and monitoring configuration
# ------------------------------------------------------------

# Locate the main project directory.
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Use the existing project database.
DATABASE_PATH = PROJECT_DIR / "network.db"

# Check for new completed minutes every 10 seconds.
CHECK_INTERVAL = 10

# Devices currently monitored by the system.
# Add more LAN device IP addresses here in the future.
MONITORED_DEVICES = [
    "192.168.50.10"
]


# ------------------------------------------------------------
# 2. Extract missing completed minute records
# ------------------------------------------------------------

def extract_completed_minutes():

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        # Identify the beginning of the current minute.
        current_minute = datetime.now().replace(
            second=0,
            microsecond=0
        )

        # Only process minutes that have fully ended.
        completed_boundary = current_minute.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Create placeholders for monitored device IPs.
        if not MONITORED_DEVICES:
            print("No devices configured for monitoring.")
            return

        placeholders = ",".join(
            "?" for _ in MONITORED_DEVICES
        )

        # Find completed minute/device combinations
        # that do not yet have a feature record.
        query = f"""
            SELECT
                strftime(
                    '%Y-%m-%d %H:%M',
                    p.timestamp
                ) AS minute,

                p.src_ip AS device_ip,

                COUNT(*) AS packet_count,

                SUM(p.packet_size) AS total_bytes,

                AVG(p.packet_size) AS average_packet_size,

                SUM(
                    CASE
                        WHEN LOWER(p.protocol) = 'tcp'
                        THEN 1
                        ELSE 0
                    END
                ) AS tcp_count,

                SUM(
                    CASE
                        WHEN LOWER(p.protocol) = 'udp'
                        THEN 1
                        ELSE 0
                    END
                ) AS udp_count,

                COUNT(DISTINCT p.dst_ip)
                    AS unique_destinations,

                COUNT(DISTINCT p.dst_port)
                    AS unique_ports,

                SUM(
                    CASE
                        WHEN p.src_port = 53
                          OR p.dst_port = 53
                        THEN 1
                        ELSE 0
                    END
                ) AS dns_count

            FROM packets p

            WHERE p.timestamp < ?
              AND p.src_ip IN ({placeholders})

              AND NOT EXISTS (
                  SELECT 1
                  FROM device_traffic_features f
                  WHERE f.minute = strftime(
                      '%Y-%m-%d %H:%M',
                      p.timestamp
                  )
                  AND f.device_ip = p.src_ip
              )

            GROUP BY minute, device_ip

            ORDER BY minute, device_ip
        """

        cursor.execute(
            query,
            [completed_boundary] + MONITORED_DEVICES
        )

        feature_records = cursor.fetchall()

        # Insert new feature records without replacing
        # existing historical records.
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
                DO NOTHING
            """, record)

            print(
                f"Processed: {record[0]} | "
                f"Device: {record[1]} | "
                f"Packets: {record[2]} | "
                f"Bytes: {record[3]} | "
                f"DNS: {record[9]}"
            )

        # Save new feature records.
        connection.commit()

        if not feature_records:
            print("No missing completed feature windows.")

    except sqlite3.Error as error:
        connection.rollback()
        print(f"Database error: {error}")

    finally:
        connection.close()


# ------------------------------------------------------------
# 3. Run feature extraction continuously
# ------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 55)
    print("LIVE FEATURE EXTRACTION STARTED")
    print("=" * 55)

    print(f"Database: {DATABASE_PATH}")
    print(f"Monitored devices: {MONITORED_DEVICES}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")

    print("Press Ctrl+C to stop.")
    print("=" * 55)

    try:
        while True:

            extract_completed_minutes()

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:

        print("\nLive feature extraction stopped.")

