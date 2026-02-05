import os
import time
import sys
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
import hashlib  # <-- ДОБАВИТЬ

import requests

# ====== Настройки ======
LAT = 45.053637
LON = 35.390155
TZ = "Europe/Moscow"
TARGET_HOUR = 6
RETRIES = 2
BACKOFF_BASE = 2  # секунды
# =======================

# --- ДОБАВИТЬ: фразы "гороскоп дня" (1 строка) ---
HOROSCOPE_LINES = [
    "✨ Гороскоп дня: не спешите — лучше сделать один шаг уверенно, чем три впопыхах.",
    "✨ Гороскоп дня: удачное время для коротких дел и наведения порядка.",
    "✨ Гороскоп дня: прислушайтесь к интуиции — она сегодня подскажет верный маршрут.",
    "✨ Гороскоп дня: хороший день для новых планов и спокойных решений.",
    "✨ Гороскоп дня: берегите энергию — выбирайте главное и не распыляйтесь.",
    "✨ Гороскоп дня: удача в мелочах — проверьте списки и документы.",
    "✨ Гороскоп дня: день подходит для встреч, переписок и договорённостей.",
    "✨ Гороскоп дня: не откладывайте важный разговор — сегодня он пройдёт мягче.",
    "✨ Гороскоп дня: время завершать начатое и радоваться маленьким победам.",
    "✨ Гороскоп дня: держите фокус на главном — остальное решится проще.",
]

def pick_horoscope_line(dt: datetime) -> str:
    """Выбираем фразу детерминированно по дате (каждый день — новая)."""
    if not HOROSCOPE_LINES:
        return ""
    key = dt.strftime("%Y-%m-%d").encode("utf-8")
    n = int(hashlib.sha256(key).hexdigest(), 16)
    return HOROSCOPE_LINES[n % len(HOROSCOPE_LINES)]
# --- /ДОБАВИТЬ ---

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN is not set in environment", file=sys.stderr)
    sys.exit(1)
if not CHANNEL_ID:
    print("ERROR: CHANNEL_ID is not set in environment", file=sys.stderr)
    sys.exit(1)

# ... ваш код без изменений до main() ...


def main():
    tz = ZoneInfo(TZ)
    now = datetime.now(tz)

    if now.hour != TARGET_HOUR:
        print(f"[main] Not {TARGET_HOUR:02d}:00 in {TZ} now ({now:%H:%M}). Skip.")
        return

    target_dt = datetime.combine(now.date(), dtime(hour=TARGET_HOUR), tzinfo=tz)

    hour_str = build_hour_string_for_api(target_dt)
    time_label = target_dt.strftime("%H:%M")
    print(f"[main] target hour: {hour_str} (label {time_label})")

    forecast = request_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": LAT,
            "longitude": LON,
            "hourly": "temperature_2m,apparent_temperature,precipitation,wind_speed_10m,winddirection_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": TZ,
        },
    )

    marine = request_json(
        "https://marine-api.open-meteo.com/v1/marine",
        {
            "latitude": LAT,
            "longitude": LON,
            "hourly": "sea_surface_temperature",
            "timezone": TZ,
        },
    )

    air = pick_hour_value(forecast, hour_str, "temperature_2m")
    feels = pick_hour_value(forecast, hour_str, "apparent_temperature")
    wind = pick_hour_value(forecast, hour_str, "wind_speed_10m")
    wind_dir = pick_hour_value(forecast, hour_str, "winddirection_10m")
    precip = pick_hour_value(forecast, hour_str, "precipitation")
    sea = pick_hour_value(marine, hour_str, "sea_surface_temperature")

    daily = forecast.get("daily", {}) or {}
    tmax = first_or_none(daily.get("temperature_2m_max"))
    tmin = first_or_none(daily.get("temperature_2m_min"))
    psum = first_or_none(daily.get("precipitation_sum"))

    wind_part = fmt_int(wind, " м/с")
    if wind_dir is not None:
        wind_part += f" (напр. {round(wind_dir)}°)"

    # --- ДОБАВИТЬ: строка гороскопа на сегодня ---
    horoscope_line = pick_horoscope_line(now)
    # --- /ДОБАВИТЬ ---

    text = (
        f"Доброе утро, Феодосия! {time_label}\n\n"
        f"Воздух: {fmt_int(air,'°')} (ощущается {fmt_int(feels,'°')})\n\n"
        f"Ветер: {wind_part} • Осадки: {fmt_1(precip,' мм')}\n\n"
        f"Температура моря: {fmt_int(sea,'°')}\n\n"
        f"Сегодня: {fmt_int(tmin,'°')}…{fmt_int(tmax,'°')} • Осадки: {fmt_1(psum,' мм')}\n\n"
        f"{horoscope_line}"
    )

    print("[main] message:\n" + text)
    send_message(text)

