# bot.py
import os
import sys
import json
import time
import argparse
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

import requests

LAT = 45.053637
LON = 35.390155
TZ = "Europe/Moscow"

# Окна времени (в минутах): "примерно в 10" и "примерно в 22"
POST_HOUR = 10
DELETE_HOUR = 22
WINDOW_MINUTES = 20  # можно 10/15/30 — как вам нужно

RETRIES = 2
BACKOFF_BASE = 2
STATE_PATH = "state.json"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN is not set", file=sys.stderr)
    sys.exit(1)
if not CHANNEL_ID:
    print("ERROR: CHANNEL_ID is not set", file=sys.stderr)
    sys.exit(1)

HOROSCOPE_LINES = [
    "🔮 <b>Гороскоп дня:</b> Сегодня лучше завершать начатое — результат порадует.",
    "🌟 <b>Гороскоп дня:</b> День благоприятен для новых знакомств и общения.",
    "🧠 <b>Гороскоп дня:</b> Доверьтесь опыту: решение придёт вовремя.",
    "🏡 <b>Гороскоп дня:</b> Домашние дела сегодня помогут навести порядок в голове.",
    "💫 <b>Гороскоп дня:</b> Цените простые радости — день станет теплее.",
    "🧹 <b>Гороскоп дня:</b> Хороший момент разобрать мелочи и закрыть хвосты.",
    "🎯 <b>Гороскоп дня:</b> Маленькая цель сегодня — большой шаг завтра.",
    "🚶 <b>Гороскоп дня:</b> Прогулка и свежий воздух дадут ясность и энергию.",
    "💡 <b>Гороскоп дня:</b> Будьте открыты новым идеям — одна из них выстрелит.",
    "📝 <b>Гороскоп дня:</b> Аккуратность в делах сегодня принесёт бонусы.",
    "🤝 <b>Гороскоп дня:</b> Общение с близкими добавит сил и уверенности.",
    "🔥 <b>Гороскоп дня:</b> Время проявить инициативу — вас заметят.",
    "✨ <b>Гороскоп дня:</b> Попробуйте то, что давно откладывали — пора.",
    "😊 <b>Гороскоп дня:</b> Ваш настрой задаст тон всему дню — выбирайте позитив.",
    "🐢 <b>Гороскоп дня:</b> Не спешите: спокойный темп сегодня эффективнее.",
    "⚖️ <b>Гороскоп дня:</b> Баланс между делами и отдыхом — ваш главный плюс.",
    "🔍 <b>Гороскоп дня:</b> Внимание к деталям убережёт от лишних ошибок.",
    "🎨 <b>Гороскоп дня:</b> Хороший день для творчества и красивых идей.",
    "🎤 <b>Гороскоп дня:</b> Скажите важное мягко и прямо — вас поймут.",
    "📚 <b>Гороскоп дня:</b> День подходит для обучения и планирования.",
    "🙏 <b>Гороскоп дня:</b> Похвалите себя за пройденный путь — это важно.",
    "🛍️ <b>Гороскоп дня:</b> Покупки лучше делать по списку — так спокойнее.",
    "😌 <b>Гороскоп дня:</b> Эмоции под контролем — и день пройдёт ровно.",
    "📩 <b>Гороскоп дня:</b> Новая информация окажется полезнее, чем кажется.",
    "😃 <b>Гороскоп дня:</b> Поделитесь хорошим — оно вернётся к вам.",
    "🦁 <b>Гороскоп дня:</b> Смелость сегодня будет вознаграждена.",
    "🛌 <b>Гороскоп дня:</b> Не перегружайте себя: отдых — тоже задача.",
    "🗣️ <b>Гороскоп дня:</b> Ваш совет может помочь кому-то очень сильно.",
    "📢 <b>Гороскоп дня:</b> Важная новость рядом — будьте внимательны.",
    "🧩 <b>Гороскоп дня:</b> Сложное упростится, если начать с первого шага.",
    "📆 <b>Гороскоп дня:</b> Самое время заняться тем, что долго откладывали.",
    "🧘 <b>Гороскоп дня:</b> Интуиция подскажет верно — прислушайтесь.",
    "✍️ <b>Гороскоп дня:</b> Записывайте идеи — сегодня их будет много.",
    "🌍 <b>Гороскоп дня:</b> Расширяйте круг общения — это даст возможности.",
    "🌄 <b>Гороскоп дня:</b> Важное решение лучше принимать без спешки.",
    "🕊️ <b>Гороскоп дня:</b> Доброта сегодня работает как магнит.",
    "🎁 <b>Гороскоп дня:</b> Приятные сюрпризы возможны в самых простых вещах.",
    "⚡ <b>Гороскоп дня:</b> Решительность поможет быстро закрыть вопросы.",
    "🛀 <b>Гороскоп дня:</b> Снимите напряжение: телу тоже нужен отдых.",
    "🔄 <b>Гороскоп дня:</b> Пересмотрите цели — пора обновить маршрут.",
    "😁 <b>Гороскоп дня:</b> Улыбка и лёгкость сегодня открывают двери.",
    "📌 <b>Гороскоп дня:</b> Подведите итоги — это даст ясность на завтра.",
    "🍬 <b>Гороскоп дня:</b> Порадуйте себя маленькой приятностью — заслужили.",
    "🌠 <b>Гороскоп дня:</b> Новые впечатления сделают день запоминающимся.",
    "💪 <b>Гороскоп дня:</b> Доверяйте себе — вы всё делаете правильно.",
    "🌿 <b>Гороскоп дня:</b> Спокойный разговор сегодня решит больше, чем спор.",
    "🧭 <b>Гороскоп дня:</b> Держите курс на главное — остальное подождёт.",
    "☕ <b>Гороскоп дня:</b> Начните утро без суеты — и день сложится легче.",
    "🎈 <b>Гороскоп дня:</b> Добавьте радости в рутину — это даст энергию.",
]


def load_state():
    if not os.path.exists(STATE_PATH):
        return {}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


def request_json(url: str, params: dict, retries: int = RETRIES):
    last_exc = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            last_exc = e
            if attempt < retries:
                time.sleep(BACKOFF_BASE * (attempt + 1))
    raise last_exc


def pick_hour_value(data: dict, hour_str: str, field: str):
    hourly = (data or {}).get("hourly") or {}
    times = hourly.get("time") or []
    values = hourly.get(field) or []
    try:
        idx = times.index(hour_str)
    except ValueError:
        return None
    return values[idx] if idx < len(values) else None


def fmt_int(x, suffix=""):
    return "—" if x is None else f"{round(x)}{suffix}"


def fmt_1(x, suffix=""):
    return "—" if x is None else f"{x:.1f}{suffix}"


def build_hour_string_for_api(dt: datetime):
    return dt.strftime("%Y-%m-%dT%H:%M")


def first_or_none(x):
    if x is None:
        return None
    if isinstance(x, (list, tuple)) and x:
        return x[0]
    return x


def is_within_window(now: datetime, target_hour: int, window_minutes: int) -> bool:
    # окно: target_hour:00 ... target_hour:(window_minutes-1)
    return now.hour == target_hour and 0 <= now.minute < window_minutes


def get_weather_text(now: datetime):
    tz = ZoneInfo(TZ)

    # Пишем реальное время отправки (примерно 10:xx)
    time_label = now.strftime("%H:%M")

    # Для hourly берём ближайший час вниз (10:00, 10:xx -> 10:00)
    api_dt = datetime.combine(now.date(), dtime(hour=now.hour, minute=0), tzinfo=tz)
    hour_str = build_hour_string_for_api(api_dt)

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

    return (
        f"🌞 print(f"[delete] Not in window {DELETE_HOUR:02d}:00-{DELETE_HOUR:02d}:{WINDOW_MINUTES-1:02d} {TZ} now ({now:%H:%M}). Skip.")
            return

        # защита от повторного удаления в тот же день
        if state.get("last_delete_date") == now.date().isoformat():
            print("[delete] Already deleted today. Skip.")
            return

        mid = state.get("last_message_id")
        if not mid:
            print("[delete] No last_message_id in state.json. Nothing to delete.")
            state["last_delete_date"] = now.date().isoformat()
            save_state(state)
            return

        tg_delete_message(int(mid))
        print("[delete] OK")
        state.pop("last_message_id", None)
        state["last_delete_date"] = now.date().isoformat()
        save_state(state)
        return

    # post
    if not is_within_window(now, POST_HOUR, WINDOW_MINUTES):
        print(f"[post] Not in window {POST_HOUR:02d}:00-{POST_HOUR:02d}:{WINDOW_MINUTES-1:02d} {TZ} now ({now:%H:%M}). Skip.")
        return

    # защита от двойной отправки в один день
    if state.get("last_post_date") == now.date().isoformat():
        print("[post] Already posted today. Skip.")
        return

    weather = get_weather_text(now)
    horoscope = get_horoscope_and_advance(state)
    post = f"{weather}\n\n{horoscope}"

    message_id = tg_send_message_html(post)
    print(f"[post] OK message_id={message_id}")

    state["last_message_id"] = message_id
    state["last_post_date"] = now.date().isoformat()
    save_state(state)


if __name__ == "__main__":
    main()


