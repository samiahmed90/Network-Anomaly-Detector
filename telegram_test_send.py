
# ============================================================
# Telegram Notification Test
# ============================================================

import os
import requests
from dotenv import load_dotenv

# Load Telegram credentials from the .env file.
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Check that both credentials are available.
if not BOT_TOKEN or not CHAT_ID:
    print("ERROR: Telegram credentials are missing from .env")
    exit()

# Telegram Bot API endpoint.
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Message to send to your Telegram account.
payload = {
    "chat_id": CHAT_ID,
    "text": "Network Anomaly Detector: Telegram alert test successful!"
}

# Send the message.
try:
    response = requests.post(url, data=payload, timeout=15)
    result = response.json()

    if result.get("ok"):
        print("SUCCESS: Telegram notification sent!")
    else:
        print("Telegram API error:", result.get("description"))

except requests.RequestException as error:
    print("Connection error:", error)

