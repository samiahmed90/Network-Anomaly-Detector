from scapy.all import sniff, IP, TCP, UDP

def process_packet(packet):
    if IP in packet:
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        protocol = packet[IP].proto
        size = len(packet)

        src_port = None
        dst_port = None

        if TCP in packet:
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif UDP in packet:
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport

        print(
            f"{src_ip} -> {dst_ip} | "
            f"Protocol: {protocol} | "
            f"Src Port: {src_port} | "
            f"Dst Port: {dst_port} | "
            f"Size: {size}"
        )

sniff(iface="enp0s8", prn=process_packet)