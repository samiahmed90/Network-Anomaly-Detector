import sqlite3

# Connect to the SQLite database
connection = sqlite3.connect("network.db")
cursor = connection.cursor()

# Count packets for each one-minute time window
cursor.execute("""
    SELECT strftime('%Y-%m-%d %H:%M', timestamp) AS minute,
           COUNT(*) AS packet_count
    FROM packets
    GROUP BY minute
    ORDER BY minute
""")

for minute, packet_count in cursor.fetchall():
    print(f"{minute} | {packet_count} packets")


# Calculate packets and total bytes for each one-minute time window
cursor.execute("""
    SELECT strftime('%Y-%m-%d %H:%M', timestamp) AS minute,
           COUNT(*) AS packet_count,
           SUM(packet_size) AS total_bytes
    FROM packets
    GROUP BY minute
    ORDER BY minute
""")

for minute, packet_count, total_bytes in cursor.fetchall():
    print(
        f"{minute} | "
        f"Packets: {packet_count} | "
        f"Bytes: {total_bytes}"
    )

# Calculate the total number of TCP packets captured
cursor.execute("SELECT COUNT(*) FROM packets WHERE protocol = 'tcp'")
tcp_count = cursor.fetchone()[0]
print(f"TCP packets: {tcp_count}")

# Calculate the total number of UDP packets captured
cursor.execute("SELECT COUNT(*) FROM packets WHERE protocol = 'udp'")
udp_count = cursor.fetchone()[0]
print(f"UDP packets: {udp_count}")

# Calculate the number of unique destination IP addresses
cursor.execute("SELECT COUNT(DISTINCT dst_ip) FROM packets")
unique_destinations = cursor.fetchone()[0]
print(f"Unique destinations: {unique_destinations}")

# Calculate the number of uniquie destination ports
cursor.execute("SELECT COUNT(DISTINCT dst_port) FROM packets")
unique_ports = cursor.fetchone()[0]
print(f"Unique ports: {unique_ports}")

# Calculate the average packet size
cursor.execute("SELECT AVG(packet_size) FROM packets")
average_packet_size = cursor.fetchone()[0]
print(f"Average packet size: {average_packet_size:.2f} bytes")

# Calculate the packet capture duration
cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM packets")
start_time, end_time = cursor.fetchone()

# Calculate the duration in seconds
cursor.execute(
    "SELECT (julianday(?) - julianday(?)) * 86400",
    (end_time, start_time)
)
duration = cursor.fetchone()[0]

# Calculate packets per second
packets_per_second = packet_count / duration
print(f"Packets per second: {packets_per_second:.2f}")

# Calculate the number of DNS packets
cursor.execute("SELECT COUNT(*) FROM packets WHERE dst_port = 53")
dns_count = cursor.fetchone()[0]
print(f"DNS packets: {dns_count}")

# Calculate the number of unique communication pairs
cursor.execute(
    "SELECT COUNT(DISTINCT src_ip || ' → ' || dst_ip) FROM packets"
)
unique_pairs = cursor.fetchone()[0]
print(f"Unique communication pairs: {unique_pairs}")
