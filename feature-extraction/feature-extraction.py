import sqlite3

# Connect to the SQLite database
connection = sqlite3.connect("network.db")
cursor = connection.cursor()

# Calculate packets, bytes, TCP, UDP, and unique destinations
# for each one-minute time window
cursor.execute("""
    SELECT strftime('%Y-%m-%d %H:%M', timestamp) AS minute,
           COUNT(*) AS packet_count,
           SUM(packet_size) AS total_bytes,
           AVG(packet_size) AS average_packet_size,
           SUM(CASE WHEN protocol = 'tcp' THEN 1 ELSE 0 END) AS tcp_count,
           SUM(CASE WHEN protocol = 'udp' THEN 1 ELSE 0 END) AS udp_count,
           COUNT(DISTINCT dst_ip) AS unique_destinations,
           COUNT(DISTINCT dst_port) AS unique_ports,
           SUM(CASE WHEN dst_port = 53 THEN 1 else 0 END) AS dns_count    
    FROM packets
    GROUP BY minute
    ORDER BY minute
""")
for minute, packet_count, total_bytes, average_packet_size, tcp_count, udp_count, unique_destinations, unique_ports, dns_count in cursor.fetchall():
    print(
    f"{minute} | "
    f"Packets: {packet_count} | "
    f"Bytes: {total_bytes} | "
    f"Avg packet size: {average_packet_size:.2f} | "
    f"TCP: {tcp_count} | "
    f"UDP: {udp_count} | "
    f"Unique destinations: {unique_destinations} | "
    f"Unique ports: {unique_ports} | "
    f"DNS: {dns_count}"
    
)



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

# Calculate the number of unique communication pairs
cursor.execute(
    "SELECT COUNT(DISTINCT src_ip || ' → ' || dst_ip) FROM packets"
)
unique_pairs = cursor.fetchone()[0]
print(f"Unique communication pairs: {unique_pairs}")
