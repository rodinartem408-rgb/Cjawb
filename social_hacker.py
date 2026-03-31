import os
from telebot import TeleBot, types

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = TeleBot(BOT_TOKEN)

print("[+] LAST SIMPLE TEST STARTED")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Тестовый фишинг запущен.\nНапиши любое сообщение.")

@bot.message_handler(func=lambda m: True)
def any_message(message):
    bot.send_message(ADMIN_ID, f"Сообщение от {message.from_user.id}: {message.text}")
    bot.send_message(message.chat.id, "Сообщение получено. Код бы пришёл сюда, если бы ты его ввёл.")

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Админ активен.")

print("[+] Бот запущен. Напиши /start")
bot.infinity_polling(none_stop=True)
