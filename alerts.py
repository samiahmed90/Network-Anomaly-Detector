
# ============================================================
# Network Anomaly Detector - Telegram Alert Handler
# ============================================================

# Import os to access environment variables.
import os

# Import Path to locate the project directory.
from pathlib import Path

# Import requests to communicate with Telegram.
import requests

# Import load_dotenv to load credentials from .env.
from dotenv import load_dotenv


# ============================================================
# Step 1: Load Telegram credentials
# ============================================================

# Locate the project directory.
PROJECT_DIRECTORY = Path(__file__).resolve().parent

# Load credentials from the project's .env file.
load_dotenv(PROJECT_DIRECTORY / ".env")

# Retrieve the Telegram bot token.
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Retrieve the Telegram chat ID.
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ============================================================
# Step 2: Define the Telegram alert function
# ============================================================

def send_telegram_alert(
    minute,
    device_ip,
    packet_count,
    total_bytes,
    anomaly_score
):

    # Check that Telegram credentials are available.
    if not BOT_TOKEN or not CHAT_ID:
        print("ERROR: Telegram credentials are missing.")
        return False

    # Calculate traffic volume in megabytes.
    total_mb = total_bytes / (1024 * 1024)

    # Prepare the alert message.
    message = (
        "NETWORK ANOMALY DETECTOR\n\n"
        "Potential unusual network activity detected!\n\n"
        f"Device IP: {device_ip}\n"
        f"Detection time: {minute}\n"
        f"Packet count: {packet_count:,}\n"
        f"Traffic volume: {total_mb:.2f} MB\n"
        f"Anomaly score: {anomaly_score:.5f}\n\n"
        "The Isolation Forest model flagged this "
        "traffic window as unusual.\n"
        "This does not confirm malicious activity."
    )

    # Construct the Telegram Bot API endpoint.
    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    # Prepare the message information.
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    # Attempt to send the notification.
    try:
        response = requests.post(
            url,
            data=payload,
            timeout=15
        )

        # Convert the response into JSON.
        result = response.json()

        # Check whether Telegram accepted the message.
        if result.get("ok"):
            print(
                f"Telegram alert sent for {device_ip} "
                f"at {minute}"
            )
            return True

        # Display an API error without exposing credentials.
        print(
            "Telegram API error:",
            result.get("description")
        )

        return False

    except requests.RequestException as error:

        # Handle connection and timeout errors.
        print("Telegram connection error:", error)
        return False
