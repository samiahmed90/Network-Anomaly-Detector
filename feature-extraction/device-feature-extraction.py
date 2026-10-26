
import sqlite3

# Connect to the database
connection = sqlite3.connect("network.db")
cursor = connection.cursor()

# Create a separate table for per-device features
cursor.execute("""
    CREATE TABLE IF NOT EXISTS device_traffic_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        minute TEXT NOT NULL,
        device_ip TEXT NOT NULL,
        packet_count INTEGER,
        total_bytes INTEGER,
        average_packet_size REAL,
        tcp_count INTEGER,
        udp_count INTEGER,
        unique_destinations INTEGER,
        unique_ports INTEGER,
        dns_count INTEGER,
        UNIQUE(minute, device_ip)
    )
""")

# Calculate traffic features for each device per minute
cursor.execute("""
    SELECT
        strftime('%Y-%m-%d %H:%M', timestamp) AS minute,
        src_ip AS device_ip,
        COUNT(*) AS packet_count,
        SUM(packet_size) AS total_bytes,
        AVG(packet_size) AS average_packet_size,
        SUM(CASE WHEN LOWER(protocol) = 'tcp' THEN 1 ELSE 0 END)
            AS tcp_count,
        SUM(CASE WHEN LOWER(protocol) = 'udp' THEN 1 ELSE 0 END)
            AS udp_count,
        COUNT(DISTINCT dst_ip) AS unique_destinations,
        COUNT(DISTINCT dst_port) AS unique_ports,
        SUM(CASE WHEN dst_port = 53 THEN 1 ELSE 0 END)
            AS dns_count
    FROM packets
    GROUP BY minute, device_ip
    ORDER BY minute, device_ip
""")

rows = cursor.fetchall()

# Save the results without creating duplicate records
cursor.executemany("""
    INSERT OR REPLACE INTO device_traffic_features (
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
""", rows)

connection.commit()

print(f"Device feature records processed: {len(rows)}")

# Show a sample of the results
for row in rows[:10]:
    (
        minute, device_ip, packet_count, total_bytes,
        average_packet_size, tcp_count, udp_count,
        unique_destinations, unique_ports, dns_count
    ) = row

    print(
        f"{minute} | Device: {device_ip} | "
        f"Packets: {packet_count} | Bytes: {total_bytes} | "
        f"Avg size: {average_packet_size:.2f} | "
        f"TCP: {tcp_count} | UDP: {udp_count} | "
        f"Destinations: {unique_destinations} | "
        f"Ports: {unique_ports} | DNS: {dns_count}"
    )

connection.close()
