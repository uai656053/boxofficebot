from curl_cffi import requests as curl_requests
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==============================
# URLs
# ==============================

TRACK_URL = "https://tracktollywood.com/box-office-collection/the-paradise/"

SACNILK_URL = (
    "https://www.sacnilk.com/quicknews/"
    "The_Paradise_2026_Seventh_Day_Advance_Booking_Report"
)

# ==============================
# TrackTollywood
# ==============================

def get_tracktollywood():

    response = curl_requests.get(
        TRACK_URL,
        impersonate="chrome",
        timeout=30
    )

    print("TrackTollywood Status:", response.status_code)

    if response.status_code != 200:
        raise Exception(
            f"TrackTollywood failed: {response.status_code}"
        )

    html = response.text

    match = re.search(
        r'<script type="application/json" id="tt-mv-card-data">(.*?)</script>',
        html,
        re.DOTALL
    )

    if not match:
        raise Exception(
            "TrackTollywood movie data not found."
        )

    data = json.loads(match.group(1))

    today_collection = None

    for tile in data["tiles"]:

        if tile["label"] == "Today's Gross":
            today_collection = tile["value"]
            break

    if today_collection is None:
        raise Exception(
            "Today's Gross not found."
        )

    updated = data.get("updated")

    return today_collection, updated


# ==============================
# Sacnilk
# ==============================

def get_sacnilk():

    response = requests.get(
        SACNILK_URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    print("Sacnilk Status:", response.status_code)

    if response.status_code != 200:
        raise Exception(
            f"Sacnilk failed: {response.status_code}"
        )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # Find required section
    heading = soup.find(
        lambda tag:
        tag.name in ["h2", "h3"]
        and
        "all days on sale" in
        tag.get_text(" ", strip=True).lower()
    )

    if not heading:
        raise Exception(
            "Sacnilk 'all days on sale' section not found."
        )

    table = heading.find_next("table")

    if not table:
        raise Exception(
            "Sacnilk table not found."
        )

    day_data = []

    rows = table.find_all("tr")

    for row in rows:

        cells = row.find_all(
            ["th", "td"]
        )

        if len(cells) < 2:
            continue

        day = cells[0].get_text(
            " ",
            strip=True
        )

        gross = cells[1].get_text(
            " ",
            strip=True
        )

        # Skip table header
        if day.lower() == "day":
            continue

        # Skip Total row
        if day.lower() == "total":
            continue

        # Remove extra value inside brackets
        # Example:
        # ₹23.77 Cr [₹20.41 Cr]
        # becomes:
        # ₹23.77 Cr

        gross = gross.split("[")[0].strip()

        day_data.append(
            (day, gross)
        )

    return day_data


# ==============================
# Telegram
# ==============================

def send_telegram(message):

    bot_token = os.getenv(
        "TELEGRAM_BOT_TOKEN"
    )

    chat_id = os.getenv(
        "TELEGRAM_CHAT_ID"
    )

    if not bot_token:
        raise Exception(
            "TELEGRAM_BOT_TOKEN is missing."
        )

    if not chat_id:
        raise Exception(
            "TELEGRAM_CHAT_ID is missing."
        )

    url = (
        f"https://api.telegram.org/"
        f"bot{bot_token}/sendMessage"
    )

    data = {
        "chat_id": chat_id,
        "text": message
    }

    response = requests.post(
        url,
        json=data,
        timeout=30
    )

    print(
        "Telegram Status:",
        response.status_code
    )

    print(
        "Telegram Response:",
        response.text
    )

    if response.status_code != 200:

        raise Exception(
            f"Telegram failed: {response.text}"
        )


# ==============================
# Main
# ==============================

def main():

    print("\n================================")
    print("THE PARADISE BOX OFFICE BOT")
    print("================================\n")

    # --------------------------------
    # TrackTollywood
    # --------------------------------

    today_collection, updated = (
        get_tracktollywood()
    )

    print("\nTrackTollywood:")
    print(
        "Today's Collection:",
        today_collection
    )

    print(
        "Updated:",
        updated
    )

    # --------------------------------
    # Sacnilk
    # --------------------------------

    day_data = get_sacnilk()

    print("\nSacnilk:")

    for day, gross in day_data:

        print(
            f"{day} -> {gross}"
        )

    # --------------------------------
    # Create Telegram message
    # --------------------------------

    message = (
        "🎬 THE PARADISE — BOX OFFICE\n"
        "\n"
        "📊 TRACKTOLLYWOOD\n"
        f"Today's Collection: {today_collection}\n"
        f"Updated: {updated}\n"
        "\n"
        "🎟️ SACNILK — ADVANCE BOOKING\n"
    )

    for day, gross in day_data:

        message += (
            f"{day}: {gross}\n"
        )

    message += (
        "\n"
        "📡 Sources: TrackTollywood & Sacnilk"
    )

    # --------------------------------
    # Display message in terminal
    # --------------------------------

    print("\n--------------------------------")
    print("MESSAGE TO SEND:")
    print("--------------------------------")

    print(message)

    # --------------------------------
    # Send Telegram
    # --------------------------------

    send_telegram(message)

    print(
        "\n✅ Telegram message sent!"
    )


# ==============================
# Run
# ==============================

if __name__ == "__main__":
    main()