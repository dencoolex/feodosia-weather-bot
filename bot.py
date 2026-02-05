# bot.py
# Публикует утренний пост в Telegram с прогнозом для Феодосии.
# Поведение:
# - По умолчанию использует текущее время запуска (удобно для ручного теста).
# - Если запускать по cron ровно в 06:00 (timezone Europe/Moscow), пост будет с меткой 06:00.
#
# Перед запуском в среде (GitHub Actions или локально) задайте переменные окружения:
# - BOT_TOKEN (telegram bot token)
# - CHANNEL_ID (например @feo_sea или numeric chat id -1001234567890)
#
# requirements.txt:
# requests==2.32.3
#
# Запуск:
# python bot.py

import os
import time
import sys
from datetime import datetime, date, time as dtime
from zoneinfo import ZoneInfo

import requests

# ====== Настройки (можно менять) ======
LAT = 45.053637
LON = 35.390155
TZ = "Europe/Moscow"

# Если True — используем текущее время запуска (удобно для теста). Если False — фиксируем TARGET_HOUR.
USE_CURRENT_HOUR = True

# Час (0-23), для которого берём прогноз, если USE_CURRENT_HOUR=False
TARGET_HOUR = 6

# Retry/backoff
RETRIES = 2
BACKOFF_BASE = 2  # секунды, умножается на попытку (exponential-ish)

# ======================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN is not set in environment", file=sys.stderr)
    sys.exit(1)
if not CHANNEL_ID:
    print("ERROR: CHANNEL_ID is not set in environment", file=sys.stderr)
    sys.exit(1)


def request_json(url: str, params: dict, retries: int = RETRIES):
    last_exc = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            last_exc = e
            print(f"[request_json] attempt {attempt} error: {e}", file=sys.stderr)
            if attempt < retries:
                wait = BACKOFF_BASE * (attempt + 1)
                print(f"[request_json] sleeping {wait}s before retry...", file=sys.stderr)
                time.sleep(wait)
    raise last_exc


def pick_hour_value(data: dict, hour_str: str, field: str):
    """Вернуть значение hourly[field] для hour_str (формат 'YYYY-MM-DDTHH:MM'), иначе None."""
    if not isinstance(data, dict):
        return None
    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    values = hourly.get(field) or []
    try:
        idx = times.index(hour_str)
    except ValueError:
        return None
    if idx < len(values):
        return values[idx]
    return None


def send_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "disable_web_page_preview": True}
    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        print("[send_message] OK")
    except requests.RequestException as e:
        print(f"[send_message] error: {e}", file=sys.stderr)
        raise


def fmt_int(x, suffix=""):
    return "—" if x is None else f"{round(x)}{suffix}"


def fmt_1(x, suffix=""):
    return "—" if x is None else f"{x:.1f}{suffix}"


def build_hour_string_for_api(dt: datetime):
    # open-meteo при timezone возвращает часы в виде "YYYY-MM-DDTHH:MM" (без смещения)
    return dt.strftime("%Y-%m-%dT%H:%M")


def first_or_none(x):
    if x is None:
        return None
    if isinstance(x, (list, tuple)) and x:
        return x[0]
    return x


def main():
    tz = ZoneInfo(TZ)
    now = datetime.now(tz)

    if USE_CURRENT_HOUR:
        target_dt = now.replace(minute=0, second=0, microsecond=0)
    else:
        today_in_tz = now.date()
        target_dt = datetime.combine(today_in_tz, dtime(hour=TARGET_HOUR), tzinfo=tz)

    hour_str = build_hour_string_for_api(target_dt)
    time_label = target_dt.strftime("%H:%M")

    print(f"[main] target hour: {hour_str} (label {time_label})")

    # Получаем прогнозы
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

    # Извлечение значений
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

    # Build wind part
    wind_part = fmt_int(wind, " м/с")
    if wind_dir is not None:
        wind_part += f" (напр. {round(wind_dir)}°)"

    text = (
        f"Доброе утро, Феодосия! {time_label}\n\n"
        f"Воздух: {fmt_int(air,'°')} (ощущается {fmt_int(feels,'°')})\n\n"
        f"Ветер: {wind_part} • Осадки: {fmt_1(precip,' мм')}\n\n"
        f"Температура моря: {fmt_int(sea,'°')}\n\n"
        f"Сегодня: {fmt_int(tmin,'°')}…{fmt_int(tmax,'°')} • Осадки: {fmt_1(psum,' мм')}"
    )

    # Печатаем текст в лог (удобно для Actions) и отправляем
    print("[main] message:\n" + text)
    send_message(text)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[fatal] {e}", file=sys.stderr)
        sys.exit(2)

