# Imports
import logging
import requests
import os
from datetime import date, datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from fastapi import FastAPI
import asyncio
import uvicorn

API_KEY = os.environ.get("API_KEY")
url = "https://tahveltp.edu.ee/hois_back/schoolBoard/8/timetableByGroup"
params = {
    "lang": "ET",
    "studentGroupUuid": "a01d68d7-7bff-497b-b1ee-4f04e258d9fb"
}

# --- Schedule fetcher ---
def get_schedule(date_obj: date, url):
    response = requests.get(url, params=params)
    data = response.json()

    # Format label for message
    if date_obj == date.today():
        date_label = 'Сегодня'
    elif date_obj == (date.today() + timedelta(days=1)):
        date_label = 'Завтра'
    else:
        date_label = date_obj.isoformat()

    text = f"Расписание на *{date_label}*:\n\n"

    # Filter events for this date
    events = [
        e for e in data.get("timetableEvents", [])
        if e.get("date", "")[:10] == date_obj.isoformat()
    ]
    events.sort(key=lambda x: x.get("timeStart", ""))

    for event in events:
        subject = event.get("nameEt") or event.get("nameEn") or "—"
        start = event.get("timeStart") or "—"
        end = event.get("timeEnd") or "—"

        groups = event.get("studentGroups", [])
        group = ", ".join([g.get("code", "") for g in groups]) if groups else "—"

        teachers = event.get("teachers", [])
        teacher = ", ".join([f"{t.get('firstname', '')} {t.get('lastname', '')}" for t in teachers]) if teachers else "—"

        rooms = event.get("rooms", [])
        room = ", ".join([f"{r.get('roomCode', '')}, {r.get('buildingCode', '')}" for r in rooms]) if rooms else "—"

        text += f"*{start}-{end}: {subject}*\nУчитель: {teacher}\nКласс: {room}\nГруппы: {group}\n\n"

    if not events:
        text += "Расписание не найдено."

    return text

# --- Telegram bot handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Используй командную палитру для получения расписания")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=get_schedule(date.today(), url),
                                   parse_mode="Markdown")

async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=get_schedule(date.today() + timedelta(days=1), url),
                                   parse_mode="Markdown")

async def custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        custom_date_str = context.args[0]
        try:
            custom_date = datetime.strptime(custom_date_str, '%Y-%m-%d').date()
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=get_schedule(custom_date, url),
                                           parse_mode="Markdown")
        except ValueError:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Неправильный формат. Нужен ГГГГ-ММ-ДД.",
                                           parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Неправильный формат. Нужен ГГГГ-ММ-ДД.",
                                       parse_mode="Markdown")

async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_date = date.today()
    start_of_week = today_date - timedelta(days=today_date.weekday())

    for i in range(5):  # Mon–Fri
        day = start_of_week + timedelta(days=i)
        schedule_text = get_schedule(day, url)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=schedule_text,
                                       parse_mode="Markdown")

# --- FastAPI setup for Render ---
app = FastAPI()

# Build bot once globally
application = ApplicationBuilder().token(API_KEY).build()
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('today', today))
application.add_handler(CommandHandler('tomorrow', tomorrow))
application.add_handler(CommandHandler('custom', custom))
application.add_handler(CommandHandler('week', week))

@app.on_event("startup")
async def startup_event():
    await application.initialize()
    await application.start()
    asyncio.create_task(application.updater.start_polling())

@app.on_event("shutdown")
async def shutdown_event():
    await application.updater.stop()
    await application.stop()
    await application.shutdown()

@app.get("/ping")
def ping():
    return {"status": "alive"}

# --- Run Uvicorn for Render ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
