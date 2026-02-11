# bot.py
import os
import sys
import json
import time
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

import requests

LAT = 45.053637
LON = 35.390155
TZ = "Europe/Moscow"

# Окно отправки: 05:00–08:00 (MSK) (08:00 включительно)
WINDOW_START = dtime(5, 0)
WINDOW_END = dtime(8, 0)

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
    "🎯 <b>Гороскоп дня:</b> Сфокусируйтесь на одном главном деле — так быстрее придёте к результату.",
    "🚶 <b>Гороскоп дня:</b> Небольшая прогулка поможет разложить мысли по полочкам.",
    "💡 <b>Гороскоп дня:</b> Свежая идея придёт внезапно — запишите её сразу.",
    "🧩 <b>Гороскоп дня:</b> Начните с малого — и сложная задача станет простой.",
    "🤝 <b>Гороскоп дня:</b> Разговор по душам сегодня может укрепить важные отношения.",
    "🔥 <b>Гороскоп дня:</b> Инициатива будет замечена — действуйте смелее.",
    "🧘 <b>Гороскоп дня:</b> Спокойный темп сегодня эффективнее гонки и суеты.",
    "📌 <b>Гороскоп дня:</b> Порядок в мелочах освободит место для больших планов.",
    "📚 <b>Гороскоп дня:</b> Хороший день, чтобы учиться и задавать вопросы.",
    "📝 <b>Гороскоп дня:</b> Составьте короткий список дел — и станет легче.",
    "💬 <b>Гороскоп дня:</b> Говорите прямо, но мягко — вас услышат.",
    "🎨 <b>Гороскоп дня:</b> Творческий подход поможет обойти ограничения.",
    "⚖️ <b>Гороскоп дня:</b> Ищите баланс: перегибы сегодня ни к чему.",
    "🌿 <b>Гороскоп дня:</b> Сбавьте обороты и сделайте паузу — это пойдёт на пользу.",
    "☕ <b>Гороскоп дня:</b> Начните день без спешки — и всё сложится ровнее.",
    "📩 <b>Гороскоп дня:</b> Важное сообщение может прийти неожиданно — будьте внимательны.",
    "🧹 <b>Гороскоп дня:</b> Освободите пространство: уборка принесёт ясность.",
    "🔍 <b>Гороскоп дня:</b> Внимание к деталям убережёт от лишних ошибок.",
    "🚀 <b>Гороскоп дня:</b> Самое время сделать шаг вперёд — не откладывайте.",
    "🛌 <b>Гороскоп дня:</b> Отдых сегодня — часть успеха, а не слабость.",
    "🧭 <b>Гороскоп дня:</b> Держите курс на главное — остальное подождёт.",
    "🎁 <b>Гороскоп дня:</b> Маленький подарок себе поднимет настроение и мотивацию.",
    "📆 <b>Гороскоп дня:</b> Перепроверьте планы — и день станет предсказуемее.",
    "🌄 <b>Гороскоп дня:</b> Утреннее решение задаст тон всему дню — выбирайте мудро.",
    "😌 <b>Гороскоп дня:</b> Не принимайте всё близко к сердцу — лишние эмоции помешают.",
    "😃 <b>Гороскоп дня:</b> Поделитесь хорошими новостями — это вернётся теплом.",
    "🦁 <b>Гороскоп дня:</b> Смелость сегодня особенно к месту — проявите характер.",
    "🗣️ <b>Гороскоп дня:</b> Ваш совет может оказаться решающим для кого-то.",
    "📢 <b>Гороскоп дня:</b> Не бойтесь заявить о себе — момент подходящий.",
    "🛍️ <b>Гороскоп дня:</b> Покупки делайте по списку — так спокойнее и выгоднее.",
    "✍️ <b>Гороскоп дня:</b> Записывайте мысли — среди них будет ценная.",
    "🌍 <b>Гороскоп дня:</b> Новые знакомства откроют неожиданные возможности.",
    "🕊️ <b>Гороскоп дня:</b> Доброта сегодня работает сильнее любых аргументов.",
    "⚡ <b>Гороскоп дня:</b> Решительность поможет быстро закрыть старый вопрос.",
    "🔄 <b>Гороскоп дня:</b> Пересмотрите приоритеты — что-то пора отпустить.",
    "😁 <b>Гороскоп дня:</b> Лёгкость и юмор помогут договориться даже в споре.",
    "📈 <b>Гороскоп дня:</b> Маленький прогресс сегодня важнее идеального результата.",
    "🍬 <b>Гороскоп дня:</b> Побалуйте себя — это добавит сил и вдохновения.",
    "🌠 <b>Гороскоп дня:</b> День подходит для мечты и первого шага к ней.",
    "💪 <b>Гороскоп дня:</b> Вы сильнее, чем кажется — просто начните действовать.",
    "🤍 <b>Гороскоп дня:</b> Поддержка близких сегодня особенно ценна — не отталкивайте её.",
    "🧠 <b>Гороскоп дня:</b> Задайте себе один честный вопрос — ответ многое прояснит.",
    "⏳ <b>Гороскоп дня:</b> Терпение сегодня принесёт больше, чем давление и спешка.",
    "🏁 <b>Гороскоп дня:</b> Завершите начатое — и почувствуете облегчение и гордость.",
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


def in_window(now: datetime) -> bool:
    t = now.time()
    return WINDOW_START <= t <= WINDOW_END


def request_json(url: str, params: dict, retries: int = 2):
    last_exc = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            last_exc = e
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
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


def first_or_none(x):
    if x is None:
        return None
    if isinstance(x, (list, tuple)) and x:
        return x[0]
    return x


def fmt_int(x, suffix=""):
    return "—" if x is None else f"{round(x)}{suffix}"


def fmt_1(x, suffix=""):
    return "—" if x is None else f"{x:.1f}{suffix}"


def get_horoscope_and_advance(state: dict) -> str:
    idx = int(state.get("horoscope_index", 0) or 0)
    line = HOROSCOPE_LINES[idx % len(HOROSCOPE_LINES)]
    state["horoscope_index"] = (idx + 1) % len(HOROSCOPE_LINES)
    return line


def get_weather_text(now: datetime) -> str:
    hour_str = now.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")

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

    time_label = now.strftime("%H:%M")

    return (
        f"🌞 <b>Феодосия</b> {time_label}\n\n"
        f"🌡️ <b>Воздух:</b> {fmt_int(air,'°')} (ощущается {fmt_int(feels,'°')})\n\n"
        f"💨 <b>Ветер:</b> {wind_part} • <b>Осадки:</b> {fmt_1(precip,' мм')}\n\n"
        f"🌊 <b>Море:</b> {fmt_int(sea,'°')}\n\n"
        f"📈 <b>Сегодня:</b> {fmt_int(tmin,'°')}…{fmt_int(tmax,'°')} • <b>Осадки:</b> {fmt_1(psum,' мм')}"
    )


def tg_send_message_html(text: str) -> int:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["result"]["message_id"]


def main():
    tz = ZoneInfo(TZ)
    now = datetime.now(tz)
    print(f"[debug] Moscow now: {now:%Y-%m-%d %H:%M}")

    state = load_state()
    today = now.date().isoformat()

    if not in_window(now):
        print(
            f"[skip] Not in window {WINDOW_START.strftime('%H:%M')}-"
            f"{WINDOW_END.strftime('%H:%M')}"
        )
        return

    if state.get("last_post_date") == today:
        print("[skip] Already posted today")
        return

    weather = get_weather_text(now)
    horoscope = get_horoscope_and_advance(state)
    text = f"{weather}\n\n{horoscope}"

    mid = tg_send_message_html(text)
    print(f"[ok] sent message_id={mid}")

    state["last_post_date"] = today
    save_state(state)


if __name__ == "__main__":
    main()
