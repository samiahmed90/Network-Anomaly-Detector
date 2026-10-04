import sqlite3

# Connect to the SQLite database
connection = sqlite3.connect("network.db")
cursor = connection.cursor()

# Calculate network traffic features for each one-minute time window
cursor.execute("""
    SELECT strftime('%Y-%m-%d %H:%M', timestamp) AS minute,
           COUNT(*) AS packet_count,
           SUM(packet_size) AS total_bytes,
           AVG(packet_size) AS average_packet_size,
           SUM(CASE WHEN protocol = 'tcp' THEN 1 ELSE 0 END) AS tcp_count,
           SUM(CASE WHEN protocol = 'udp' THEN 1 ELSE 0 END) AS udp_count,
           COUNT(DISTINCT dst_ip) AS unique_destinations,
           COUNT(DISTINCT dst_port) AS unique_ports,
           SUM(CASE WHEN dst_port = 53 THEN 1 ELSE 0 END) AS dns_count,
           COUNT(DISTINCT src_ip || '-' || dst_ip) AS unique_communication_pairs
    FROM packets
    GROUP BY minute
    ORDER BY minute
""")
for minute, packet_count, total_bytes, average_packet_size, tcp_count, udp_count, unique_destinations, unique_ports, dns_count, unique_communication_pairs in cursor.fetchall():

    cursor.execute("""
        INSERT INTO traffic_features (
            minute,
            packet_count,
            total_bytes,
            average_packet_size,
            tcp_count,
            udp_count,
            unique_destinations,
            unique_ports,
            dns_count,
            unique_communication_pairs
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        minute,
        packet_count,
        total_bytes,
        average_packet_size,
        tcp_count,
        udp_count,
        unique_destinations,
        unique_ports,
        dns_count,
        unique_communication_pairs
    ))

    print(
        f"{minute} | "
        f"Packets: {packet_count} | "
        f"Bytes: {total_bytes} | "
        f"Avg packet size: {average_packet_size:.2f} | "
        f"TCP: {tcp_count} | "
        f"UDP: {udp_count} | "
        f"Unique destinations: {unique_destinations} | "
        f"Unique ports: {unique_ports} | "
        f"DNS: {dns_count} | "
        f"Communication pairs: {unique_communication_pairs}"
    )

connection.commit()