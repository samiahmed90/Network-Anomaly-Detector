import sqlite3

# Connect to the SQLite database
connection = sqlite3.connect("network.db")

cursor = connection.cursor()
cursor.execute("SELECT COUNT(*) FROM packets")

packet_count = cursor.fetchone()[0]
print(f"Total packets: {packet_count}")