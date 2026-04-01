from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
import asyncio
import sqlite3
import time
import os
import requests
from aiohttp import web   # Добавляем простой веб-сервер для Railway

# ==================== НАСТРОЙКИ ====================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
TON_WALLET = os.getenv("TON_WALLET")

PROMOCODES = {"Malot": 5, "Lala": 1000}

conn = sqlite3.connect("autosender.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, subscription_end INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY, user_id INTEGER, session_name TEXT, phone TEXT)''')
conn.commit()

app = Client("feAutoSender", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Простой веб-сервер чтобы Railway не убивал процесс
async def health_handler(request):
    return web.Response(text="MALOT AutoSender is running")

async def start_web_server():
    app_web = web.Application()
    app_web.router.add_get('/', health_handler)
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)   # Railway любит 8080
    await site.start()
    print("Web health check запущен на порту 8080")

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Мои рассылки", callback_data="my_mailings")],
        [InlineKeyboardButton("👤 Аккаунты", callback_data="accounts")],
        [InlineKeyboardButton("💰 Подписка", callback_data="subscription")],
        [InlineKeyboardButton("🤝 Рефералы", callback_data="referrals")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ])

def check_subscription(user_id):
    cursor.execute("SELECT subscription_end FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    return res and res[0] > int(time.time())

async def check_ton_payments():
    while True:
        try:
            url = f"https://tonapi.io/v2/accounts/{TON_WALLET}/transactions?limit=30"
            resp = requests.get(url, timeout=10).json()
            for tx in resp.get("transactions", []):
                if tx.get("in_msg", {}).get("value", 0) >= 1000000000:
                    comment = tx.get("in_msg", {}).get("comment", "")
                    if comment.isdigit():
                        uid = int(comment)
                        new_end = int(time.time()) + 30 * 86400
                        cursor.execute("INSERT OR REPLACE INTO users (user_id, subscription_end) VALUES (?, ?)", (uid, new_end))
                        conn.commit()
                        await app.send_message(uid, "✅ 1 TON получен! Подписка на 30 дней активирована.")
        except:
            pass
        await asyncio.sleep(30)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    if not check_subscription(message.from_user.id) and message.from_user.id != ADMIN_ID:
        await message.reply("❌ Подписка не активна.\nОплати 1 TON или введи промокод Malot / Lala", reply_markup=main_menu())
        return
    await message.reply("👋 fe|AutoSender MALOT Edition\n\nБот полностью живой!", reply_markup=main_menu())

@app.on_callback_query(filters.regex("subscription"))
async def subscription_menu(client, query: CallbackQuery):
    text = f"""💰 Подписка

Кошелёк: `{TON_WALLET}`
1 TON = 30 дней

В комментарии платежа укажи свой ID: {query.from_user.id}

Промокоды:
Malot — +5 дней
Lala — +1000 дней"""
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Ввести промокод", callback_data="enter_promo")], [InlineKeyboardButton("Назад", callback_data="main")]])
    await query.edit_message_text(text, reply_markup=kb)

@app.on_callback_query(filters.regex("enter_promo"))
async def enter_promo(client, query):
    await query.message.reply("Отправь промокод одним сообщением:")

@app.on_message(filters.text)
async def text_handler(client, message: Message):
    code = message.text.strip()
    if code in PROMOCODES:
        days = PROMOCODES[code]
        new_end = int(time.time()) + days * 86400
        cursor.execute("INSERT OR REPLACE INTO users (user_id, subscription_end) VALUES (?, ?)", (message.from_user.id, new_end))
        conn.commit()
        await message.reply(f"✅ Промокод {code} активирован! +{days} дней.")
    else:
        await message.reply("Используй кнопки меню.")

@app.on_callback_query()
async def all_buttons(client, query: CallbackQuery):
    if query.data == "main":
        await query.edit_message_text("👋 Главное меню", reply_markup=main_menu())
    else:
        await query.edit_message_text("🔧 Раздел в разработке (рассылка, аккаунты и т.д. скоро будут)", 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main")]]))

async def main():
    await start_web_server()          # ← Это решает проблему с Railway
    asyncio.create_task(check_ton_payments())
    print("MALOT Bomber Bot ЗАПУЩЕН УСПЕШНО! (с health check)")
    await app.start()
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
