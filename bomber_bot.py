from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import asyncio
import sqlite3
import time
import os
import requests

# ==================== НАСТРОЙКИ ====================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
TON_WALLET = os.getenv("TON_WALLET")

PROMOCODES = {
    "Malot": 5,
    "Lala": 1000
}

conn = sqlite3.connect("autosender.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    subscription_end INTEGER
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_name TEXT UNIQUE,
    phone TEXT
)''')
conn.commit()

app = Client("AutoSenderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

# ==================== TON АВТОПРОВЕРКА ====================
async def check_ton_payments():
    while True:
        try:
            url = f"https://tonapi.io/v2/accounts/{TON_WALLET}/transactions?limit=30"
            resp = requests.get(url, timeout=10).json()
            for tx in resp.get("transactions", []):
                in_msg = tx.get("in_msg", {})
                if in_msg.get("value", 0) >= 1_000_000_000:  # 1 TON
                    comment = in_msg.get("comment", "")
                    if comment.isdigit():
                        uid = int(comment)
                        new_end = int(time.time()) + (30 * 86400)
                        cursor.execute("INSERT OR REPLACE INTO users (user_id, subscription_end) VALUES (?, ?)", 
                                     (uid, new_end))
                        conn.commit()
                        try:
                            await app.send_message(uid, "✅ Оплата получена!\nПодписка на 30 дней активирована.")
                        except:
                            pass
        except:
            pass
        await asyncio.sleep(30)

# ==================== СТАРТ ====================
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user_id = message.from_user.id
    if not check_subscription(user_id) and user_id != ADMIN_ID:
        await message.reply("❌ Подписка не активна.\nОплати 1 TON или введи промокод Malot / Lala", reply_markup=main_menu())
        return
    await message.reply("👋 fe|AutoSender MALOT Edition", reply_markup=main_menu())

# ==================== ПОДПИСКА ====================
@app.on_callback_query(filters.regex("^subscription$"))
async def subscription_menu(client, query):
    text = f"""💰 Подписка

Цена: 1 TON = 30 дней
Кошелёк: `{TON_WALLET}`

После оплаты в комментарии укажи свой ID: {query.from_user.id}

Промокоды:
Malot — +5 дней
Lala — +1000 дней"""

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ввести промокод", callback_data="enter_promo")],
        [InlineKeyboardButton("Назад", callback_data="main")]
    ])
    await query.edit_message_text(text, reply_markup=kb)

@app.on_callback_query(filters.regex("^enter_promo$"))
async def enter_promo(client, query):
    await query.message.reply("Отправь промокод одним сообщением:")

# Обработка промокодов и текста
@app.on_message(filters.text & ~filters.command("start"))
async def text_handler(client, message: Message):
    code = message.text.strip()
    user_id = message.from_user.id

    if code in PROMOCODES:
        days = PROMOCODES[code]
        new_end = int(time.time()) + (days * 86400)
        cursor.execute("INSERT OR REPLACE INTO users (user_id, subscription_end) VALUES (?, ?)", (user_id, new_end))
        conn.commit()
        await message.reply(f"✅ Промокод {code} активирован!\n+{days} дней подписки.")
    else:
        await message.reply("❌ Неизвестная команда или промокод.")

# ==================== МЕНЮ ====================
@app.on_callback_query(filters.regex("^main$"))
async def back_main(client, query):
    await query.edit_message_text("👋 Главное меню", reply_markup=main_menu())

@app.on_callback_query()
async def other(client, query):
    await query.edit_message_text("🔧 Этот раздел скоро будет готов.\n\nПока работает подписка и промокоды.", 
                                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="main")]]))

# ==================== ЗАПУСК ====================
async def main():
    asyncio.create_task(check_ton_payments())
    print("MALOT AutoSender v2.1 запущен на Railway 🔥")
    await app.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
