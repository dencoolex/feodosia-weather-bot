import os
import requests
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

def send_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHANNEL_ID, "text": text}, timeout=30)
    r.raise_for_status()

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_message(f"Тест: бот работает. Время: {now}")

if __name__ == "__main__":
    main()
