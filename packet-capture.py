from scapy.all import sniff, IP, TCP, UDP
from scapy.layers.inet import IP_PROTOS
from datetime import datetime
import sqlite3


# Connect to SQLite database
connection = sqlite3.connect("network.db")


def process_packet(packet):
    if IP not in packet:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    src_ip = packet[IP].src
    dst_ip = packet[IP].dst
    packet_size = len(packet)

    # Get protocol name automatically
    protocol_number = packet[IP].proto
    try:
        protocol = IP_PROTOS[protocol_number]
    except KeyError:
        protocol = f"Protocol-{protocol_number}"

    # Get ports for TCP/UDP
    if TCP in packet:
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport

    elif UDP in packet:
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport

    else:
        src_port = None
        dst_port = None

    # Save packet to database
    connection.execute(
        """
        INSERT INTO packets
        (timestamp, src_ip, dst_ip, protocol, protocol_number,
         src_port, dst_port, packet_size)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            src_ip,
            dst_ip,
            protocol,
            protocol_number,
            src_port,
            dst_port,
            packet_size
        )
    )

    connection.commit()

    print(
        f"{timestamp} | "
        f"{src_ip} -> {dst_ip} | "
        f"Protocol: {protocol} ({protocol_number}) | "
        f"Src Port: {src_port} | "
        f"Dst Port: {dst_port} | "
        f"Size: {packet_size}"
    )


try:
    sniff(iface="enp0s8", prn=process_packet)

except KeyboardInterrupt:
    print("\nCapture stopped.")

finally:
    connection.close()