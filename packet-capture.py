from scapy.all import sniff, IP

def process_packet(packet):
    if IP in packet:
        print(
            packet[IP].src, "->", packet[IP].dst, "| Protocol:", packet[IP].proto, "| Size:", len(packet)
        )

sniff(iface="enp0s8", prn=process_packet)