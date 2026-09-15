from scapy.all import sniff, IP, TCP, UDP
from datetime import datetime


def process_packet(packet):
    if IP not in packet:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    src_ip = packet[IP].src
    dst_ip = packet[IP].dst
    packet_size = len(packet)

    if TCP in packet:
        protocol = "TCP"
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport

    elif UDP in packet:
        protocol = "UDP"
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport

    else:
        protocol = str(packet[IP].proto)
        src_port = "-"
        dst_port = "-"

    print(
        f"{timestamp} | "
        f"{src_ip} -> {dst_ip} | "
        f"Protocol: {protocol} | "
        f"Src Port: {src_port} | "
        f"Dst Port: {dst_port} | "
        f"Size: {packet_size}"
    )


sniff(iface="enp0s8", prn=process_packet)