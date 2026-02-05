# bot.py
import os
import time
from datetime import datetime, date, time as dtime
from zoneinfo import ZoneInfo

import requests

# Coordinates (Feodosia)
LAT = 45.053637
LON = 35.390155

# Настройки
TARGET_HOUR = 6  # час, для которого берём прогноз (0-23). Оставь 6 для 06:00 по TZ.
USE_CURRENT_HOUR = False  # True — подставлять текущее время запуска (удобно для тестов)
TZ = "Europe/Moscow"
RETRIES = 2
BACKOFF = 2  # секунды, умножается на попытку

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]  # например: @feo_sea или -1001234567890


def request_json(url: str, params: dict, retries: int = RETRIES):
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[request_json] error (attempt {attempt}): {e}")
            if attempt < retries:
                time.sleep(BACKOFF * (attempt + 1))
            else:
                raise


def pick_hour_value(data: dict, hour_str: str, field: str):
    """Безопасно вернуть значение hourly[field] для указанного time (hour_str).
    Если поле отсутствует или время не найдено — вернуть None."""
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
        print("[send_message] ok")
    except requests.RequestException as e:
        print(f"[send_message] error: {e}")
        raise


def fmt_int(x, suffix=""):
    return "—" if x is None else f"{round(x)}{suffix}"


def fmt_1(x, suffix=""):
    return "—" if x is None else f"{x:.1f}{suffix}"


def build_hour_string_for_api(target_dt: datetime):
    # API ожидает формат "YYYY-MM-DDTHH:MM" (minutes precision)
    return target_dt.replace(second=0, microsecond=0).isoformat(timespec="minutes")


def main():
    # Вычисляем нужный час в таймзоне
    tz = ZoneInfo(TZ)
    now = datetime.now(tz)

    if USE_CURRENT_HOUR:
        target_dt = now.replace(minute=0, second=0, microsecond=0)
    else:
        # Используем сегодняшнюю дату и TARGET_HOUR в TZ
        today = date.today()
        target_dt = datetime.combine(today, dtime(hour=TARGET_HOUR), tzinfo=tz)

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

    # Извлекаем значения безопасно
    air = pick_hour_value(forecast, hour_str, "temperature_2m")
    feels = pick_hour_value(forecast, hour_str, "apparent_temperature")
    wind = pick_hour_value(forecast, hour_str, "wind_speed_10m")
    wind_dir = pick_hour_value(forecast, hour_str, "winddirection_10m")
    precip = pick_hour_value(forecast, hour_str, "precipitation")
    sea = pick_hour_value(marine, hour_str, "sea_surface_temperature")

    # Дневные агрегаты (могут быть строками/списками)
    daily = forecast.get("daily", {}) or {}
    tmax = daily.get("temperature_2m_max")
    tmin = daily.get("temperature_2m_min")
    psum = daily.get("precipitation_sum")

    # Если daily поля - списки, берём первый элемент
    def first_or_none(x):
        if x is None:
            return None
        if isinstance(x, (list, tuple)) and x:
            return x[0]
        return x

    tmax = first_or_none(tmax)
    tmin = first_or_none(tmin)
    psum = first_or_none(psum)

    # Построение текста
    wind_part = fmt_int(wind, " м/с")
    if wind_dir is not None:
        wind_part += f" (направление {round(wind_dir)}°)"

    text = (
        f"Доброе утро, Феодосия! {time_label}\n\n"
        f"Воздух: {fmt_int(air,'°')} (ощущается {fmt_int(feels,'°')})\n\n"
        f"Ветер: {wind_part} • Осадки: {fmt_1(precip,' мм')}\n\n"
        f"Температура моря: {fmt_int(sea,'°')}\n\n"
        f"Сегодня: {fmt_int(tmin,'°')}…{fmt_int(tmax,'°')} • Осадки: {fmt_1(psum,' мм')}"
    )

    print("[main] message:\n" + text)
    send_message(text)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[fatal] {e}")
        raise
