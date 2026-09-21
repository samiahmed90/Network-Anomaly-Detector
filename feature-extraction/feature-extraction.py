import sqlite3

# Connect to the SQLite database
connection = sqlite3.connect("network.db")


cursor = connection.cursor()

# Count the total number of captured packets

cursor.execute("SELECT COUNT(*) FROM packets")
packet_count = cursor.fetchone()[0]
print(f"Total packets: {packet_count}")


# Calculate the total amount of captured data in bytes

cursor.execute("SELECT SUM(packet_size) FROM packets")

total_bytes = cursor.fetchone()[0]

print(f"Total bytes: {total_bytes}")

# Calculate the total number of TCP packets captured
cursor.execute("SELECT COUNT(*) FROM packets WHERE protocol = 'tcp'")
tcp_count = cursor.fetchone()[0]
print(f"TCP packets: {tcp_count}")
