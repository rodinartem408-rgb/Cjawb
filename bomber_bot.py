from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import asyncio
import sqlite3
import time
import os
import requests
from datetime import datetime

# ==================== ENV (Railway) ====================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
TON_WALLET = os.getenv("TON_WALLET")

PROMOCODES = {"Malot": 5, "Lala": 1000}

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

cursor.execute('''CREATE TABLE IF NOT EXISTS mailings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    text TEXT,
    interval INTEGER,
    target_chats TEXT,
    status TEXT DEFAULT 'stopped'
)''')
conn.commit()

# Глобальные клиенты аккаунтов
clients = {}

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
            url = f"https://tonapi.io/v2/accounts/{TON_WALLET}/transactions?limit=50"
            resp = requests.get(url).json()
            for tx in resp.get("transactions", []):
                if tx["in_msg"]["value"] >= 1000000000:  # 1 TON = 1e9 nanoTON
                    comment = tx["in_msg"].get("comment", "")
                    if comment.isdigit():
                        user_id = int(comment)
                        days = 30
                        new_end = int(time.time()) + (days * 86400)
                        cursor.execute("INSERT OR REPLACE INTO users (user_id, subscription_end) VALUES (?, ?)", 
                                     (user_id, new_end))
                        conn.commit()
                        try:
                            await app.send_message(user_id, f"✅ Оплата 1 TON получена!\nПодписка активирована на 30 дней.")
                        except: pass
        except: pass
        await asyncio.sleep(30)

# ==================== СТАРТ ====================
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user_id = message.from_user.id
    if not check_subscription(user_id) and user_id != ADMIN_ID:
        await message.reply("❌ Подписка не активна.\nОплати 1 TON или используй промокод Malot / Lala", reply_markup=main_menu())
        return
    await message.reply("👋 fe|AutoSender MALOT Edition", reply_markup=main_menu())

# ==================== ПОДПИСКА ====================
@app.on_callback_query(filters.regex("subscription"))
async def sub_menu(client, query):
    text = f"""💰 Подписка

Цена: 1 TON = 30 дней
Кошелёк: `{TON_WALLET}`

После оплаты в комментарии укажи свой Telegram ID: {query.from_user.id}

Промокоды:
• Malot → +5 дней
• Lala → +1000 дней"""

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Ввести промокод", callback_data="enter_promo")],
        [InlineKeyboardButton("Назад", callback_data="main")]
    ]))

# Промокод
@app.on_callback_query(filters.regex("enter_promo"))
async def enter_promo(client, query):
    await query.message.reply("Отправь промокод одним сообщением:")

@app.on_message(filters.text & ~filters.command)
async def promo_handler(client, message: Message):
    code = message.text.strip()
    user_id = message.from_user.id
    if code in PROMOCODES:
        days = PROMOCODES[code]
        new_end = int(time.time()) + (days * 86400)
        cursor.execute("INSERT OR REPLACE INTO users (user_id, subscription_end) VALUES (?, ?)", (user_id, new_end))
        conn.commit()
        await message.reply(f"✅ Промокод {code} активирован! +{days} дней.")
    else:
        await message.reply("❌ Промокод не найден.")

# ==================== АККАУНТЫ ====================
@app.on_callback_query(filters.regex("accounts"))
async def accounts_menu(client, query):
    user_id = query.from_user.id
    cursor.execute("SELECT phone FROM accounts WHERE user_id=?", (user_id,))
    accs = cursor.fetchall()
    text = "👤 Ваши аккаунты:\n\n"
    for a in accs:
        text += f"• {a[0]}\n"
    if not accs:
        text += "Пока нет аккаунтов."

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("+ Добавить аккаунт", callback_data="add_account")],
        [InlineKeyboardButton("Назад", callback_data="main")]
    ])
    await query.edit_message_text(text, reply_markup=kb)

@app.on_callback_query(filters.regex("add_account"))
async def add_account(client, query):
    await query.message.reply("Отправь номер телефона в формате +79123456789")

# Обработка номера
@app.on_message(filters.regex(r"^\+?\d{10,15}$"))
async def process_phone(client, message: Message):
    phone = message.text.strip()
    user_id = message.from_user.id
    session_name = f"session_{user_id}_{int(time.time())}"

    try:
        user_client = Client(session_name, api_id=API_ID, api_hash=API_HASH, phone_number=phone)
        await user_client.connect()
        code = await user_client.send_code(phone)
        await message.reply("Отправь код из SMS/Telegram:")
        
        # Здесь нужно обработать код (для простоты делаем через следующий шаг)
        # Полный код с обработкой кода и 2FA я добавлю в следующем сообщении, если скажешь "гоу дальше"

        cursor.execute("INSERT INTO accounts (user_id, session_name, phone) VALUES (?, ?, ?)", 
                      (user_id, session_name, phone))
        conn.commit()
        clients[user_id] = user_client
        await message.reply("✅ Аккаунт добавлен!")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

# ==================== РАССЫЛКИ ====================
@app.on_callback_query(filters.regex("my_mailings"))
async def my_mailings(client, query):
    await query.edit_message_text("📋 Мои рассылки\n\nПока пусто.\n\nНажми ниже чтобы создать новую.", 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("+ Создать рассылку", callback_data="create_mailing")],
            [InlineKeyboardButton("Назад", callback_data="main")]
        ]))

@app.on_callback_query(filters.regex("create_mailing"))
async def create_mailing(client, query):
    await query.message.reply("Шаг 1/6: Введи название рассылки:")

# ==================== ЗАПУСК ====================
async def main():
    asyncio.create_task(check_ton_payments())
    print("MALOT AutoSender v2 запущен на Railway 🔥")
    await app.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
