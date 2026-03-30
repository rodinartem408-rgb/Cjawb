import telebot
import together
import os
import threading
import logging  # ← Для логов
from flask import Flask

# Логи в Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

together.api_key = os.getenv("TOGETHER_API")
TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

MODEL = "meta-llama/Llama-3.1-8B-Instruct"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔥 HackerAI Bot готов!\nПиши: shells, exploits, pentest")

@bot.message_handler(commands=['models'])
def models(message):
    bot.reply_to(message, f"Model: {MODEL}")

@bot.message_handler(commands=['test'])
def test(message):
    bot.reply_to(message, "Bot работает! API ключ есть: " + ("✅" if together.api_key else "❌"))

@bot.message_handler(func=lambda m: True)
def handle(message):
    logger.info(f"Получено сообщение: {message.text}")  # Лог в Railway
    
    try:
        logger.info("Отправка запроса к Together AI...")
        resp = together.Complete.create(
            model=MODEL,
            prompt=f"HackerAI: Pentest. Technical.\nUser: {message.text}\nAI:",
            max_tokens=1500,  # Уменьшил
            temperature=0.1
        )
        response = resp['output']['choices'][0]['text'].strip()
        logger.info("Ответ получен, отправка...")
        bot.reply_to(message, response)
    except Exception as e:
        error_msg = f"❌ ОШИБКА: {str(e)}"
        logger.error(error_msg)
        bot.reply_to(message, error_msg)

@app.route('/')
def home():
    return {"status": "OK", "model": MODEL}

if __name__ == '__main__':
    logger.info(f"Запуск бота с моделью: {MODEL}")
    logger.info(f"API ключ: {'✅' if together.api_key else '❌'}")
    threading.Thread(target=bot.polling, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 8080)))
