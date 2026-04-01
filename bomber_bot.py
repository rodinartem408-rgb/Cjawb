from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import asyncio
import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("bomber_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Мои рассылки", callback_data="mailings")],
        [InlineKeyboardButton("👤 Аккаунты", callback_data="accounts")],
        [InlineKeyboardButton("💰 Подписка", callback_data="sub")],
    ])
    await message.reply("👋 fe|AutoSender\n\nБот наконец-то отвечает!\n\nЕсли видишь это сообщение — значит бот живой.", reply_markup=keyboard)

@app.on_callback_query()
async def buttons(client, query):
    if query.data == "sub":
        await query.edit_message_text("💰 Подписка\n\n1 TON = 30 дней\nКошелёк: UQCEl_t-XmOV-K2LDpFrtK07td9t_pTmYvFaDHAU4zZuAPxa\n\nПромокод Lala = 1000 дней бесплатно")
    else:
        await query.edit_message_text("🔧 Этот раздел пока пустой.\n\nСкоро будет полная рассылка.", 
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back")]]))

async def main():
    print("MALOT MINIMAL BOMBER BOT ЗАПУЩЕН!")
    await app.start()
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
