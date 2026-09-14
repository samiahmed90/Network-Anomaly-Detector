# Network Setup

## Overview

The Network Anomaly Detector is developed and tested inside a controlled VirtualBox laboratory environment.

The lab consists of two virtual machines:

- **Ubuntu Sensor VM** — acts as the network sensor and gateway.
- **Windows Test VM** — generates normal and anomalous network traffic for testing.

The Windows VM does not connect directly to the Internet. Instead, its traffic is routed through the Ubuntu Sensor VM. This allows the project to monitor the Windows VM's traffic using Scapy while keeping the experiment isolated from the host and school network.

---

## Network Architecture

The lab uses two different VirtualBox network types:

1. **NAT** — provides Internet access to the Ubuntu Sensor VM.
2. **Internal Network** — provides a private network between the Ubuntu Sensor VM and Windows Test VM.

The resulting network topology is:

```text
                         INTERNET
                            │
                            │
                     VirtualBox NAT
                            │
                     10.0.2.15
                            │
                  ┌─────────────────┐
                  │  Ubuntu Sensor  │
                  │                 │
                  │ enp0s3: NAT     │
                  │ 10.0.2.15       │
                  │                 │
                  │ enp0s8: Internal │
                  │ 192.168.50.1    │
                  └────────┬────────┘
                           │
                    Internal Network
                      "AnomalyLab"
                           │
                           │
                  192.168.50.10
                           │
                  ┌────────┴────────┐
                  │  Windows Test   │
                  │       VM        │
                  └─────────────────┘
```

---

## VirtualBox Configuration

### Ubuntu Sensor VM

The Ubuntu VM has two network adapters.

| Adapter | VirtualBox Network | Purpose | IP Address |
|---|---|---|---|
| Adapter 1 | NAT | Internet access | `10.0.2.15` |
| Adapter 2 | Internal Network | Private lab traffic | `192.168.50.1` |

The Internal Network is named:

```text
AnomalyLab
```

Ubuntu's interfaces are:

```text
enp0s3 → NAT
enp0s8 → Internal Network
```

### Windows Test VM

The Windows VM has one network adapter:

| Adapter | VirtualBox Network | Purpose | IP Address |
|---|---|---|---|
| Adapter 1 | Internal Network | Private lab traffic | `192.168.50.10` |

The Windows VM does **not** have its own NAT adapter.

This ensures that its Internet traffic must pass through the Ubuntu Sensor VM.

---

## Ubuntu Internal Network Configuration

The Ubuntu Sensor VM uses `enp0s8` for the private laboratory network.

The interface was assigned:

```text
IP Address: 192.168.50.1
Subnet:     255.255.255.0
```

The interface was configured with:

```bash
sudo ip addr add 192.168.50.1/24 dev enp0s8
sudo ip link set enp0s8 up
```

The configuration was verified with:

```bash
ip addr show enp0s8
```

The result showed:

```text
inet 192.168.50.1/24
```

### Screenshot

<!-- <img width="1570" height="1244" alt="Screenshot 2026-09-13 200856" src="https://github.com/user-attachments/assets/02a0bc03-b315-4ae7-953e-8e7892494579" />
 -->

<br><br><br><br><br>

---

## Windows Network Configuration

The Windows Test VM was assigned:

```text
IP Address:       192.168.50.10
Subnet Mask:      255.255.255.0
Default Gateway:  192.168.50.1
DNS Server:       8.8.8.8
```

The Ubuntu Sensor VM (`192.168.50.1`) is therefore the Windows VM's default gateway.

### Screenshot

<!-- <img width="1282" height="932" alt="image" src="https://github.com/user-attachments/assets/663e5ca2-69c8-4489-b293-c5f04dcd5514" />
 -->

<br><br><br><br><br>

---

## Testing the Private Network

Before enabling Internet routing, connectivity between the two VMs was tested.

From the Windows VM:

```cmd
ping 192.168.50.1
```

The Windows VM successfully received replies from the Ubuntu Sensor VM.

This confirmed that the VirtualBox Internal Network was functioning correctly.

### Screenshot

<!-- <img width="1282" height="932" alt="image" src="https://github.com/user-attachments/assets/92585a44-f0b9-4940-a207-18b3e836abb1" />
 -->

<br><br><br><br><br>

---

## Configuring Ubuntu as a Router

Ubuntu was configured to forward IPv4 traffic.

IPv4 forwarding was enabled with:

```bash
sudo sysctl -w net.ipv4.ip_forward=1
```

This allows Ubuntu to forward packets between its two network interfaces.

The traffic flow is:

```text
Windows VM
192.168.50.10
      │
      │
      ▼
Ubuntu enp0s8
192.168.50.1
      │
      │ IP forwarding
      ▼
Ubuntu enp0s3
10.0.2.15
      │
      │ NAT
      ▼
Internet
```

---

## NAT Configuration

Ubuntu uses NAT (Network Address Translation) so that traffic originating from the Windows VM can access the Internet through Ubuntu's NAT interface.

The following rule was added:

```bash
sudo iptables -t nat -A POSTROUTING -o enp0s3 -j MASQUERADE
```

Forwarding from the Internal Network to the Internet was allowed with:

```bash
sudo iptables -A FORWARD -i enp0s8 -o enp0s3 -j ACCEPT
```

Return traffic was allowed with:

```bash
sudo iptables -A FORWARD -i enp0s3 -o enp0s8 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
```

---

## Testing Internet Connectivity

Internet connectivity was tested from the Windows VM.

First, the Windows VM successfully reached Google's public DNS server:

```cmd
ping 8.8.8.8
```

This confirmed that traffic was successfully being routed:

```text
Windows → Ubuntu → Internet
```

### Screenshot

<!-- <img width="1280" height="996" alt="image" src="https://github.com/user-attachments/assets/17fe2fb3-8c2f-4ea8-b80a-53e36ee84fe9" />
 -->

<br><br><br><br><br>

---

## DNS Configuration

Initially, the Windows VM could reach `8.8.8.8` but could not resolve domain names.

For example:

```cmd
ping google.com
```

failed because Ubuntu was not configured as a DNS server.

The Windows DNS server was therefore changed to:

```text
8.8.8.8
```

After changing the DNS server, the following test succeeded:

```cmd
ping google.com
```

This confirmed that both Internet connectivity and DNS resolution were working.

### Screenshot

<!-- <img width="1280" height="996" alt="image" src="https://github.com/user-attachments/assets/9343fb72-82e5-43a0-9806-76270dfe3abf" />
 -->

<br><br><br><br><br>

---

## Verifying Traffic Visibility

Once routing was working, traffic generated by the Windows VM was monitored from Ubuntu.

The Ubuntu Sensor VM monitored its Internal Network interface:

```text
enp0s8
```

Traffic was initially verified using:

```bash
sudo tcpdump -i enp0s8
```

While the Windows VM generated Internet traffic, Ubuntu observed packets such as:

```text
192.168.50.10 → external IP:443
external IP:443 → 192.168.50.10
```

This confirmed that the Windows VM's Internet traffic passes through the Ubuntu Sensor VM before reaching the Internet.

### Screenshot

<!-- <img width="1626" height="1364" alt="image" src="https://github.com/user-attachments/assets/e32aa73d-fdf0-4c59-b3ae-c00794151081" />
 -->

<br><br><br><br><br>

---

## Why This Architecture Is Used

This architecture provides a controlled environment for developing and testing the Network Anomaly Detector.

The project does **not** monitor the school's production network or other users' traffic.

Instead:

- The Windows VM generates test traffic.
- Ubuntu acts as the controlled network sensor.
- The Internal Network isolates the laboratory traffic.
- Ubuntu provides the Internet connection for the test VM.
- Scapy can monitor the traffic passing through Ubuntu's Internal Network interface.
- Different traffic patterns can be generated to test anomaly detection.

This allows the project to simulate a small network environment without requiring access to a real production network.

---

## Traffic Capture Interface

The project will use:

```text
enp0s8
```

as the primary network interface for packet capture.

The NAT interface:

```text
enp0s3
```

is used by Ubuntu for its own Internet connectivity and is not the intended interface for monitoring the Windows test traffic.

The Scapy sensor will therefore capture traffic specifically from:

```text
enp0s8
```

---

## Current Lab Status

| Component | Status |
|---|---|
| Ubuntu NAT connectivity | Working |
| Ubuntu Internal Network | Working |
| Windows → Ubuntu connectivity | Working |
| Ubuntu IPv4 forwarding | Working |
| Ubuntu NAT | Working |
| Windows → Internet | Working |
| Windows DNS resolution | Working |
| Windows traffic visible on Ubuntu | Working |
| Scapy packet capture | Next step |

---

