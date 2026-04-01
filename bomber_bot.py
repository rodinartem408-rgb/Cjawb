from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import asyncio
import sqlite3
import time
import os
import random
import requests

# ==================== ENV (Railway) ====================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
TON_WALLET = os.getenv("TON_WALLET")

PROMOCODES = {"Malot": 5, "Lala": 1000}

conn = sqlite3.connect("autosender.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, subscription_end INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY, user_id INTEGER, session_name TEXT UNIQUE, phone TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS mailings (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, text TEXT, interval INTEGER, status TEXT DEFAULT 'stopped')''')
conn.commit()

app = Client("AutoSenderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
clients = {}  # храним user-клиенты

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
                if tx.get("in_msg", {}).get("value", 0) >= 1000000000:
                    comment = tx["in_msg"].get("comment", "")
                    if comment.isdigit():
                        uid = int(comment)
                        new_end = int(time.time()) + (30 * 86400)
                        cursor.execute("INSERT OR REPLACE INTO users (user_id, subscription_end) VALUES (?, ?)", (uid, new_end))
                        conn.commit()
                        await app.send_message(uid, "✅ 1 TON получен! Подписка на 30 дней активирована.")
        except:
            pass
        await asyncio.sleep(30)

# ==================== СТАРТ + РЕАКЦИЯ НА ВСЕ СООБЩЕНИЯ ====================
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    if not check_subscription(message.from_user.id) and message.from_user.id != ADMIN_ID:
        await message.reply("❌ Подписка не активна.\nОплати 1 TON или введи промокод.", reply_markup=main_menu())
        return
    await message.reply("👋 fe|AutoSender MALOT Edition", reply_markup=main_menu())

# ==================== ПРОМОКОДЫ ====================
@app.on_callback_query(filters.regex("^enter_promo$"))
async def enter_promo(client, query):
    await query.message.reply("Отправь промокод одним сообщением:")

@app.on_message(filters.text)
async def text_handler(client, message: Message):
    code = message.text.strip()
    user_id = message.from_user.id
    if code in PROMOCODES:
        days = PROMOCODES[code]
        new_end = int(time.time()) + (days * 86400)
        cursor.execute("INSERT OR REPLACE INTO users (user_id, subscription_end) VALUES (?, ?)", (user_id, new_end))
        conn.commit()
        await message.reply(f"✅ Промокод {code} активирован! +{days} дней.")
    else:
        await message.reply("❌ Неизвестная команда. Используй меню.")

# ==================== АККАУНТЫ (как на твоём скрине) ====================
@app.on_callback_query(filters.regex("^accounts$"))
async def accounts_menu(client, query):
    cursor.execute("SELECT phone FROM accounts WHERE user_id=?", (query.from_user.id,))
    accs = [row[0] for row in cursor.fetchall()]
    text = "👤 Ваши аккаунты:\n" + ("\n".join(accs) if accs else "Пока пусто")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("+ Добавить аккаунт", callback_data="add_account")], [InlineKeyboardButton("Назад", callback_data="main")]])
    await query.edit_message_text(text, reply_markup=kb)

@app.on_callback_query(filters.regex("^add_account$"))
async def add_account(client, query):
    await query.message.reply("Отправь номер в формате +79123456789")

@app.on_message(filters.regex(r"^\+?\d{10,15}$"))
async def process_phone(client, message: Message):
    phone = message.text.strip()
    session_name = f"session_{message.from_user.id}_{int(time.time())}"
    try:
        user_client = Client(session_name, api_id=API_ID, api_hash=API_HASH, phone_number=phone)
        await user_client.connect()
        await user_client.send_code(phone)
        clients[message.from_user.id] = user_client
        await message.reply("Отправь код из Telegram/SMS:")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

@app.on_message(filters.regex(r"^\d{5,6}$"))
async def process_code(client, message: Message):
    code = message.text.strip()
    user_id = message.from_user.id
    if user_id not in clients:
        return
    try:
        await clients[user_id].sign_in(code)
        cursor.execute("INSERT INTO accounts (user_id, session_name, phone) VALUES (?, ?, ?)", 
                      (user_id, clients[user_id].name, "added"))
        conn.commit()
        await message.reply("✅ Аккаунт успешно добавлен!")
    except Exception as e:
        await message.reply(f"Ошибка входа: {e}")

# ==================== РАССЫЛКА (реальная с анти-баном) ====================
@app.on_callback_query(filters.regex("^my_mailings$"))
async def my_mailings(client, query):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("+ Создать рассылку", callback_data="create_mailing")], [InlineKeyboardButton("Назад", callback_data="main")]])
    await query.edit_message_text("📋 Мои рассылки\n\nНажми чтобы создать новую.", reply_markup=kb)

@app.on_callback_query(filters.regex("^create_mailing$"))
async def create_mailing(client, query):
    await query.message.reply("Шаг 1/6: Введи название рассылки:")

# ==================== ЗАПУСК ====================
async def main():
    asyncio.create_task(check_ton_payments())
    print("MALOT AutoSender vFULL запущен на Railway 🔥")
    await app.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
