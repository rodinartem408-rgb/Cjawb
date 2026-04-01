from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import sqlite3
import time
import os
import aiohttp

# ==================== НАСТРОЙКИ ====================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
TON_WALLET = os.getenv("TON_WALLET")

if not all([API_ID, API_HASH, BOT_TOKEN, TON_WALLET]):
    raise ValueError("❌ Не заданы ENV переменные!")

PROMOCODES = {"Malot": 5, "Lala": 1000}

# ==================== БД ====================
conn = sqlite3.connect("autosender.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    subscription_end INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS processed_tx (
    tx_hash TEXT PRIMARY KEY
)
""")

conn.commit()

# ==================== БОТ ====================
app = Client("feAutoSender", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ==================== UI ====================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Мои рассылки", callback_data="my_mailings")],
        [InlineKeyboardButton("👤 Аккаунты", callback_data="accounts")],
        [InlineKeyboardButton("💰 Подписка", callback_data="subscription")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ])

# ==================== ЛОГИКА ====================
def get_subscription(user_id):
    cursor.execute("SELECT subscription_end FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else 0

def add_days(user_id, days):
    now = int(time.time())
    current = get_subscription(user_id)

    if current < now:
        current = now

    new_end = current + days * 86400

    cursor.execute("""
    INSERT INTO users (user_id, subscription_end)
    VALUES (?, ?)
    ON CONFLICT(user_id) DO UPDATE SET subscription_end=excluded.subscription_end
    """, (user_id, new_end))

    conn.commit()
    return new_end

def has_subscription(user_id):
    return get_subscription(user_id) > int(time.time())

# ==================== TON ПРОВЕРКА ====================
async def check_ton():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                url = f"https://tonapi.io/v2/accounts/{TON_WALLET}/transactions?limit=20"
                async with session.get(url, timeout=10) as resp:
                    data = await resp.json()

                for tx in data.get("transactions", []):
                    tx_hash = tx.get("hash")

                    # Проверка дубля
                    cursor.execute("SELECT 1 FROM processed_tx WHERE tx_hash=?", (tx_hash,))
                    if cursor.fetchone():
                        continue

                    value = int(tx.get("in_msg", {}).get("value", 0))
                    comment = tx.get("in_msg", {}).get("comment", "")

                    # 1 TON
                    if value >= 1_000_000_000 and comment.isdigit():
                        user_id = int(comment)

                        add_days(user_id, 30)

                        cursor.execute("INSERT INTO processed_tx VALUES (?)", (tx_hash,))
                        conn.commit()

                        try:
                            await app.send_message(user_id, "✅ Оплата получена!\n+30 дней подписки.")
                        except:
                            pass

            except Exception as e:
                print("TON ERROR:", e)

            await asyncio.sleep(30)

# ==================== СТАРТ ====================
@app.on_message(filters.command("start"))
async def start(_, message):
    user_id = message.from_user.id

    if user_id != ADMIN_ID and not has_subscription(user_id):
        await message.reply(
            "❌ Подписка не активна.\n\n"
            "Оплати 1 TON или введи промокод.",
            reply_markup=main_menu()
        )
        return

    await message.reply("👋 fe|AutoSender работает!", reply_markup=main_menu())

# ==================== ПОДПИСКА ====================
@app.on_callback_query(filters.regex("subscription"))
async def subscription(_, query):
    text = f"""
💰 Подписка

1 TON = 30 дней

Кошелёк:
`{TON_WALLET}`

Комментарий:
{query.from_user.id}

Промокоды:
Malot (+5 дней)
Lala (+1000 дней)
"""

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ввести промокод", callback_data="promo")],
        [InlineKeyboardButton("Назад", callback_data="main")]
    ])

    await query.edit_message_text(text, reply_markup=kb)

@app.on_callback_query(filters.regex("promo"))
async def promo(_, query):
    await query.message.reply("Отправь промокод:")

# ==================== ПРОМОКОДЫ ====================
@app.on_message(filters.text & ~filters.command)
async def promo_handler(_, message):
    code = message.text.strip()
    user_id = message.from_user.id

    if code in PROMOCODES:
        days = PROMOCODES[code]
        add_days(user_id, days)

        await message.reply(f"✅ Промокод активирован!\n+{days} дней.")
    else:
        await message.reply("❌ Неизвестная команда.")

# ==================== КНОПКИ ====================
@app.on_callback_query()
async def callbacks(_, query):
    if query.data == "main":
        await query.edit_message_text("Главное меню", reply_markup=main_menu())
    else:
        await query.answer("В разработке", show_alert=False)

# ==================== ЗАПУСК ====================
async def main():
    asyncio.create_task(check_ton())

    print("🚀 Бот запущен")
    await app.start()
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
