from scapy.all import sniff, IP, TCP, UDP
from scapy.layers.inet import IP_PROTOS
from datetime import datetime


def process_packet(packet):
    if IP not in packet:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    src_ip = packet[IP].src
    dst_ip = packet[IP].dst
    packet_size = len(packet)

    # Get protocol name automatically
    protocol_number = packet[IP].proto
    protocol = IP_PROTOS.get(
        protocol_number,
        f"Protocol-{protocol_number}"
    )

    # Get ports for TCP/UDP
    if TCP in packet:
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport

    elif UDP in packet:
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport

    else:
        src_port = "-"
        dst_port = "-"

    print(
        f"{timestamp} | "
        f"{src_ip} -> {dst_ip} | "
        f"Protocol: {protocol} ({protocol_number}) | "
        f"Src Port: {src_port} | "
        f"Dst Port: {dst_port} | "
        f"Size: {packet_size}"
    )


sniff(iface="enp0s8", prn=process_packet)