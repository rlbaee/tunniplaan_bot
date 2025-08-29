# Imports
import logging
import requests
import os
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from datetime import date, datetime, timedelta

# url = 'https://tahveltp.edu.ee/#/schoolBoard/8/group/a01d68d7-7bff-497b-b1ee-4f04e258d9fb'

API_KEY = os.environ.get("API_KEY")
url = "https://tahveltp.edu.ee/hois_back/schoolBoard/8/timetableByGroup"
params = {
    "lang": "ET",
    "studentGroupUuid": "a01d68d7-7bff-497b-b1ee-4f04e258d9fb"
}


def get_schedule(date_str, url):
    response = requests.get(url, params=params)
    data = response.json()
    if date_str == date.today():
        date_str = 'Сегодня'
    elif date_str == (date.today() + timedelta(days=1)):
        date_str = 'Завтра'

    text = f"Расписание на *{date_str}*:\n\n"

    events = [e for e in data.get("timetableEvents", []) if e.get("date", "")[:10] == date_str]

    # Sort by start time
    events.sort(key=lambda x: x.get("timeStart", ""))

    for event in events:
        subject = event.get("nameEt") or event.get("nameEn") or "—"
        start = event.get("timeStart") or "—"
        end = event.get("timeEnd") or "—"
        group = event.get("studentGroups", [])

        # Handle teachers
        teachers = event.get("teachers", [])
        if teachers:
            teacher = ", ".join([f"{t.get('firstname', '')} {t.get('lastname', '')}" for t in teachers])
        else:
            teacher = "—"

        # Handle rooms
        rooms = event.get("rooms", [])
        if rooms:
            room = ", ".join([f"{r.get('roomCode', '')} ({r.get('buildingCode', '')})" for r in rooms])
        else:
            room = "—"

        text += f"*{start}-{end}: {subject}*\nУчитель: {teacher}\nКласс: {room}\n\n"

    if not events:
        text += "Расписание не найдено."

    return text


        
    

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Используй командную палитру для получения расписания")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{get_schedule(date.today(), url)}", parse_mode="Markdown")

async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tomorrow_date = (date.today() + timedelta(days=1)).isoformat()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{get_schedule(tomorrow_date, url)}", parse_mode="Markdown")

async def custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        custom_date = context.args[0]
        try:
            datetime.strptime(custom_date, '%Y-%m-%d')
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"\n{get_schedule(custom_date, url)}", parse_mode="Markdown")
        except ValueError:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Неправильный формат. Нужен ГГГГ-ММ-ДД.", parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Неправильный формат. Нужен ГГГГ-ММ-ДД.", parse_mode="Markdown")

async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_date = date.today()

    start_of_week = today_date - timedelta(days=today_date.weekday())
    
    for i in range(5):
        day = start_of_week + timedelta(days=i)
        schedule_text = get_schedule(day.isoformat(), url)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=schedule_text, parse_mode="Markdown")

    

if __name__ == '__main__':
    application = ApplicationBuilder().token(API_KEY).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    today_handler = CommandHandler('today', today)
    application.add_handler(today_handler)

    tomorrow_handler = CommandHandler('tomorrow', tomorrow)
    application.add_handler(tomorrow_handler)

    custom_handler = CommandHandler('custom', custom)
    application.add_handler(custom_handler)

    week_handler = CommandHandler('week', week)
    application.add_handler(week_handler)

    
    application.run_polling()    

get_schedule(date, url)